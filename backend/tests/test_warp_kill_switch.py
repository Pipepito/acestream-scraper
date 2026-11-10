"""What the app reports and does about the WARP traffic guard."""
import asyncio
import os
import subprocess

import pytest

import warp_guard
from app.services import warp_service as module
from app.services.startup_service import StartupService
from app.services.warp_service import WarpService, kill_switch_state
from warp_prerequisites import WARP_DOCKER_GUIDANCE, WARP_GUARD_GUIDANCE, WarpStartupError
from warp_startup import Store, process_identity


@pytest.fixture
def boot(tmp_path, monkeypatch):
    store = Store(tmp_path, 'this-boot')
    store.initialize()
    monkeypatch.setenv('SUPERVISOR_RUN_DIR', str(tmp_path))
    monkeypatch.setenv('SCRAPER_WARP_BOOT', store.boot)
    monkeypatch.setenv('SCRAPER_WARP_GUARD', str(tmp_path / 'warp-guard.nft'))
    return store


def configure(store, generation='daemon-1', pid=None):
    pid = pid or os.getpid()
    store.write('daemon', pid=pid, identity=process_identity(pid), generation=generation)
    state = {key: value for key, value in store.state().items() if key != 'boot'}
    store.write('json', **{**state, 'phase': 'configured', 'generation': generation,
                          'heartbeat': __import__('time').monotonic()})


def test_kill_switch_is_reported_off_when_the_guard_does_not_apply(monkeypatch):
    monkeypatch.delenv('SCRAPER_WARP_GUARD', raising=False)
    assert kill_switch_state() == {'enabled': False, 'blocking': False}


def test_kill_switch_blocks_until_warp_is_configured(boot):
    assert kill_switch_state() == {'enabled': True, 'blocking': True}
    configure(boot)
    assert kill_switch_state() == {'enabled': True, 'blocking': False}


def test_kill_switch_blocks_again_when_the_daemon_is_gone(boot):
    exited = subprocess.Popen(['true'])
    exited.wait()
    configure(boot, pid=exited.pid)
    assert kill_switch_state() == {'enabled': True, 'blocking': True}


def test_kill_switch_state_is_unknown_rather_than_guessed(boot):
    boot.path('json').write_text('not json')
    assert kill_switch_state() == {'enabled': True, 'blocking': None}


def test_status_carries_the_kill_switch_even_when_warp_is_not_running(boot):
    service = WarpService()

    async def not_running():
        return False

    service.is_running = not_running
    status = asyncio.run(service.get_status())
    assert status['running'] is False
    assert status['kill_switch'] == {'enabled': True, 'blocking': True}


class Commands:
    def __init__(self, failing=()):
        self.calls, self.failing = [], failing

    async def __call__(self, args):
        self.calls.append(args[0])
        return (1, '', 'refused') if args[0] in self.failing else (0, 'Success', '')


def test_reconnect_blocks_direct_traffic_before_disconnecting(boot, monkeypatch):
    service = WarpService()
    commands = Commands()
    service._run_command = commands
    monkeypatch.setattr(warp_guard.Guard, 'arm', lambda self: commands.calls.append('arm'))

    async def status():
        return {'connected': True}

    service.get_status = status
    result = asyncio.run(service.reconnect())
    assert result['success'] is True
    assert commands.calls == ['arm', 'disconnect', 'connect']


def test_reconnect_without_the_guard_only_reconnects(monkeypatch):
    monkeypatch.delenv('SCRAPER_WARP_GUARD', raising=False)
    service = WarpService()
    commands = Commands()
    service._run_command = commands
    monkeypatch.setattr(warp_guard.Guard, 'arm', lambda self: pytest.fail('guard does not apply'))

    async def status():
        return {'connected': True}

    service.get_status = status
    assert asyncio.run(service.reconnect())['success'] is True
    assert commands.calls == ['disconnect', 'connect']


def test_reconnect_never_disconnects_when_it_cannot_block_first(boot, monkeypatch):
    service = WarpService()
    commands = Commands()
    service._run_command = commands

    def broken(self):
        raise warp_guard.GuardError('nft failed')

    monkeypatch.setattr(warp_guard.Guard, 'arm', broken)
    result = asyncio.run(service.reconnect())
    assert result['success'] is False
    assert commands.calls == []


def test_reconnect_reports_a_failed_disconnect_without_connecting(boot, monkeypatch):
    service = WarpService()
    commands = Commands(failing=('disconnect',))
    service._run_command = commands
    monkeypatch.setattr(warp_guard.Guard, 'arm', lambda self: None)
    result = asyncio.run(service.reconnect())
    assert result['success'] is False
    assert commands.calls == ['disconnect']


def test_reconnect_endpoint_maps_failures_like_connect(client, monkeypatch):
    async def failed():
        return {'success': False, 'message': 'refused', 'error': 'refused'}

    monkeypatch.setattr(module.warp_service, 'reconnect', failed)
    response = client.post('/api/v1/warp/reconnect')
    assert response.status_code == 400
    assert response.json()['error']['code'] == 'WARP_RECONNECT_FAILED'

    async def worked():
        return {'success': True, 'message': 'Reconnected to WARP successfully', 'status': {'connected': True}}

    monkeypatch.setattr(module.warp_service, 'reconnect', worked)
    response = client.post('/api/v1/warp/reconnect')
    assert response.status_code == 200
    assert response.json()['success'] is True


def test_guard_startup_failure_explains_the_way_out(monkeypatch):
    monkeypatch.setenv('SCRAPER_WARP_STARTUP_ERROR', 'guard')
    service = StartupService()
    service.fail(WarpStartupError())
    assert service.guidance == WARP_GUARD_GUIDANCE
    assert service.startup_dependency == 'warp'
    assert 'WARP_KILL_SWITCH=false' in WARP_GUARD_GUIDANCE
    assert 'paused' in WARP_GUARD_GUIDANCE


def test_container_guidance_names_the_selinux_case():
    # Issue #329: Podman on an SELinux host maps the device but denies access.
    assert '--security-opt label=disable' in WARP_DOCKER_GUIDANCE
    assert 'SELinux' in WARP_DOCKER_GUIDANCE
