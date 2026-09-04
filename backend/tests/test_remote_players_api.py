import base64

import httpx
import pytest

VLC_OK = {"apiversion": 3, "version": "3.0.23", "state": "playing", "time": 5, "length": 0, "volume": 128, "information": {"category": {"meta": {"title": "Arena"}}}}
IH = "0" * 40


@pytest.fixture
def vlc(monkeypatch):
    """Route every driver client through a MockTransport; tests set `vlc.handler`."""
    import app.api.endpoints.remote_players as endpoint
    state = {"handler": lambda r: httpx.Response(200, json=VLC_OK)}

    def factory():
        return httpx.Client(transport=httpx.MockTransport(lambda r: state["handler"](r)))
    monkeypatch.setattr(endpoint, "_client_factory", factory)
    return state


def _create(client, **overrides):
    body = {"name": "Living room", "kind": "vlc", "host": "192.168.1.20", "port": 8080, "password": "pw"}
    body.update(overrides)
    return client.post("/api/v1/remote-players", json=body)


def test_crud_masks_the_password(alembic_client, vlc):
    created = _create(alembic_client)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_password"] is True and "password" not in body and body["base_url_id"] is None
    assert _create(alembic_client).status_code == 409
    patched = alembic_client.patch(f"/api/v1/remote-players/{body['id']}", json={"name": "Lounge"})
    assert patched.json()["name"] == "Lounge" and patched.json()["port"] == 8080 and patched.json()["has_password"] is True
    assert alembic_client.get("/api/v1/remote-players").json()[0]["name"] == "Lounge"
    assert alembic_client.delete(f"/api/v1/remote-players/{body['id']}").status_code == 204
    assert alembic_client.get("/api/v1/remote-players").json() == []


def test_forbidden_host_is_422(alembic_client, vlc):
    response = _create(alembic_client, host="169.254.169.254")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REMOTE_PLAYER_HOST_FORBIDDEN"


def test_test_endpoint_without_a_row(alembic_client, vlc):
    probes = []

    def handler(request):
        probes.append(request.headers.get("Authorization"))
        return httpx.Response(403)
    vlc["handler"] = handler
    response = alembic_client.post("/api/v1/remote-players/test", json={"kind": "vlc", "host": "192.168.1.20", "port": 8080})
    assert response.status_code == 200
    body = response.json()
    assert body["reachable"] and not body["authenticated"] and "password" in body["hint"].lower()
    assert set(body["tuner_access"]) == {"addresses", "allowed"}
    assert alembic_client.get("/api/v1/remote-players").json() == []


def test_status_play_command_and_error_codes(alembic_client, vlc):
    player = _create(alembic_client).json()
    status = alembic_client.get(f"/api/v1/remote-players/{player['id']}/status").json()
    assert status == {"state": "playing", "title": "Arena", "position_s": 5, "length_s": None, "volume_pct": 50, "message": None}
    play = alembic_client.post(f"/api/v1/remote-players/{player['id']}/play", json={"content_id": IH, "title": "Arena"})
    assert play.status_code == 202 and play.json()["url"].endswith(f"/tuner/stream/{IH}.ts")
    assert alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "volume", "value": 50}).status_code == 204
    assert alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "seek", "value": 1}).status_code == 422

    vlc["handler"] = lambda r: httpx.Response(401)
    response = alembic_client.get(f"/api/v1/remote-players/{player['id']}/status")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "REMOTE_PLAYER_AUTH" and response.json()["error"]["context"]["kind"] == "wrong_password"

    def down(request):
        raise httpx.ConnectError("down")
    vlc["handler"] = down
    assert alembic_client.get(f"/api/v1/remote-players/{player['id']}/status").json()["error"]["code"] == "REMOTE_PLAYER_UNREACHABLE"

    vlc["handler"] = lambda r: httpx.Response(200, text="<pre>bad argument</pre>", headers={"Content-Type": "text/html"})
    response = alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "stop"})
    assert response.status_code == 400 and response.json()["error"]["code"] == "REMOTE_PLAYER_COMMAND_FAILED"


def test_scan_validation_and_default(alembic_client, vlc):
    assert alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "8.8.8.0/22"}).json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"
    assert alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "10.0.0.0/8"}).json()["error"]["code"] == "SCAN_TOO_LARGE"
    body = alembic_client.get("/api/v1/remote-players/scan/default").json()
    assert body["cidr"] is None and body["hint"]
    response = alembic_client.post("/api/v1/remote-players/scan", json={"cidr": "127.0.0.1/32", "ports": [1], "timeout_ms": 100})
    assert response.json()["error"]["code"] == "SCAN_CIDR_NOT_PRIVATE"


def test_volume_without_a_value_is_rejected(alembic_client, vlc):
    """A client mistake must not reach the driver as a 500."""
    player = _create(alembic_client).json()
    response = alembic_client.post(f"/api/v1/remote-players/{player['id']}/command", json={"command": "volume"})
    assert response.status_code == 422


def _basic_secret(header):
    """The password half of a Basic auth header."""
    return base64.b64decode(header.split(" ", 1)[1]).decode().split(":", 1)[1]


def test_probe_answers_when_the_port_is_not_a_player(alembic_client, vlc):
    """A router page or a printer on the probed port is an answer, not a 500."""
    vlc["handler"] = lambda r: httpx.Response(200, text="<html><body>Router login</body></html>", headers={"Content-Type": "text/html"})
    response = alembic_client.post("/api/v1/remote-players/test", json={"kind": "vlc", "host": "192.168.1.20", "port": 80})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reachable"] is False and body["authenticated"] is False and body["hint"]

    player = _create(alembic_client).json()
    vlc["handler"] = lambda r: httpx.Response(500, text="server error")
    saved = alembic_client.post(f"/api/v1/remote-players/{player['id']}/test")
    assert saved.status_code == 200, saved.text
    assert saved.json()["reachable"] is False


def test_probe_with_an_id_reuses_the_password_only_for_that_target(alembic_client, vlc):
    """The stored secret must not travel to any address the body names."""
    player = _create(alembic_client).json()  # 192.168.1.20:8080, password "pw"
    seen = []

    def handler(request):
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=VLC_OK)
    vlc["handler"] = handler

    same = alembic_client.post("/api/v1/remote-players/test", json={"kind": "vlc", "host": "192.168.1.20", "port": 8080, "id": player["id"]})
    assert same.status_code == 200 and same.json()["authenticated"] is True
    for elsewhere in ({"host": "192.168.1.99", "port": 8080}, {"host": "192.168.1.20", "port": 9090}):
        body = {"kind": "vlc", "id": player["id"], **elsewhere}
        assert alembic_client.post("/api/v1/remote-players/test", json=body).status_code == 200
    assert _basic_secret(seen[0]) == "pw"
    assert [_basic_secret(header) for header in seen[1:]] == ["", ""]


def test_moving_a_player_forgets_its_password(alembic_client, vlc):
    """PATCH host, then POST /{id}/test: without this rule those two requests
    hand the stored secret to an address the row never talked to, which is
    exactly what probe()'s _same_target guard exists to prevent."""
    player = _create(alembic_client).json()  # 192.168.1.20:8080, password "pw"
    seen = []

    def handler(request):
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=VLC_OK)
    vlc["handler"] = handler

    moved = alembic_client.patch(f"/api/v1/remote-players/{player['id']}", json={"host": "192.168.1.99"})
    assert moved.status_code == 200, moved.text
    assert moved.json()["has_password"] is False
    assert alembic_client.post(f"/api/v1/remote-players/{player['id']}/test").status_code == 200
    assert _basic_secret(seen[0]) == ""

    repointed = alembic_client.patch(f"/api/v1/remote-players/{player['id']}", json={"port": 9090})
    assert repointed.json()["has_password"] is False


def test_editing_a_player_in_place_keeps_its_password(alembic_client, vlc):
    """The edit dialog resends host and port unchanged and leaves the password
    field empty; only a real move to another address drops the secret."""
    player = _create(alembic_client).json()
    same = {"name": "Lounge", "kind": "vlc", "host": "192.168.1.20", "port": 8080}
    assert alembic_client.patch(f"/api/v1/remote-players/{player['id']}", json=same).json()["has_password"] is True
    moved_with_secret = alembic_client.patch(
        f"/api/v1/remote-players/{player['id']}", json={"host": "192.168.1.99", "password": "new"}
    )
    assert moved_with_secret.json()["has_password"] is True
