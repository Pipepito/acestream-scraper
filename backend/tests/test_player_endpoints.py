"""/api/v1/player: session create/status/delete, HLS files, token propagation (spec 5.1, 4.4)."""
from __future__ import annotations

import re
from pathlib import Path

import anyio.from_thread
import httpx
import pytest

from app.services.engine_client import EngineClient
from app.services.player_service import PlayerService

FAKE_FFMPEG = Path(__file__).parent / "fake_ffmpeg.py"
IH = "0" * 40
TOKEN = "s3cret"


def _engine():
    def handler(request):
        if request.url.path == "/ace/getstream":
            return httpx.Response(200, json={"response": {"playback_url": "http://engine:6878/content/x/1", "stat_url": "http://engine:6878/ace/stat/x/s", "command_url": "http://engine:6878/ace/cmd/x/s", "is_live": 1}, "error": None})
        return httpx.Response(200, json={"response": {"status": "dl", "peers": 1, "speed_down": 1, "speed_up": 0}, "error": None})
    return EngineClient("http://engine:6878", client=httpx.Client(transport=httpx.MockTransport(handler)))


class _Settings:
    def __init__(self, hls_dir):
        self.PLAYER_HLS_DIR = str(hls_dir)
        self.PLAYER_MAX_SESSIONS = 1
        self.PLAYER_START_TIMEOUT_SECONDS = 45
        self.FFMPEG_BINARY_PATH = ""


@pytest.fixture
def player(client, tmp_path, monkeypatch):
    """A PlayerService bound to a temp HLS dir, a mock engine and the fake ffmpeg.

    ``TestClient`` spins up a fresh event loop per request unless it is given a
    portal. The player keeps live state on its loop (the ffmpeg subprocess
    transport and its stderr reader task), so every request — and the final
    ``stop()`` — must share one loop, exactly as they do under uvicorn.
    """
    import app.api.endpoints.player as endpoint
    svc = PlayerService(settings_getter=lambda: _Settings(tmp_path / "hls"), engine_factory=_engine, ffmpeg_path=str(FAKE_FFMPEG))
    monkeypatch.setattr(endpoint, "player_service", svc)
    with anyio.from_thread.start_blocking_portal(**client.async_backend) as portal:
        client.portal = portal
        try:
            yield svc
        finally:
            portal.call(svc.stop)
            client.portal = None


def _wait_ready(client, session_id, tries=60):
    for _ in range(tries):
        body = client.get(f"/api/v1/player/sessions/{session_id}").json()
        if body["hls_ready"]:
            return body
        import time; time.sleep(0.05)
    raise AssertionError("session never became ready")


def test_create_status_playlist_segment_delete(client, player):
    created = client.post("/api/v1/player/sessions", json={"content_id": IH})
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["state"] == "starting" and body["content_id"] == IH and body["viewers"] == 1
    assert body["playlist_url"] == f"/api/v1/player/sessions/{body['id']}/index.m3u8"
    ready = _wait_ready(client, body["id"])
    assert ready["codecs"] == {"video": "h264", "audio": "ac3"}

    playlist = client.get(ready["playlist_url"])
    assert playlist.status_code == 200
    assert playlist.headers["content-type"].startswith("application/vnd.apple.mpegurl")
    assert playlist.headers["cache-control"] == "no-store"
    lines = [l for l in playlist.text.splitlines() if l and not l.startswith("#")]
    assert lines and all(l.endswith(".ts") for l in lines)
    segment = client.get(f"/api/v1/player/sessions/{body['id']}/{lines[0]}")
    assert segment.status_code == 200 and segment.headers["content-type"] == "video/mp2t"

    assert client.get(f"/api/v1/player/sessions/{body['id']}/../etc").status_code in (404, 422)
    assert client.get(f"/api/v1/player/sessions/{body['id']}/evil.ts").status_code == 404
    assert client.delete(f"/api/v1/player/sessions/{body['id']}").status_code == 204
    assert client.get(f"/api/v1/player/sessions/{body['id']}").json()["viewers"] == 0
    listing = client.get("/api/v1/player/sessions").json()
    assert [s["id"] for s in listing["sessions"]] == [body["id"]]


def test_join_existing_session(client, player):
    first = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    second = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    assert second["id"] == first["id"] and second["viewers"] == 2


def test_limit_reached_envelope(client, player):
    client.post("/api/v1/player/sessions", json={"content_id": IH})
    response = client.post("/api/v1/player/sessions", json={"content_id": "1" * 40})
    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "PLAYER_LIMIT_REACHED" and error["context"] == {"limit": 1, "active": 1}


def test_invalid_content_id(client, player):
    assert client.post("/api/v1/player/sessions", json={"content_id": "nope"}).status_code == 422


def test_unknown_session_404(client, player):
    assert client.get("/api/v1/player/sessions/" + "f" * 32).status_code == 404
    assert client.get("/api/v1/player/sessions/" + "f" * 32 + "/index.m3u8").status_code == 404


def test_capabilities(client, player):
    body = client.get("/api/v1/player/capabilities").json()
    assert body["ffmpeg_available"] is True and body["ffmpeg_path"] == str(FAKE_FFMPEG)
    assert body["max_sessions"] == 1 and body["hls_dir"].endswith("hls")


def test_playlist_propagates_query_token_for_native_players(client, player, monkeypatch):
    monkeypatch.setenv("API_TOKEN", TOKEN)
    created = client.post(f"/api/v1/player/sessions?token={TOKEN}", json={"content_id": IH}).json()
    ready = _wait_ready_with_token(client, created["id"])
    by_query = client.get(f"{ready['playlist_url']}?token={TOKEN}")
    assert by_query.status_code == 200
    uris = [l for l in by_query.text.splitlines() if l and not l.startswith("#")]
    assert uris and all(l.endswith(f"?token={TOKEN}") for l in uris)
    assert all(l.startswith("#") or l.endswith(f"?token={TOKEN}") for l in by_query.text.splitlines() if l)
    # Each rewritten URI resolves and is accepted; the same segment without a token is 401.
    seg = uris[0]
    assert client.get(f"/api/v1/player/sessions/{created['id']}/{seg}").status_code == 200
    assert client.get(f"/api/v1/player/sessions/{created['id']}/{seg.split('?')[0]}").status_code == 401
    # A header-authenticated request gets the playlist verbatim: no query is appended.
    by_header = client.get(ready["playlist_url"], headers={"X-Api-Token": TOKEN})
    assert "token=" not in by_header.text
    assert all(re.fullmatch(r"seg\d{5}\.ts", l) for l in by_header.text.splitlines() if l and not l.startswith("#"))
    assert client.delete(f"/api/v1/player/sessions/{created['id']}?token={TOKEN}").status_code == 204


def test_reserved_characters_in_token_are_encoded(client, player, monkeypatch):
    monkeypatch.setenv("API_TOKEN", "a b&c")
    created = client.post("/api/v1/player/sessions", json={"content_id": IH}, headers={"X-Api-Token": "a b&c"}).json()
    ready = _wait_ready_with_token(client, created["id"], token="a b&c")
    text = client.get(ready["playlist_url"], params={"token": "a b&c"}).text
    assert "seg00000.ts?token=a+b%26c" in text or "?token=a+b%26c" in text


def _wait_ready_with_token(client, session_id, token=TOKEN, tries=60):
    for _ in range(tries):
        body = client.get(f"/api/v1/player/sessions/{session_id}", headers={"X-Api-Token": token}).json()
        if body["hls_ready"]:
            return body
        import time; time.sleep(0.05)
    raise AssertionError("session never became ready")
