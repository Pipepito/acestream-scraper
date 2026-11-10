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


@pytest.mark.parametrize('manual', [False, True])
def test_entrypoint_recovers_without_replacing_web_process_or_double_launch(tmp_path, manual):
    root = Path(__file__).parents[2]
    stage = tmp_path / 'stage'
    (stage / 'backend').mkdir(parents=True)
    shutil.copy(root / 'entrypoint.sh', stage)
    shutil.copy(root / 'backend/capture_logs.py', stage / 'backend')
    # Exercise the real coordinator with a short injected window for exhaustion.
    # No test-only configuration is added to the production deployment surface.
    (stage / 'backend/warp_startup.py').write_text(
        f'import sys\nsys.path.insert(0, {str(root / "backend")!r})\nimport warp_startup as w\n'
        'original = w.Coordinator.__init__\n'
        f'def init(self, *args, **kwargs):\n    original(self, *args, window_seconds={2 if manual else 600}, **kwargs)\n'
        'w.Coordinator.__init__ = init\nw.main()\n')
    (stage / 'warp-setup.sh').write_text(
        'if [ "$1" = prepare ]; then exit 0; fi\n'
        f'echo configure >> {shlex.quote(str(tmp_path / "calls"))}\n'
        f'test -f {shlex.quote(str(tmp_path / "connected"))}\n')
    worker = tmp_path / 'worker.py'
    worker.write_text(
        'import os, sys, time\nfrom pathlib import Path\n'
        f'root = Path({str(tmp_path)!r})\n'
        'name = sys.argv[1]\n'
        "with (root / (name + '.launches')).open('a') as f: f.write(str(os.getpid()) + '\\n')\n"
        "if name == 'web': (root / 'boot').write_text(os.environ['SCRAPER_WARP_BOOT'])\n"
        'while True: time.sleep(0.1)\n')
    command = f'exec {shlex.quote(sys.executable)} {shlex.quote(str(worker))}'
    env = {**os.environ, 'SCRAPER_RUNTIME_LOADED': '1',
           'LOG_DIR': str(tmp_path / 'logs'), 'LOGROTATE_DIR': str(tmp_path / 'rotate'),
           'SUPERVISOR_RUN_DIR': str(tmp_path / 'run'),
           'ENABLE_WARP': 'true', 'WARP_ENABLE_NAT': 'true', 'WARP_START_COMMAND': command + ' warp',
           'ENABLE_ACESTREAM_ENGINE': 'true', 'IMAGE_HAS_ACESTREAM': 'true',
           'ACESTREAM_START_COMMAND': command + ' engine', 'ACESTREAM_GLUETUN_PORT_FILE': '',
           'ENABLE_ACESTREAM_CHECK_ENGINE': 'false', 'ACE_CHECK_ENGINE_URL': '',
           'ENABLE_ACEXY': 'false', 'ENABLE_ZERONET': 'false', 'ENABLE_IPFS': 'false', 'ENABLE_TOR': 'false'}

    def until(predicate, timeout=12):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            assert process.poll() is None, (tmp_path / 'console').read_text()
            if predicate():
                return
            time.sleep(0.05)
        pytest.fail((tmp_path / 'console').read_text())

    with (tmp_path / 'console').open('w') as output:
        process = subprocess.Popen(['bash', str(stage / 'entrypoint.sh'), sys.executable, str(worker), 'web'],
                                   env=env, stdout=output, stderr=output, start_new_session=True)
        try:
            until(lambda: (tmp_path / 'boot').exists() and (tmp_path / 'calls').exists())
            store = Store(tmp_path / 'run', (tmp_path / 'boot').read_text())
            until(lambda: store.state()['phase'] == ('failed' if manual else 'backoff'))
            web_pid = (tmp_path / 'web.launches').read_text()
            assert not (tmp_path / 'engine.launches').exists()
            assert not store.released()
            assert (tmp_path / 'warp.launches').read_text().count('\n') == 1
            (tmp_path / 'connected').touch()
            if manual:
                store.retry()
            until(store.released)
            assert (tmp_path / 'web.launches').read_text() == web_pid
            assert (tmp_path / 'engine.launches').read_text().count('\n') == 1
            assert (tmp_path / 'warp.launches').read_text().count('\n') == 1
            time.sleep(1.1)
            assert (tmp_path / 'engine.launches').read_text().count('\n') == 1
        finally:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                terminate(process)
