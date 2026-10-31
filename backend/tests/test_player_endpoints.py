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
    # Endpoint contracts need stable media, not the fake's 50 ms rotation race.
    # Deletion during transfer is exercised deterministically below.
    monkeypatch.setenv("FAKE_FFMPEG_MODE", "static_playlist")
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


def test_segment_missing_is_404_and_served_response_carries_its_own_stat(client, player):
    """Missing/non-file paths are 404; valid segments retain their stat headers."""
    import app.api.endpoints.player as endpoint

    created = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    ready = _wait_ready(client, created["id"])
    uris = [l for l in client.get(ready["playlist_url"]).text.splitlines() if l and not l.startswith("#")]
    newest = uris[-1]

    # Well-formed name, no such file: 404, never a 500.
    missing = client.get(f"/api/v1/player/sessions/{created['id']}/seg99999.ts")
    assert missing.status_code == 404, missing.text

    # A directory sitting where a segment should be is a 404 too, not a mid-send crash.
    (player.get(created["id"]).dir / "seg99998.ts").mkdir()
    assert client.get(f"/api/v1/player/sessions/{created['id']}/seg99998.ts").status_code == 404

    # File metadata stays consistent with the handler's check. The separate
    # rotation tests exercise deletion before open and during delivery.
    response = client.portal.call(endpoint.segment, created["id"], newest)
    assert response.stat_result is not None
    assert response.headers["content-length"] == str(response.stat_result.st_size)


def test_active_streams_lists_relays_next_to_browser_sessions_with_channel_names(client, player, db_session):
    """The Integrations page asks one question -- what is streaming right now --
    and tuner/remote-player relays are half the answer."""
    from app.models.models import AcestreamChannel
    from app.services.stream_relay import relay_registry

    relay_id = "1" * 40
    db_session.add(AcestreamChannel(id=IH, name="Arena TV"))
    db_session.add(AcestreamChannel(id=relay_id, name="Sports 1"))
    db_session.commit()

    session = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    relay = relay_registry.open(relay_id, "tuner:192.168.1.5")
    try:
        body = client.get("/api/v1/player/streams").json()
    finally:
        relay_registry.close(relay.id)

    streams = {stream["kind"]: stream for stream in body["streams"]}
    assert set(streams) == {"browser", "relay"}
    assert streams["browser"]["id"] == session["id"] and streams["browser"]["content_id"] == IH
    assert streams["browser"]["channel_name"] == "Arena TV" and streams["browser"]["viewers"] == 1
    assert streams["relay"]["content_id"] == relay_id and streams["relay"]["channel_name"] == "Sports 1"
    assert streams["relay"]["state"] == "streaming" and streams["relay"]["client_label"] == "tuner:192.168.1.5"
    assert streams["relay"]["started_at"]

    client.delete(f"/api/v1/player/sessions/{session['id']}")


def test_active_streams_names_an_unknown_channel_nothing(client, player):
    session = client.post("/api/v1/player/sessions", json={"content_id": IH}).json()
    try:
        body = client.get("/api/v1/player/streams").json()
        assert [stream["channel_name"] for stream in body["streams"]] == [None]
    finally:
        client.delete(f"/api/v1/player/sessions/{session['id']}")


def test_audio_track_request_validation_and_status(client, player):
    assert client.post('/api/v1/player/sessions', json={'content_id': IH, 'audio_index': -1}).status_code == 422
    assert client.post('/api/v1/player/sessions', json={'content_id': IH, 'audio_index': 64}).status_code == 422
    response = client.post('/api/v1/player/sessions', json={'content_id': IH, 'audio_index': 1})
    assert response.status_code == 200
    assert response.json()['audio_index'] == 1
    assert isinstance(response.json()['audio_tracks'], list)


@pytest.mark.parametrize('when', ['before_send', 'after_headers', 'cancel_during_body'])
@pytest.mark.parametrize('byte_range', [None, 'bytes=7-31', 'bytes=0-3,20-23'])
def test_segment_rotation_during_response(client, player, when, byte_range, monkeypatch):
    """Force deletion at both sides of the response's file-open boundary."""
    import asyncio
    import builtins
    from starlette.exceptions import HTTPException
    import app.api.endpoints.player as endpoint

    created = client.post('/api/v1/player/sessions', json={'content_id': IH}).json()
    path = player.get(created['id']).dir / 'seg99997.ts'
    content = bytes(range(256)) * 1024  # More than one response chunk.
    path.write_bytes(content)
    response = client.portal.call(endpoint.segment, created['id'], path.name)
    opened = []
    original_open = builtins.open

    def record_open(file, *args, **kwargs):
        handle = original_open(file, *args, **kwargs)
        if file == path:
            opened.append(handle)
        return handle

    monkeypatch.setattr(builtins, 'open', record_open)
    messages = []

    async def deliver():
        async def send(message):
            messages.append(message)
            if message['type'] == 'http.response.start' and when != 'before_send':
                path.unlink()
            if message['type'] == 'http.response.body' and when == 'cancel_during_body':
                raise asyncio.CancelledError

        async def receive():
            raise AssertionError('ASGI 2.4 should not poll disconnects')

        if when == 'before_send':
            path.unlink()
        scope = {'type': 'http', 'method': 'GET', 'asgi': {'spec_version': '2.4'},
                 'headers': [(b'range', byte_range.encode())] if byte_range else [],
                 'extensions': {'http.response.pathsend': {}}}
        if when == 'cancel_during_body':
            with pytest.raises(asyncio.CancelledError):
                await response(scope, receive, send)
        else:
            await response(scope, receive, send)

    if when == 'before_send':
        with pytest.raises(HTTPException) as error:
            client.portal.call(deliver)
        assert error.value.status_code == 404
        assert messages == []  # Never send a successful status before opening.
    elif when == 'cancel_during_body':
        client.portal.call(deliver)
        assert opened and all(handle.closed for handle in opened)
    else:
        client.portal.call(deliver)
        assert messages[0]['status'] == (206 if byte_range else 200)
        assert all(message['type'] != 'http.response.pathsend' for message in messages)
        body = b''.join(message.get('body', b'') for message in messages)
        headers = dict(messages[0]['headers'])
        assert len(body) == int(headers[b'content-length'])
        if byte_range is None:
            assert body == content
        elif byte_range == 'bytes=7-31':
            assert body == content[7:32]
        else:
            assert content[:4] in body and content[20:24] in body
        assert opened and all(handle.closed for handle in opened)


def test_segment_removed_before_open_returns_http_404(client, player, monkeypatch):
    from starlette.responses import FileResponse

    created = client.post('/api/v1/player/sessions', json={'content_id': IH}).json()
    path = player.get(created['id']).dir / 'seg99996.ts'
    path.write_bytes(b'G' * 188)
    original_call = FileResponse.__call__

    async def remove_before_send(response, scope, receive, send):
        if response.path == path:
            path.unlink()
        await original_call(response, scope, receive, send)

    monkeypatch.setattr(FileResponse, '__call__', remove_before_send)
    response = client.get(f"/api/v1/player/sessions/{created['id']}/{path.name}")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Segment not ready'}


def test_imported_http_stream_plays_without_engine_or_probe(client, player, db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.api.endpoints.player import tuner_probe_service

    from sqlalchemy.orm import sessionmaker
    monkeypatch.setattr('app.config.database.SessionLocal', sessionmaker(bind=db_session.get_bind()))
    stream_id = 'url:' + 'b' * 40
    db_session.add(AcestreamChannel(id=stream_id, name='laSexta', stream_url='https://media.example/live.m3u8'))
    db_session.commit()
    def no_engine(*args, **kwargs):
        raise AssertionError('HTTP streams must not start or probe AceStream')
    monkeypatch.setattr(player, '_engine_factory', no_engine)
    monkeypatch.setattr(tuner_probe_service, 'start_for_stream', no_engine)
    monkeypatch.setenv('API_TOKEN', TOKEN)
    assert client.post('/api/v1/player/sessions', json={'content_id': stream_id}).status_code == 401
    response = client.post('/api/v1/player/sessions', json={'content_id': stream_id}, headers={'X-Api-Token': TOKEN})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['content_id'] == stream_id and body['error'] is None and body['stats'] is None
    ready = _wait_ready_with_token(client, body['id'])
    assert client.get(ready['playlist_url'], params={'token': TOKEN}).status_code == 200
    assert player.get(body['id']).http_source is not None


def test_unknown_http_id_fails_cleanly_without_engine(client, player, db_session, monkeypatch):
    from sqlalchemy.orm import sessionmaker
    monkeypatch.setattr('app.config.database.SessionLocal', sessionmaker(bind=db_session.get_bind()))
    def no_engine():
        raise AssertionError('Missing HTTP sources must not fall back to AceStream')
    monkeypatch.setattr(player, '_engine_factory', no_engine)
    response = client.post('/api/v1/player/sessions', json={'content_id': 'url:' + 'c' * 40})
    assert response.status_code == 200
    assert response.json()['error'] == 'source_unavailable'
    assert client.post('/api/v1/player/sessions', json={'content_id': 'https://media.example/live.m3u8'}).status_code == 422


def test_subtitle_playlists_and_vtt_preserve_authentication(client, player, monkeypatch):
    monkeypatch.setenv('API_TOKEN', 'a b&c')
    headers = {'X-Api-Token': 'a b&c'}
    created = client.post('/api/v1/player/sessions', json={'content_id': IH, 'subtitle_index': 0}, headers=headers).json()
    assert created['subtitle_index'] == 0
    session = player.get(created['id'])
    (session.dir / 'index_vtt.m3u8').write_text('#EXTM3U\n#EXTINF:2,\nindex0.vtt\n')
    (session.dir / 'index0.vtt').write_text('WEBVTT\n\n00:00:00.000 --> 00:00:02.000\nCaption\n')
    root = f"/api/v1/player/sessions/{session.id}"
    master = client.get(root + '/index.m3u8', params={'token': 'a b&c'})
    assert 'URI="subtitles.m3u8?token=a+b%26c"' in master.text
    assert 'video.m3u8?token=a+b%26c' in master.text
    subs = client.get(root + '/subtitles.m3u8', params={'token': 'a b&c'})
    assert 'index0.vtt?token=a+b%26c' in subs.text
    assert client.get(root + '/subtitles.m3u8').status_code == 401
    assert client.get(root + '/index0.vtt').status_code == 401
    caption = client.get(root + '/index0.vtt', headers=headers)
    assert caption.headers['content-type'].startswith('text/vtt') and 'Caption' in caption.text
    assert client.get(root + '/anything.vtt', headers=headers).status_code == 404
    assert client.post('/api/v1/player/sessions', json={'content_id': IH, 'subtitle_index': -1}, headers=headers).status_code == 422
    assert client.post('/api/v1/player/sessions', json={'content_id': IH, 'subtitle_index': 64}, headers=headers).status_code == 422


def test_w3u_http_import_uses_existing_player_and_releases_viewer(client, player, db_session, monkeypatch):
    import json
    from sqlalchemy.orm import sessionmaker
    from app.api.endpoints.player import tuner_probe_service
    monkeypatch.setattr('app.config.database.SessionLocal', sessionmaker(bind=db_session.get_bind()))
    def no_engine(*args, **kwargs):
        raise AssertionError('W3U HTTP playback must remain engine-independent')
    monkeypatch.setattr(player, '_engine_factory', no_engine)
    monkeypatch.setattr(tuner_probe_service, 'start_for_stream', no_engine)
    preview = client.post('/api/v1/catalogues/preview', json={'sample': json.dumps({
        'stations': [{'name': 'Synthetic HLS', 'url': 'https://media.example/live.m3u8', 'userAgent': 'Fixture'}]})})
    assert preview.status_code == 200
    imported = client.post('/api/v1/catalogues', json={'preview_token': preview.json()['preview_token'],
        'name': 'Player fixture', 'confirm_live': True, 'selected_branches': ['root']})
    assert imported.status_code == 200
    stream_id = imported.json()['entries'][1]['channel_id']
    response = client.post('/api/v1/player/sessions', json={'content_id': stream_id})
    assert response.status_code == 200
    session_id = response.json()['id']
    ready = _wait_ready(client, session_id)
    assert client.get(ready['playlist_url']).status_code == 200
    assert player.get(session_id).http_source is not None
    stopped = client.delete(f'/api/v1/player/sessions/{session_id}')
    assert stopped.status_code in (200, 204)
    assert client.get(f'/api/v1/player/sessions/{session_id}').json()['viewers'] == 0


def test_event_refresh_and_alternate_playback_preserve_other_viewers(client, player, db_session, monkeypatch):
    """Event-only HTTP sources share the player lifecycle without channel insertion."""
    from sqlalchemy.orm import sessionmaker
    from app.models.models import AcestreamChannel, TVChannel
    from app.api.endpoints.player import tuner_probe_service
    from app.services.player_http_source import stored_http_source
    monkeypatch.setattr('app.config.database.SessionLocal', sessionmaker(bind=db_session.get_bind()))
    settings = player._settings()
    settings.PLAYER_MAX_SESSIONS = 3
    monkeypatch.setattr(player, '_settings', lambda: settings)

    def no_engine(*args, **kwargs):
        raise AssertionError('Event HTTP playback must not touch AceStream')
    monkeypatch.setattr(player, '_engine_factory', no_engine)
    monkeypatch.setattr(tuner_probe_service, 'start_for_stream', no_engine)
    payload = {'observations': [{'source_id': 'test', 'source_name': 'Guide', 'external_id': 'match',
        'title': 'Match', 'timezone': 'UTC', 'broadcasts': [
            {'id': 'es', 'label': 'Spanish', 'url': 'https://media.example/live.m3u8?token=first'},
            {'id': 'en', 'label': 'English', 'url': 'https://media.example/alternate.m3u8'}]}]}

    def import_event():
        preview = client.post('/api/v1/events/preview', json=payload)
        assert preview.status_code == 200
        result = client.post('/api/v1/events/apply', json={'token': preview.json()['token'],
            'selected_ids': [preview.json()['events'][0]['id']]})
        assert result.status_code == 200
        return result.json()[0]

    event = import_event()
    original_id = event['broadcasts'][0]['content_id']
    original = client.post('/api/v1/player/sessions', json={'content_id': original_id}).json()
    joined = client.post('/api/v1/player/sessions', json={'content_id': original_id}).json()
    assert joined['id'] == original['id'] and joined['viewers'] == 2
    assert original['error'] is None
    alternate = client.post('/api/v1/player/sessions', json={'content_id': event['broadcasts'][1]['content_id']}).json()
    assert alternate['error'] is None and alternate['id'] != original['id']
    client.delete('/api/v1/player/sessions/' + original['id'])
    assert client.get('/api/v1/player/sessions/' + original['id']).json()['viewers'] == 1
    payload['observations'][0]['broadcasts'][0]['url'] = 'https://media.example/live.m3u8?token=rotated'
    refreshed = import_event()
    assert refreshed['id'] == event['id']
    assert refreshed['broadcasts'][0]['content_id'] != original_id
    assert stored_http_source(original_id) is None
    retained = player.get(original['id'])
    assert retained.viewers == 1 and retained.http_source.url.endswith('token=first')
    assert db_session.query(AcestreamChannel).count() == db_session.query(TVChannel).count() == 0
    client.delete('/api/v1/player/sessions/' + alternate['id'])
    assert retained.viewers == 1
