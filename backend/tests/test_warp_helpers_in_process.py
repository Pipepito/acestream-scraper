"""The WARP runtime helpers, exercised in this process.

Their command lines are also covered through real subprocesses elsewhere; these
tests reach the same code where a failure can be pinned to one decision.
"""
import fcntl
import os
from pathlib import Path
import runpy
import signal
import subprocess
import sys
import time

import pytest

import warp_guard
import warp_startup
from warp_guard import Guard, GuardError
from warp_startup import Coordinator, StateError, Store, process_identity

UNAVAILABLE = 'WARP startup coordinator unavailable; network startup remains blocked.\n'
UNKNOWN_GUARD_ACTION = 'WARP traffic guard unavailable: Unknown guard action.\n'
# Never a real process in these tests: every call that could signal it is replaced.
RECORDED_PID = 4242


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv('SUPERVISOR_RUN_DIR', str(tmp_path))
    monkeypatch.setenv('SCRAPER_WARP_BOOT', 'this-boot')
    monkeypatch.delenv('SCRAPER_WARP_GUARD', raising=False)
    return Store(tmp_path, 'this-boot')


@pytest.fixture
def previous_handlers():
    """Coordinator.run replaces the process handlers; pytest keeps its own."""
    previous = {signum: signal.getsignal(signum) for signum in (signal.SIGTERM, signal.SIGINT)}
    yield previous
    for signum, handler in previous.items():
        if handler is not None:
            signal.signal(signum, handler)


def live_daemon(store, generation='daemon-1'):
    store.write('daemon', pid=os.getpid(), identity=process_identity(os.getpid()), generation=generation)


def write_state(store, **overrides):
    state = {'phase': 'configured', 'window': 'window-1', 'attempt': 3,
             'generation': 'daemon-1', 'heartbeat': time.monotonic()}
    store.write('json', **{**state, **overrides})


def record_kills(monkeypatch, *, identity='start-ticks', group=RECORDED_PID):
    """Stand in for /proc and the process table, absent on macOS."""
    kills = []
    monkeypatch.setattr(warp_startup, 'process_identity', lambda pid: identity)

    def getpgid(pid):
        if isinstance(group, BaseException):
            raise group
        return group

    monkeypatch.setattr(warp_startup.os, 'getpgid', getpgid)
    monkeypatch.setattr(warp_startup.os, 'killpg', lambda pid, signum: kills.append((pid, signum)))
    return kills


def lease_is_held(path) -> bool:
    fd = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return True
    finally:
        os.close(fd)
    return False


def finish(coordinator, fd):
    deadline = time.monotonic() + 3
    while coordinator.process is not None and time.monotonic() < deadline:
        coordinator.tick(fd)
        time.sleep(0.01)
    assert coordinator.process is None


def record_coordinators(monkeypatch):
    """Coordinators the command line would have run; none takes the lease."""
    started = []

    def run(coordinator):
        started.append(coordinator)

    monkeypatch.setattr(Coordinator, 'run', run)
    return started


def run_main(monkeypatch, *arguments):
    monkeypatch.setattr(sys, 'argv', ['warp_startup.py', *arguments])
    warp_startup.main()


# --- warp_startup: stored state -------------------------------------------


@pytest.mark.parametrize('pid', [1, 0, -1])
def test_init_and_process_groups_are_never_probed_as_a_daemon(monkeypatch, pid):
    probes = []
    monkeypatch.setattr(warp_startup.os, 'kill', lambda *arguments: probes.append(arguments))
    assert warp_startup.alive(pid) is False
    # Signal 0 to these would address init or a whole group, not one process.
    assert probes == []


@pytest.mark.parametrize('boot', ['', 'x' * 129])
def test_store_rejects_an_empty_or_oversized_boot_identity(tmp_path, boot):
    with pytest.raises(StateError, match='Invalid WARP boot identity'):
        Store(tmp_path, boot)
    assert Store(tmp_path, 'x' * 128).boot == 'x' * 128


@pytest.mark.parametrize('overrides', [
    {'phase': 'released'},
    {'window': 7},
    {'attempt': '3'},
    # A boolean is an int to Python, not to the attempt counter.
    {'attempt': True},
    {'heartbeat': 'now'},
    {'heartbeat': None},
])
def test_state_with_an_unknown_phase_or_wrong_types_is_refused(store, overrides):
    write_state(store)
    assert store.state()['phase'] == 'configured'
    write_state(store, **overrides)
    with pytest.raises(StateError, match='Invalid WARP startup state'):
        store.state()


def test_daemon_record_for_a_recycled_pid_is_not_the_daemon(store):
    live_daemon(store)
    assert store.daemon() == 'daemon-1'
    # The PID is alive, but it is not the process that was recorded.
    store.write('daemon', pid=os.getpid(), identity='another-process', generation='daemon-1')
    assert store.daemon() is None


@pytest.mark.parametrize('record', [
    None,
    {},
    {'generation': 'daemon-1'},
    {'pid': 'current'},
    {'pid': 'current', 'generation': 7},
    {'pid': '4242', 'generation': 'daemon-1'},
    {'pid': True, 'generation': 'daemon-1'},
])
def test_missing_or_malformed_daemon_record_means_no_daemon(store, record):
    store.root.mkdir(parents=True, exist_ok=True)
    if record is not None:
        if record.get('pid') == 'current':
            record = {**record, 'pid': os.getpid()}
        store.write('daemon', **record)
    assert store.daemon() is None
    write_state(store)
    assert store.configured() is False


# --- warp_startup: process control ----------------------------------------


@pytest.mark.parametrize('platform, raised', [('darwin', False), ('linux', True)])
def test_group_signal_permission_error_is_only_tolerated_on_macos(monkeypatch, platform, raised):
    calls = []

    def killpg(pid, signum):
        calls.append((pid, signum))
        raise PermissionError(1, 'Operation not permitted')

    monkeypatch.setattr(warp_startup.os, 'killpg', killpg)
    monkeypatch.setattr(sys, 'platform', platform)
    if raised:
        with pytest.raises(PermissionError):
            warp_startup.signal_group(RECORDED_PID, signal.SIGTERM)
    else:
        warp_startup.signal_group(RECORDED_PID, signal.SIGTERM)
    assert calls == [(RECORDED_PID, signal.SIGTERM)]


@pytest.mark.parametrize('platform', ['darwin', 'linux'])
def test_group_signal_ignores_a_group_that_already_exited(monkeypatch, platform):
    def killpg(pid, signum):
        raise ProcessLookupError(3, 'No such process')

    monkeypatch.setattr(warp_startup.os, 'killpg', killpg)
    monkeypatch.setattr(sys, 'platform', platform)
    warp_startup.signal_group(RECORDED_PID, signal.SIGKILL)


def test_disconnect_runs_the_warp_client_once_with_a_bounded_wait(monkeypatch):
    calls = []

    def run(argv, **options):
        calls.append((argv, options))
        return subprocess.CompletedProcess(argv, 1, b'', b'not connected')

    monkeypatch.setattr(warp_startup.subprocess, 'run', run)
    warp_startup.disconnect_warp()
    assert calls == [(['warp-cli', '--accept-tos', 'disconnect'],
                      {'capture_output': True, 'timeout': 10, 'check': False})]


@pytest.mark.parametrize('failure', [
    FileNotFoundError('warp-cli'),
    PermissionError('warp-cli'),
    subprocess.TimeoutExpired(['warp-cli'], 10),
])
def test_disconnect_failure_never_stops_the_coordinator(monkeypatch, failure):
    attempts = []

    def run(argv, **options):
        attempts.append(argv)
        raise failure

    monkeypatch.setattr(warp_startup.subprocess, 'run', run)
    warp_startup.disconnect_warp()
    assert len(attempts) == 1


def test_terminate_kills_and_reaps_a_group_that_ignores_sigterm():
    process = subprocess.Popen(['sh', '-c', 'trap "" TERM; echo ready; sleep 30'],
                               start_new_session=True, stdout=subprocess.PIPE)
    try:
        # The trap is in place before the first signal arrives.
        assert process.stdout.readline() == b'ready\n'
        started = time.monotonic()
        warp_startup.terminate(process)
        elapsed = time.monotonic() - started
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        process.stdout.close()
    assert process.returncode == -signal.SIGKILL
    # It was given the grace period before being killed.
    assert elapsed >= 2


def test_cleanup_kills_the_recorded_attempt_group(store, monkeypatch):
    kills = record_kills(monkeypatch)
    store.write('attempt', pid=RECORDED_PID, identity='start-ticks')
    warp_startup.cleanup_attempt(store)
    assert kills == [(RECORDED_PID, signal.SIGKILL)]


@pytest.mark.parametrize('attempt, identity, group', [
    # The PID now belongs to another process.
    ({'pid': RECORDED_PID, 'identity': 'start-ticks'}, 'later-ticks', RECORDED_PID),
    ({'pid': RECORDED_PID, 'identity': 'start-ticks'}, '', RECORDED_PID),
    # Not a group leader: its group belongs to someone else.
    ({'pid': RECORDED_PID, 'identity': 'start-ticks'}, 'start-ticks', 1),
    ({'pid': RECORDED_PID, 'identity': 'start-ticks'}, 'start-ticks', ProcessLookupError(3, 'gone')),
    # Recorded where the process could not be identified.
    ({'pid': RECORDED_PID, 'identity': ''}, '', RECORDED_PID),
    ({'pid': str(RECORDED_PID), 'identity': 'start-ticks'}, 'start-ticks', RECORDED_PID),
    ({'pid': RECORDED_PID}, 'start-ticks', RECORDED_PID),
    ({'identity': 'start-ticks'}, 'start-ticks', RECORDED_PID),
    (None, 'start-ticks', RECORDED_PID),
])
def test_cleanup_signals_nothing_it_cannot_prove_is_the_attempt(store, monkeypatch, attempt, identity, group):
    kills = record_kills(monkeypatch, identity=identity, group=group)
    store.root.mkdir(parents=True, exist_ok=True)
    if attempt is not None:
        store.write('attempt', **attempt)
    warp_startup.cleanup_attempt(store)
    assert kills == []


def test_cleanup_ignores_an_attempt_recorded_by_another_boot(store, monkeypatch):
    kills = record_kills(monkeypatch)
    Store(store.root, 'previous-boot').write('attempt', pid=RECORDED_PID, identity='start-ticks')
    warp_startup.cleanup_attempt(store)
    assert kills == []


def test_cleanup_survives_a_group_it_may_not_signal(store, monkeypatch):
    record_kills(monkeypatch)
    attempts = []

    def killpg(pid, signum):
        attempts.append((pid, signum))
        raise PermissionError(1, 'Operation not permitted')

    monkeypatch.setattr(warp_startup.os, 'killpg', killpg)
    store.write('attempt', pid=RECORDED_PID, identity='start-ticks')
    warp_startup.cleanup_attempt(store)
    assert attempts == [(RECORDED_PID, signal.SIGKILL)]


# --- warp_startup: coordinator --------------------------------------------


class FailingStandbyGuard:
    def __init__(self):
        self.calls = []

    def arm(self):
        self.calls.append('arm')

    def standby(self):
        self.calls.append('standby')
        raise GuardError('nft is unavailable or did not answer.')


def test_guard_that_cannot_stand_down_stops_the_coordinator(store, tmp_path):
    store.initialize()
    live_daemon(store)
    script = tmp_path / 'configure.sh'
    script.write_text('exit 0\n')
    guard = FailingStandbyGuard()
    coordinator = Coordinator(store, script, guard=guard)
    try:
        with (tmp_path / 'test-lock').open('w') as lock:
            coordinator.tick(lock.fileno())
            with pytest.raises(StateError, match='traffic guard is unavailable'):
                finish(coordinator, lock.fileno())
    finally:
        coordinator.stop_attempt()
    assert store.state()['phase'] == 'configured'
    assert guard.calls[0] == 'arm'
    assert guard.calls[-1] == 'standby'
    # The block was never reported as lifted.
    assert coordinator.blocking is True


def test_no_reconnect_request_means_no_reconnect(store, tmp_path):
    store.initialize()
    live_daemon(store)
    coordinator = Coordinator(store, tmp_path / 'configure.sh', guard=FailingStandbyGuard())
    assert coordinator.reconnect_requested('daemon-1') is False
    store.write('reconnect', generation='daemon-1', request='request-1')
    assert coordinator.reconnect_requested('daemon-1') is True
    # Consumed: the same request is never carried out twice.
    assert not store.path('reconnect').exists()
    assert coordinator.reconnect_requested('daemon-1') is False


def test_exhausted_window_stays_failed_until_a_retry_is_requested(store, tmp_path):
    store.initialize()
    live_daemon(store)
    marker = tmp_path / 'configured-once'
    script = tmp_path / 'configure.sh'
    script.write_text(f'touch "{marker}"\n')
    now = [time.monotonic()]

    def clock():
        return now[0]

    coordinator = Coordinator(store, script, clock=clock)
    window = store.state()['window']
    with (tmp_path / 'test-lock').open('w') as lock:
        now[0] += warp_startup.WINDOW_SECONDS
        coordinator.tick(lock.fileno())
        assert store.state()['phase'] == 'failed'
        now[0] += 30
        coordinator.tick(lock.fileno())
    state = store.state()
    assert state['phase'] == 'failed'
    assert state['window'] == window
    assert state['attempt'] == 0
    # Still alive: the heartbeat moves while it waits for the operator.
    assert state['heartbeat'] == now[0]
    assert coordinator.process is None
    assert not marker.exists()
    assert not store.path('attempt').exists()


def test_daemon_relaunch_does_not_reopen_an_exhausted_window(store, tmp_path):
    store.initialize()
    live_daemon(store)
    now = [time.monotonic()]

    def clock():
        return now[0]

    coordinator = Coordinator(store, tmp_path / 'configure.sh', clock=clock)
    with (tmp_path / 'test-lock').open('w') as lock:
        now[0] += warp_startup.WINDOW_SECONDS
        coordinator.tick(lock.fileno())
        live_daemon(store, 'daemon-2')
        now[0] += 1
        coordinator.tick(lock.fileno())
    assert coordinator.generation == 'daemon-2'
    assert store.state()['phase'] == 'failed'
    assert store.state()['attempt'] == 0
    assert coordinator.process is None


@pytest.mark.parametrize('signum', [signal.SIGTERM, signal.SIGINT])
def test_run_holds_the_lease_until_signalled_then_reaps_its_attempt(
        store, tmp_path, monkeypatch, previous_handlers, signum):
    store.initialize()
    coordinator = Coordinator(store, tmp_path / 'configure.sh')
    attempt = subprocess.Popen(['sleep', '30'], start_new_session=True)
    coordinator.process = attempt
    store.write('attempt', pid=attempt.pid, identity=process_identity(attempt.pid))
    sleeps = []
    ticks = []
    real_tick = coordinator.tick

    def tick(lock_fd):
        ticks.append(lock_fd)
        # The handler must end the loop; never spin forever if it does not.
        assert len(ticks) < 100
        real_tick(lock_fd)
        if len(ticks) > 1:
            return
        lock = store.path('lock')
        assert os.fstat(lock_fd).st_ino == lock.stat().st_ino
        assert lock.stat().st_mode & 0o077 == 0
        assert lease_is_held(lock)
        assert signal.getsignal(signum) is not previous_handlers[signum]
        os.kill(os.getpid(), signum)

    try:
        monkeypatch.setattr(coordinator, 'tick', tick)
        monkeypatch.setattr(warp_startup.time, 'sleep', sleeps.append)
        coordinator.run()
    finally:
        if attempt.poll() is None:
            attempt.kill()
            attempt.wait()
    assert coordinator.stopping is True
    assert len(ticks) >= 1
    assert sleeps[0] == 0.25
    assert store.state()['phase'] == 'starting'
    assert attempt.returncode == -signal.SIGTERM
    assert coordinator.process is None
    assert not store.path('attempt').exists()
    assert not lease_is_held(store.path('lock'))


def test_run_reaps_its_attempt_when_a_tick_fails(store, tmp_path, previous_handlers):
    store.initialize()
    coordinator = Coordinator(store, tmp_path / 'configure.sh')
    attempt = subprocess.Popen(['sleep', '30'], start_new_session=True)
    coordinator.process = attempt
    store.write('attempt', pid=attempt.pid, identity=process_identity(attempt.pid))

    def tick(lock_fd):
        raise StateError('WARP relaunch configuration failed.')

    coordinator.tick = tick
    try:
        with pytest.raises(StateError, match='relaunch'):
            coordinator.run()
    finally:
        if attempt.poll() is None:
            attempt.kill()
            attempt.wait()
    assert attempt.returncode == -signal.SIGTERM
    assert coordinator.process is None
    assert not store.path('attempt').exists()
    assert not lease_is_held(store.path('lock'))


def test_second_coordinator_cannot_run_while_the_lease_is_held(store, tmp_path, previous_handlers):
    store.initialize()
    coordinator = Coordinator(store, tmp_path / 'configure.sh')
    ticks = []
    coordinator.tick = ticks.append
    with store.path('lock').open('w') as holder:
        fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            coordinator.run()
    assert ticks == []
    # It gave up before taking over the process signals.
    for signum, handler in previous_handlers.items():
        assert signal.getsignal(signum) is handler


# --- warp_startup: command line -------------------------------------------


def test_identity_action_prints_a_fresh_boot_identity_without_any_environment(monkeypatch, capsys):
    monkeypatch.delenv('SUPERVISOR_RUN_DIR', raising=False)
    monkeypatch.delenv('SCRAPER_WARP_BOOT', raising=False)
    run_main(monkeypatch, 'identity')
    run_main(monkeypatch, 'identity')
    first, second = capsys.readouterr().out.split()
    for identity in (first, second):
        assert len(identity) == 32
        int(identity, 16)
    assert first != second


def test_init_action_starts_a_new_window_and_discards_earlier_release(store, monkeypatch):
    store.root.mkdir(parents=True, exist_ok=True)
    for name in ('released', 'command', 'daemon', 'attempt', 'reconnect'):
        store.write(name, released=True)
    run_main(monkeypatch, 'init')
    state = store.state()
    assert (state['phase'], state['attempt'], state['generation']) == ('starting', 0, None)
    assert len(state['window']) == 32
    assert not store.released()
    for name in ('released', 'command', 'daemon', 'attempt', 'reconnect'):
        assert not store.path(name).exists()


def test_daemon_action_records_the_process_under_a_new_generation(store, monkeypatch):
    run_main(monkeypatch, 'init')
    run_main(monkeypatch, 'daemon', str(os.getpid()))
    first = store.read('daemon')
    assert first['pid'] == os.getpid()
    assert first['identity'] == process_identity(os.getpid())
    assert len(first['generation']) == 32
    assert store.daemon() == first['generation']
    # A relaunch under the same PID is still a different daemon.
    run_main(monkeypatch, 'daemon', str(os.getpid()))
    assert store.read('daemon')['generation'] != first['generation']


def test_daemon_action_requires_a_numeric_pid(store, monkeypatch):
    run_main(monkeypatch, 'init')
    with pytest.raises(ValueError):
        run_main(monkeypatch, 'daemon', 'warp-svc')
    assert not store.path('daemon').exists()


@pytest.mark.parametrize('guarded', [False, True])
def test_run_action_starts_the_coordinator_with_the_guard_only_when_configured(
        store, tmp_path, monkeypatch, guarded):
    started = record_coordinators(monkeypatch)
    rules = tmp_path / 'warp-guard.nft'
    if guarded:
        monkeypatch.setenv('SCRAPER_WARP_GUARD', str(rules))
    run_main(monkeypatch, 'init')
    run_main(monkeypatch, 'run', str(tmp_path / 'warp-setup.sh'))
    assert len(started) == 1
    coordinator = started[0]
    assert coordinator.script == tmp_path / 'warp-setup.sh'
    assert coordinator.store.root == store.root
    assert coordinator.store.boot == store.boot
    if guarded:
        assert isinstance(coordinator.guard, Guard)
        assert coordinator.guard.rules == rules
    else:
        assert coordinator.guard is None


def test_run_action_refuses_to_start_without_this_boot_state(store, tmp_path, monkeypatch):
    started = record_coordinators(monkeypatch)
    store.root.mkdir(parents=True, exist_ok=True)
    with pytest.raises(StateError):
        run_main(monkeypatch, 'run', str(tmp_path / 'warp-setup.sh'))
    assert started == []


@pytest.mark.parametrize('overrides, daemon, code', [
    ({}, 'daemon-1', 0),
    ({'phase': 'configuring'}, 'daemon-1', 1),
    # The daemon was replaced after it was configured.
    ({}, 'daemon-2', 1),
    ({}, None, 1),
    ({'generation': None}, None, 1),
    # A coordinator that stopped publishing no longer vouches for anything.
    ({'heartbeat': -11.0}, 'daemon-1', 1),
])
def test_configured_action_answers_through_its_exit_status(store, monkeypatch, overrides, daemon, code):
    store.root.mkdir(parents=True, exist_ok=True)
    if 'heartbeat' in overrides:
        overrides = {**overrides, 'heartbeat': time.monotonic() + overrides['heartbeat']}
    write_state(store, **overrides)
    if daemon is not None:
        live_daemon(store, daemon)
    with pytest.raises(SystemExit) as stopped:
        run_main(monkeypatch, 'configured')
    assert stopped.value.code == code


def test_release_action_admits_startup_only_while_configured(store, monkeypatch):
    store.root.mkdir(parents=True, exist_ok=True)
    write_state(store, phase='configuring')
    live_daemon(store)
    with pytest.raises(StateError, match='changed before startup release'):
        run_main(monkeypatch, 'release')
    assert not store.path('released').exists()
    write_state(store)
    run_main(monkeypatch, 'release')
    assert store.read('released') == {'boot': 'this-boot', 'released': True}
    assert store.released()


def test_cleanup_action_kills_the_attempt_left_by_a_lost_coordinator(store, monkeypatch):
    kills = record_kills(monkeypatch)
    store.root.mkdir(parents=True, exist_ok=True)
    run_main(monkeypatch, 'cleanup')
    assert kills == []
    store.write('attempt', pid=RECORDED_PID, identity='start-ticks')
    run_main(monkeypatch, 'cleanup')
    assert kills == [(RECORDED_PID, signal.SIGKILL)]


def test_lost_action_marks_the_window_failed_and_keeps_its_identity(store, monkeypatch):
    store.root.mkdir(parents=True, exist_ok=True)
    write_state(store, phase='configuring', heartbeat=time.monotonic() - 100)
    before = time.monotonic()
    run_main(monkeypatch, 'lost')
    state = store.state()
    assert before <= state.pop('heartbeat') <= time.monotonic()
    assert state == {'boot': 'this-boot', 'phase': 'failed', 'window': 'window-1',
                     'attempt': 3, 'generation': 'daemon-1'}
    # The operator can now ask for a new window, and the entrypoint sees it.
    store.retry()
    with pytest.raises(SystemExit) as stopped:
        run_main(monkeypatch, 'retry-pending')
    assert stopped.value.code == 0


@pytest.mark.parametrize('phase, window, code', [
    ('failed', 'window-1', 0),
    # Asked for a window that has since been replaced.
    ('failed', 'window-0', 1),
    ('backoff', 'window-1', 1),
    ('configured', 'window-1', 1),
])
def test_retry_pending_action_accepts_only_a_request_for_the_failed_window(
        store, monkeypatch, phase, window, code):
    store.root.mkdir(parents=True, exist_ok=True)
    write_state(store, phase=phase)
    store.write('command', window=window, request='request-1')
    with pytest.raises(SystemExit) as stopped:
        run_main(monkeypatch, 'retry-pending')
    assert stopped.value.code == code


def test_retry_pending_action_without_a_request_is_an_error_not_a_yes(store, monkeypatch):
    store.root.mkdir(parents=True, exist_ok=True)
    write_state(store, phase='failed')
    with pytest.raises(StateError):
        run_main(monkeypatch, 'retry-pending')


def test_unknown_coordinator_action_is_refused(store, monkeypatch):
    with pytest.raises(StateError, match='Unknown WARP coordinator action'):
        run_main(monkeypatch, 'restart')
    assert not store.path('json').exists()


def run_startup_script(monkeypatch, *arguments):
    script = Path(warp_startup.__file__)
    monkeypatch.setattr(sys, 'argv', [str(script), *arguments])
    runpy.run_path(str(script), run_name='__main__')


@pytest.mark.parametrize('arguments, variables', [
    # KeyError: the entrypoint did not provide the run directory or boot.
    (['init'], {}),
    (['init'], {'SUPERVISOR_RUN_DIR': 'run'}),
    # StateError
    (['restart'], {'SUPERVISOR_RUN_DIR': 'run', 'SCRAPER_WARP_BOOT': 'this-boot'}),
    (['release'], {'SUPERVISOR_RUN_DIR': 'run', 'SCRAPER_WARP_BOOT': 'this-boot'}),
    # ValueError
    (['daemon', 'warp-svc'], {'SUPERVISOR_RUN_DIR': 'run', 'SCRAPER_WARP_BOOT': 'this-boot'}),
    # OSError: the run directory does not exist.
    (['daemon', '4242'], {'SUPERVISOR_RUN_DIR': 'missing/run', 'SCRAPER_WARP_BOOT': 'this-boot'}),
])
def test_script_failures_exit_nonzero_with_one_fixed_message(tmp_path, monkeypatch, capsys, arguments, variables):
    (tmp_path / 'run').mkdir()
    monkeypatch.delenv('SUPERVISOR_RUN_DIR', raising=False)
    monkeypatch.delenv('SCRAPER_WARP_BOOT', raising=False)
    monkeypatch.delenv('SCRAPER_WARP_GUARD', raising=False)
    for name, value in variables.items():
        monkeypatch.setenv(name, str(tmp_path / value) if name == 'SUPERVISOR_RUN_DIR' else value)
    with pytest.raises(SystemExit) as stopped:
        run_startup_script(monkeypatch, *arguments)
    assert stopped.value.code == 1
    captured = capsys.readouterr()
    assert captured.err == UNAVAILABLE
    assert captured.out == ''


def test_script_passes_answers_through_without_the_failure_message(store, monkeypatch, capsys):
    run_startup_script(monkeypatch, 'init')
    assert store.state()['phase'] == 'starting'
    with pytest.raises(SystemExit) as stopped:
        run_startup_script(monkeypatch, 'configured')
    assert stopped.value.code == 1
    write_state(store)
    live_daemon(store)
    with pytest.raises(SystemExit) as stopped:
        run_startup_script(monkeypatch, 'configured')
    assert stopped.value.code == 0
    assert capsys.readouterr().err == ''


# --- warp_guard: the daemon's group ---------------------------------------


class ChildExit(BaseException):
    """Stands in for os._exit, which would end the test process."""


def forked_child(monkeypatch, *, denied=None):
    """Run group_available as the forked child, recording instead of changing IDs."""
    calls = []

    def change(name):
        def call(value):
            calls.append((name, value))
            if name == denied:
                raise PermissionError(1, 'Operation not permitted')
        return call

    def leave(code):
        raise ChildExit(code)

    def unexpected(*arguments):
        pytest.fail('the child never waits for a process')

    monkeypatch.setattr(warp_guard.os, 'fork', lambda: 0)
    monkeypatch.setattr(warp_guard.os, 'setgroups', change('setgroups'))
    monkeypatch.setattr(warp_guard.os, 'setgid', change('setgid'))
    monkeypatch.setattr(warp_guard.os, '_exit', leave)
    monkeypatch.setattr(warp_guard.os, 'waitpid', unexpected)
    with pytest.raises(ChildExit) as left:
        warp_guard.group_available()
    return calls, left.value.args[0]


def forked_parent(monkeypatch, status):
    """Run group_available as the parent of a child that ended with status."""
    waits = []

    def unexpected(*arguments):
        pytest.fail('the parent keeps its own groups')

    def waitpid(pid, options):
        waits.append((pid, options))
        return pid, status

    monkeypatch.setattr(warp_guard.os, 'fork', lambda: RECORDED_PID)
    monkeypatch.setattr(warp_guard.os, 'waitpid', waitpid)
    monkeypatch.setattr(warp_guard.os, 'setgroups', unexpected)
    monkeypatch.setattr(warp_guard.os, 'setgid', unexpected)
    return waits


def test_group_probe_child_drops_extra_groups_then_enters_the_daemon_group(monkeypatch):
    calls, code = forked_child(monkeypatch)
    assert calls == [('setgroups', []), ('setgid', warp_guard.GROUP_ID)]
    assert code == 0


def test_group_probe_child_reports_groups_it_may_not_drop(monkeypatch):
    calls, code = forked_child(monkeypatch, denied='setgroups')
    assert calls == [('setgroups', [])]
    assert code == 1


def test_group_probe_child_reports_a_group_it_may_not_enter(monkeypatch):
    calls, code = forked_child(monkeypatch, denied='setgid')
    assert calls == [('setgroups', []), ('setgid', warp_guard.GROUP_ID)]
    assert code == 1


def test_group_probe_accepts_a_child_that_entered_the_group(monkeypatch):
    waits = forked_parent(monkeypatch, 0)
    warp_guard.group_available()
    assert waits == [(RECORDED_PID, 0)]


@pytest.mark.parametrize('status', [1 << 8, signal.SIGKILL])
def test_group_probe_names_the_missing_capability_when_the_child_failed(monkeypatch, status):
    waits = forked_parent(monkeypatch, status)
    with pytest.raises(GuardError, match='SETGID capability is required'):
        warp_guard.group_available()
    # The child is always reaped, also when it failed.
    assert waits == [(RECORDED_PID, 0)]


def test_daemon_is_never_started_outside_its_group(monkeypatch):
    steps = []

    def setgid(gid):
        steps.append(('gid', gid))
        raise PermissionError(1, 'Operation not permitted')

    monkeypatch.setattr(warp_guard.os, 'setgroups', lambda groups: steps.append(('groups', groups)))
    monkeypatch.setattr(warp_guard.os, 'setgid', setgid)
    monkeypatch.setattr(warp_guard.os, 'execvp', lambda program, argv: steps.append((program, argv)))
    with pytest.raises(PermissionError):
        warp_guard.run_daemon('warp-svc --accept-tos')
    assert steps == [('groups', []), ('gid', warp_guard.GROUP_ID)]


def test_daemon_drops_groups_enters_its_group_then_becomes_the_command(monkeypatch):
    steps = []
    monkeypatch.setattr(warp_guard.os, 'setgroups', lambda groups: steps.append(('groups', groups)))
    monkeypatch.setattr(warp_guard.os, 'setgid', lambda gid: steps.append(('gid', gid)))
    monkeypatch.setattr(warp_guard.os, 'execvp', lambda program, argv: steps.append((program, argv)))
    warp_guard.run_daemon('warp-svc --accept-tos | tee "/var/log/warp.log"')
    # One argument: the launch line reaches the login shell unsplit.
    assert steps == [('groups', []), ('gid', warp_guard.GROUP_ID),
                     ('bash', ['bash', '-lc', 'warp-svc --accept-tos | tee "/var/log/warp.log"'])]


# --- warp_guard: rules and state ------------------------------------------


@pytest.mark.parametrize('stderr', ['Error: Operation not permitted', 'netlink: Error: cache initialization failed', ''])
def test_active_is_an_error_when_nft_fails_for_another_reason_than_a_missing_table(tmp_path, stderr):
    def run(argv, **options):
        return subprocess.CompletedProcess(argv, 1, '', stderr)

    # Not "inactive": the caller must not report traffic as unblocked.
    with pytest.raises(GuardError, match='could not report the guard state'):
        Guard(tmp_path / 'rules', run=run).active()


def test_install_reports_rules_it_cannot_write_and_does_not_arm(tmp_path):
    def run(argv, **options):
        pytest.fail('nft must not run without the rules')

    rules = tmp_path / 'missing' / 'warp-guard.nft'
    with pytest.raises(GuardError, match='guard rules could not be written'):
        Guard(rules, run=run).install(check_group=lambda: None)
    assert not rules.parent.exists()


# --- warp_guard: command line ---------------------------------------------


@pytest.fixture
def nft(monkeypatch):
    """What the guard would hand to nft; nothing reaches the kernel."""
    calls = []

    def record(self, source, text=None):
        calls.append((source, text))

    monkeypatch.setattr(Guard, '_nft', record)
    return calls


@pytest.fixture
def no_warp_environment(monkeypatch):
    for name in ('ENABLE_WARP', 'WARP_ENABLE_NAT', 'WARP_DNS_ONLY', 'WARP_KILL_SWITCH'):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize('variables, code', [
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true'}, 0),
    ({'ENABLE_WARP': 'TRUE', 'WARP_ENABLE_NAT': '1', 'WARP_KILL_SWITCH': 'on'}, 0),
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true', 'WARP_KILL_SWITCH': 'false'}, 1),
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true', 'WARP_DNS_ONLY': 'true'}, 1),
    ({'ENABLE_WARP': 'true'}, 1),
    ({}, 1),
])
def test_enabled_action_reads_the_process_environment(monkeypatch, no_warp_environment, capsys, variables, code):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    assert warp_guard.main(['warp_guard.py', 'enabled']) == code
    assert capsys.readouterr().err == ''


def test_daemon_action_hands_the_launch_line_to_the_group_change(monkeypatch):
    launched = []
    monkeypatch.setattr(warp_guard, 'run_daemon', launched.append)
    assert warp_guard.main(['warp_guard.py', 'daemon', 'warp-svc --accept-tos']) == 0
    assert launched == ['warp-svc --accept-tos']


def test_daemon_action_reports_a_group_it_could_not_enter_without_system_detail(monkeypatch, capsys):
    steps = []

    def setgid(gid):
        raise PermissionError(1, 'Operation not permitted')

    monkeypatch.setattr(warp_guard.os, 'setgroups', lambda groups: None)
    monkeypatch.setattr(warp_guard.os, 'setgid', setgid)
    monkeypatch.setattr(warp_guard.os, 'execvp', lambda program, argv: steps.append(program))
    assert warp_guard.main(['warp_guard.py', 'daemon', 'warp-svc']) == 1
    assert capsys.readouterr().err == 'WARP traffic guard unavailable: The daemon group could not be entered.\n'
    assert steps == []


def test_install_action_checks_the_group_writes_the_rules_then_arms(tmp_path, monkeypatch, nft):
    waits = forked_parent(monkeypatch, 0)
    rules = tmp_path / 'warp-guard.nft'
    assert warp_guard.main(['warp_guard.py', 'install', str(rules)]) == 0
    assert waits == [(RECORDED_PID, 0)]
    assert rules.read_text() == warp_guard.armed_rules()
    assert nft == [(str(rules), None)]


def test_install_action_stops_before_writing_when_the_group_is_unavailable(tmp_path, monkeypatch, nft, capsys):
    forked_parent(monkeypatch, 1 << 8)
    rules = tmp_path / 'warp-guard.nft'
    assert warp_guard.main(['warp_guard.py', 'install', str(rules)]) == 1
    assert capsys.readouterr().err == (
        'WARP traffic guard unavailable: The container cannot change group; '
        'the default SETGID capability is required.\n')
    assert not rules.exists()
    assert nft == []


def test_arm_action_loads_the_installed_rules(tmp_path, nft):
    rules = tmp_path / 'warp-guard.nft'
    assert warp_guard.main(['warp_guard.py', 'arm', str(rules)]) == 0
    assert nft == [(str(rules), None)]


def test_standby_action_removes_the_table_without_a_rules_file(nft):
    assert warp_guard.main(['warp_guard.py', 'standby']) == 0
    assert nft == [('-', warp_guard.REMOVAL)]


@pytest.mark.parametrize('action', ['arm', 'standby'])
def test_guard_failure_detail_reaches_the_operator(tmp_path, monkeypatch, capsys, action):
    def refuse(self, source, text=None):
        raise GuardError('nftables rejected the guard rules; the host kernel may lack support.')

    monkeypatch.setattr(Guard, '_nft', refuse)
    argv = ['warp_guard.py', action] + ([str(tmp_path / 'warp-guard.nft')] if action == 'arm' else [])
    assert warp_guard.main(argv) == 1
    assert capsys.readouterr().err == (
        'WARP traffic guard unavailable: nftables rejected the guard rules; '
        'the host kernel may lack support.\n')


@pytest.mark.parametrize('arguments', [
    [],
    ['disable'],
    ['daemon'],
    ['daemon', 'warp-svc', '--accept-tos'],
    ['install'],
    ['install', 'rules.nft', 'extra'],
    ['arm'],
    ['arm', 'rules.nft', 'extra'],
    ['standby', 'rules.nft'],
])
def test_unknown_guard_actions_and_argument_counts_change_nothing(monkeypatch, nft, capsys, arguments):
    launched = []
    monkeypatch.setattr(warp_guard, 'run_daemon', launched.append)
    assert warp_guard.main(['warp_guard.py', *arguments]) == 1
    assert capsys.readouterr().err == UNKNOWN_GUARD_ACTION
    assert launched == []
    assert nft == []


def test_guard_without_any_arguments_is_an_unknown_action(capsys):
    assert warp_guard.main([]) == 1
    assert capsys.readouterr().err == UNKNOWN_GUARD_ACTION


@pytest.mark.parametrize('variables, code', [
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true'}, 0),
    ({'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true', 'WARP_KILL_SWITCH': 'false'}, 1),
    ({}, 1),
])
def test_guard_script_exits_with_whether_the_guard_applies(monkeypatch, no_warp_environment, variables, code):
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    script = Path(warp_guard.__file__)
    monkeypatch.setattr(sys, 'argv', [str(script), 'enabled'])
    with pytest.raises(SystemExit) as stopped:
        runpy.run_path(str(script), run_name='__main__')
    assert stopped.value.code == code
