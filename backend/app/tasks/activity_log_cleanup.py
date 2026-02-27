from datetime import datetime
from sqlalchemy.orm import Session
from ..services.activity_log_service import ActivityLogService
from ..utils.db import get_db_session
import logging

logger = logging.getLogger(__name__)

# This function is intended to be scheduled by the main scheduler (e.g., Celery, APScheduler, or FastAPI background task)
def run_activity_log_cleanup(retention_days: int = 7):
    db: Session = next(get_db_session())
    service = ActivityLogService(db)
    deleted_count = service.cleanup_old_logs(retention_days=retention_days)
    logger.info(f"Activity log cleanup complete. Deleted {deleted_count} old log entries (retention: {retention_days} days)")
    return deleted_count
