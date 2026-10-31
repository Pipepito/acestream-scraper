"""Account boundaries use real migrations, password hashing and HTTP requests."""
import pytest
from fastapi.testclient import TestClient
from app.repositories.access_repository import AccessRepository
from app.schemas.access import AccountUpdate, AccessPolicy


@pytest.fixture
def access_client(tmp_path, monkeypatch):
    import app.repositories.access_repository as module
    import app.services.access_service as service
    monkeypatch.setattr(module, 'config_path', lambda url: tmp_path / 'runtime-config.json')
    monkeypatch.delenv('API_TOKEN', raising=False)
    service._ATTEMPTS.clear()
    repo = AccessRepository()
    repo.initialize(fresh=True)
    import main
    client = TestClient(main.app, base_url='https://testserver')
    csrf = client.get('/api/v1/auth/status').json()['csrf']
    client.headers['X-CSRF-Token'] = csrf
    yield client, repo
    client.close()


def enable(client):
    response = client.post('/api/v1/auth/bootstrap', json={'username': 'owner', 'password': 'a sufficiently long password',
        'password_confirmation': 'a sufficiently long password'})
    assert response.status_code == 200, response.text
    return response.json()


def test_fresh_migration_and_atomic_first_admin(access_client):
    client, repo = access_client
    assert client.get('/api/v1/config').status_code == 401
    owner = enable(client)
    repo.initialize()
    assert repo.state()[0] == 'accounts'
    assert client.get('/api/v1/auth/users').json()[0]['id'] == owner['id']
    assert client.post('/api/v1/auth/bootstrap', json={'username': 'other', 'password': 'a sufficiently long password',
        'password_confirmation': 'a sufficiently long password'}).status_code == 409
    assert len(repo.users()) == 1


def test_receiver_preflight_is_read_only_without_application_credentials(access_client):
    client, _ = access_client
    enable(client)
    client.cookies.clear()
    headers = {'Origin': 'https://receiver.example', 'Access-Control-Request-Method': 'GET',
               'Access-Control-Request-Headers': 'Range'}
    response = client.options('/api/v1/viewers/' + 'a' * 32 + '/media/index.m3u8', headers=headers)
    assert response.status_code == 204
    assert response.headers['Access-Control-Allow-Origin'] == '*'
    assert response.headers['Access-Control-Allow-Methods'] == 'GET, HEAD, OPTIONS'
    assert 'Access-Control-Allow-Credentials' not in response.headers
    assert client.options('/api/v1/config', headers=headers).status_code == 400


def test_password_change_revokes_sessions(access_client):
    client, repo = access_client
    enable(client)
    old_cookie = client.cookies.get('scraper_session')
    response = client.put('/api/v1/auth/password', json={'current_password': 'a sufficiently long password',
        'password': 'replacement long password', 'password_confirmation': 'replacement long password'})
    assert response.status_code == 204
    client.cookies.set('scraper_session', old_cookie)
    assert client.get('/api/v1/auth/users').status_code == 403
    assert repo.session_user(old_cookie) is None


def test_csrf_secret_redaction_and_anonymous_boundaries(access_client):
    client, repo = access_client
    response = client.post('/api/v1/auth/bootstrap', json={'username': 'x', 'password': 'DO NOT ECHO', 'password_confirmation': 'x', 'unexpected': 'SECRET'})
    assert response.status_code == 422
    assert 'SECRET' not in response.text and 'DO NOT ECHO' not in response.text
    client.headers['Origin'] = 'https://attacker.example'
    assert client.post('/api/v1/auth/bootstrap', json={'username': 'x', 'password': 'long password value', 'password_confirmation': 'long password value'}).status_code == 403
    del client.headers['Origin']
    enable(client)
    client.cookies.clear()
    for path in ['/api/v1/system/storage', '/api/v1/config/base-url', '/api/v1/player/sessions', '/api/v1/setup', '/playlist.m3u', '/openapi.json', '/docs', '/api/v1/startup/diagnostics']:
        assert client.get(path).status_code == 401, path
    startup = client.get('/api/v1/startup').json()
    assert startup['recovery_token'] == '' and startup['events'] == []


def test_last_admin_and_scoped_credentials(access_client):
    client, repo = access_client
    owner = enable(client)
    assert client.put('/api/v1/auth/users/' + owner['id'], json={'administrator': False, 'enabled': True, 'permissions': ['live']}).status_code == 409
    token = client.post('/api/v1/auth/credentials', json={'label': 'TV', 'kind': 'playback'}).json()['token']
    client.cookies.clear()
    assert client.get('/api/v1/auth/users', headers={'X-Api-Token': token}).status_code == 403
    assert client.get('/api/v1/system/storage', params={'token': token}).status_code == 401


def test_missing_store_fails_closed(access_client):
    client, repo = access_client
    enable(client)
    repo.path.unlink()
    assert client.get('/api/v1/config').status_code == 503
    with pytest.raises(RuntimeError, match='missing'):
        repo.initialize()


def test_skip_then_enable_without_deployment_configuration(access_client):
    client, repo = access_client
    assert client.post('/api/v1/auth/bootstrap', json={'enabled': False, 'username': 'unused', 'password': 'unused', 'password_confirmation': 'unused'}).status_code == 200
    assert repo.state()[0] == 'open'
    enable(client)
    assert repo.state()[0] == 'accounts'


def test_legacy_migration_requires_old_header_and_explicit_consent(access_client, monkeypatch):
    client, repo = access_client
    monkeypatch.setenv('API_TOKEN', 'existing-playback-secret')
    payload = {'username': 'owner', 'password': 'a sufficiently long password',
               'password_confirmation': 'a sufficiently long password'}
    assert client.post('/api/v1/auth/bootstrap', json=payload).status_code == 401
    client.headers['X-Api-Token'] = 'existing-playback-secret'
    assert client.post('/api/v1/auth/bootstrap', json=payload).status_code == 409
    assert client.post('/api/v1/auth/bootstrap', json={**payload, 'migrate_legacy_token': True}).status_code == 200
    client.cookies.clear()
    assert client.get('/api/v1/config').status_code == 401
    assert client.get('/tuner/lineup_status.json?token=existing-playback-secret').status_code == 200


def test_permissions_are_individual_and_new_methods_default_deny(access_client):
    client, repo = access_client
    enable(client)
    user = client.post('/api/v1/auth/users', json={'username': 'viewer', 'password': 'a sufficiently long password',
        'permissions': ['live', 'guide', 'cast']}).json()
    client.post('/api/v1/auth/logout')
    assert client.post('/api/v1/auth/login', json={'username': 'viewer', 'password': 'a sufficiently long password'}).status_code == 200
    assert client.get('/api/v1/auth/status').json()['permissions'] == ['cast', 'guide', 'live']
    for method, path in [('get', '/api/v1/config'), ('get', '/api/v1/auth/users'), ('get', '/api/v1/cast/devices'),
                         ('get', '/api/v1/view/recordings'), ('get', '/api/v1/view/channels'),
                         ('post', '/api/v1/auth/status'), ('delete', '/api/v1/view/guide'), ('post', '/api/v1/config')]:
        assert getattr(client, method)(path).status_code == 403, (method, path)
    repo.update_user(user['id'], AccountUpdate(administrator=False, enabled=False, permissions=[]))
    assert client.get('/api/v1/auth/status').json()['user'] is None


def test_header_admin_credentials_never_authorize_query_strings(access_client):
    client, repo = access_client
    enable(client)
    secret = client.post('/api/v1/auth/credentials', json={'label': 'Automation', 'kind': 'admin'}).json()['token']
    client.cookies.clear()
    assert client.get('/api/v1/auth/users', headers={'Authorization': 'Bearer ' + secret}).status_code == 200
    assert client.get('/api/v1/auth/users?token=' + secret).status_code == 403
    assert client.get('/tuner/lineup_status.json?token=' + secret).status_code == 401


def test_csrf_is_stable_across_tabs_and_cookie_mutations_are_checked(access_client):
    client, repo = access_client
    enable(client)
    assert client.get('/api/v1/auth/status').json()['csrf'] == client.headers['X-CSRF-Token']
    csrf = client.headers.pop('X-CSRF-Token')
    assert client.put('/api/v1/auth/policy', json=AccessPolicy().model_dump()).status_code == 403
    client.headers['X-CSRF-Token'] = csrf
    assert client.put('/api/v1/auth/policy', json=AccessPolicy().model_dump()).status_code == 200
    assert client.get('/api/v1/auth/users', headers={'Origin': 'https://other.testserver'}).status_code == 403
    assert client.get('/api/v1/auth/users', headers={'Origin': 'https://testserver:443'}).status_code == 200


def test_local_recovery_revokes_credentials_without_disabling_protection(access_client, monkeypatch, capsys):
    from app import auth
    client, repo = access_client
    enable(client)
    old_session = client.cookies.get('scraper_session')
    monkeypatch.setattr('sys.argv', ['auth', 'reset-password'])
    monkeypatch.setattr('builtins.input', lambda prompt: 'owner')
    monkeypatch.setattr(auth.getpass, 'getpass', lambda prompt: 'the new long password')
    auth.main()
    assert repo.state()[0] == 'accounts' and repo.session_user(old_session) is None
    assert 'the new long password' not in capsys.readouterr().out
    assert client.post('/api/v1/auth/login', json={'username': 'owner', 'password': 'the new long password'}).status_code == 200


def test_home_network_never_trusts_spoofed_forwarding(access_client, monkeypatch):
    from starlette.requests import Request
    from app.services.access_service import trusted_client
    from types import SimpleNamespace
    monkeypatch.setattr('app.config.settings.get_settings', lambda: SimpleNamespace(FORWARDED_ALLOW_IPS='10.0.0.2'))
    def request(peer, client, headers=()):
        return Request({'type': 'http', 'method': 'GET', 'scheme': 'http', 'path': '/', 'headers': headers,
                        'client': (client, 1234), 'state': {'peer': (peer, 1234)}})
    networks = ['192.168.1.0/24']
    assert trusted_client(request('192.168.1.22', '192.168.1.22'), networks)
    assert not trusted_client(request('203.0.113.8', '203.0.113.8', [(b'x-forwarded-for', b'192.168.1.22')]), networks)
    assert not trusted_client(request('10.0.0.2', '10.0.0.2'), ['10.0.0.0/24'])
    assert trusted_client(request('10.0.0.2', '192.168.1.22', [(b'x-forwarded-for', b'192.168.1.22')]), networks)
    assert not trusted_client(request('10.0.0.2', '203.0.113.8', [(b'x-forwarded-for', b'203.0.113.8')]), networks)


def test_public_features_cannot_expose_recordings_or_server_devices():
    from pydantic import ValidationError
    for feature in ['recordings', 'cast_server', 'playlists']:
        with pytest.raises(ValidationError):
            AccessPolicy(public_features=[feature])


def test_mount_prefix_cannot_bypass_authentication(access_client):
    import main
    client, repo = access_client
    enable(client)
    prefixed = TestClient(main.app, base_url='https://testserver', root_path='/tv')
    try:
        for path in ['/tv/api/v1/config', '/tv/playlist.m3u', '/tv/tuner/lineup.json', '/tv/openapi.json']:
            assert prefixed.get(path).status_code == 401, path
        assert prefixed.get('/tv/api/v1/auth/status').json()['mode'] == 'accounts'
    finally:
        prefixed.close()


def test_access_and_cast_forms_preserve_each_others_settings(access_client):
    client, repo = access_client
    enable(client)
    casting = {'compatibility_conversion': True, 'cast_media_url': 'https://tv.example/app'}
    assert client.put('/api/v1/cast/settings', json=casting).status_code == 200
    response = client.put('/api/v1/auth/policy', json={'public_features': ['guide'], 'local_iptv': True})
    assert response.status_code == 200
    assert response.json()['cast_media_url'] == casting['cast_media_url']
    assert client.get('/api/v1/cast/settings').json()['compatibility_conversion'] is True
    assert client.put('/api/v1/cast/settings', json={**casting, 'remote_casting': True}).status_code == 200
    assert repo.state()[1].public_features == ['guide']
    assert client.post('/api/v1/auth/disable', json={'current_password': 'a sufficiently long password'}).status_code == 204
    assert repo.state()[0] == 'open'
    assert repo.state()[1].cast_media_url == casting['cast_media_url']
    enable(client)
    assert client.get('/api/v1/cast/settings').json()['cast_media_url'] == casting['cast_media_url']


@pytest.mark.parametrize('mode', ['open', 'accounts'])
@pytest.mark.parametrize('host,allowed', [('192.168.1.22', True), ('8.8.8.8', False), ('172.17.0.1', False), ('127.0.0.1', False)])
def test_cast_network_defaults_without_manual_networks(mode, host, allowed, monkeypatch):
    from types import SimpleNamespace
    from starlette.requests import Request
    from fastapi import HTTPException
    from app.services.access_service import require_server_cast
    monkeypatch.setattr('app.config.settings.get_settings', lambda: SimpleNamespace(FORWARDED_ALLOW_IPS=''))
    request = Request({'type': 'http', 'method': 'GET', 'scheme': 'http', 'path': '/', 'headers': [(b'host', b'app.test')],
        'server': ('app.test', 80), 'client': (host, 1234), 'state': {'peer': (host, 1234), 'access_mode': mode,
        'access_policy': AccessPolicy(), 'access_user': {'id': 'owner', 'administrator': True, 'permissions': []} if mode == 'accounts' else None}})
    if allowed:
        require_server_cast(request)
    else:
        with pytest.raises(HTTPException) as error:
            require_server_cast(request)
        assert error.value.status_code == 403


def test_local_open_cast_api_requires_csrf_and_blocks_outsiders(access_client, monkeypatch):
    from fastapi.testclient import TestClient
    from app.services.cast_service import cast_service
    import main
    _, repo = access_client
    repo.bootstrap('unused', '', False)
    monkeypatch.setattr(cast_service.discovery, 'start', lambda: None)
    client = TestClient(main.app, base_url='http://192.168.1.10:8000', client=('192.168.1.22', 1234))
    try:
        assert client.get('/api/v1/cast/capabilities').json()['server_devices'] is True
        assert client.get('/api/v1/cast/capabilities').json()['media_url'] == 'http://192.168.1.10:8000'
        assert client.get('/api/v1/cast/devices').status_code == 200
        assert client.put('/api/v1/cast/settings', json={}).status_code == 403
        csrf = client.get('/api/v1/auth/status').json()['csrf']
        client.headers['X-CSRF-Token'] = csrf
        assert client.put('/api/v1/cast/settings', json={'compatibility_conversion': True}).status_code == 200
        assert client.get('/api/v1/cast/settings').json()['compatibility_conversion'] is True
        assert client.get('/api/v1/cast/sessions').json() == []
        assert client.post('/api/v1/cast/sessions', json={'content_id': 'a' * 40}).status_code == 422
        client.headers['Origin'] = 'https://attacker.example'
        assert client.post('/api/v1/cast/sessions', json={'content_id': 'a' * 40}).status_code == 403
        assert client.put('/api/v1/cast/settings', json={}).status_code == 403
    finally:
        client.close()
    remote = TestClient(main.app, base_url='https://app.test', client=('8.8.8.8', 1234))
    try:
        csrf = remote.get('/api/v1/auth/status').json()['csrf']
        remote.headers['X-CSRF-Token'] = csrf
        assert remote.get('/api/v1/cast/capabilities').json()['server_devices'] is False
        for path in ['settings', 'devices', 'sessions']:
            assert remote.get('/api/v1/cast/' + path).status_code == 403
        assert remote.put('/api/v1/cast/settings', json={'remote_casting': True}).status_code == 403
        assert remote.post('/api/v1/cast/home-connection').status_code == 403
        repo.update_policy({'remote_casting': True})
        assert remote.get('/api/v1/cast/capabilities').json()['server_devices'] is False
    finally:
        remote.close()


def test_public_https_home_connection_can_be_trusted_without_remote_control(access_client):
    import main
    _, repo = access_client
    client = TestClient(main.app, base_url='https://app.test', client=('8.8.4.4', 1234))
    try:
        client.headers['X-CSRF-Token'] = client.get('/api/v1/auth/status').json()['csrf']
        enable(client)
        assert client.get('/api/v1/cast/capabilities').json()['server_devices'] is False
        response = client.post('/api/v1/cast/home-connection')
        assert response.status_code == 200, response.text
        assert '8.8.4.4/32' in response.json()['home_networks']
        assert response.json()['remote_casting'] is False
        assert client.get('/api/v1/cast/capabilities').json()['server_devices'] is True
        assert repo.state()[1].home_networks
    finally:
        client.close()


def test_cast_settings_cannot_be_changed_by_viewer_accounts(access_client):
    client, _ = access_client
    enable(client)
    client.post('/api/v1/auth/users', json={'username': 'viewer', 'password': 'a sufficiently long password', 'permissions': ['cast_server', 'live']})
    client.post('/api/v1/auth/logout')
    assert client.post('/api/v1/auth/login', json={'username': 'viewer', 'password': 'a sufficiently long password'}).status_code == 200
    assert client.get('/api/v1/cast/settings').status_code == 403
    assert client.put('/api/v1/cast/settings', json={'remote_casting': True}).status_code == 403
    assert client.post('/api/v1/cast/home-connection').status_code == 403
