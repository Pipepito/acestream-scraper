"""
Service for managing background tasks using APScheduler in FastAPI.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.base import JobLookupError
from threading import Event
import logging

class TaskService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.shutdown_event = Event()
        self.logger = logging.getLogger("TaskService")

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Background scheduler started.")

    def shutdown(self):
        self.scheduler.shutdown(wait=False)
        self.shutdown_event.set()
        self.logger.info("Background scheduler shut down.")

    def add_interval_task(self, func, seconds, job_id, args=None, kwargs=None):
        self.scheduler.add_job(
            func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            args=args or [],
            kwargs=kwargs or {},
            replace_existing=True
        )
        self.logger.info(f"Scheduled task '{job_id}' every {seconds} seconds.")

    def remove_task(self, job_id):
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Removed scheduled task '{job_id}'.")
        except JobLookupError:
            self.logger.warning(f"Tried to remove non-existent task '{job_id}'.")

    def get_jobs(self):
        return self.scheduler.get_jobs()

task_service = TaskService()
