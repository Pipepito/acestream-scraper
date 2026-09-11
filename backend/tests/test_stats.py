import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_stats_endpoint():
    response = client.get("/api/v1/stats/")
    assert response.status_code == 200
    data = response.json()
    # Check required fields
    for field in [
        "urls", "total_channels", "channels_checked", "channels_online", "channels_offline",
        "base_url", "ace_engine_url", "rescrape_interval", "addpid", "task_manager_status"
    ]:
        assert field in data
    assert isinstance(data["urls"], list)

def test_tv_channel_stats_endpoint():
    response = client.get("/api/v1/stats/tv-channels/")
    assert response.status_code == 200
    data = response.json()
    for field in ["total", "active", "with_epg", "acestreams"]:
        assert field in data
