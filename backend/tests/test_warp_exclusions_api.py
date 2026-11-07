"""Desired/active WARP exclusions, persistence, concurrency and safe argv."""
import json
import subprocess
import time

import pytest

from runtime_config import ConfigConflict, ConfigError
from warp_exclusions import WarpExclusions, normalize_hosts, read_state


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.delenv('WARP_EXCLUDE_HOSTS', raising=False)
    svc = WarpExclusions(tmp_path / 'warp-exclusions.json')
    active = {'outside.example.com'}
    calls = []

    def command(args, deadline):
        calls.append(args)
        if args[-1] == 'list':
            return json.dumps({'mode': 'exclude', 'hosts': [{'value': host, 'description': 'CLI exclude'} for host in sorted(active)]})
        if args[-2] == 'add':
            active.add(args[-1])
        elif args[-2] == 'remove':
            active.remove(args[-1])
        return ''

    monkeypatch.setattr(svc, 'command', command)
    svc.test_active, svc.test_calls = active, calls
    return svc


@pytest.mark.parametrize('host', ['https://api.example.com', '--help', '*.example.com', 'a..com',
                                  'a.com:443', '127.0.0.1', 'a.com;id', 'a.com\n--help', 'a_b.com', 'a.' + 'b'*64])
def test_invalid_hosts(host):
    with pytest.raises(ConfigError):
        normalize_hosts([host])


def test_normalization():
    assert normalize_hosts([' API.Example.com. ', 'api.example.com']) == ['api.example.com']


def test_unconfigured_startup_does_not_write_to_the_application_root(tmp_path, monkeypatch):
    monkeypatch.delenv('WARP_EXCLUDE_HOSTS', raising=False)
    parent = tmp_path / 'absent'
    WarpExclusions(parent / 'warp-exclusions.json').startup()
    assert not parent.exists()


def test_save_remove_restart_and_stale_revision(service):
    before = service.state()
    result = service.save(['api.atresplayer.com', 'atres-live.atresmedia.com'], before['revision'])
    assert result['applied']
    assert service.test_active == {'api.atresplayer.com', 'atres-live.atresmedia.com', 'outside.example.com'}
    with pytest.raises(ConfigConflict):
        service.save([], before['revision'])
    service.test_active.clear()  # A new WARP profile gets the saved list back.
    service.startup()
    assert service.test_active == set(result['hosts'])
    result = service.save([], service.state()['revision'])
    assert result['applied'] and service.test_active == set()
    assert read_state(service.path)['hosts'] == []


def test_unrelated_hosts_are_never_removed(service):
    saved = service.save(['api.example.com'], service.state()['revision'])
    service.save([], saved['revision'])
    assert service.test_active == {'outside.example.com'}


def test_failed_apply_retains_desired_state_and_removal_history(service, monkeypatch):
    saved = service.save(['old.example.com'], service.state()['revision'])
    real = service.command
    def fail(args, deadline):
        if args[-2] == 'remove':
            raise ConfigError('WARP unavailable')
        return real(args, deadline)
    monkeypatch.setattr(service, 'command', fail)
    result = service.save(['new.example.com'], saved['revision'])
    assert not result['applied'] and result['error'] == 'WARP unavailable'
    assert read_state(service.path)['managed_hosts'] == ['new.example.com', 'old.example.com']
    monkeypatch.setattr(service, 'command', real)
    service.startup()
    assert service.test_active == {'outside.example.com', 'new.example.com'}


def test_saved_empty_overrides_environment(service, monkeypatch):
    monkeypatch.setenv('WARP_EXCLUDE_HOSTS', 'api.example.com, media.example.com')
    initial = service.state()
    assert initial['hosts'] == ['api.example.com', 'media.example.com']
    service.save([], initial['revision'])
    assert service.state()['hosts'] == []


def test_symlinks_fail_closed(service, tmp_path):
    victim = tmp_path / 'untouched'
    victim.write_text('unchanged')
    service.path.symlink_to(victim)
    with pytest.raises(ConfigError):
        service.state()
    assert victim.read_text() == 'unchanged'


def test_cli_timeout_has_safe_error(service, monkeypatch):
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired('private command', 1)))
    with pytest.raises(ConfigError, match='WARP is unavailable'):
        WarpExclusions.command(service, ['--json', 'tunnel', 'host', 'list'], time.monotonic() + 10)


def test_include_mode_is_not_modified(service, monkeypatch):
    monkeypatch.setattr(service, 'command', lambda *a: '{"mode":"include","hosts":[]}')
    result = service.save(['example.com'], service.state()['revision'])
    assert not result['applied'] and 'exclusion mode' in result['error']


def test_api_validation_and_conflict(client, service, monkeypatch):
    import warp_exclusions
    monkeypatch.setattr(warp_exclusions, 'exclusions_path', lambda *a: service.path)
    monkeypatch.setattr(warp_exclusions.WarpExclusions, 'command', lambda self, *args: service.command(*args))
    state = client.get('/api/v1/warp/exclusions').json()
    assert client.put('/api/v1/warp/exclusions', json={'hosts':['https://bad.com'], 'expected_revision':state['revision']}).status_code == 422
    response = client.put('/api/v1/warp/exclusions', json={'hosts':['api.example.com'], 'expected_revision':state['revision']})
    assert response.status_code == 200 and response.json()['applied']
    assert client.put('/api/v1/warp/exclusions', json={'hosts':[], 'expected_revision':state['revision']}).status_code == 409
