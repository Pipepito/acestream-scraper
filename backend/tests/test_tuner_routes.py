"""HDHomeRun routes and the token-gated /api/v1/tuner settings/status API (spec 7.2)."""
import pytest

from app.config.settings import get_settings
from app.services.tuner_network import get_tuner_gate

IH = "a" * 40


@pytest.fixture
def open_gate(monkeypatch):
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "*")
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    yield
    get_settings.cache_clear(); get_tuner_gate.cache_clear()


def _seed(db):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name="DAZN 1", channel_number=12, epg_id="DAZN LaLiga HD", category="Sports", is_active=True, logo_url="http://logo")
    db.add(tv); db.flush()
    db.add(AcestreamChannel(id=IH, name="feed", is_online=True, is_active=True, tv_channel_id=tv.id)); db.commit()
    return tv


def test_discover_lineup_status_and_device_xml(client, db_session, open_gate):
    _seed(db_session)
    discover = client.get("/tuner/discover.json", headers={"Host": "scraper.lan:8000"}).json()
    assert discover["Manufacturer"] == "Silicondust" and discover["ModelNumber"] == "HDTC-2US"
    assert discover["FirmwareName"] == "hdhomeruntc_atsc" and discover["FirmwareVersion"] == "20240101"
    assert discover["BaseURL"] == "http://scraper.lan:8000/tuner" and discover["LineupURL"] == "http://scraper.lan:8000/tuner/lineup.json"
    assert discover["TunerCount"] == 4 and discover["DeviceAuth"] == "" and len(discover["DeviceID"]) == 8
    lineup = client.get("/tuner/lineup.json", headers={"Host": "scraper.lan:8000"}).json()
    assert lineup == [{"GuideNumber": "12", "GuideName": "DAZN 1", "URL": f"http://scraper.lan:8000/tuner/stream/{IH}.ts"}]
    assert client.get("/tuner/lineup_status.json").json() == {"ScanInProgress": 0, "ScanPossible": 0, "Source": "Cable", "SourceList": ["Cable"]}
    assert client.post("/tuner/lineup.post").status_code == 200
    xml = client.get("/tuner/device.xml", headers={"Host": "scraper.lan:8000"})
    assert xml.headers["content-type"].startswith("application/xml")
    assert f"uuid:{discover['DeviceID']}" in xml.text and "<URLBase>http://scraper.lan:8000/tuner</URLBase>" in xml.text


def test_guide_playlist_and_epg_variants(client, db_session, open_gate):
    _seed(db_session)
    guide = client.get("/tuner/guide.xml")
    assert guide.status_code == 200 and '<channel id="12">' in guide.text and "content-encoding" not in guide.headers
    playlist = client.get("/tuner/playlist.m3u", headers={"Host": "scraper.lan:8000"}).text
    assert 'tvg-id="DAZN LaLiga HD"' in playlist and f"http://scraper.lan:8000/tuner/stream/{IH}.ts" in playlist
    epg = client.get("/tuner/epg.xml")
    assert epg.status_code == 200 and epg.headers["content-type"].startswith("application/xml")


def test_settings_and_status_are_token_gated_and_reflect_the_gate(client, db_session, open_gate, monkeypatch):
    _seed(db_session)
    body = client.get("/api/v1/tuner/status").json()
    assert body["channel_count"] == 1 and body["renumbered"] == [] and body["overflow"] == 0
    assert body["urls"]["lineup"].endswith("/tuner/lineup.json") and body["urls"]["stream_template"].endswith("/tuner/stream/{content_id}.ts")
    assert body["client_allowed"] is True and body["client_source"] == "direct" and body["allowed_networks"] == ["*"]
    assert isinstance(body["ffmpeg_available"], bool)
    updated = client.put("/api/v1/tuner/settings", json={"friendly_name": "Lounge", "tuner_count": 2, "max_channels": 100, "only_online": True}).json()
    assert updated == {"friendly_name": "Lounge", "tuner_count": 2, "max_channels": 100, "only_online": True}
    assert client.get("/tuner/discover.json").json()["FriendlyName"] == "Lounge"
    assert client.put("/api/v1/tuner/settings", json={"max_channels": 0}).status_code == 422

    monkeypatch.setenv("API_TOKEN", "t")
    assert client.get("/api/v1/tuner/status").status_code == 401
    assert client.get("/tuner/discover.json").status_code == 200


def test_status_reports_docker_gateway_warning_and_denials(client, db_session, monkeypatch):
    monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", "10.0.0.0/8")
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    try:
        assert client.get("/tuner/lineup.json").status_code == 403
        body = client.get("/api/v1/tuner/status").json()
        assert body["client_allowed"] is False
        assert body["recent_denials"][0]["path"] == "/tuner/lineup.json"
        gate = get_tuner_gate()
        assert gate.classify_source("172.17.0.1", False) == "docker-gateway"
    finally:
        get_settings.cache_clear(); get_tuner_gate.cache_clear()


def test_stream_relays_are_capped_by_tuner_count(alembic_client, alembic_db_session, open_gate):
    # The alembic runtime is the one whose SessionLocal the route reads the cap
    # through (the fast-path `client` binds the app to the default database).
    from app.services.stream_relay import relay_registry
    from app.services.tuner_service import TunerService
    TunerService(alembic_db_session).update_settings(tuner_count=1)
    relay_registry.open(IH, "tuner:test")  # one active relay already
    try:
        response = alembic_client.get(f"/tuner/stream/{IH}.ts")
        assert response.status_code == 503 and response.json()["error"]["code"] == "TUNER_BUSY"
    finally:
        for info in relay_registry.active():
            relay_registry.close(info.id)


def test_two_clients_starting_at_once_cannot_exceed_the_tuner_count(alembic_client, alembic_db_session, open_gate, monkeypatch):
    """The slot has to be claimed, not just counted: the engine round-trip in
    between takes seconds, and every client arriving in that window would pass
    a plain count check."""
    import threading

    from app.api.endpoints import tuner as tuner_module
    from app.services.engine_client import EngineUnavailableError
    from app.services.stream_relay import relay_registry
    from app.services.tuner_service import TunerService
    TunerService(alembic_db_session).update_settings(tuner_count=1)

    in_engine, release = threading.Event(), threading.Event()

    def slow_engine():
        in_engine.set()
        release.wait(5)
        raise EngineUnavailableError("Acestream engine is not configured")

    monkeypatch.setattr(tuner_module, "_engine", slow_engine)
    statuses = {}
    first = threading.Thread(target=lambda: statuses.update(first=alembic_client.get(f"/tuner/stream/{IH}.ts").status_code))
    first.start()
    try:
        assert in_engine.wait(5), "the first request never reached the engine"
        statuses["second"] = alembic_client.get(f"/tuner/stream/{IH}.ts").status_code
    finally:
        release.set()
        first.join(5)
    assert statuses["second"] == 503  # the one slot is already claimed
    assert statuses["first"] == 502
    assert relay_registry.count_active() == 0


def test_a_relay_that_never_starts_gives_its_tuner_slot_back(alembic_client, alembic_db_session, open_gate, monkeypatch):
    """The slot is claimed before the engine is contacted, so every path that
    fails afterwards has to release it -- otherwise one 502 leaves a one-tuner
    device permanently busy."""
    from app.api.endpoints import tuner as tuner_module
    from app.services.engine_client import EngineUnavailableError
    from app.services.stream_relay import relay_registry
    from app.services.tuner_service import TunerService
    TunerService(alembic_db_session).update_settings(tuner_count=1)

    def unavailable():
        raise EngineUnavailableError("Acestream engine is not configured")

    monkeypatch.setattr(tuner_module, "_engine", unavailable)
    try:
        first = alembic_client.get(f"/tuner/stream/{IH}.ts")
        assert first.status_code == 502 and first.json()["error"]["code"] == "ENGINE_UNAVAILABLE"
        assert relay_registry.count_active() == 0
        second = alembic_client.get(f"/tuner/stream/{IH}.ts")
        assert second.status_code == 502 and second.json()["error"]["code"] == "ENGINE_UNAVAILABLE"
    finally:
        for info in relay_registry.active():
            relay_registry.close(info.id)


def test_status_warns_when_the_allowlist_cannot_see_clients_apart_and_when_capped(backend_runtime, override_get_db, db_session, open_gate):
    from fastapi.testclient import TestClient
    from app.models.models import AcestreamChannel, TVChannel
    _seed(db_session)
    second = TVChannel(name="DAZN 2", channel_number=13, is_active=True)
    db_session.add(second); db_session.flush()
    db_session.add(AcestreamChannel(id="b" * 40, name="feed 2", is_online=True, is_active=True, tv_channel_id=second.id))
    db_session.commit()
    from app.services.tuner_service import TunerService
    TunerService(db_session).update_settings(max_channels=1)
    # Behind Docker's bridge every client arrives as the gateway address, so the
    # allowlist cannot tell them apart and the page has to say so.
    docker = TestClient(backend_runtime.app, client=("172.17.0.1", 51000))
    body = docker.get("/api/v1/tuner/status").json()
    assert body["client_source"] == "docker-gateway"
    assert body["warnings"] == ["TUNER_ALLOWLIST_INEFFECTIVE", "TUNER_LINEUP_CAPPED"]
    assert body["channel_count"] == 1 and body["overflow"] == 1
