"""
Task service reliability and scheduler lifecycle tests.
"""
import time

from app.services.task_service import TaskService


def test_scheduler_start_and_shutdown_are_idempotent():
    service = TaskService()
    try:
        assert service.start() is True
        assert service.start() is False
        assert service.shutdown() is True
        assert service.shutdown() is False
    finally:
        service.shutdown()


def test_interval_task_updates_runtime_status():
    service = TaskService()

    executed = {"runs": 0}

    def ok_job():
        executed["runs"] += 1
        return {"runs": executed["runs"]}

    try:
        service.start()
        service.add_interval_task(ok_job, seconds=1, job_id="test_ok_job")
        time.sleep(1.4)
        state = service.get_task_state("test_ok_job")

        assert executed["runs"] >= 1
        assert state is not None
        assert state["last_run"] is not None
        assert state["status"] in {"idle", "running"}
        assert state["last_error"] is None
        assert isinstance(state["last_result"], dict)
    finally:
        service.remove_task("test_ok_job")
        service.shutdown()


def test_interval_task_failure_surfaces_error_state():
    service = TaskService()

    def failing_job():
        raise RuntimeError("intentional failure")

    try:
        service.start()
        service.add_interval_task(failing_job, seconds=1, job_id="test_failing_job")
        time.sleep(1.4)
        state = service.get_task_state("test_failing_job")

        assert state is not None
        assert state["status"] == "error"
        assert "intentional failure" in (state["last_error"] or "")
        assert state["last_run"] is not None
    finally:
        service.remove_task("test_failing_job")
        service.shutdown()
