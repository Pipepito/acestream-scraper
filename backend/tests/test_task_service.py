"""
Test background task system integration and scheduling.
"""
import time
from app.services.task_service import task_service

def dummy_job():
    # No-op job for testing
    pass

def test_task_scheduling():
    try:
        # Start scheduler
        task_service.start()
        # Add a test task with a short interval
        task_service.add_interval_task(dummy_job, seconds=1, job_id="test_dummy_job")
        jobs = task_service.get_jobs()
        assert any(job.id == "test_dummy_job" for job in jobs)
        # Wait for at least one run
        time.sleep(1.5)
        # Remove test task
        task_service.remove_task("test_dummy_job")
        assert not any(job.id == "test_dummy_job" for job in task_service.get_jobs())
    finally:
        # Always shut down the scheduler to avoid hanging threads
        task_service.shutdown()
