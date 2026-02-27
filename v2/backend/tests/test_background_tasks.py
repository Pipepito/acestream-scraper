import pytest
from fastapi.testclient import TestClient
from app.api.endpoints.background_tasks import status_service
from main import app

client = TestClient(app)

def test_get_background_tasks_status():
    response = client.get("/api/v1/background-tasks/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any('task_name' in task for task in data)


def test_get_background_tasks_status_failure_returns_error_contract(monkeypatch):
    monkeypatch.setattr(
        status_service,
        "get_all_statuses",
        lambda: (_ for _ in ()).throw(RuntimeError("scheduler unavailable")),
    )
    response = client.get("/api/v1/background-tasks/status")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "BACKGROUND_TASK_STATUS_FAILED"
    assert data["error"]["correlation_id"]
