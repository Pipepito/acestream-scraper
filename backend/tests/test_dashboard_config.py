import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_dashboard_config():
    response = client.get("/api/v1/config/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "retention_days" in data
    assert "auto_refresh_interval" in data

def test_update_dashboard_config():
    response = client.put(
        "/api/v1/config/dashboard",
        json={"retention_days": 10, "auto_refresh_interval": 120}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["retention_days"] == 10
    assert data["auto_refresh_interval"] == 120
