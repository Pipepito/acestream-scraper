"""
Service for managing background tasks using APScheduler in FastAPI.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError, SchedulerNotRunningError
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from threading import Event, Lock
import logging


class TaskService:
    def __init__(self):
        self.scheduler = self._new_scheduler()
        self.shutdown_event = Event()
        self.logger = logging.getLogger("TaskService")
        self._state_lock = Lock()
        self._task_states: Dict[str, Dict[str, Any]] = {}

    def _new_scheduler(self) -> BackgroundScheduler:
        return BackgroundScheduler()

    def _ensure_task_state(self, job_id: str, interval_seconds: Optional[int] = None) -> Dict[str, Any]:
        with self._state_lock:
            state = self._task_states.setdefault(
                job_id,
                {
                    "task_name": job_id,
                    "last_run": None,
                    "next_run": None,
                    "status": "idle",
                    "last_error": None,
                    "last_result": None,
                },
            )
            if interval_seconds:
                state["next_run"] = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
            return state

    def start(self):
        if self.scheduler.running:
            self.logger.info("Background scheduler already running; skipping start.")
            return False
        try:
            self.scheduler.start()
            self.logger.info("Background scheduler started.")
            self.shutdown_event.clear()
            return True
        except SchedulerAlreadyRunningError:
            self.logger.info("Background scheduler already running; skipping start.")
            return False
        except Exception:
            # APScheduler instances are not safely restartable after shutdown in all runtimes.
            self.logger.warning("Scheduler start failed; recreating scheduler and retrying once.")
            self.scheduler = self._new_scheduler()
            self.scheduler.start()
            self.shutdown_event.clear()
            self.logger.info("Background scheduler started after recreation.")
            return True

    def shutdown(self):
        if not self.scheduler.running:
            self.logger.info("Background scheduler already stopped; skipping shutdown.")
            self.shutdown_event.set()
            return False
        try:
            self.scheduler.shutdown(wait=False)
        except SchedulerNotRunningError:
            self.logger.info("Background scheduler already stopped during shutdown.")
        finally:
            # Fresh scheduler instance avoids invalid restart state and stale worker threads.
            self.scheduler = self._new_scheduler()
        self.shutdown_event.set()
        self.logger.info("Background scheduler shut down.")
        return True

    def _instrument_task(self, job_id: str, func: Callable[..., Any]) -> Callable[..., Any]:
        def _runner(*args, **kwargs):
            state = self._ensure_task_state(job_id)
            with self._state_lock:
                state["status"] = "running"
                state["last_error"] = None
                state["last_result"] = None
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = asyncio.run(result)
                next_run = None
                job = self.scheduler.get_job(job_id)
                if job is not None:
                    next_run = job.next_run_time
                with self._state_lock:
                    state["status"] = "idle"
                    state["last_run"] = datetime.now(timezone.utc)
                    state["next_run"] = next_run
                    state["last_result"] = result
                return result
            except Exception as exc:
                next_run = None
                job = self.scheduler.get_job(job_id)
                if job is not None:
                    next_run = job.next_run_time
                with self._state_lock:
                    state["status"] = "error"
                    state["last_run"] = datetime.now(timezone.utc)
                    state["next_run"] = next_run
                    state["last_error"] = str(exc)
                    state["last_result"] = None
                self.logger.exception("Scheduled task failed task=%s error=%s", job_id, exc)
                raise

        return _runner

    def add_interval_task(self, func, seconds, job_id, args=None, kwargs=None):
        self._ensure_task_state(job_id, interval_seconds=seconds)
        self.scheduler.add_job(
            self._instrument_task(job_id, func),
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            args=args or [],
            kwargs=kwargs or {},
            replace_existing=True,
            # APScheduler's default misfire_grace_time of 1s silently DROPS a
            # run dispatched late (including run_task_now triggers on a busy
            # executor). These maintenance tasks should run late, not skip;
            # coalesce (default True) collapses bursts into one run.
            misfire_grace_time=None
        )
        self.logger.info(f"Scheduled task '{job_id}' every {seconds} seconds.")

    def run_task_now(self, job_id: str) -> str:
        """Trigger a scheduled job to run immediately, outside its interval.

        Returns one of:
        - "triggered": the job was rescheduled to run now.
        - "already_running": the job is currently executing; not re-triggered.
        - "unavailable": the scheduler is not running or the job is not registered.
        """
        state = self.get_task_state(job_id)
        if state and state.get("status") == "running":
            return "already_running"
        if not self.scheduler.running:
            return "unavailable"
        job = self.scheduler.get_job(job_id)
        if job is None:
            return "unavailable"
        self.scheduler.modify_job(job_id, next_run_time=datetime.now(timezone.utc))
        self.logger.info(f"Triggered immediate run of task '{job_id}'.")
        return "triggered"

    def remove_task(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed scheduled task '{job_id}'.")
            state = self._ensure_task_state(job_id)
            with self._state_lock:
                state["status"] = "removed"
                state["next_run"] = None
        except JobLookupError:
            self.logger.warning(f"Tried to remove non-existent task '{job_id}'.")

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def get_task_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._state_lock:
            state = self._task_states.get(job_id)
            return dict(state) if state else None

    def get_task_states(self) -> Dict[str, Dict[str, Any]]:
        with self._state_lock:
            return {job_id: dict(state) for job_id, state in self._task_states.items()}

task_service = TaskService()
