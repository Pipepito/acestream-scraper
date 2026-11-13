"""Private, per-boot WARP startup barrier and single configuration owner.

Stdlib only: also used by the entrypoint before application dependencies load.
No catalogue state, network requests or wall-clock deadlines belong here.
"""
from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path
import secrets
import signal
import stat
import subprocess
import sys
import tempfile
import time

import warp_guard

WINDOW_SECONDS = 600
PHASES = {'starting', 'configuring', 'backoff', 'failed', 'configured'}


class StateError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd) as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > 8192:
                raise ValueError
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (OSError, ValueError, UnicodeError) as exc:
        raise StateError('WARP startup state is unavailable.') from exc


def write_json(path: Path, value: dict) -> None:
    if path.is_symlink():
        raise StateError('WARP startup state must be a regular file.')
    fd, temporary = tempfile.mkstemp(prefix='.warp-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, allow_nan=False)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def process_identity(pid: int) -> str:
    """Linux start ticks prevent signalling a recycled PID; no guessing."""
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
        fields = text[text.rindex(')') + 2:].split()
        return fields[19] if fields[0] != 'Z' else ''
    except (OSError, ValueError, IndexError):
        return ''


def alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
        return not Path('/proc').is_dir() or bool(process_identity(pid))
    except OSError:
        return False


class Store:
    def __init__(self, root: Path, boot: str):
        if not boot or len(boot) > 128:
            raise StateError('Invalid WARP boot identity.')
        self.root, self.boot = root, boot

    @classmethod
    def environment(cls):
        return cls(Path(os.environ['SUPERVISOR_RUN_DIR']), os.environ['SCRAPER_WARP_BOOT'])

    def path(self, name: str) -> Path:
        return self.root / ('warp-startup.' + name)

    def write(self, name: str, **values):
        write_json(self.path(name), {'boot': self.boot, **values})

    def read(self, name: str) -> dict:
        value = read_json(self.path(name))
        if value.get('boot') != self.boot:
            raise StateError('WARP startup state belongs to another boot.')
        return value

    def initialize(self):
        self.root.mkdir(parents=True, exist_ok=True)
        # Old state cannot release this boot, even with a persisted run directory.
        for name in ('released', 'command', 'daemon', 'attempt', 'reconnect'):
            self.path(name).unlink(missing_ok=True)
        self.write('json', phase='starting', window=secrets.token_hex(16),
                   attempt=0, generation=None, heartbeat=time.monotonic())

    def state(self) -> dict:
        value = self.read('json')
        if (value.get('phase') not in PHASES or not isinstance(value.get('window'), str)
                or type(value.get('attempt')) is not int
                or type(value.get('heartbeat')) not in (int, float)):
            raise StateError('Invalid WARP startup state.')
        return value

    def released(self) -> bool:
        try:
            return self.read('released').get('released') is True
        except StateError:
            return False

    def daemon(self) -> str | None:
        try:
            value = self.read('daemon')
            pid = value['pid']
            if type(pid) is not int or not alive(pid):
                return None
            if value.get('identity') and value['identity'] != process_identity(pid):
                return None
            generation = value['generation']
            return generation if isinstance(generation, str) else None
        except (StateError, KeyError):
            return None

    def configured(self) -> bool:
        state = self.state()
        return (state['phase'] == 'configured'
                and time.monotonic() - state['heartbeat'] < 10
                and state.get('generation') is not None
                and state['generation'] == self.daemon())

    def release(self):
        if not self.configured():
            raise StateError('WARP changed before startup release.')
        self.write('released', released=True)

    def reconnect(self) -> str:
        """Ask the coordinator to reconnect; it alone holds the guard meanwhile."""
        state = self.state()
        if not self.released() or not self.configured():
            raise StateError('WARP is not connected under this boot.')
        request = secrets.token_hex(16)
        self.write('reconnect', generation=state['generation'], request=request)
        return request

    def retry(self) -> str:
        state = self.state()
        if self.released() or state['phase'] != 'failed':
            raise StateError('WARP recovery is not available.')
        # The HTTP recovery nonce serializes requests; the window also protects
        # this mailbox against a delayed request after a newer attempt started.
        request = secrets.token_hex(16)
        self.write('command', window=state['window'], request=request)
        return request


def signal_group(pid: int, signum: int) -> None:
    try:
        os.killpg(pid, signum)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS answers EPERM, not ESRCH, for a group left with only unreaped
        # members. Linux, the deployment target, keeps the real error.
        if sys.platform != 'darwin':
            raise


def disconnect_warp() -> None:
    """Best effort: configuration reconnects whatever this leaves behind."""
    try:
        subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], capture_output=True, timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        pass


def terminate(process: subprocess.Popen) -> None:
    """Reap the whole attempt group, including descendants after shell exit."""
    signal_group(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    signal_group(process.pid, signal.SIGKILL)
    process.wait()


def cleanup_attempt(store: Store):
    """Called only after the owning coordinator exited, before retry/shutdown."""
    try:
        value = store.read('attempt')
        pid, identity = value['pid'], value['identity']
        if (type(pid) is int and identity and identity == process_identity(pid)
                and os.getpgid(pid) == pid):
            os.killpg(pid, signal.SIGKILL)
    except (StateError, KeyError, OSError):
        pass


class Coordinator:
    def __init__(self, store: Store, script: Path, *, clock=time.monotonic,
                 window_seconds=WINDOW_SECONDS, guard=None, disconnect=disconnect_warp):
        self.store, self.script, self.clock = store, script, clock
        self.disconnect = disconnect
        # None: the traffic guard does not apply to this WARP mode.
        self.guard, self.blocking, self.guard_refresh = guard, None, 0.0
        self.window_seconds = window_seconds
        self.stopping = False
        self.process = None
        self.generation = None
        self.state = store.state()
        self.deadline = clock() + window_seconds
        self.next_attempt = clock()
        self.failures = 0

    def publish(self, phase=None, **values):
        self.state.update(values, heartbeat=self.clock())
        if phase is not None:
            self.state['phase'] = phase
        self.store.write('json', **{key: value for key, value in self.state.items() if key != 'boot'})

    def stop_attempt(self):
        if self.process is not None:
            terminate(self.process)
            self.process = None
            self.store.path('attempt').unlink(missing_ok=True)

    def block(self, now: float, *, force=False):
        """Hold the guard; it expires by itself unless this keeps running."""
        if self.guard is None or not (force or self.blocking is not True or now >= self.guard_refresh):
            return
        try:
            self.guard.arm()
        except warp_guard.GuardError as exc:
            raise StateError('WARP traffic guard is unavailable.') from exc
        self.blocking, self.guard_refresh = True, now + warp_guard.REFRESH_SECONDS

    def sync_guard(self):
        if self.guard is None:
            return
        # WARP's own firewall takes over only for a configured, living daemon.
        if (self.state['phase'] == 'configured' and self.generation is not None
                and self.generation == self.store.daemon()):
            if self.blocking is not False:
                try:
                    self.guard.standby()
                except warp_guard.GuardError as exc:
                    raise StateError('WARP traffic guard is unavailable.') from exc
                self.blocking = False
        else:
            self.block(self.clock())

    def reconnect_requested(self, generation) -> bool:
        try:
            request = self.store.read('reconnect')
        except StateError:
            return False
        self.store.path('reconnect').unlink(missing_ok=True)
        # A request for an earlier daemon is discarded, never replayed.
        return self.guard is not None and request.get('generation') == generation

    def tick(self, lock_fd: int):
        try:
            self.step(lock_fd)
        except StateError:
            # The entrypoint ends the container next: start a full hold for it.
            self.block(self.clock(), force=True)
            raise
        self.sync_guard()

    def step(self, lock_fd: int):
        now = self.clock()
        released = self.store.released()
        generation = self.store.daemon()
        if generation != self.generation:
            # Before anything slower: the previous daemon's firewall may be gone.
            self.block(now, force=True)
            self.stop_attempt()
            self.generation = generation
            # Before initial release, daemon restarts never extend the budget.
            if released:
                self.deadline = now + self.window_seconds
            if self.state['phase'] != 'failed':
                self.next_attempt = now
                self.publish('starting', generation=generation)

        if self.state['phase'] == 'failed':
            try:
                request = self.store.read('command')
            except StateError:
                request = {}
            if not released and request.get('window') == self.state['window'] and request.get('request'):
                self.store.path('command').unlink(missing_ok=True)
                self.deadline = now + self.window_seconds
                self.next_attempt, self.failures = now, 0
                self.publish('starting', window=request['request'], attempt=0, generation=generation)
            else:
                self.publish()
                return

        if self.state['phase'] == 'configured':
            if not (released and generation and self.reconnect_requested(generation)):
                self.publish()
                return
            # Block before disconnecting, and keep blocking until this daemon
            # is configured again: a reconnect never becomes a disconnect.
            self.block(now, force=True)
            self.disconnect()
            self.deadline = now + self.window_seconds
            self.next_attempt, self.failures = now, 0
            self.publish('starting', generation=generation)
        if now >= self.deadline:
            self.stop_attempt()
            self.publish('failed')
            if released:
                raise StateError('WARP relaunch configuration failed.')
            return
        if self.process is not None:
            result = self.process.poll()
            if result is not None:
                self.stop_attempt()
                if result == 0 and generation and generation == self.store.daemon():
                    self.publish('configured', generation=generation)
                elif released and self.guard is None:
                    # Without the traffic guard, only ending the container
                    # stops network services from using a direct connection.
                    raise StateError('WARP relaunch configuration failed.')
                else:
                    delay = (5, 10, 20, 30)[min(self.failures, 3)]
                    self.failures += 1
                    self.next_attempt = now + delay
                    self.publish('backoff')
            else:
                self.publish()
            return
        if generation and now >= self.next_attempt:
            self.process = subprocess.Popen(['bash', str(self.script), 'configure'],
                start_new_session=True, pass_fds=(lock_fd,))
            self.store.write('attempt', pid=self.process.pid, identity=process_identity(self.process.pid))
            self.publish('configuring', attempt=self.state['attempt'] + 1, generation=generation)
        else:
            self.publish()

    def run(self):
        # Children inherit the lease: even abrupt coordinator death cannot
        # admit a second configure while an old configuration child survives.
        fd = os.open(self.store.path('lock'), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, 'w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            signal.signal(signal.SIGTERM, lambda *_: setattr(self, 'stopping', True))
            signal.signal(signal.SIGINT, lambda *_: setattr(self, 'stopping', True))
            try:
                while not self.stopping:
                    self.tick(lock.fileno())
                    time.sleep(0.25)
            finally:
                self.stop_attempt()


def main():
    action = sys.argv[1]
    if action == 'identity':
        print(secrets.token_hex(16))
        return
    store = Store.environment()
    if action == 'init':
        store.initialize()
    elif action == 'daemon':
        pid = int(sys.argv[2])
        store.write('daemon', pid=pid, identity=process_identity(pid), generation=secrets.token_hex(16))
    elif action == 'run':
        rules = os.environ.get('SCRAPER_WARP_GUARD')
        Coordinator(store, Path(sys.argv[2]), guard=warp_guard.Guard(Path(rules)) if rules else None).run()
    elif action == 'configured':
        sys.exit(0 if store.configured() else 1)
    elif action == 'release':
        store.release()
    elif action == 'cleanup':
        cleanup_attempt(store)
    elif action == 'lost':
        state = store.state()
        store.write('json', **{**{k: v for k, v in state.items() if k != 'boot'},
                              'phase': 'failed', 'heartbeat': time.monotonic()})
    elif action == 'retry-pending':
        state, command = store.state(), store.read('command')
        sys.exit(0 if state['phase'] == 'failed' and command.get('window') == state['window'] else 1)
    else:
        raise StateError('Unknown WARP coordinator action.')


if __name__ == '__main__':
    try:
        main()
    except (StateError, OSError, ValueError, KeyError):
        print('WARP startup coordinator unavailable; network startup remains blocked.', file=sys.stderr)
        sys.exit(1)
