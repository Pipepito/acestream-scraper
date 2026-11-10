"""Recover real configuration children without weakening the startup barrier."""
import asyncio
import os
from pathlib import Path
import signal
import shutil
import shlex
import subprocess
import sys
import time

import pytest

from app.services.startup_service import StartupService
from app.api.endpoints.startup import status as startup_status
from types import SimpleNamespace
from app.services.warp_startup_service import wait_for_warp
from warp_prerequisites import WarpStartupError
import warp_guard
from warp_startup import Coordinator, StateError, Store, process_identity, read_json, terminate, write_json


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    store = Store(tmp_path, 'this-boot')
    store.initialize()
    store.write('daemon', pid=os.getpid(), identity=process_identity(os.getpid()), generation='daemon-1')
    monkeypatch.setenv('SUPERVISOR_RUN_DIR', str(tmp_path))
    monkeypatch.setenv('SCRAPER_WARP_BOOT', store.boot)
    monkeypatch.delenv('SCRAPER_WARP_STARTUP_ERROR', raising=False)
    script = tmp_path / 'configure.sh'
    script.write_text('exit 1\n')
    now = [time.monotonic()]
    coordinator = Coordinator(store, script, clock=lambda: now[0])
    with (tmp_path / 'test-lock').open('w') as lock:
        yield store, coordinator, now, lock.fileno()
    coordinator.stop_attempt()


def finish(coordinator, fd):
    deadline = time.monotonic() + 3
    while coordinator.process is not None and time.monotonic() < deadline:
        coordinator.tick(fd)
        time.sleep(0.01)
    assert coordinator.process is None


def test_retry_backoff_exhaustion_and_new_manual_window(runtime):
    store, coordinator, now, fd = runtime
    start = now[0]
    for attempt, delay in enumerate((5, 10, 20, 30, 30), 1):
        coordinator.tick(fd)
        finish(coordinator, fd)
        assert store.state()['phase'] == 'backoff'
        assert store.state()['attempt'] == attempt
        now[0] += delay - 0.1
        coordinator.tick(fd)
        assert coordinator.process is None
        now[0] += 0.1
    now[0] = start + 600
    coordinator.tick(fd)
    assert store.state()['phase'] == 'failed'
    request = store.retry()
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    assert store.state()['phase'] == 'configured'
    assert store.state()['window'] == request
    assert store.state()['attempt'] == 1
    with pytest.raises(StateError):
        store.retry()


@pytest.mark.parametrize('wall_clock', [0, 99999999999])
def test_wall_clock_changes_never_affect_budget(runtime, monkeypatch, wall_clock):
    store, coordinator, now, fd = runtime
    monkeypatch.setattr(time, 'time', lambda: wall_clock)
    now[0] += 599
    coordinator.tick(fd)
    finish(coordinator, fd)
    assert store.state()['phase'] == 'backoff'
    now[0] += 1
    coordinator.tick(fd)
    assert store.state()['phase'] == 'failed'


def test_stale_retry_cannot_restart_an_exhausted_window(runtime):
    store, coordinator, now, fd = runtime
    now[0] += 600
    coordinator.tick(fd)
    store.write('command', window='old-window', request='late-request')
    coordinator.tick(fd)
    assert store.state()['phase'] == 'failed'
    assert coordinator.process is None


def test_daemon_replacement_discards_inflight_success_without_extending_budget(runtime):
    store, coordinator, now, fd = runtime
    coordinator.script.write_text('sleep 30\n')
    coordinator.tick(fd)
    previous = coordinator.process
    deadline = coordinator.deadline
    store.write('daemon', pid=os.getpid(), identity=process_identity(os.getpid()), generation='daemon-2')
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    assert previous.poll() is not None
    assert coordinator.deadline == deadline
    finish(coordinator, fd)
    assert store.state()['generation'] == 'daemon-2'
    store.release()
    assert store.released()
    # A stale release cannot admit a different container boot.
    assert not Store(store.root, 'next-boot').released()


def test_hung_attempt_is_terminated_at_deadline(runtime):
    store, coordinator, now, fd = runtime
    coordinator.script.write_text('sleep 30\n')
    coordinator.tick(fd)
    process = coordinator.process
    now[0] += 600
    coordinator.tick(fd)
    assert process.poll() is not None
    assert store.state()['phase'] == 'failed'
    assert not store.path('attempt').exists()


def test_release_rechecks_current_daemon(runtime):
    store, coordinator, _, fd = runtime
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.write('daemon', pid=os.getpid(), generation='replacement')
    with pytest.raises(StateError):
        store.release()
    assert not store.released()


def test_post_start_relaunch_configuration_failure_remains_fatal(runtime):
    store, coordinator, _, fd = runtime
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    store.write('daemon', pid=os.getpid(), generation='replacement')
    coordinator.script.write_text('exit 1\n')
    coordinator.tick(fd)
    with pytest.raises(StateError, match='relaunch'):
        finish(coordinator, fd)


class RecordingGuard:
    def __init__(self):
        self.calls = []

    def arm(self):
        self.calls.append('arm')

    def standby(self):
        self.calls.append('standby')


@pytest.fixture
def guarded(runtime):
    store, coordinator, now, fd = runtime
    guard = RecordingGuard()
    coordinator = Coordinator(store, coordinator.script, clock=lambda: now[0], guard=guard)
    yield store, coordinator, now, fd, guard
    coordinator.stop_attempt()


def test_guard_blocks_until_the_current_daemon_is_configured(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.tick(fd)
    finish(coordinator, fd)
    assert store.state()['phase'] == 'backoff'
    assert set(guard.calls) == {'arm'}
    # The block is refreshed on a schedule, not by every quarter-second tick.
    guard.calls.clear()
    coordinator.tick(fd)
    coordinator.tick(fd)
    assert guard.calls == []
    # Written before the tick that starts the next attempt: no race with its shell.
    coordinator.script.write_text('exit 0\n')
    now[0] += 5
    coordinator.tick(fd)
    assert guard.calls == ['arm']
    finish(coordinator, fd)
    assert store.state()['phase'] == 'configured'
    assert guard.calls[-1] == 'standby'
    # WARP's own firewall is now in charge: no further changes while it runs.
    guard.calls.clear()
    now[0] += 60
    coordinator.tick(fd)
    assert guard.calls == []


def test_guard_blocks_in_the_same_tick_that_loses_the_daemon(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    assert guard.calls[-1] == 'standby'
    # A clean daemon exit removes WARP's firewall and leaves no process behind.
    exited = subprocess.Popen(['true'])
    exited.wait()
    store.write('daemon', pid=exited.pid, generation='gone')
    guard.calls.clear()
    coordinator.tick(fd)
    assert guard.calls == ['arm']
    assert store.state()['phase'] == 'starting'
    # A relaunched daemon stays blocked until its own configuration succeeds.
    store.write('daemon', pid=os.getpid(), identity=process_identity(os.getpid()), generation='daemon-2')
    coordinator.tick(fd)
    assert 'standby' not in guard.calls
    finish(coordinator, fd)
    assert store.state()['phase'] == 'configured'
    assert guard.calls[-1] == 'standby'


def test_post_start_configuration_failure_retries_behind_the_guard(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    store.write('daemon', pid=os.getpid(), identity=process_identity(os.getpid()), generation='replacement')
    coordinator.script.write_text('exit 1\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    # Direct traffic is blocked, so a slow network no longer has to end the container.
    assert store.state()['phase'] == 'backoff'
    assert guard.calls[-1] == 'arm'
    coordinator.script.write_text('exit 0\n')
    now[0] += 5
    coordinator.tick(fd)
    finish(coordinator, fd)
    assert store.state()['phase'] == 'configured'
    assert guard.calls[-1] == 'standby'


def test_post_start_recovery_window_still_ends_the_container(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    exited = subprocess.Popen(['true'])
    exited.wait()
    store.write('daemon', pid=exited.pid, generation='gone')
    coordinator.tick(fd)
    now[0] += 599
    coordinator.tick(fd)
    assert store.state()['phase'] == 'starting'
    now[0] += 1
    guard.calls.clear()
    with pytest.raises(StateError, match='relaunch'):
        coordinator.tick(fd)
    # The entrypoint stops the container; it stays blocked while that happens.
    assert guard.calls == ['arm']


def test_reconnect_request_is_carried_out_by_the_coordinator_behind_the_guard(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.disconnect = lambda: guard.calls.append('disconnect')
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    guard.calls.clear()
    store.reconnect()
    coordinator.tick(fd)
    # Blocked first, then disconnected: never the other way round.
    assert guard.calls[:2] == ['arm', 'disconnect']
    assert store.state()['phase'] != 'configured'
    assert not store.path('reconnect').exists()
    finish(coordinator, fd)
    assert store.state()['phase'] == 'configured'
    assert guard.calls[-1] == 'standby'
    assert guard.calls.count('disconnect') == 1


def test_failed_reconnect_stays_blocked_and_keeps_trying(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.disconnect = lambda: None
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    coordinator.script.write_text('exit 1\n')
    store.reconnect()
    coordinator.tick(fd)
    finish(coordinator, fd)
    assert store.state()['phase'] == 'backoff'
    guard.calls.clear()
    # Far longer than one hold: the block is refreshed, never left to lapse.
    for _ in range(12):
        now[0] += 5
        coordinator.tick(fd)
        finish(coordinator, fd)
    assert 'standby' not in guard.calls
    assert guard.calls.count('arm') >= 12


def test_reconnect_is_only_accepted_for_the_connected_daemon_of_this_boot(guarded):
    store, coordinator, now, fd, guard = guarded
    coordinator.disconnect = lambda: guard.calls.append('disconnect')
    with pytest.raises(StateError):
        store.reconnect()  # not configured, not released
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    with pytest.raises(StateError):
        store.reconnect()  # configured, but network services are not released
    store.release()
    # A request left behind for an earlier daemon is discarded, not replayed.
    store.write('reconnect', generation='an-earlier-daemon', request='late')
    guard.calls.clear()
    coordinator.tick(fd)
    assert guard.calls == []
    assert store.state()['phase'] == 'configured'
    assert not store.path('reconnect').exists()


def test_reconnect_requests_are_ignored_without_the_guard(runtime):
    store, coordinator, _, fd = runtime
    coordinator.disconnect = lambda: pytest.fail('the app reconnects by itself without the guard')
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    store.reconnect()
    coordinator.tick(fd)
    assert store.state()['phase'] == 'configured'


def test_guard_failure_stops_the_coordinator_instead_of_running_unprotected(guarded):
    store, coordinator, now, fd, guard = guarded

    def broken():
        raise warp_guard.GuardError('nft failed')

    guard.arm = broken
    with pytest.raises(StateError, match='guard'):
        coordinator.tick(fd)


@pytest.mark.parametrize('value', ['not json', '[]', '{"boot":"another-boot"}', 'x' * 8193])
def test_state_is_bounded_and_fail_closed(runtime, value):
    store, _, _, _ = runtime
    store.path('json').write_text(value)
    with pytest.raises(StateError):
        store.state()


def test_state_rejects_symlinks(runtime):
    store, _, _, _ = runtime
    original = store.path('json').read_text()
    store.path('json').unlink()
    target = store.root / 'target'
    target.write_text(original)
    store.path('json').symlink_to(target)
    with pytest.raises(StateError):
        store.state()
    with pytest.raises(StateError):
        write_json(store.path('json'), {})


def test_restricted_startup_status_does_not_disclose_warp_dependency(monkeypatch):
    from app.services.startup_service import startup_service
    monkeypatch.setattr(startup_service, 'startup_dependency', 'warp')
    monkeypatch.setattr(startup_service, 'status', 'failed')
    request = SimpleNamespace(state=SimpleNamespace(access_mode='accounts', access_user={'administrator': False}))
    response = startup_status(request)
    assert response.startup_dependency is None
    assert response.recovery_token == ''
    assert response.phase == 'Application status'
    assert response.server_time.tzinfo is not None


@pytest.mark.asyncio
async def test_backend_waits_for_entrypoint_release_and_cancels_on_shutdown(runtime):
    store, coordinator, _, fd = runtime
    service, stopping = StartupService(), asyncio.Event()
    waiter = asyncio.create_task(wait_for_warp(service, stopping))
    await asyncio.sleep(0.02)
    assert not waiter.done()
    assert service.startup_dependency == 'warp'
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    await asyncio.sleep(0.02)
    assert not waiter.done(), 'Configured is not the entrypoint release'
    store.release()
    assert await asyncio.wait_for(waiter, 2)
    assert service.startup_dependency is None
    store.path('released').unlink()
    waiter = asyncio.create_task(wait_for_warp(service, stopping))
    await asyncio.sleep(0.02)
    stopping.set()
    assert not await asyncio.wait_for(waiter, 1)


@pytest.mark.asyncio
async def test_backend_retry_waits_for_new_window_and_preserves_database_retry(runtime):
    store, coordinator, now, fd = runtime
    now[0] += 600
    coordinator.tick(fd)
    service, stopping = StartupService(), asyncio.Event()
    with pytest.raises(WarpStartupError):
        await wait_for_warp(service, stopping)
    waiter = asyncio.create_task(wait_for_warp(service, stopping, retry=True))
    for _ in range(100):
        if store.path('command').exists():
            break
        await asyncio.sleep(0.01)
    coordinator.script.write_text('exit 0\n')
    coordinator.tick(fd)
    finish(coordinator, fd)
    store.release()
    assert await asyncio.wait_for(waiter, 2)
    assert await wait_for_warp(service, stopping, retry=True)
    assert not store.path('command').exists()


@pytest.mark.asyncio
async def test_missing_or_stale_coordinator_never_releases_backend(runtime):
    store, _, _, _ = runtime
    store.path('json').unlink()
    with pytest.raises(WarpStartupError):
        await wait_for_warp(StartupService(), asyncio.Event())


def test_coordinator_termination_reaps_real_attempt(runtime):
    store, coordinator, _, _ = runtime
    coordinator.script.write_text('sleep 60\n')
    process = subprocess.Popen([sys.executable, str(Path(__file__).parents[1] / 'warp_startup.py'),
                                'run', str(coordinator.script)], start_new_session=True)
    try:
        deadline = time.monotonic() + 5
        while not store.path('attempt').exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        attempt = read_json(store.path('attempt'))['pid']
        process.send_signal(signal.SIGTERM)
        assert process.wait(timeout=5) == 0
        with pytest.raises(ProcessLookupError):
            os.kill(attempt, 0)
        assert not store.path('attempt').exists()
    finally:
        terminate(process)


class EntrypointHarness:
    """Run the real entrypoint and coordinator around recording stand-ins."""

    def __init__(self, tmp_path, *, window_seconds=600, environment=None, group_available=True):
        self.tmp = tmp_path
        root = Path(__file__).parents[2]
        stage = tmp_path / 'stage'
        (stage / 'backend').mkdir(parents=True)
        (tmp_path / 'bin').mkdir()
        shutil.copy(root / 'entrypoint.sh', stage)
        shutil.copy(root / 'backend/capture_logs.py', stage / 'backend')
        backend = str(root / 'backend')
        # Exercise the real coordinator with a short injected window for exhaustion.
        # No test-only configuration is added to the production deployment surface.
        (stage / 'backend/warp_startup.py').write_text(
            f'import sys\nsys.path.insert(0, {backend!r})\nimport warp_startup as w\n'
            'original = w.Coordinator.__init__\n'
            f'def init(self, *args, **kwargs):\n    original(self, *args, window_seconds={window_seconds}, **kwargs)\n'
            f'if sys.argv[1] == "run": open({str(tmp_path / "coordinator.pid")!r}, "w").write(str(__import__("os").getpid()))\n'
            'w.Coordinator.__init__ = init\nw.main()\n')
        # Changing group needs root; everything else in the guard is real.
        (stage / 'backend/warp_guard.py').write_text(
            f'import os, sys\nsys.path.insert(0, {backend!r})\nimport warp_guard as g\n'
            f'def group_available():\n    if not {group_available!r}: raise g.GuardError("no group")\n'
            'def run_daemon(command):\n'
            f'    open({str(tmp_path / "events")!r}, "a").write("daemon-group\\n")\n'
            '    os.execvp("bash", ["bash", "-lc", command])\n'
            'g.Guard.install.__kwdefaults__["check_group"] = group_available\n'
            'g.run_daemon = run_daemon\nsys.exit(g.main(sys.argv))\n')
        nft = tmp_path / 'bin/nft'
        nft.write_text(
            '#!/usr/bin/env bash\n'
            f'if [ "$2" = - ]; then echo standby >> {shlex.quote(str(tmp_path / "events"))}; cat > /dev/null\n'
            f'else echo "arm $(basename "$2")" >> {shlex.quote(str(tmp_path / "events"))}; test -r "$2"; fi\n')
        nft.chmod(0o755)
        (stage / 'warp-setup.sh').write_text(
            'if [ "$1" = prepare ]; then exit 0; fi\n'
            f'echo configure >> {shlex.quote(str(tmp_path / "calls"))}\n'
            f'test -f {shlex.quote(str(tmp_path / "connected"))}\n')
        worker = tmp_path / 'worker.py'
        worker.write_text(
            'import os, signal, sys, time\nfrom pathlib import Path\n'
            f'root = Path({str(tmp_path)!r})\n'
            'name = sys.argv[1]\n'
            "with (root / (name + '.launches')).open('a') as f: f.write(str(os.getpid()) + '\\n')\n"
            "with (root / 'events').open('a') as f: f.write('launch ' + name + '\\n')\n"
            "if name == 'web': (root / 'boot').write_text(os.environ.get('SCRAPER_WARP_BOOT', ''))\n"
            "if name == 'web': (root / 'web.env').write_text('|'.join(os.environ.get(key, '') for key in ('SCRAPER_WARP_STARTUP_ERROR', 'SCRAPER_WARP_GUARD', 'SCRAPER_WARP_GUARD_UNAVAILABLE')))\n"
            # Like warp-svc: SIGTERM is a clean exit.
            "signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))\n"
            'while True: time.sleep(0.1)\n')
        self.worker = worker
        command = f'exec {shlex.quote(sys.executable)} {shlex.quote(str(worker))}'
        self.env = {**os.environ, 'SCRAPER_RUNTIME_LOADED': '1',
                    'PATH': f'{tmp_path / "bin"}{os.pathsep}{os.environ["PATH"]}',
                    'LOG_DIR': str(tmp_path / 'logs'), 'LOGROTATE_DIR': str(tmp_path / 'rotate'),
                    'SUPERVISOR_RUN_DIR': str(tmp_path / 'run'), 'SUPERVISED_RESTART_DELAY_SECONDS': '1',
                    'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true', 'WARP_START_COMMAND': command + ' warp',
                    'ENABLE_ACESTREAM_ENGINE': 'true', 'IMAGE_HAS_ACESTREAM': 'true',
                    'ACESTREAM_START_COMMAND': command + ' engine', 'ACESTREAM_GLUETUN_PORT_FILE': '',
                    'ENABLE_ACESTREAM_CHECK_ENGINE': 'false', 'ACE_CHECK_ENGINE_URL': '',
                    'ENABLE_ACEXY': 'false', 'ENABLE_ZERONET': 'false', 'ENABLE_IPFS': 'false', 'ENABLE_TOR': 'false',
                    **(environment or {})}
        for name in ('WARP_KILL_SWITCH', 'WARP_DNS_ONLY'):
            if name not in (environment or {}):
                self.env.pop(name, None)
        self.stage = stage
        self.process = None

    def __enter__(self):
        self.output = (self.tmp / 'console').open('w')
        self.process = subprocess.Popen(
            ['bash', str(self.stage / 'entrypoint.sh'), sys.executable, str(self.worker), 'web'],
            env=self.env, stdout=self.output, stderr=self.output, start_new_session=True)
        return self

    def __exit__(self, *_):
        self.stop()
        self.output.close()

    def stop(self):
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                terminate(self.process)

    def console(self):
        return (self.tmp / 'console').read_text()

    def until(self, predicate, timeout=20, alive=True):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if alive:
                assert self.process.poll() is None, self.console()
            if predicate():
                return
            time.sleep(0.05)
        pytest.fail(self.console())

    def launches(self, name):
        path = self.tmp / (name + '.launches')
        return path.read_text().split() if path.exists() else []

    def events(self):
        path = self.tmp / 'events'
        return path.read_text().splitlines() if path.exists() else []

    def store(self):
        self.until(lambda: (self.tmp / 'boot').exists())
        return Store(self.tmp / 'run', (self.tmp / 'boot').read_text())

    def ready(self):
        (self.tmp / 'connected').touch()
        store = self.store()
        self.until(store.released)
        self.until(lambda: len(self.launches('engine')) == 1)
        return store


# A first launch that exits within the fast-exit window ends the container by
# contract. These tests stop a daemon that counts as established.
ESTABLISHED = {'SUPERVISED_FAST_EXIT_WINDOW': '0'}


@pytest.mark.parametrize('manual', [False, True])
def test_entrypoint_recovers_without_replacing_web_process_or_double_launch(tmp_path, manual):
    with EntrypointHarness(tmp_path, window_seconds=2 if manual else 600) as run:
        run.until(lambda: (tmp_path / 'calls').exists())
        store = run.store()
        run.until(lambda: store.state()['phase'] == ('failed' if manual else 'backoff'))
        web_pid = run.launches('web')
        assert not run.launches('engine')
        assert not store.released()
        assert len(run.launches('warp')) == 1
        (tmp_path / 'connected').touch()
        if manual:
            store.retry()
        run.until(store.released)
        run.until(lambda: len(run.launches('engine')) == 1)
        assert run.launches('web') == web_pid
        assert len(run.launches('warp')) == 1
        time.sleep(1.1)
        assert len(run.launches('engine')) == 1


def test_entrypoint_blocks_direct_traffic_before_warp_and_until_it_is_configured(tmp_path):
    with EntrypointHarness(tmp_path) as run:
        store = run.store()
        run.until(lambda: store.state()['phase'] == 'backoff')
        events = run.events()
        # Armed before the daemon exists; the daemon runs in the exempt group.
        assert events.index('arm warp-guard.nft') < events.index('daemon-group') < events.index('launch warp')
        assert 'standby' not in events
        assert (tmp_path / 'web.env').read_text() == '|' + str(tmp_path / 'run/warp-guard.nft') + '|'
        run.ready()
        run.until(lambda: 'standby' in run.events())
        events = run.events()
        # WARP's own firewall is in charge from here on.
        assert 'arm warp-guard.nft' not in events[events.index('standby'):]


def test_entrypoint_relaunches_warp_after_a_clean_exit_behind_the_guard(tmp_path):
    """Issue #329: a clean daemon exit used to end supervision and leak traffic."""
    with EntrypointHarness(tmp_path, environment=ESTABLISHED) as run:
        store = run.ready()
        run.until(lambda: 'standby' in run.events())
        before = len(run.events())
        web_pid, engine_pid = run.launches('web'), run.launches('engine')
        os.kill(int(run.launches('warp')[0]), signal.SIGTERM)
        run.until(lambda: len(run.launches('warp')) == 2)
        after = run.events()[before:]
        # Blocked again before the replacement daemon starts.
        assert after.index('arm warp-guard.nft') < after.index('launch warp')
        run.until(lambda: store.configured() and run.events()[-1] == 'standby')
        assert 'WARP exited with status 0; restarting' in run.console()
        assert 'not restarting' not in run.console()
        # Nothing else is replaced: only the daemon came back.
        assert run.launches('web') == web_pid
        assert run.launches('engine') == engine_pid


def test_entrypoint_blocks_during_shutdown_and_leaves_no_rules_behind(tmp_path):
    with EntrypointHarness(tmp_path) as run:
        run.ready()
        run.until(lambda: 'standby' in run.events())
        before = len(run.events())
        run.stop()
        after = run.events()[before:]
        # WARP stops before the engines do: block first, remove the table last.
        assert after[0] == 'arm warp-guard.nft'
        assert after[-1] == 'standby'
        # Stopping the container is not a WARP failure.
        assert 'WARP relaunch configuration failed' not in run.console()
        assert run.process.returncode == 0


def test_entrypoint_continues_without_the_guard_on_a_host_that_cannot_support_it(tmp_path):
    """An upgrade must not stop WARP on a host without nftables or SETGID."""
    with EntrypointHarness(tmp_path, group_available=False, environment=ESTABLISHED) as run:
        run.ready()
        # No startup error; the app is told so it can say WARP runs unguarded.
        assert (tmp_path / 'web.env').read_text() == '||1'
        assert 'WARP kill switch is unavailable on this host' in run.console()
        # The previous launch and supervision are kept, including the relaunch.
        assert 'daemon-group' not in run.events()
        os.kill(int(run.launches('warp')[0]), signal.SIGTERM)
        run.until(lambda: len(run.launches('warp')) == 2)
        run.stop()
        assert not [event for event in run.events() if not event.startswith('launch ')]


def test_entrypoint_without_the_guard_keeps_the_previous_daemon_launch(tmp_path):
    with EntrypointHarness(tmp_path, environment={**ESTABLISHED, 'WARP_KILL_SWITCH': 'false'}) as run:
        run.ready()
        # Turned off on purpose: nothing to warn about.
        assert (tmp_path / 'web.env').read_text() == '||'
        os.kill(int(run.launches('warp')[0]), signal.SIGTERM)
        # The clean-exit relaunch does not depend on the guard.
        run.until(lambda: len(run.launches('warp')) == 2)
        run.stop()
        assert not [event for event in run.events() if not event.startswith('launch ')]


def test_entrypoint_gives_up_loudly_when_warp_keeps_exiting_cleanly(tmp_path):
    with EntrypointHarness(tmp_path, environment={'WARP_START_COMMAND': 'exit 0'}) as run:
        run.until(lambda: run.process.poll() is not None, alive=False)
        assert run.process.returncode != 0
        assert 'WARP startup command exited with status 0' in run.console()


def test_entrypoint_keeps_blocking_when_the_coordinator_is_lost_before_release(tmp_path):
    """Nothing else refreshes the block; it must not lapse while WARP is unconfigured."""
    with EntrypointHarness(tmp_path) as run:
        store = run.store()
        run.until(lambda: store.state()['phase'] == 'backoff')
        os.kill(int((tmp_path / 'coordinator.pid').read_text()), signal.SIGKILL)
        run.until(lambda: store.state()['phase'] == 'failed')
        before = len(run.events())
        run.until(lambda: run.events()[before:].count('arm warp-guard.nft') >= 2, timeout=25)
        assert not run.launches('engine')
        assert not store.released()
