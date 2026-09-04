import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def alembic_started_client(alembic_backend_runtime, alembic_override_get_db):
    with TestClient(alembic_backend_runtime.app) as client:
        yield client


def test_get_background_tasks_status(alembic_started_client):
    response = alembic_started_client.get("/api/v1/background-tasks/status")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all("task_name" in task for task in data)
    assert all("status" in task for task in data)


def test_startup_scheduler_includes_activity_log_cleanup(alembic_started_client):
    response = alembic_started_client.get("/api/v1/background-tasks/status")
    assert response.status_code == 200

    task_names = {task["task_name"] for task in response.json()}
    assert "activity_log_cleanup" in task_names
    assert "epg_program_cleanup" in task_names


def test_background_task_status_uses_scheduler_runtime_state(alembic_started_client):
    from app.api.endpoints.background_tasks import status_service
    from app.services.task_service import TaskService

    service = TaskService()
    previous_service = status_service._task_service
    try:
        service.start()
        service.add_interval_task(lambda: {"ok": True}, seconds=60, job_id="status_contract_job")
        status_service._task_service = service
        response = alembic_started_client.get("/api/v1/background-tasks/status")
    finally:
        status_service._task_service = previous_service
        service.remove_task("status_contract_job")
        service.shutdown()

    assert response.status_code == 200
    data = response.json()
    job = next(task for task in data if task["task_name"] == "status_contract_job")
    assert job["next_run"] is not None
    assert job["status"] in {"idle", "running"}


def test_get_background_tasks_status_failure_returns_error_contract(alembic_started_client, monkeypatch):
    from app.api.endpoints.background_tasks import status_service

    monkeypatch.setattr(
        status_service,
        "get_all_statuses",
        lambda: (_ for _ in ()).throw(RuntimeError("scheduler unavailable")),
    )
    response = alembic_started_client.get("/api/v1/background-tasks/status")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "BACKGROUND_TASK_STATUS_FAILED"
    assert data["error"]["correlation_id"]
