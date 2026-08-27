"""The /api/v1/health engine probe must use an endpoint every supported engine serves."""
from __future__ import annotations

import httpx


class _FakeResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text


class _FakeClient:
    seen: list[tuple[str, float]] = []

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url: str, timeout: float):
        _FakeClient.seen.append((url, timeout))
        # Mirror the real engines: get_version answers, /server/ping is unknown.
        if url.endswith("webui/api/service?method=get_version"):
            return _FakeResponse(200, '{"result": {"platform": "android", "version": "3.1.80"}, "error": null}')
        return _FakeResponse(500, "Internal Server Error, couldn't find resource")


def test_health_probe_uses_get_version_on_engine_root(monkeypatch, db_session):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.config_service import ConfigService

    _FakeClient.seen.clear()
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    service = ConfigService(SettingsRepository(db_session))
    monkeypatch.setattr(service, "get_ace_engine_url", lambda: "http://localhost:6878")

    status = service.check_acestream_status()

    assert _FakeClient.seen == [("http://localhost:6878/webui/api/service?method=get_version", 1.0)]
    assert status["status"] == "online"
    assert status["accessible"] is True
    assert status["engine_url"] == "http://localhost:6878"
