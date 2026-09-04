"""Jellyfin/Plex sync (spec 7.3) against recorded fake servers."""
import json
import socket
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.services.media_servers.base import MediaServerAuthError, MediaServerError, MediaServerUnreachable
from app.services.media_servers.service import MediaServerService, RefreshResult

PUBLIC = "http://scraper.lan:8000"


@pytest.fixture(autouse=True)
def resolvable_fake_hosts(monkeypatch):
    """Every client guards its request with validate_lan_target(resolve=True)
    (spec 4.4), so the fake ``.lan`` servers must resolve to a LAN address."""
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, *args, **kwargs):
        if str(host).endswith(".lan"):
            return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.50", 0))]
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


class FakeJellyfin:
    """Enough of the Jellyfin API for the client: tuners/providers upsert, tasks, channels."""

    def __init__(self):
        self.tuners = {}
        self.providers = {}
        self.started = []
        self.requests = []
        self.refresh_state = "Idle"
        self.reject_key = False

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        auth = request.headers.get("Authorization", "")
        path = request.url.path
        if path == "/System/Info/Public":
            return httpx.Response(200, json={"Version": "10.11.11", "ServerName": "jf"})
        if not auth.startswith('MediaBrowser Token="good"') or self.reject_key:
            return httpx.Response(401, text="Unauthorized")
        if path == "/System/Configuration/livetv":
            return httpx.Response(200, json={"TunerHosts": list(self.tuners.values()), "ListingProviders": list(self.providers.values()), "GuideDays": 7})
        if path == "/LiveTv/TunerHosts" and request.method == "POST":
            body = json.loads(request.content)
            body["Id"] = body.get("Id") or f"tuner{len(self.tuners) + 1}"
            self.tuners[body["Id"]] = body
            return httpx.Response(200, json=body)
        if path == "/LiveTv/TunerHosts" and request.method == "DELETE":
            self.tuners.pop(request.url.params["id"], None)
            return httpx.Response(204)
        if path == "/LiveTv/ListingProviders" and request.method == "POST":
            body = json.loads(request.content)
            body["Id"] = body.get("Id") or f"prov{len(self.providers) + 1}"
            self.providers[body["Id"]] = body
            return httpx.Response(200, json=body)
        if path == "/LiveTv/ListingProviders" and request.method == "DELETE":
            self.providers.pop(request.url.params["id"], None)
            return httpx.Response(204)
        if path == "/ScheduledTasks":
            return httpx.Response(200, json=[{"Id": "abc", "Key": "RefreshGuide", "Name": "Refresh Guide", "State": self.refresh_state, "LastExecutionResult": {"Status": "Completed"}}, {"Id": "x", "Key": "Other", "State": "Idle"}])
        if path == "/ScheduledTasks/Running/abc" and request.method == "POST":
            self.started.append(1)
            return httpx.Response(204)
        if path == "/LiveTv/Channels":
            return httpx.Response(200, json={"Items": [], "TotalRecordCount": 42})
        return httpx.Response(404)


@pytest.fixture
def jellyfin():
    return FakeJellyfin()


def _service(db, handler):
    return MediaServerService(db, client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)))


def _server(svc, **overrides):
    fields = dict(kind="jellyfin", name="Jelly", base_url="http://jellyfin.lan:8096", api_key="good", tuner_mode="hdhomerun")
    fields.update(overrides)
    return svc.repo.create(**fields)


def test_validate_base_url(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    assert svc.validate_base_url(" http://jellyfin.lan:8096/ ") == "http://jellyfin.lan:8096"
    assert svc.validate_base_url("https://plex.lan:32400/plex") == "https://plex.lan:32400/plex"
    for bad in ("jellyfin.lan", "http://user:pw@host", "http://169.254.169.254:8096", "ftp://x"):
        with pytest.raises(Exception):
            svc.validate_base_url(bad)


def test_jellyfin_connect_upserts_and_refresh_triggers_task(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    svc.connect(server, PUBLIC)
    assert server.tuner_host_id == "tuner1" and server.listing_provider_id == "prov1" and server.server_version == "10.11.11"
    tuner = jellyfin.tuners["tuner1"]
    assert tuner["Type"] == "hdhomerun" and tuner["Url"] == f"{PUBLIC}/tuner" and tuner["AllowHWTranscoding"] is False and tuner["TunerCount"] == 0
    provider = jellyfin.providers["prov1"]
    assert provider["Type"] == "xmltv" and provider["Path"] == f"{PUBLIC}/tuner/guide.xml" and provider["EnabledTuners"] == ["tuner1"] and provider["EnableAllTuners"] is False
    header = next(r.headers["Authorization"] for r in jellyfin.requests if "Authorization" in r.headers)
    assert 'Client="acestream-scraper"' in header and 'DeviceId="' in header and 'Version="' in header
    # Reconnect reuses the ids (no duplicates)
    svc.connect(server, PUBLIC)
    assert len(jellyfin.tuners) == 1 and len(jellyfin.providers) == 1

    result = svc.refresh(server)
    assert result.status == "ok" and jellyfin.started == [1]
    jellyfin.refresh_state = "Running"
    assert svc.refresh(server).status == "ok" and jellyfin.started == [1]  # already running: not re-triggered

    status = svc.status(server, PUBLIC)
    assert status["connected"] is True and status["channel_count"] == 42 and status["refresh_state"] == "Running"

    svc.disconnect(server)
    assert jellyfin.tuners == {} and jellyfin.providers == {} and server.tuner_host_id is None


def test_jellyfin_m3u_mode_uses_playlist_and_epg(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc, tuner_mode="m3u")
    svc.connect(server, PUBLIC)
    assert jellyfin.tuners["tuner1"]["Type"] == "m3u" and jellyfin.tuners["tuner1"]["Url"] == f"{PUBLIC}/tuner/playlist.m3u"
    assert jellyfin.providers["prov1"]["Path"] == f"{PUBLIC}/tuner/epg.xml"


def test_test_uses_stored_key_when_none_given_and_maps_auth(alembic_db_session, jellyfin):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    probe = svc.test("jellyfin", "http://jellyfin.lan:8096", None, stored_id=server.id)
    assert probe["reachable"] and probe["authenticated"] and probe["version"] == "10.11.11"
    probe = svc.test("jellyfin", "http://jellyfin.lan:8096", "bad", stored_id=None)
    assert probe["reachable"] and probe["authenticated"] is False
    # ... but only for the address that row already talks to.
    jellyfin.requests.clear()
    probe = svc.test("jellyfin", "http://collector.lan:8096", None, stored_id=server.id)
    assert probe["authenticated"] is False
    assert all("good" not in r.headers.get("Authorization", "") for r in jellyfin.requests)
    jellyfin.reject_key = True
    with pytest.raises(MediaServerAuthError):
        svc.refresh(server)


class FakePlex:
    def __init__(self):
        self.reloads = []

    def handler(self, request):
        path = request.url.path
        if path == "/identity":
            return httpx.Response(200, json={"MediaContainer": {"version": "1.43.0.1", "machineIdentifier": "m"}})
        if request.headers.get("X-Plex-Token") != "tok":
            return httpx.Response(401)
        if path == "/livetv/dvrs":
            return httpx.Response(200, json={"MediaContainer": {"Dvr": [{"key": "7", "uuid": "u", "lineup": "lineup://tv.plex.providers.epg.xmltv/x", "Device": [{"uri": f"device://tv.plex.grabbers.hdhomerun/{'A' * 8}", "uuid": "d"}]}]}})
        if path == "/livetv/dvrs/7/reloadGuide" and request.method == "POST":
            self.reloads.append(1)
            return httpx.Response(200)
        return httpx.Response(404)


def test_plex_connect_finds_the_dvr_and_refreshes(alembic_db_session, monkeypatch):
    plex = FakePlex()
    svc = _service(alembic_db_session, plex.handler)
    server = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key="tok", tuner_mode="hdhomerun")
    monkeypatch.setattr("app.services.media_servers.service.TunerService.device_id", lambda self: "A" * 8)
    svc.connect(server, PUBLIC)
    assert server.dvr_key == "7"
    assert svc.refresh(server).status == "ok" and plex.reloads == [1]
    instructions = svc.status(server, PUBLIC)
    assert instructions["steps"] and f"{PUBLIC}/tuner/guide.xml" in json.dumps(instructions)


def test_plex_without_token_is_manual(alembic_db_session):
    plex = FakePlex()
    svc = _service(alembic_db_session, plex.handler)
    server = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None, tuner_mode="hdhomerun")
    assert svc.refresh(server).status == "manual"


def test_sync_if_changed_debounces_and_records_manual(alembic_db_session, jellyfin, monkeypatch):
    svc = _service(alembic_db_session, jellyfin.handler)
    server = _server(svc)
    svc.connect(server, PUBLIC)
    monkeypatch.setenv("MEDIA_SERVER_MIN_REFRESH_MINUTES", "30")
    from app.config.settings import get_settings
    get_settings.cache_clear()
    try:
        first = svc.sync_if_changed(server)
        assert first is not None and first.status == "ok" and jellyfin.started == [1]
        assert svc.sync_if_changed(server) is None  # nothing changed
        # Lineup changes but the debounce window has not elapsed
        from app.models.models import AcestreamChannel, TVChannel
        tv = TVChannel(name="New", channel_number=3, is_active=True); alembic_db_session.add(tv); alembic_db_session.flush()
        alembic_db_session.add(AcestreamChannel(id="b" * 40, name="f", is_online=True, is_active=True, tv_channel_id=tv.id)); alembic_db_session.commit()
        assert svc.sync_if_changed(server) is None and jellyfin.started == [1]
        server.last_sync_at = datetime.now(timezone.utc) - timedelta(minutes=31); alembic_db_session.commit()
        assert svc.sync_if_changed(server).status == "ok" and jellyfin.started == [1, 1]
        # Plex without token: manual status stored, last_sync_at untouched
        plex = svc.repo.create(kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None, tuner_mode="hdhomerun")
        assert svc.sync_if_changed(plex).status == "manual"
        assert plex.last_sync_status == "manual" and plex.last_sync_at is None and plex.last_lineup_fingerprint
    finally:
        get_settings.cache_clear()


def test_refresh_retries_once_while_jellyfin_is_busy(alembic_db_session, jellyfin, monkeypatch):
    busy = {"left": 1}

    def handler(request):
        if request.url.path == "/ScheduledTasks" and busy["left"]:
            busy["left"] -= 1
            return httpx.Response(503, text="Service Unavailable")
        return jellyfin.handler(request)

    svc = _service(alembic_db_session, handler)
    server = _server(svc)
    slept = []
    monkeypatch.setattr("app.services.media_servers.service.time.sleep", slept.append)
    assert svc.refresh(server).status == "ok" and jellyfin.started == [1] and slept == [2.0]


def test_connect_hints_at_the_public_address_when_jellyfin_refuses_the_tuner(alembic_db_session, jellyfin):
    def handler(request):
        if request.url.path == "/LiveTv/TunerHosts" and request.method == "POST":
            return httpx.Response(400, text="Unable to download the lineup")
        return jellyfin.handler(request)

    svc = _service(alembic_db_session, handler)
    server = _server(svc)
    with pytest.raises(MediaServerError) as raised:
        svc.connect(server, PUBLIC)
    assert raised.value.status_code == 400
    assert f"{PUBLIC}/tuner" in str(raised.value) and "check the public address" in str(raised.value)
    assert server.tuner_host_id is None and jellyfin.providers == {}


def test_sync_task_skips_disabled_servers_and_isolates_errors(alembic_db_session, jellyfin, monkeypatch):
    from app.tasks import media_server_sync_task as task_module

    svc = _service(alembic_db_session, jellyfin.handler)
    _server(svc, name="refreshed")
    svc.repo.create(kind="plex", name="needs a rescan", base_url="http://plex.lan:32400", api_key=None, tuner_mode="hdhomerun")
    _server(svc, name="broken")
    _server(svc, name="unchanged")
    _server(svc, name="auto refresh off", auto_refresh=False)
    _server(svc, name="disabled", enabled=False)

    outcomes = {"refreshed": RefreshResult("ok"), "needs a rescan": RefreshResult("manual"), "unchanged": None}

    def fake_sync(self, server):
        if server.name == "broken":
            raise MediaServerUnreachable("no answer from the server")
        return outcomes[server.name]

    monkeypatch.setattr(MediaServerService, "sync_if_changed", fake_sync)
    monkeypatch.setattr(task_module, "SessionLocal", lambda: alembic_db_session)

    assert task_module.run_media_server_sync_task() == {"checked": 4, "refreshed": 1, "manual": 1, "errors": 1}
    broken = svc.repo.get_by_name("broken")
    assert broken.last_sync_status == "error" and "no answer" in broken.last_error


def test_a_failed_sync_keeps_the_fingerprints_so_the_next_pass_retries(alembic_db_session, jellyfin):
    """An error must not consume the change: the next pass has to try it again."""
    broken = {"passes": 1}

    def handler(request):
        if request.url.path == "/ScheduledTasks" and broken["passes"]:
            broken["passes"] -= 1
            return httpx.Response(500, text="Internal Server Error")
        return jellyfin.handler(request)

    svc = _service(alembic_db_session, handler)
    server = _server(svc)

    failed = svc.sync_if_changed(server)
    assert failed.status == "error" and jellyfin.started == []
    assert server.last_sync_status == "error" and "500" in server.last_error
    assert server.last_lineup_fingerprint is None and server.last_guide_fingerprint is None

    retried = svc.sync_if_changed(server)
    assert retried.status == "ok" and jellyfin.started == [1]
    assert server.last_lineup_fingerprint and server.last_guide_fingerprint
    assert server.last_sync_status == "ok" and server.last_error is None


def test_a_non_json_answer_stays_inside_the_error_contract(alembic_db_session):
    """A wrong port/path answers 200 with HTML; that must map to MediaServerError."""

    def html(request):
        return httpx.Response(200, text="<html><body>not the API</body></html>", headers={"content-type": "text/html"})

    svc = _service(alembic_db_session, html)

    with pytest.raises(MediaServerError) as raised:
        svc.test("jellyfin", "http://jellyfin.lan:8096", "good")
    assert raised.value.status_code == 200 and "expected JSON" in str(raised.value)
    with pytest.raises(MediaServerError):
        svc.test("plex", "http://plex.lan:32400", "tok")

    server = _server(svc)
    server.tuner_host_id, server.listing_provider_id = "t1", "p1"
    svc.repo.save(server)
    assert svc.sync_if_changed(server).status == "error"
    assert server.last_lineup_fingerprint is None and "expected JSON" in server.last_error
    reported = svc.status(server, PUBLIC)
    assert reported["connected"] is True and "expected JSON" in reported["error"]
