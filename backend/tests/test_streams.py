import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_active_streams():
    response = client.get("/api/v1/streams/active")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "source" in data
    assert isinstance(data["count"], int)
