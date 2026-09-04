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

    def test_non_ascii_token_is_401_not_500(self, client, token_enabled):
        # compare_digest raises TypeError on non-ASCII str input; the
        # dependency must compare bytes so this stays a clean 401.
        response = client.get("/api/v1/channels/?token=se%C3%B1or")
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

    def test_web_player_routes_require_token(self, client, token_enabled):
        assert client.get("/api/v1/player/capabilities").status_code == 401
        assert client.get(f"/api/v1/player/capabilities?token={TOKEN}").status_code == 200

    def test_tuner_routes_stay_public(self, client, token_enabled, monkeypatch):
        from app.config.settings import get_settings
        from app.services.tuner_network import get_tuner_gate
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
        get_settings.cache_clear(); get_tuner_gate.cache_clear()
        try:
            response = client.head("/tuner/stream/" + "0" * 40 + ".ts")
            assert response.status_code == 200
            assert client.get("/tuner/nope").status_code == 404
        finally:
            get_settings.cache_clear(); get_tuner_gate.cache_clear()

    def test_tuner_admin_routes_require_token_but_tuner_routes_stay_public(self, client, token_enabled, monkeypatch):
        from app.config.settings import get_settings
        from app.services.tuner_network import get_tuner_gate
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
        get_settings.cache_clear(); get_tuner_gate.cache_clear()
        try:
            assert client.get("/api/v1/tuner/settings").status_code == 401
            assert client.get("/api/v1/tuner/status").status_code == 401
            assert client.get("/tuner/discover.json").status_code == 200
            assert client.get("/tuner/settings").status_code == 404
        finally:
            get_settings.cache_clear(); get_tuner_gate.cache_clear()
