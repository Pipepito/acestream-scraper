"""Contract tests for the media-integration payload shapes (spec 4.3, 5.1).

Key sets rather than values: these pin the JSON the OpenAPI document and the
frontend's generated types are built from, so a renamed or dropped field fails
here before it reaches a browser.
"""
import httpx
import pytest
from pydantic import ValidationError

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


def test_public_url_response_contract(client):
    response = client.get("/api/v1/system/public-url")
    assert response.status_code == 200
    assert set(response.json()) == {"url", "source", "warnings"}


# --- Remote players (spec 6.1) -------------------------------------------------

VLC_STATUS = {"apiversion": 3, "version": "3.0.21", "state": "stopped", "volume": 128}


@pytest.fixture
def remote_player_transport(monkeypatch):
    """Route every driver client through a MockTransport; tests set `.handler`."""
    import app.api.endpoints.remote_players as endpoint

    state = {"handler": lambda request: httpx.Response(200, json=VLC_STATUS)}
    monkeypatch.setattr(
        endpoint,
        "_client_factory",
        lambda: httpx.Client(transport=httpx.MockTransport(lambda r: state["handler"](r))),
    )
    return state


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


def test_public_scan_cidr_error_contract(alembic_client):
    response = alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "8.8.8.0/24"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"
