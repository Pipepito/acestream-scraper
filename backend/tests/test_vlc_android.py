"""Contracts from VideoLAN VLC Android 3.6.5 Remote access source."""
import hashlib
import json
from contextlib import contextmanager
from unittest.mock import MagicMock
from urllib.parse import parse_qs

import httpx
import pytest

from app.services.remote_players import vlc_android as android
from app.services.remote_players.base import PlayerAuthError, PlayerCommandError

HOST = '192.168.1.20'
PIN = 'a' * 64
COOKIE = 'paired-session'
CREDENTIAL = json.dumps({'host': HOST, 'port': 8443, 'fingerprint': PIN, 'session': COOKIE})


@pytest.fixture
def remote(monkeypatch):
    state = {'requests': [], 'pins': [], 'handler': lambda r: httpx.Response(200)}

    def handler(request):
        state['requests'].append(request)
        return state['handler'](request)

    @contextmanager
    def client(host, port, fingerprint):
        state['pins'].append(fingerprint)
        with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False) as client:
            yield client, PIN

    monkeypatch.setattr(android, 'secure_client', client)
    monkeypatch.setattr(android, 'guard', lambda host: None)
    return state


def test_pairing_hash_and_session_not_otp_are_saved(remote):
    def handler(request):
        if request.url.path == '/code':
            assert 'cookie' not in request.headers
            return httpx.Response(200, text='challenge')
        assert parse_qs(request.content.decode()) == {'code': [hashlib.sha256(b'123456challenge').hexdigest()]}
        return httpx.Response(302, headers={'location': '/', 'set-cookie': f'user_session={COOKIE}; Path=/; HttpOnly'})
    remote['handler'] = handler
    assert android.start_pairing(HOST, 8443) == {'challenge': 'challenge', 'fingerprint': PIN}
    credential = android.finish_pairing(HOST, 8443, 'challenge', PIN, '123456')
    assert json.loads(credential) == json.loads(CREDENTIAL)
    assert '123456' not in credential
    assert remote['pins'] == [None, PIN]


@pytest.mark.parametrize('response', [
    httpx.Response(302, headers={'location': '/index.html#/login/error'}),
    httpx.Response(302, headers={'location': '/'}),
    httpx.Response(200, text='<html>Login</html>'),
])
def test_wrong_expired_or_missing_cookie_pairing_fails(remote, response):
    remote['handler'] = lambda r: response
    with pytest.raises(PlayerAuthError, match='incorrect or expired'):
        android.finish_pairing(HOST, 8443, 'challenge', PIN, '123456')


def test_play_and_controls_use_android_protocol(remote):
    driver = android.VlcAndroidDriver(HOST, 8443, CREDENTIAL)
    url = 'http://192.168.1.10/tuner/stream/abc.ts?x=1&y=2'
    driver.play(url, 'Channel')
    driver.pause()
    driver.resume()
    driver.set_volume(200)
    assert [(r.url.path, dict(r.url.params)) for r in remote['requests']] == [
        ('/play', {'id': '0', 'path': url, 'append': 'false'}),
        ('/playback-event', {'message': 'pause'}),
        ('/playback-event', {'message': 'play'}),
        ('/playback-event', {'message': 'set-volume', 'id': '100'}),
    ]
    assert all(r.url.scheme == 'https' and r.headers['cookie'] == f'user_session={COOKIE}' for r in remote['requests'])
    assert all(pin == PIN for pin in remote['pins'])
    with pytest.raises(PlayerCommandError, match='does not expose Stop'):
        driver.stop()
    assert len(remote['requests']) == 4


def test_status_drains_unrelated_events_and_converts_milliseconds(remote):
    responses = iter([
        [{'type': 'volume', 'volume': 12}],
        [{'type': 'now-playing', 'title': 'Arena', 'playing': False, 'progress': 12340, 'duration': 90000, 'volume': 35}],
    ])
    remote['handler'] = lambda r: httpx.Response(200, json=next(responses))
    status = android.VlcAndroidDriver(HOST, 8443, CREDENTIAL).status()
    assert (status.state, status.title, status.position_s, status.length_s, status.volume_pct) == ('paused', 'Arena', 12, 90, 35)


@pytest.mark.parametrize('body', [{}, '<html>', [{'type': 'now-playing', 'playing': True, 'progress': 'oops'}]])
def test_invalid_status_is_controlled_failure(remote, body):
    remote['handler'] = lambda r: httpx.Response(200, json=body)
    with pytest.raises(PlayerCommandError, match='invalid playback status'):
        android.VlcAndroidDriver(HOST, 8443, CREDENTIAL).status()


@pytest.mark.parametrize('status, error, message', [
    (401, PlayerAuthError, 'Pair VLC Android again'),
    (403, PlayerCommandError, 'playback control'),
    (302, PlayerCommandError, 'redirected'),
    (429, PlayerCommandError, 'too many pairing'),
])
def test_remote_errors_do_not_expose_response_or_follow_redirects(remote, status, error, message):
    remote['handler'] = lambda r: httpx.Response(status, text='upstream-secret', headers={'location': 'http://elsewhere'})
    with pytest.raises(error, match=message) as caught:
        android.VlcAndroidDriver(HOST, 8443, CREDENTIAL).pause()
    assert 'upstream-secret' not in str(caught.value)
    assert len(remote['requests']) == 1


@pytest.mark.parametrize('host, port, credential', [(HOST, 8443, None), ('192.168.1.21', 8443, CREDENTIAL), (HOST, 8080, CREDENTIAL)])
def test_missing_or_moved_pairing_never_sends_session(remote, host, port, credential):
    with pytest.raises(PlayerAuthError):
        android.VlcAndroidDriver(host, port, credential).pause()
    assert remote['requests'] == []
    assert remote['pins'] == []


def test_changed_certificate_is_rejected_before_http(monkeypatch):
    monkeypatch.setattr(android, 'guard', lambda host: None)
    tls = MagicMock()
    tls.__enter__.return_value.getpeercert.return_value = b'changed certificate'
    context = MagicMock()
    context.wrap_socket.return_value = tls
    monkeypatch.setattr(android.ssl, 'SSLContext', lambda protocol: context)
    monkeypatch.setattr(android.socket, 'create_connection', lambda *a, **kw: MagicMock())
    with pytest.raises(PlayerAuthError, match='certificate changed'):
        android.certificate_context(HOST, 8443, PIN)
    context.load_verify_locations.assert_not_called()


def test_android_pairing_api_masks_saved_credentials(alembic_client, monkeypatch):
    monkeypatch.setattr(android, 'start_pairing', lambda host, port: {'challenge': 'challenge', 'fingerprint': PIN})
    monkeypatch.setattr(android, 'finish_pairing', lambda *args: CREDENTIAL)
    base = '/api/v1/remote-players'
    response = alembic_client.post(base + '/android/pair/start', json={'host': HOST})
    assert response.status_code == 200
    assert response.headers['cache-control'] == 'no-store'
    response = alembic_client.post(base + '/android/pair/finish', json={'host': HOST, 'challenge': 'challenge', 'fingerprint': PIN, 'code': '123456'})
    assert response.status_code == 200
    assert response.json()['password'] == CREDENTIAL
    created = alembic_client.post(base, json={'name': 'Android TV', 'kind': 'vlc_android', 'host': HOST, 'port': 8443, 'password': response.json()['password']})
    assert created.status_code == 201
    assert created.json()['has_password'] is True
    assert COOKIE not in created.text
    assert COOKIE not in alembic_client.get(base).text
    moved = alembic_client.patch(f"{base}/{created.json()['id']}", json={'kind': 'vlc'})
    assert moved.json()['has_password'] is False


def test_pairing_api_rejects_unsafe_target_before_connecting(alembic_client, monkeypatch):
    start = MagicMock()
    monkeypatch.setattr(android, 'start_pairing', start)
    response = alembic_client.post('/api/v1/remote-players/android/pair/start', json={'host': '169.254.169.254'})
    assert response.status_code == 422
    start.assert_not_called()
