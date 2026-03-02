import pytest
from fastapi.testclient import TestClient
from app.api.endpoints.background_tasks import status_service
from app.services.task_service import TaskService
from main import app

client = TestClient(app)

def test_get_background_tasks_status():
    response = client.get("/api/v1/background-tasks/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("task_name" in task for task in data)
    assert all("status" in task for task in data)


def test_background_task_status_uses_scheduler_runtime_state():
    service = TaskService()
    previous_service = status_service._task_service
    try:
        service.start()
        service.add_interval_task(lambda: {"ok": True}, seconds=60, job_id="status_contract_job")
        status_service._task_service = service
        response = client.get("/api/v1/background-tasks/status")
    finally:
        status_service._task_service = previous_service
        service.remove_task("status_contract_job")
        service.shutdown()

    assert response.status_code == 200
    data = response.json()
    job = next(task for task in data if task["task_name"] == "status_contract_job")
    assert job["next_run"] is not None
    assert job["status"] in {"idle", "running"}


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
