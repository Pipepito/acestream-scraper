from unittest.mock import Mock

import pytest


@pytest.fixture(autouse=True)
def configured_status_engine(db_session, monkeypatch):
    """Use isolated settings and mocked HTTP, never the developer's runtime DB."""
    from app.repositories.settings_repository import SettingsRepository
    monkeypatch.setenv('ENABLE_ACESTREAM_ENGINE', 'false')
    SettingsRepository(db_session).set_setting('ace_engine_url', 'http://engine.test:6878')
    response = Mock(status_code=200)
    response.json.return_value = {'result': {'version': {'version': 'test'}}}
    monkeypatch.setattr('requests.get', Mock(return_value=response))


class TestAcestreamStatusEndpoint:
    def test_status_fields_present(self, client):
        response = client.get("/api/v1/acestream/status")
        assert response.status_code == 200
        data = response.json()
        # Check all required fields
        for field in [
            "enabled", "is_internal", "engine_url", "available", "message",
            "version", "platform", "playlist_loaded", "connected"
        ]:
            assert field in data

    def test_status_engine_unreachable(self, client, monkeypatch):
        # Patch requests.get to simulate unreachable engine
        import requests
        def mock_get(*args, **kwargs):
            raise requests.ConnectionError("Connection refused")
        monkeypatch.setattr(requests, "get", mock_get)
        response = client.get("/api/v1/acestream/status")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "Could not connect" in data["message"]

    def test_status_engine_partial_failure(self, client, monkeypatch):
        # Patch requests.get to simulate partial API failure
        import requests
        class MockResponse:
            def __init__(self, status_code):
                self.status_code = status_code
            def json(self):
                return {}
        def mock_get(url, *args, **kwargs):
            if "get_status" in url:
                return MockResponse(500)
            else:
                return MockResponse(200)
        monkeypatch.setattr(requests, "get", mock_get)
        response = client.get("/api/v1/acestream/status")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "not responding" in data["message"]

    def test_status_without_engine_does_not_request_http(self, client, db_session):
        import requests
        from app.repositories.settings_repository import SettingsRepository
        SettingsRepository(db_session).set_setting('ace_engine_url', '')
        response = client.get('/api/v1/acestream/status')
        assert response.status_code == 200
        assert response.json()['engine_url'] == ''
        assert response.json()['available'] is False
        assert 'No playback engine configured' in response.json()['message']
        requests.get.assert_not_called()
