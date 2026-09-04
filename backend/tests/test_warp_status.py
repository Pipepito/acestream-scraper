import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_warp_status():
    response = client.get("/api/v1/warp/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "last_connected" in data or "connected" in data
