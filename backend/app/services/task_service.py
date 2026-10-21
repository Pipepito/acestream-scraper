"""
Service for managing background tasks using APScheduler in FastAPI.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional
from app.schemas.config import ScheduleAnchors

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError, SchedulerNotRunningError
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from threading import Event, Lock, Condition
from collections import deque
import logging


class TaskService:
    def __init__(self, state_store=None):
        self._state_store = state_store
        self.scheduler = self._new_scheduler()
        self.shutdown_event = Event()
        self.logger = logging.getLogger("TaskService")
        self._state_lock = Lock()
        self._persist_lock = Lock()
        self._maintenance_condition = Condition()
        self._maintenance_queue = deque()
        self._schedule_anchors = {}
        self._interval_seconds = {}
        self._schedule_timezone = "UTC"
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
                    "progress": None,
                },
            )
            if interval_seconds:
                state["next_run"] = datetime.now(timezone.utc) + timedelta(seconds=interval_seconds)
            return state

    def restore_states(self):
        """Called after schema upgrade, off the application event loop."""
        if self._state_store is None:
            return
        try:
            states = self._state_store.load()
            for state in states.values():
                if state["status"] in {"running", "waiting"}:
                    state["status"] = "interrupted"
                    state["last_error"] = "Application stopped before this run completed"
                    self._state_store.save(state)
            with self._state_lock:
                self._task_states = states
        except Exception:
            self.logger.exception("Could not restore scheduled task history")

    def _persist_state(self, state):
        if self._state_store is not None:
            try:
                self._state_store.save(dict(state))
            except Exception:
                # History failure must not turn successful maintenance into failure.
                self.logger.exception("Could not save scheduled task history task=%s", state["task_name"])

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

    def configure_schedule(self, schedule: ScheduleAnchors) -> None:
        self._schedule_anchors = {
            name: getattr(schedule, name)
            for name in ("url_scraping", "epg_refresh", "channel_status")
        }
        self._schedule_timezone = schedule.timezone
        for name in self._schedule_anchors:
            job = self.scheduler.get_job(name)
            if job is not None:
                self.reschedule_task(name, self._interval_seconds[name])

    def _interval_trigger(self, job_id: str, seconds: int) -> IntervalTrigger | CronTrigger:
        from zoneinfo import ZoneInfo
        anchor = self._schedule_anchors.get(job_id)
        if not anchor:
            return IntervalTrigger(seconds=seconds)
        hour, minute = map(int, anchor.split(":"))
        if seconds % 3600 == 0 and 86400 % seconds == 0:
            hours = sorted({(hour + offset) % 24 for offset in range(0, 24, seconds // 3600)})
            return CronTrigger(hour=",".join(map(str, hours)), minute=minute, second=0, timezone=self._schedule_timezone)
        if seconds % 60 == 0 and 3600 % seconds == 0:
            minutes = sorted({(minute + offset) % 60 for offset in range(0, 60, seconds // 60)})
            return CronTrigger(minute=",".join(map(str, minutes)), second=0, timezone=self._schedule_timezone)
        # Stable epoch preserves the cadence across restarts and intervals >24h.
        start = datetime(2020, 1, 1, hour, minute, tzinfo=ZoneInfo(self._schedule_timezone))
        return IntervalTrigger(seconds=seconds, start_date=start, timezone=self._schedule_timezone)

    def _instrument_task(self, job_id: str, func: Callable[..., Any], *, maintenance=False) -> Callable[..., Any]:
        def _execute(*args, **kwargs):
            state = self._ensure_task_state(job_id)
            with self._state_lock:
                state["status"] = "running"
                state["last_run"] = datetime.now(timezone.utc)
                state["last_error"] = None
                state["last_result"] = None
                state["progress"] = None
            self.persist_current_state(job_id, state)
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
                    state["next_run"] = next_run
                    state["last_result"] = result
                self.persist_current_state(job_id, state)
                return result
            except Exception as exc:
                next_run = None
                job = self.scheduler.get_job(job_id)
                if job is not None:
                    next_run = job.next_run_time
                with self._state_lock:
                    state["status"] = "error"
                    state["next_run"] = next_run
                    state["last_error"] = self._error_message(exc)
                    state["last_result"] = None
                self.persist_current_state(job_id, state)
                self.logger.exception("Scheduled task failed task=%s error=%s", job_id, exc)
                raise

        def _runner(*args, **kwargs):
            if not maintenance:
                return _execute(*args, **kwargs)
            ticket = object()
            state = self._ensure_task_state(job_id)
            with self._maintenance_condition:
                self._maintenance_queue.append(ticket)
                with self._state_lock:
                    state["status"] = "waiting"
                while self._maintenance_queue[0] is not ticket:
                    if self.shutdown_event.is_set():
                        self._maintenance_queue.remove(ticket)
                        with self._state_lock:
                            state["status"] = "interrupted"
                        return None
                    self._maintenance_condition.wait(timeout=0.25)
            try:
                if self.shutdown_event.is_set():
                    with self._state_lock:
                        state["status"] = "interrupted"
                    return None
                return _execute(*args, **kwargs)
            finally:
                with self._maintenance_condition:
                    self._maintenance_queue.popleft()
                    self._maintenance_condition.notify_all()

        return _runner

    @staticmethod
    def _error_message(exc: Exception) -> str:
        from app.config.database_retry import is_database_locked
        if is_database_locked(exc):
            return "Database is busy. This run could not save its changes; try again after other work finishes."
        return str(exc)

    def add_interval_task(self, func, seconds, job_id, args=None, kwargs=None):
        self._interval_seconds[job_id] = seconds
        self._ensure_task_state(job_id, interval_seconds=seconds)
        self.scheduler.add_job(
            self._instrument_task(job_id, func, maintenance=True),
            trigger=self._interval_trigger(job_id, seconds),
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

    def reschedule_task(self, job_id: str, seconds: int) -> bool:
        """Change a running interval job's period (settings changed at runtime)."""
        job = self.scheduler.get_job(job_id)
        if job is None:
            return False
        self._interval_seconds[job_id] = seconds
        self.scheduler.reschedule_job(job_id, trigger=self._interval_trigger(job_id, seconds))
        state = self._ensure_task_state(job_id, interval_seconds=seconds)
        with self._state_lock:
            state["interval_seconds"] = seconds
        self.logger.info(f"Rescheduled task '{job_id}' every {seconds} seconds.")
        return True

    def add_oneoff_task(self, func, job_id, args=None, kwargs=None):
        """Run ``func`` once, as soon as the scheduler can, under ``job_id``.

        The job is removed from the scheduler after it fires, but its runtime
        state (status, result, progress) stays visible via
        :meth:`get_task_state` for the lifetime of the process.
        """
        self._ensure_task_state(job_id)
        self.scheduler.add_job(
            self._instrument_task(job_id, func),
            trigger=DateTrigger(run_date=datetime.now(timezone.utc)),
            id=job_id,
            args=args or [],
            kwargs=kwargs or {},
            replace_existing=True,
            misfire_grace_time=None,
        )
        self.logger.info(f"Scheduled one-off task '{job_id}'.")

    def update_task_progress(self, job_id: str, progress: Optional[Dict[str, Any]]) -> None:
        """Record a progress snapshot for a running task (shown on the dashboard)."""
        state = self._ensure_task_state(job_id)
        with self._state_lock:
            state["progress"] = dict(progress) if progress is not None else None

    # Jobs that only download files and are safe to run as soon as the
    # application starts. A WHITELIST on purpose:
    #   channel_status       opens engine sessions; on a small box that is
    #                        already loading its catalogue it chokes it
    #   epg_program_cleanup  is the one that EMPTIES the guide; running it
    #                        early would make the problem worse
    #   channel_cleanup      deletes; let it keep its own time
    # Guide first: an empty guide is what the viewer sees.
    CATCH_UP_JOBS = ("epg_refresh", "url_scraping")

    def catch_up_missed_runs(self, job_ids=CATCH_UP_JOBS, stagger_seconds: int = 300,
                             now: Optional[datetime] = None, start_after_seconds: int = 0) -> list:
        """Run now the jobs whose last run is older than their interval.

        Interval jobs live in memory and are re-created on every start, so
        their first run lands one whole interval after startup. A machine
        that is only switched on for a few hours never reaches it: on a real
        box `epg_refresh` (6 h) had never run, while `epg_program_cleanup`
        (1 h) kept deleting expired programmes -- the guide emptied itself.
        `last_run` is persisted and restored, so we can tell.

        A job with a user-set start time is left alone: whoever asked for
        04:00 wants 04:00. Jobs are staggered so a small box does not fetch
        playlists and guides at once.

        ``start_after_seconds`` holds the first one back: right after power-on
        is when someone opens a channel, and the guide refresh writes thousands
        of rows -- on a small ARM box (2026-10-18) two channel opens at 2 min
        failed with `database is locked` while it ran.

        Returns the job ids that were brought forward.
        """
        now = now or datetime.now(timezone.utc)
        brought = []
        for job_id in job_ids:
            overdue, last, interval = self._overdue(job_id, now)
            if not overdue:
                continue
            when = now + timedelta(seconds=start_after_seconds + stagger_seconds * len(brought))
            self.scheduler.modify_job(job_id, next_run_time=when)
            self.logger.info(
                "Catching up task '%s' (last run %s, interval %ss): runs at %s",
                job_id, last or "never", interval, when.isoformat())
            brought.append(job_id)
        return brought

    def _overdue(self, job_id: str, now: datetime):
        """(overdue, last_run, interval) for a registered interval job.

        Never overdue when the user set a start time for it or it is not
        registered: whoever asked for 04:00 wants 04:00.
        """
        if self._schedule_anchors.get(job_id):
            return False, None, None
        interval = self._interval_seconds.get(job_id)
        if not interval or self.scheduler.get_job(job_id) is None:
            return False, None, interval
        last = (self.get_task_state(job_id) or {}).get("last_run")
        if isinstance(last, str):
            try:
                last = datetime.fromisoformat(last)
            except ValueError:
                last = None
        if last is not None and last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last is not None and (now - last).total_seconds() < interval:
            return False, last, interval
        return True, last, interval

    def catch_up_later(self, job_id: str, delay_seconds: int = 900,
                       now: Optional[datetime] = None) -> bool:
        """Look again ``delay_seconds`` after startup and run ``job_id`` then
        if it is still overdue.

        For ``channel_status``, which CATCH_UP_JOBS leaves out: it opens the
        engine, and at startup the box is loading its catalogue and the
        viewer is opening a channel. Without it the first pass came one whole
        interval after startup, and every restart pushed it back again. The
        decision is taken when it fires, not now: if a pass ran meanwhile
        (by hand, or a quick restart) nothing is duplicated.

        Returns whether the check was scheduled.
        """
        if self._schedule_anchors.get(job_id) or self.scheduler.get_job(job_id) is None:
            return False
        when = (now or datetime.now(timezone.utc)) + timedelta(seconds=delay_seconds)
        self.scheduler.add_job(
            self.run_if_overdue, trigger=DateTrigger(run_date=when), args=[job_id],
            id=f"{job_id}_catch_up", replace_existing=True, misfire_grace_time=None)
        self.logger.info("Task '%s' is checked for catch-up at %s", job_id, when.isoformat())
        return True

    def run_if_overdue(self, job_id: str, now: Optional[datetime] = None) -> str:
        """Run ``job_id`` now if its last run is older than its interval."""
        overdue, last, interval = self._overdue(job_id, now or datetime.now(timezone.utc))
        if not overdue:
            self.logger.info("Catch-up of '%s' not needed (last run %s)", job_id, last)
            return "not_needed"
        self.logger.info("Catching up task '%s' (last run %s, interval %ss)", job_id, last or "never", interval)
        return self.run_task_now(job_id)

    def run_task_now(self, job_id: str) -> str:
        """Trigger a scheduled job to run immediately, outside its interval.

        Returns one of:
        - "triggered": the job was rescheduled to run now.
        - "already_running": the job is currently executing; not re-triggered.
        - "unavailable": the scheduler is not running or the job is not registered.
        """
        state = self.get_task_state(job_id)
        if state and state.get("status") in {"running", "waiting"}:
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

    def set_manual_state(self, job_id, state):
        with self._state_lock:
            self._task_states[job_id] = state

    def persist_current_state(self, job_id, state):
        # An older overlapping manual run must not overwrite the latest run.
        # Keep database waits outside the state lock so Overview stays responsive.
        with self._persist_lock:
            with self._state_lock:
                snapshot = dict(state) if self._task_states.get(job_id) is state else None
            if snapshot is not None:
                self._persist_state(snapshot)

    def get_jobs(self):
        return self.scheduler.get_jobs()

    def get_task_state(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._state_lock:
            state = self._task_states.get(job_id)
            return dict(state) if state else None

    def get_task_states(self) -> Dict[str, Dict[str, Any]]:
        with self._state_lock:
            return {job_id: dict(state) for job_id, state in self._task_states.items()}

from app.repositories.task_state_repository import TaskStateRepository

task_service = TaskService(state_store=TaskStateRepository())
