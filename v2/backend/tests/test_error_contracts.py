"""Tests for standardized API error envelope behavior."""
from app.api.dependencies import get_scraper_service
from app.api.endpoints.background_tasks import status_service
from fastapi.testclient import TestClient
from main import app


class _FailingScraperService:
    async def scrape_url(self, url, url_type):  # pragma: no cover - invoked via endpoint
        raise RuntimeError("upstream scraper unavailable")

    def get_scraped_urls(self, skip=0, limit=100):  # pragma: no cover - invoked via endpoint
        raise RuntimeError("repository read failure")


def test_error_envelope_shape_for_core_endpoints(client, monkeypatch):
    monkeypatch.setattr(
        status_service,
        "get_all_statuses",
        lambda: (_ for _ in ()).throw(RuntimeError("status backend unavailable")),
    )
    response = client.get("/api/v1/background-tasks/status")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "BACKGROUND_TASK_STATUS_FAILED"
    assert data["error"]["message"]
    assert data["error"]["correlation_id"]


def test_unexpected_error_uses_internal_error_contract(client):
    app.dependency_overrides[get_scraper_service] = lambda: _FailingScraperService()
    try:
        with TestClient(app, raise_server_exceptions=False) as safe_client:
            response = safe_client.get("/api/v1/scrapers/urls")
    finally:
        app.dependency_overrides.pop(get_scraper_service, None)

    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_ERROR"
    assert data["error"]["correlation_id"]
    assert data["error"]["context"]["path"] == "/api/v1/scrapers/urls"


def test_scrape_failures_return_actionable_error_code(client):
    app.dependency_overrides[get_scraper_service] = lambda: _FailingScraperService()
    try:
        response = client.post(
            "/api/v1/scrapers/scrape",
            json={"url": "https://example.com/fail.m3u", "url_type": "regular"},
        )
    finally:
        app.dependency_overrides.pop(get_scraper_service, None)

    assert response.status_code == 502
    data = response.json()
    assert data["error"]["code"] == "SCRAPE_EXECUTION_FAILED"
    assert data["error"]["context"]["url"] == "https://example.com/fail.m3u"
