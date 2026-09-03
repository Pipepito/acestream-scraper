"""RemotePlayerService: CRUD, host guard, probe, stream URL, commands (spec 6.1, 6.3)."""
import httpx
import pytest

from app.services.remote_players.base import PlayerAuthError
from app.services.remote_players.service import RemotePlayerService
from app.utils.url_guard import BlockedURLError

VLC_OK = {"apiversion": 3, "version": "3.0.23", "state": "stopped", "time": 0, "length": 0, "volume": 256, "information": {}}
IH = "0" * 40


def _service(db, handler=None):
    def factory():
        return httpx.Client(transport=httpx.MockTransport(handler or (lambda r: httpx.Response(200, json=VLC_OK))))
    return RemotePlayerService(db, client_factory=factory)


def test_crud_and_password_masking(alembic_db_session):
    svc = _service(alembic_db_session)
    player = svc.repo.create(name="Living room", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    assert svc.repo.get_by_name("Living room").id == player.id
    svc.repo.update(player, name="Lounge", password=None)  # None = keep
    assert svc.repo.get(player.id).password == "pw" and svc.repo.get(player.id).name == "Lounge"
    svc.repo.update(player, password="")  # empty = clear
    assert svc.repo.get(player.id).password == ""
    svc.repo.delete(player)
    assert svc.repo.get_all() == []


def test_validate_host_rules(alembic_db_session):
    svc = _service(alembic_db_session)
    assert svc.validate_host(" vlc.lan ") == "vlc.lan"
    assert svc.validate_host("192.168.1.5") == "192.168.1.5"
    for bad in ("http://x", "user@host", "host/path", "host?x=1", "host#frag", "vlc lan", "", "169.254.169.254"):
        with pytest.raises((BlockedURLError, ValueError)):
            svc.validate_host(bad)


def test_probe_secret_rule(alembic_db_session):
    seen = []

    def handler(request):
        seen.append(request.headers.get("Authorization"))
        return httpx.Response(200, json=VLC_OK)

    svc = _service(alembic_db_session, handler)
    stored = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="stored", base_url_id=None)
    svc.probe("vlc", "192.168.1.20", 8080, None, "typed", stored_id=stored.id)
    svc.probe("vlc", "192.168.1.20", 8080, None, "", stored_id=stored.id)
    svc.probe("vlc", "192.168.1.20", 8080, None, None, stored_id=None)
    import base64
    assert seen[0] == "Basic " + base64.b64encode(b":typed").decode()
    assert seen[1] == "Basic " + base64.b64encode(b":stored").decode()
    assert seen[2] == "Basic " + base64.b64encode(b":").decode()


def test_probe_reports_tuner_access(alembic_db_session, monkeypatch):
    svc = _service(alembic_db_session)
    import socket
    monkeypatch.setattr(socket, "getaddrinfo", lambda host, *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0))])
    probe, access = svc.probe("vlc", "public.example", 8080, None, "pw")
    assert probe.reachable
    assert access.addresses == ["8.8.8.8"] and access.allowed is False


def test_resolve_stream_url_relay_and_pattern(alembic_db_session):
    from app.repositories.base_url_repository import BaseUrlRepository
    svc = _service(alembic_db_session)
    pattern = BaseUrlRepository(alembic_db_session).create("Acexy", "http://192.168.1.10:8080/ace/getstream?id={channel_id}&pid={pid}")
    relay = svc.repo.create(name="relay", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    custom = svc.repo.create(name="custom", kind="vlc", host="192.168.1.21", port=8080, username=None, password="pw", base_url_id=pattern.id)
    assert svc.resolve_stream_url(relay, IH, "http://scraper.lan:8000") == f"http://scraper.lan:8000/tuner/stream/{IH}.ts"
    assert svc.resolve_stream_url(custom, IH, "http://scraper.lan:8000") == f"http://192.168.1.10:8080/ace/getstream?id={IH}"


def test_play_and_commands_go_through_the_driver(alembic_db_session):
    seen = []

    def handler(request):
        seen.append(dict(request.url.params))
        return httpx.Response(200, json=VLC_OK)

    svc = _service(alembic_db_session, handler)
    player = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="pw", base_url_id=None)
    url = svc.play(player, IH, "http://scraper.lan:8000", "Arena")
    assert url.endswith(f"/tuner/stream/{IH}.ts")
    svc.command(player, "volume", 50)
    svc.command(player, "stop")
    assert seen[0]["command"] == "pl_empty" and seen[1]["command"] == "in_play"
    assert seen[2] == {"command": "volume", "val": "128"} and seen[3]["command"] == "pl_stop"
    with pytest.raises(ValueError):
        svc.command(player, "seek", 10)


def test_status_propagates_auth_error(alembic_db_session):
    svc = _service(alembic_db_session, lambda r: httpx.Response(401))
    player = svc.repo.create(name="p", kind="vlc", host="192.168.1.20", port=8080, username=None, password="bad", base_url_id=None)
    with pytest.raises(PlayerAuthError):
        svc.status(player)


def test_validate_host_brackets_ipv6_literals(alembic_db_session):
    """Unbracketed IPv6 makes `http://{host}:{port}` unparseable: httpx raises
    InvalidURL, which is not an httpx.HTTPError, so the drivers cannot map it to
    a contract error code and it escapes as an unhandled 500."""
    svc = _service(alembic_db_session)
    assert svc.validate_host("fd00::1") == "[fd00::1]"
    assert svc.validate_host(" [fd00::1] ") == "[fd00::1]"
    assert svc.validate_host("2001:0DB8:0000::1") == "[2001:db8::1]"
    for bad in ("192.168.1.5:9090", "vlc.lan:8080", "[fd00::1", "fe80::1", "::", "ff02::1"):
        with pytest.raises((BlockedURLError, ValueError)):
            svc.validate_host(bad)


def test_ipv6_host_reaches_the_driver_as_a_valid_url(alembic_db_session):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json=VLC_OK)

    svc = _service(alembic_db_session, handler)
    host = svc.validate_host("fd00::1")
    probe, _access = svc.probe("vlc", host, 8080, None, "pw")
    assert probe.reachable
    assert seen == ["http://[fd00::1]:8080/requests/status.json"]
