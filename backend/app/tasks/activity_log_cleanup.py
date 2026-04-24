import logging

from app.config.database import SessionLocal
from app.services.activity_log_service import ActivityLogService

logger = logging.getLogger(__name__)

# This function is intended to be scheduled by the main scheduler (e.g., Celery, APScheduler, or FastAPI background task)
def run_activity_log_cleanup(retention_days: int = 7):
    db = SessionLocal()
    try:
        service = ActivityLogService(db)
        deleted_count = service.cleanup_old_logs(retention_days=retention_days)
        logger.info(
            "Activity log cleanup complete. Deleted %s old log entries (retention: %s days)",
            deleted_count,
            retention_days,
        )
        return deleted_count
    finally:
        db.close()
