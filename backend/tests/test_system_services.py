"""Sidecar services panel: status derivation and operator restarts."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import requests

from app.services.system_services_service import (
    ServiceNotManagedError,
    SystemServicesService,
)


class FakeHttp:
    """Answers probes by URL prefix; anything else raises a connection error."""

    def __init__(self, answers: dict[str, object]):
        self.answers = answers
        self.calls: list[str] = []

    def __call__(self, url: str, **_kwargs):
        self.calls.append(url)
        for prefix, payload in self.answers.items():
            if url.startswith(prefix):
                response = MagicMock(spec=requests.Response)
                response.status_code = 200
                response.json.return_value = payload
                return response
        raise requests.ConnectionError(f"refused {url}")


ENGINE_VERSION = {"result": {"platform": "android", "version": "3.1.80"}, "error": None}


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "IMAGE_HAS_ACESTREAM", "IMAGE_HAS_ACEXY", "IMAGE_HAS_IPFS", "IMAGE_HAS_ZERONET",
        "ENABLE_ACESTREAM_ENGINE", "ENABLE_ACEXY", "ENABLE_IPFS", "ENABLE_ZERONET", "ENABLE_WARP",
        "SUPERVISOR_RUN_DIR", "IPFS_GATEWAY_URL", "ZERONET_URL",
        "ACEXY_LISTEN_ADDR", "ACEXY_STATUS_PORT",
    ):
        monkeypatch.delenv(var, raising=False)


def _service(tmp_path: Path, http: FakeHttp, engine_url: str = "http://engine.test:6878") -> SystemServicesService:
    return SystemServicesService(run_dir=str(tmp_path), external_engine_url=engine_url, http_get=http, http_post=http)


def _by_name(payload: dict) -> dict:
    return {s["name"]: s for s in payload["services"]}


def test_nothing_installed_and_nothing_reachable(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setattr("app.services.system_services_service.shutil.which", lambda _n: None)
    services = _by_name(_service(tmp_path, FakeHttp({})).list_services())

    assert {name: s["state"] for name, s in services.items()} == {
        "acestream": "not-installed",
        "acexy": "not-installed",
        "ipfs": "not-installed",
        "zeronet": "not-installed",
        "warp": "not-installed",
    }
    assert all(not s["managed"] and not s["running"] for s in services.values())


def test_external_engine_and_gateway_are_reported_as_external(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("IPFS_GATEWAY_URL", "http://gateway.test:8080")
    monkeypatch.setattr("app.services.system_services_service.shutil.which", lambda _n: None)
    http = FakeHttp({"http://engine.test:6878/webui": ENGINE_VERSION, "http://gateway.test:8080/ipfs/bafkqaaa": {}})
    services = _by_name(_service(tmp_path, http).list_services())

    assert services["acestream"]["state"] == "external"
    assert services["acestream"]["running"] is True
    assert services["acestream"]["version"] == "3.1.80 (android)"
    assert services["acestream"]["endpoint"] == "http://engine.test:6878"
    assert services["ipfs"]["state"] == "external"
    assert services["ipfs"]["endpoint"] == "http://gateway.test:8080"


def test_supervised_engine_states(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("IMAGE_HAS_ACESTREAM", "true")
    monkeypatch.setenv("ENABLE_ACESTREAM_ENGINE", "true")
    monkeypatch.setenv("ACESTREAM_HTTP_HOST", "localhost")
    monkeypatch.setenv("ACESTREAM_HTTP_PORT", "6878")
    monkeypatch.setattr("app.services.system_services_service.shutil.which", lambda _n: None)
    (tmp_path / "acestream.pid").write_text(str(os.getpid()))
    (tmp_path / "acestream.started").write_text("1")

    running = _by_name(_service(tmp_path, FakeHttp({"http://localhost:6878/webui": ENGINE_VERSION})).list_services())["acestream"]
    assert running["state"] == "running"
    assert running["managed"] is True
    assert running["pid"] == os.getpid()
    assert running["uptime_seconds"] is not None and running["uptime_seconds"] > 0

    unhealthy = _by_name(_service(tmp_path, FakeHttp({})).list_services())["acestream"]
    assert unhealthy["state"] == "unhealthy"
    assert unhealthy["managed"] is True

    (tmp_path / "acestream.pid").unlink()
    stopped = _by_name(_service(tmp_path, FakeHttp({})).list_services())["acestream"]
    assert stopped["state"] == "stopped"
    assert stopped["managed"] is False


def test_installed_but_disabled_service(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("IMAGE_HAS_ACEXY", "true")
    monkeypatch.setenv("ENABLE_ACEXY", "false")
    monkeypatch.setattr("app.services.system_services_service.shutil.which", lambda _n: None)
    acexy = _by_name(_service(tmp_path, FakeHttp({})).list_services())["acexy"]

    assert acexy["state"] == "disabled"
    assert "ENABLE_ACEXY=false" in acexy["message"]


def test_restart_writes_marker_and_signals_the_process_group(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    (tmp_path / "acexy.pid").write_text(str(os.getpid()))
    service = _service(tmp_path, FakeHttp({}))
    signalled: list[int] = []
    monkeypatch.setattr(service, "_terminate", lambda pid: signalled.append(pid))

    result = service.restart("acexy")

    assert result["success"] is True
    assert signalled == [os.getpid()]
    assert (tmp_path / "acexy.restart").exists()


def test_restart_refused_when_not_supervised(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    with pytest.raises(ServiceNotManagedError):
        _service(tmp_path, FakeHttp({})).restart("acestream")


def test_endpoints(client, tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("SUPERVISOR_RUN_DIR", str(tmp_path))
    monkeypatch.setattr("app.services.system_services_service.shutil.which", lambda _n: None)
    monkeypatch.setattr("app.services.system_services_service.requests.get", FakeHttp({}))
    monkeypatch.setattr("app.services.system_services_service.requests.post", FakeHttp({}))

    listing = client.get("/api/v1/system/services")
    assert listing.status_code == 200
    body = listing.json()
    assert [s["name"] for s in body["services"]] == ["acestream", "acexy", "ipfs", "zeronet", "warp"]
    assert body["supervised"] is True

    assert client.get("/api/v1/system/services/nope").status_code == 404
    assert client.post("/api/v1/system/services/nope/restart").status_code == 404

    refused = client.post("/api/v1/system/services/acestream/restart")
    assert refused.status_code == 409
    assert refused.json()["error"]["code"] == "SERVICE_NOT_MANAGED"

    (tmp_path / "acexy.pid").write_text(str(os.getpid()))
    monkeypatch.setattr("app.services.system_services_service.SystemServicesService._terminate", staticmethod(lambda pid: None))
    accepted = client.post("/api/v1/system/services/acexy/restart")
    assert accepted.status_code == 202
    assert accepted.json()["success"] is True
    assert (tmp_path / "acexy.restart").exists()


@pytest.mark.parametrize(
    ("listen_addr", "endpoint"),
    [
        (":8084", "http://127.0.0.1:8084"),
        ("0.0.0.0:8084", "http://127.0.0.1:8084"),
        ("[::]:8084", "http://127.0.0.1:8084"),
        ("192.168.1.5:8084", "http://192.168.1.5:8084"),
    ],
)
def test_acexy_probe_follows_listen_addr(tmp_path, monkeypatch, listen_addr, endpoint):
    # ACEXY_LISTEN_ADDR is where Acexy really binds. The image pins
    # ACEXY_STATUS_PORT=8080, which must not win over an explicit listen
    # address, or a relocated Acexy shows as "up but not answering".
    _clear_env(monkeypatch)
    monkeypatch.setenv("IMAGE_HAS_ACEXY", "true")
    monkeypatch.setenv("ENABLE_ACEXY", "true")
    monkeypatch.setenv("ACEXY_STATUS_PORT", "8080")
    monkeypatch.setenv("ACEXY_LISTEN_ADDR", listen_addr)
    http = FakeHttp({f"{endpoint}/ace/status": {}})

    acexy = _by_name(_service(tmp_path, http).list_services())["acexy"]

    assert acexy["state"] == "running"
    assert acexy["endpoint"] == endpoint
    assert f"{endpoint}/ace/status" in http.calls
