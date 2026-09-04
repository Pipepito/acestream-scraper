"""Contract tests for the media-integration payload shapes (spec 4.3, 5.1).

Key sets rather than values: these pin the JSON the OpenAPI document and the
frontend's generated types are built from, so a renamed or dropped field fails
here before it reaches a browser.
"""
import httpx
import pytest
from pydantic import ValidationError

from app.schemas.media_servers import MediaServerCreate
from app.schemas.player import PlayerSessionCreate
from app.schemas.remote_players import RemotePlayerCreate


@pytest.mark.parametrize("content_id", ["0" * 40, "a" * 40, "F" * 40, "0123456789abcdefABCDEF" + "0" * 18])
def test_player_session_create_accepts_40_hex(content_id):
    assert PlayerSessionCreate(content_id=content_id).content_id == content_id


@pytest.mark.parametrize("content_id", ["", "0" * 39, "0" * 41, "g" * 40, "0" * 39 + "-", " " + "0" * 40])
def test_player_session_create_rejects_anything_else(content_id):
    with pytest.raises(ValidationError):
        PlayerSessionCreate(content_id=content_id)


def test_player_session_create_rejects_a_bad_content_id_over_http(client):
    assert client.post("/api/v1/player/sessions", json={"content_id": "nope"}).status_code == 422


def test_player_capabilities_response_contract(client):
    response = client.get("/api/v1/player/capabilities")
    assert response.status_code == 200
    assert set(response.json()) == {"ffmpeg_available", "ffmpeg_path", "max_sessions", "hls_dir"}


def test_player_sessions_response_contract(client):
    response = client.get("/api/v1/player/sessions")
    assert response.status_code == 200
    assert set(response.json()) == {"sessions"}


def test_active_streams_response_contract(client):
    response = client.get("/api/v1/player/streams")
    assert response.status_code == 200
    assert set(response.json()) == {"streams"}


def test_public_url_response_contract(client):
    response = client.get("/api/v1/system/public-url")
    assert response.status_code == 200
    assert set(response.json()) == {"url", "source", "warnings"}


# --- Remote players (spec 6.1) -------------------------------------------------

VLC_STATUS = {"apiversion": 3, "version": "3.0.21", "state": "stopped", "volume": 128}


@pytest.fixture
def remote_player_transport(monkeypatch):
    """Answer every driver request as a healthy VLC, so these tests touch no network."""
    import app.api.endpoints.remote_players as endpoint

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=VLC_STATUS))
    monkeypatch.setattr(endpoint, "_client_factory", lambda: httpx.Client(transport=transport))


def _player_body(**overrides):
    body = {"name": "Living room", "kind": "vlc", "host": "192.168.1.20", "port": 8080}
    body.update(overrides)
    return body


@pytest.mark.parametrize("kind", ["vlc", "kodi"])
def test_remote_player_create_accepts_both_kinds(kind):
    assert RemotePlayerCreate(**_player_body(kind=kind)).kind == kind


@pytest.mark.parametrize("kind", ["mpv", "VLC", "", "vlc "])
def test_remote_player_create_rejects_other_kinds(kind):
    with pytest.raises(ValidationError):
        RemotePlayerCreate(**_player_body(kind=kind))


@pytest.mark.parametrize("port", [1, 8080, 65535])
def test_remote_player_create_accepts_ports_in_range(port):
    assert RemotePlayerCreate(**_player_body(port=port)).port == port


@pytest.mark.parametrize("port", [0, -1, 65536, 100000])
def test_remote_player_create_rejects_ports_out_of_range(port):
    with pytest.raises(ValidationError):
        RemotePlayerCreate(**_player_body(port=port))


def test_remote_player_create_defaults_the_port_to_8080():
    body = _player_body()
    del body["port"]
    assert RemotePlayerCreate(**body).port == 8080


def test_remote_player_response_contract(alembic_client, remote_player_transport):
    created = alembic_client.post("/api/v1/remote-players", json=_player_body(password="pw"))
    assert created.status_code == 201, created.text
    keys = {
        "id",
        "name",
        "kind",
        "host",
        "port",
        "username",
        "base_url_id",
        "has_password",
        "created_at",
        "updated_at",
    }
    assert set(created.json()) == keys
    listed = alembic_client.get("/api/v1/remote-players")
    assert listed.status_code == 200
    assert [set(item) for item in listed.json()] == [keys]


def test_remote_player_probe_response_contract(alembic_client, remote_player_transport):
    response = alembic_client.post("/api/v1/remote-players/test", json=_player_body())
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"reachable", "authenticated", "version", "message", "hint", "tuner_access"}
    assert set(body["tuner_access"]) == {"addresses", "allowed"}


def test_scan_default_response_contract(alembic_client):
    response = alembic_client.get("/api/v1/remote-players/scan/default")
    assert response.status_code == 200
    assert set(response.json()) == {"cidr", "hint"}


def test_forbidden_player_host_error_contract(alembic_client, remote_player_transport):
    response = alembic_client.post("/api/v1/remote-players", json=_player_body(host="169.254.169.254"))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "REMOTE_PLAYER_HOST_FORBIDDEN"
    assert error["context"]["host"] == "169.254.169.254"


def test_non_private_scan_cidr_error_contract(alembic_client):
    response = alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "8.8.8.0/24"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"


# --- Tuner (spec 7.1, 7.2) -----------------------------------------------------


@pytest.fixture
def tuner_gate(monkeypatch):
    """Set TUNER_ALLOWED_NETWORKS for one test and clear both caches around it.

    Both are `lru_cache`d, so a test that leaves them warm decides the gate for
    every later one — the teardown matters as much as the setup.
    """
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate

    def apply(spec: str) -> None:
        monkeypatch.setenv("TUNER_ALLOWED_NETWORKS", spec)
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()

    yield apply
    get_settings.cache_clear()
    get_tuner_gate.cache_clear()


def test_tuner_settings_response_contract(client):
    response = client.get("/api/v1/tuner/settings")
    assert response.status_code == 200
    assert set(response.json()) == {"friendly_name", "tuner_count", "max_channels", "only_online"}


def test_tuner_status_response_contract(client, tuner_gate):
    tuner_gate("*")
    response = client.get("/api/v1/tuner/status")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "channel_count",
        "renumbered",
        "overflow",
        "device_id",
        "urls",
        "ffmpeg_available",
        "allowed_networks",
        "client_ip",
        "peer",
        "client_allowed",
        "client_source",
        "warnings",
        "recent_denials",
    }
    assert set(body["urls"]) == {"tuner", "lineup", "guide", "playlist", "epg", "stream_template"}


def test_denied_tuner_client_error_contract(client, tuner_gate):
    tuner_gate("10.0.0.0/8")  # the TestClient peer is "testclient", so every /tuner route is refused
    response = client.get("/tuner/discover.json")
    assert response.status_code == 403
    error = response.json()["error"]
    assert error["code"] == "TUNER_NETWORK_DENIED"
    assert set(error["context"]) == {"client_ip", "peer", "allowed_networks"}
    assert error["context"]["allowed_networks"] == ["10.0.0.0/8"]


def test_tuner_busy_error_contract(alembic_client, alembic_db_session, tuner_gate):
    """A relay beyond `tuner_count` is 503 TUNER_BUSY carrying the cap it hit."""
    tuner_gate("*")
    from app.services.stream_relay import relay_registry
    from app.services.tuner_service import TunerService

    content_id = "b" * 40
    TunerService(alembic_db_session).update_settings(tuner_count=1)
    claim = relay_registry.open(content_id, "tuner:contract-test")
    try:
        response = alembic_client.get(f"/tuner/stream/{content_id}.ts")
    finally:
        relay_registry.close(claim.id)
    assert response.status_code == 503
    error = response.json()["error"]
    assert error["code"] == "TUNER_BUSY"
    assert error["context"] == {"limit": 1}


# --- Media servers (spec 7.3) --------------------------------------------------

MEDIA_SERVER_KEYS = {
    "id",
    "kind",
    "name",
    "base_url",
    "tuner_mode",
    "enabled",
    "auto_refresh",
    "has_api_key",
    "connected",
    "tuner_host_id",
    "listing_provider_id",
    "dvr_key",
    "last_sync_at",
    "last_sync_status",
    "last_error",
    "server_version",
    "created_at",
    "updated_at",
}


JELLYFIN_INFO = {"Version": "10.11.11", "ServerName": "Jellyfin", "Id": "abc"}


@pytest.fixture
def media_server_transport(monkeypatch):
    """Answer as a healthy Jellyfin, so these tests touch no network.

    The base URL is a loopback literal: `guard()` resolves the host before every
    request, and a made-up name would fail there instead of reaching the mock.
    """
    import app.api.endpoints.media_servers as endpoint

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/System/Info/Public":
            return httpx.Response(200, json=JELLYFIN_INFO)
        if request.url.path == "/System/Configuration/livetv":
            return httpx.Response(200, json={"TunerHosts": [], "ListingProviders": []})
        return httpx.Response(404, json={})

    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(endpoint, "_client_factory", lambda: httpx.Client(transport=transport))


def _media_server_body(**overrides):
    body = {"kind": "jellyfin", "name": "Jellyfin", "base_url": "http://127.0.0.1:8096", "api_key": "good"}
    body.update(overrides)
    return body


@pytest.mark.parametrize("kind", ["jellyfin", "plex"])
def test_media_server_create_accepts_both_kinds(kind):
    assert MediaServerCreate(**_media_server_body(kind=kind)).kind == kind


@pytest.mark.parametrize("kind", ["emby", "Jellyfin", "", "plex "])
def test_media_server_create_rejects_other_kinds(kind):
    with pytest.raises(ValidationError):
        MediaServerCreate(**_media_server_body(kind=kind))


@pytest.mark.parametrize("mode", ["hdhomerun", "m3u"])
def test_media_server_create_accepts_both_tuner_modes(mode):
    assert MediaServerCreate(**_media_server_body(tuner_mode=mode)).tuner_mode == mode


@pytest.mark.parametrize("mode", ["hdhr", "M3U", "", "xmltv"])
def test_media_server_create_rejects_other_tuner_modes(mode):
    with pytest.raises(ValidationError):
        MediaServerCreate(**_media_server_body(tuner_mode=mode))


def test_media_server_create_defaults_to_the_hdhomerun_mode():
    body = _media_server_body()
    assert "tuner_mode" not in body
    created = MediaServerCreate(**body)
    assert created.tuner_mode == "hdhomerun" and created.enabled is True and created.auto_refresh is True


def test_media_server_response_contract(alembic_client, media_server_transport):
    created = alembic_client.post("/api/v1/media-servers", json=_media_server_body())
    assert created.status_code == 201, created.text
    assert set(created.json()) == MEDIA_SERVER_KEYS
    assert "api_key" not in created.json()
    listed = alembic_client.get("/api/v1/media-servers")
    assert listed.status_code == 200
    assert [set(item) for item in listed.json()] == [MEDIA_SERVER_KEYS]


def test_media_server_status_response_contract(alembic_client, media_server_transport):
    server = alembic_client.post("/api/v1/media-servers", json=_media_server_body()).json()
    response = alembic_client.get(f"/api/v1/media-servers/{server['id']}/status")
    assert response.status_code == 200
    assert set(response.json()) == {"connected", "channel_count", "refresh_state", "last_result", "steps", "paste", "error"}


def test_media_server_probe_response_contract(alembic_client, media_server_transport):
    response = alembic_client.post(
        "/api/v1/media-servers/test",
        json={"kind": "jellyfin", "base_url": "http://127.0.0.1:8096", "api_key": "good"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"reachable", "authenticated", "credentials", "version", "message", "tuner_access"}
    assert body["credentials"] == "ok"
    assert set(body["tuner_access"]) == {"addresses", "allowed"}


def test_forbidden_media_server_url_error_contract(alembic_client, media_server_transport):
    response = alembic_client.post("/api/v1/media-servers", json=_media_server_body(base_url="http://169.254.169.254"))
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "MEDIA_SERVER_URL_FORBIDDEN"
    assert error["context"]["base_url"] == "http://169.254.169.254"


def test_both_probes_publish_the_same_tuner_access_schema(alembic_client):
    """`tuner_access` means one thing, so it must be one named schema.

    Declared inline as a bare object it still serialises correctly, but the
    generated frontend types degrade it to an index signature and the fields
    disappear from the client contract.
    """
    schemas = alembic_client.get("/openapi.json").json()["components"]["schemas"]
    reference = {"$ref": "#/components/schemas/TunerAccessResponse"}
    assert schemas["MediaServerProbeResponse"]["properties"]["tuner_access"] == reference
    assert schemas["RemotePlayerProbeResponse"]["properties"]["tuner_access"] == reference
    assert set(schemas["TunerAccessResponse"]["properties"]) == {"addresses", "allowed"}
