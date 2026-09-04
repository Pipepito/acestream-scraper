"""/api/v1/media-servers endpoints (spec 7.3) against the recorded fake servers."""
import httpx
import pytest

# resolvable_fake_hosts is an autouse fixture: imported here so the fake ``.lan``
# hosts resolve for the guard every client runs before a request (spec 4.4).
from tests.test_media_servers import FakeJellyfin, FakePlex, resolvable_fake_hosts  # noqa: F401


@pytest.fixture
def fakes(monkeypatch):
    import app.api.endpoints.media_servers as endpoint
    jelly, plex = FakeJellyfin(), FakePlex()

    def handler(request):
        return (plex.handler if "plex" in request.url.host else jelly.handler)(request)
    monkeypatch.setattr(endpoint, "_client_factory", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    return jelly, plex


def _create(client, **overrides):
    body = {"kind": "jellyfin", "name": "Jelly", "base_url": "http://jellyfin.lan:8096", "api_key": "good"}
    body.update(overrides)
    return client.post("/api/v1/media-servers", json=body)


def test_crud_masks_key_and_validates_url(alembic_client, fakes):
    created = _create(alembic_client)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["has_api_key"] is True and "api_key" not in body and body["connected"] is False and body["last_sync_status"] == "never"
    assert _create(alembic_client).status_code == 409
    assert _create(alembic_client, name="bad", base_url="http://169.254.169.254").json()["error"]["code"] == "MEDIA_SERVER_URL_FORBIDDEN"
    patched = alembic_client.patch(f"/api/v1/media-servers/{body['id']}", json={"name": "Jellyfin", "auto_refresh": False})
    assert patched.json()["name"] == "Jellyfin" and patched.json()["auto_refresh"] is False and patched.json()["has_api_key"] is True
    assert alembic_client.delete(f"/api/v1/media-servers/{body['id']}").status_code == 204


def test_connect_refresh_status_disconnect(alembic_client, fakes):
    jelly, _ = fakes
    server = _create(alembic_client).json()
    alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://scraper.lan:8000"})
    connected = alembic_client.post(f"/api/v1/media-servers/{server['id']}/connect")
    assert connected.status_code == 200 and connected.json()["connected"] is True and connected.json()["server_version"] == "10.11.11"
    assert jelly.tuners and jelly.providers
    refreshed = alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh").json()
    assert refreshed["status"] == "ok" and refreshed["last_sync_at"]
    status = alembic_client.get(f"/api/v1/media-servers/{server['id']}/status").json()
    assert status["connected"] and status["channel_count"] == 42
    jelly.reject_key = True
    failed = alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh")
    assert failed.status_code == 502 and failed.json()["error"]["code"] == "MEDIA_SERVER_AUTH"
    stored = alembic_client.get("/api/v1/media-servers").json()[0]
    assert stored["last_sync_status"] == "error" and "rejected the API key" in stored["last_error"]
    jelly.reject_key = False
    assert alembic_client.post(f"/api/v1/media-servers/{server['id']}/disconnect").json()["connected"] is False
    assert alembic_client.post(f"/api/v1/media-servers/{server['id']}/refresh").status_code == 200  # refresh works without tuner registration (Jellyfin task)


def test_disconnecting_twice_is_a_conflict(alembic_client, fakes):
    server = _create(alembic_client).json()
    alembic_client.post(f"/api/v1/media-servers/{server['id']}/connect")
    assert alembic_client.post(f"/api/v1/media-servers/{server['id']}/disconnect").status_code == 200
    repeated = alembic_client.post(f"/api/v1/media-servers/{server['id']}/disconnect")
    assert repeated.status_code == 409 and repeated.json()["error"]["code"] == "MEDIA_SERVER_NOT_CONNECTED"


def test_delete_connected_jellyfin_disconnects_first(alembic_client, fakes):
    jelly, _ = fakes
    server = _create(alembic_client).json()
    alembic_client.post(f"/api/v1/media-servers/{server['id']}/connect")
    assert jelly.tuners
    assert alembic_client.delete(f"/api/v1/media-servers/{server['id']}").status_code == 204
    assert jelly.tuners == {} and jelly.providers == {}


def test_test_endpoint_and_plex_manual(alembic_client, fakes):
    probe = alembic_client.post("/api/v1/media-servers/test", json={"kind": "jellyfin", "base_url": "http://jellyfin.lan:8096", "api_key": "good"}).json()
    assert probe["reachable"] and probe["authenticated"] and probe["version"] == "10.11.11" and "tuner_access" in probe
    plex = _create(alembic_client, kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None).json()
    status = alembic_client.get(f"/api/v1/media-servers/{plex['id']}/status").json()
    assert status["steps"] and status["paste"]["guide_url"].endswith("/tuner/guide.xml")
    assert alembic_client.post(f"/api/v1/media-servers/{plex['id']}/refresh").json()["status"] == "manual"


def test_manual_refresh_leaves_nothing_for_the_sync_job(alembic_client, alembic_db_session, fakes):
    """A manual refresh records the same fingerprints a scheduled pass would, so
    the job does not refresh a second time moments later."""
    import app.api.endpoints.media_servers as endpoint
    from app.services.media_servers.service import MediaServerService

    jelly, _ = fakes
    jellyfin = _create(alembic_client).json()
    alembic_client.put("/api/v1/config/public_base_url", json={"value": "http://scraper.lan:8000"})
    alembic_client.post(f"/api/v1/media-servers/{jellyfin['id']}/connect")
    assert alembic_client.post(f"/api/v1/media-servers/{jellyfin['id']}/refresh").json()["status"] == "ok"
    assert jelly.started == [1]
    plex = _create(alembic_client, kind="plex", name="Plex", base_url="http://plex.lan:32400", api_key=None).json()
    assert alembic_client.post(f"/api/v1/media-servers/{plex['id']}/refresh").json()["status"] == "manual"

    service = MediaServerService(alembic_db_session, client_factory=endpoint._client_factory)
    assert service.sync_if_changed(service.repo.get(jellyfin["id"])) is None
    assert service.sync_if_changed(service.repo.get(plex["id"])) is None
    assert jelly.started == [1]  # the job asked Jellyfin for nothing more


def test_scheduler_registers_the_sync_job():
    import re
    from pathlib import Path
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text()
    assert re.search(r'add_interval_task\(run_media_server_sync_task, seconds=600, job_id="media_server_sync"\)', source)
