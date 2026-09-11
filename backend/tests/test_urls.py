import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.fixture
def seed_url(db_session):
    from app.models.models import ScrapedURL
    url = ScrapedURL(url="http://test-refresh-url.com", url_type="regular", status="idle", enabled=True)
    db_session.add(url)
    db_session.commit()
    return url

def test_refresh_url(client, seed_url):
    url_id = seed_url.id
    response = client.post(f"/api/v1/urls/{url_id}/refresh")
    assert response.status_code == 202
    assert response.json()["success"] is True

def test_refresh_url_not_found(client):
    response = client.post("/api/v1/urls/999999/refresh")
    assert response.status_code == 404

def test_refresh_all_urls(client, seed_url):
    response = client.post("/api/v1/urls/refresh-all")
    assert response.status_code == 202
    assert response.json()["success"] is True
    assert response.json()["count"] >= 1
