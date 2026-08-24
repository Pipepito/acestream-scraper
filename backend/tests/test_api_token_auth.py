"""
Tests for optional API token authentication (#148).
"""

import pytest


TOKEN = "s3cret-token"


@pytest.fixture
def token_enabled(monkeypatch):
    monkeypatch.setenv("API_TOKEN", TOKEN)


class TestOpenByDefault:
    def test_api_open_without_token_configured(self, client, monkeypatch):
        monkeypatch.delenv("API_TOKEN", raising=False)
        response = client.get("/api/v1/channels")
        assert response.status_code == 200

    def test_playlist_open_without_token_configured(self, client, monkeypatch):
        monkeypatch.delenv("API_TOKEN", raising=False)
        response = client.get("/playlists/m3u")
        assert response.status_code == 200


class TestTokenEnforced:
    def test_api_rejects_missing_token(self, client, token_enabled):
        response = client.get("/api/v1/channels")
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    def test_api_rejects_wrong_token(self, client, token_enabled):
        response = client.get(
            "/api/v1/channels", headers={"Authorization": "Bearer nope"}
        )
        assert response.status_code == 401

    def test_api_accepts_bearer_token(self, client, token_enabled):
        response = client.get(
            "/api/v1/channels", headers={"Authorization": f"Bearer {TOKEN}"}
        )
        assert response.status_code == 200

    def test_api_accepts_x_api_token_header(self, client, token_enabled):
        response = client.get("/api/v1/channels", headers={"X-Api-Token": TOKEN})
        assert response.status_code == 200

    def test_api_accepts_query_token(self, client, token_enabled):
        response = client.get(f"/api/v1/channels?token={TOKEN}")
        assert response.status_code == 200

    def test_health_stays_public(self, client, token_enabled):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_player_routes_require_token(self, client, token_enabled):
        for path in (
            "/playlists/m3u",
            "/playlist.m3u",
            "/api/playlists/m3u",
            "/api/playlists/tv-channels/m3u",
            "/api/playlists/all-streams/m3u",
            "/api/playlists/epg.xml",
        ):
            response = client.get(path)
            assert response.status_code == 401, path

    def test_player_routes_accept_query_token(self, client, token_enabled):
        response = client.get(f"/playlist.m3u?token={TOKEN}")
        assert response.status_code == 200
        assert response.text.startswith("#EXTM3U")
