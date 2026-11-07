"""Catalogue infohashes must be resolved before becoming playback IDs (#266)."""
import json
import threading
from unittest.mock import Mock

import httpx
import pytest

from app.models.models import AcestreamChannel
from app.repositories.settings_repository import SettingsRepository
from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError

INFOHASH = "42832fbf9a1d3bdcca043e09951d6769fbbe04e7"
CONTENT_ID = "e72d03fb9694164317260f684470be9ab781ed95"


def test_resolve_uses_server_api_without_starting_playback():
    def handler(request):
        assert request.url.path == "/server/api"
        assert dict(request.url.params) == {
            "api_version": "3", "method": "get_content_id", "infohash": INFOHASH,
        }
        assert request.extensions["timeout"]["read"] == 15
        return httpx.Response(200, json={"result": {"content_id": CONTENT_ID.upper()}})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert EngineClient("http://engine:6878", client=client).resolve_content_id(INFOHASH.upper()) == CONTENT_ID


@pytest.mark.parametrize("payload", [None, [], {}, {"result": None}, {"result": CONTENT_ID},
    {"result": {}}, {"result": {"content_id": INFOHASH[:-1]}},
    {"result": {"content_id": "g" * 40}}, {"result": {"content_id": 123}}])
def test_resolve_rejects_invalid_engine_answers(payload):
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, content=json.dumps(payload)))) as client:
        with pytest.raises(EngineUnavailableError, match="invalid content ID"):
            EngineClient("http://engine:6878", client=client).resolve_content_id(INFOHASH)


@pytest.mark.parametrize("failure", ["refused", "timeout", "http", "json", "redirect"])
def test_resolve_fails_closed_without_exposing_upstream_details(failure):
    def handler(request):
        if failure == "timeout":
            raise httpx.ReadTimeout("private engine details", request=request)
        if failure == "http":
            return httpx.Response(503, text="private engine details")
        if failure == "redirect":
            return httpx.Response(302, headers={"Location": "http://other-host/private"})
        if failure == "json":
            return httpx.Response(200, text="private engine details")
        return httpx.Response(200, json={"error": "private engine details"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises((EngineUnavailableError, EngineRefusedError)) as caught:
            EngineClient("http://engine:6878", client=client).resolve_content_id(INFOHASH)
        assert "private" not in str(caught.value)


def test_resolve_endpoint_then_save_and_play_with_content_id(client, db_session, monkeypatch):
    SettingsRepository(db_session).set_setting("ace_engine_url", "http://catalogue-engine:6878")
    calls = []

    def resolve(engine, infohash):
        assert engine.engine_url == "http://catalogue-engine:6878"
        assert not engine.use_acexy
        assert infohash == INFOHASH
        # TestClient's event loop runs in a portal thread; network must be off it.
        assert "portal" not in threading.current_thread().name
        calls.append(engine)
        return CONTENT_ID

    monkeypatch.setattr(EngineClient, "resolve_content_id", resolve)
    response = client.post(f"/api/v1/search/{INFOHASH.upper()}/resolve")
    assert response.status_code == 200
    assert response.json() == {"content_id": CONTENT_ID}
    assert db_session.query(AcestreamChannel).count() == 0
    assert calls[0]._client.is_closed
    saved = client.post("/api/v1/acestream-channels", json={"id": response.json()["content_id"], "name": "NBA TV [US]", "group": "sports"})
    assert saved.status_code == 201
    assert db_session.get(AcestreamChannel, INFOHASH) is None
    assert db_session.get(AcestreamChannel, CONTENT_ID).group == "sports"

    def start(request):
        # An engine that refuses the infohash when sent as an id.
        assert request.url.params["id"] == CONTENT_ID
        return httpx.Response(200, json={"response": {
            "playback_url": "http://engine:6878/stream", "stat_url": "http://engine:6878/stat",
            "command_url": "http://engine:6878/stop", "is_live": 1,
        }})

    with httpx.Client(transport=httpx.MockTransport(start)) as transport:
        engine = EngineClient("http://engine:6878", client=transport)
        session = engine.start(saved.json()["id"])
        monkeypatch.setattr(engine, "_stop_direct", Mock())
        engine.stop(session)
        acexy = EngineClient("http://acexy:8080", client=transport, use_acexy=True)
        assert httpx.URL(acexy.start(saved.json()["id"]).playback_url).params["id"] == CONTENT_ID


@pytest.mark.parametrize("error", [EngineRefusedError("private details"), EngineUnavailableError("private details")])
def test_resolve_endpoint_failure_preserves_inventory(client, db_session, monkeypatch, error):
    SettingsRepository(db_session).set_setting("ace_engine_url", "http://engine:6878")
    original = AcestreamChannel(id=INFOHASH, name="Previously saved", is_online=False)
    db_session.add(original)
    db_session.commit()
    monkeypatch.setattr(EngineClient, "resolve_content_id", Mock(side_effect=error))
    response = client.post(f"/api/v1/search/{INFOHASH}/resolve")
    assert response.status_code == 502
    assert "private" not in response.text
    db_session.refresh(original)
    assert original.name == "Previously saved"
    assert original.is_online is False
    assert db_session.query(AcestreamChannel).count() == 1


def test_resolve_rejects_invalid_hash_and_missing_engine(client, db_session, monkeypatch):
    resolve = Mock()
    monkeypatch.setattr(EngineClient, "resolve_content_id", resolve)
    assert client.post("/api/v1/search/not-a-hash/resolve").status_code == 422
    SettingsRepository(db_session).set_setting("ace_engine_url", "")
    assert client.post(f"/api/v1/search/{INFOHASH}/resolve").status_code == 503
    resolve.assert_not_called()
