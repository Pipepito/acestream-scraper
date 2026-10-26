"""Offline-safe release checks; all network calls are replaced with fixtures."""
from unittest.mock import Mock

import httpx
import pytest

from app.services import update_service as updates


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    monkeypatch.setattr(updates, '_cached', None)
    monkeypatch.setattr(updates, '_expires', 0)
    monkeypatch.setattr(updates, 'get_app_version', lambda: 'v2.2.0')


def release(version='v2.10.0', **overrides):
    return {'tag_name': version, 'draft': False, 'prerelease': False,
            'published_at': '2026-10-22T00:00:00Z', **overrides}


@pytest.mark.parametrize('version,available', [('v2.10.0', True), ('v3.0.0', True), ('v2.2.0', False), ('v2.1.9', False), ('v2.1', False), ('v2.10', True)])
def test_numeric_comparison_and_cache(monkeypatch, version, available):
    fetch = Mock(return_value=release(version))
    monkeypatch.setattr(updates, 'fetch_latest', fetch)
    result = updates.check_updates()
    assert result.status == 'checked' and result.update_available is available
    assert result.release_url == updates.RELEASE_URL + version
    assert updates.check_updates() == result
    fetch.assert_called_once()


@pytest.mark.parametrize('payload', [release('v2.3.0-rc1'), release(draft=True), release(prerelease=True),
                                    release(published_at=None), release('https://evil.invalid'), {}])
def test_invalid_or_unpublished_release_is_quiet(monkeypatch, payload):
    monkeypatch.setattr(updates, 'fetch_latest', lambda: payload)
    assert updates.check_updates().status == 'unavailable'
    assert not updates.check_updates().update_available


def test_offline_failure_cached_and_retried(monkeypatch):
    fetch = Mock(side_effect=[httpx.ConnectError('offline'), release()])
    monkeypatch.setattr(updates, 'fetch_latest', fetch)
    assert updates.check_updates().status == 'unavailable'
    assert updates.check_updates().status == 'unavailable'
    assert fetch.call_count == 1
    monkeypatch.setattr(updates, '_expires', 0)
    assert updates.check_updates().update_available


def test_concurrent_request_does_not_wait_or_fetch(monkeypatch):
    fetch = Mock()
    monkeypatch.setattr(updates, 'fetch_latest', fetch)
    with updates._lock:
        assert updates.check_updates().status == 'unavailable'
    fetch.assert_not_called()


@pytest.mark.parametrize('body,status', [(b'x' * (updates.MAX_BYTES + 1), 200), (b'{}', 403), (b'bad json', 200)])
def test_bounded_upstream_and_no_secrets(monkeypatch, body, status):
    real_client = httpx.Client
    def handler(request):
        assert str(request.url) == updates.API_URL
        assert 'authorization' not in request.headers
        return httpx.Response(status, content=body)
    def client(**kwargs):
        assert kwargs['trust_env'] is False and kwargs['follow_redirects'] is False
        return real_client(transport=httpx.MockTransport(handler), **kwargs)
    monkeypatch.setattr(updates.httpx, 'Client', client)
    assert updates.check_updates().status == 'unavailable'


def test_endpoint_uses_normal_token_auth(client, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setenv('API_TOKEN', 'update-test')
    get_settings.cache_clear()
    fetch = Mock(return_value=release())
    monkeypatch.setattr(updates, 'fetch_latest', fetch)
    assert client.get('/api/v1/system/updates').status_code == 401
    fetch.assert_not_called()
    response = client.get('/api/v1/system/updates', headers={'X-API-Token': 'update-test'})
    assert response.status_code == 200
    assert response.json()['update_available'] is True
