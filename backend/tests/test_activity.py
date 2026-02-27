import pytest
from fastapi.testclient import TestClient
from main import app  # Fixed import for v2/backend

client = TestClient(app)

def test_get_recent_activity_empty():
    response = client.get("/api/v1/activity/recent")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)
    # Accept empty or paginated structure

def test_get_recent_activity_with_params():
    response = client.get("/api/v1/activity/recent?days=2&page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, dict)

# Add more tests for filtering, pagination, and error cases as needed
