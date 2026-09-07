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


def test_oneoff_task_runs_once_and_keeps_its_state():
    service = TaskService()
    executed = {"runs": 0}

    def once():
        executed["runs"] += 1
        return {"done": True}

    try:
        service.start()
        service.add_oneoff_task(once, job_id="test_oneoff")
        deadline = time.time() + 5
        while time.time() < deadline and executed["runs"] == 0:
            time.sleep(0.05)
        time.sleep(0.3)  # give the instrumented wrapper time to record the result
        state = service.get_task_state("test_oneoff")

        assert executed["runs"] == 1
        assert state is not None
        assert state["status"] == "idle"
        assert state["last_result"] == {"done": True}
        # One-off jobs disappear from the scheduler once fired but stay visible
        # through the runtime state so the dashboard can show the outcome.
        assert service.scheduler.get_job("test_oneoff") is None
        assert state["next_run"] is None
    finally:
        service.shutdown()


def test_task_progress_is_reported_while_running():
    service = TaskService()
    service._ensure_task_state("progress_job")

    service.update_task_progress("progress_job", {"percent": 42.0, "processed": 42, "total": 100})
    state = service.get_task_state("progress_job")

    assert state["progress"] == {"percent": 42.0, "processed": 42, "total": 100}
    assert service.get_task_states()["progress_job"]["progress"]["percent"] == 42.0


def test_run_start_outcome_and_interruption_survive_new_service(alembic_backend_runtime):
    from app.repositories.task_state_repository import TaskStateRepository
    from app.models.background_task_status import BackgroundTaskStatus
    store = TaskStateRepository()
    service = TaskService(state_store=store)
    observed = {}

    def cleanup():
        during = store.load()['activity_log_cleanup']
        assert during['status'] == 'running'
        assert during['last_run'] is not None
        observed['started'] = during['last_run']
        return 3  # real cleanup result is a scalar, not a dictionary

    service._instrument_task('activity_log_cleanup', cleanup)()
    restored = TaskService(state_store=store)
    restored.restore_states()
    state = restored.get_task_state('activity_log_cleanup')
    assert state['last_run'] == observed['started']
    assert state['last_result'] == 3
    assert BackgroundTaskStatus(**state).last_result == 3
    store.save({**state, 'status': 'running'})
    restored.restore_states()
    interrupted = restored.get_task_state('activity_log_cleanup')
    assert interrupted['status'] == 'interrupted'
    assert 'before this run completed' in interrupted['last_error']


def test_failed_run_survives_restart(alembic_backend_runtime):
    import pytest
    from app.repositories.task_state_repository import TaskStateRepository
    store = TaskStateRepository()
    service = TaskService(state_store=store)
    def fail():
        raise ValueError('test failure')
    with pytest.raises(ValueError):
        service._instrument_task('epg_refresh', fail)()
    restored = TaskService(state_store=store)
    restored.restore_states()
    assert restored.get_task_state('epg_refresh')['last_error'] == 'test failure'
    assert restored.get_task_state('epg_refresh')['status'] == 'error'


async def _manual_overlap_scenario(monkeypatch):
    import asyncio
    from app.services import manual_job_service
    service = TaskService()
    monkeypatch.setattr(manual_job_service, 'task_service', service)
    began = asyncio.Event()
    finish = asyncio.Event()
    async def old_scrape():
        began.set()
        await finish.wait()
        return [], 'Error: older request failed'
    first = asyncio.create_task(manual_job_service.run_manual_job('url_scraping', old_scrape))
    await began.wait()
    async def new_scrape():
        return [1, 2], 'OK'
    await manual_job_service.run_manual_job('url_scraping', new_scrape)
    finish.set()
    await first
    state = service.get_task_state('manual_url_scraping')
    assert state['status'] == 'idle'
    assert state['last_result'] == {'processed': 1, 'failures': 0, 'channels': 2}
    assert state['next_run'] is None


def test_overlapping_manual_runs_keep_latest_started_outcome(monkeypatch):
    import asyncio
    asyncio.run(_manual_overlap_scenario(monkeypatch))


def test_manual_bulk_summaries():
    from app.services.manual_job_service import _summary
    assert _summary('epg_refresh', [{'success': True}, {'success': False}]) == {'sources': 2, 'successful': 1, 'failed': 1}
    assert _summary('url_scraping', [([], 'OK'), ([], 'Error: fetch failed')])['failures'] == 1
