import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAcestreamStatusEndpoint:
    def test_status_fields_present(self):
        response = client.get("/api/v1/acestream/status")
        assert response.status_code == 200
        data = response.json()
        # Check all required fields
        for field in [
            "enabled", "is_internal", "engine_url", "available", "message",
            "version", "platform", "playlist_loaded", "connected"
        ]:
            assert field in data

    def test_status_engine_unreachable(self, monkeypatch):
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

    def test_status_engine_partial_failure(self, monkeypatch):
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
