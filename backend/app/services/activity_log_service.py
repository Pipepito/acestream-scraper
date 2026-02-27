from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.models import ActivityLog
from ..repositories.activity_log_repository import ActivityLogRepository

class ActivityLogService:
    def __init__(self, db: Session):
        self.repo = ActivityLogRepository(db)

    def get_recent_activity(
        self,
        days: int = 7,
        type: Optional[str] = None,
        channel_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        if days < 0 or days > 30:
            raise ValueError("Days must be between 0 and 30")
        since = datetime.utcnow() - timedelta(days=days)
        return self.repo.get_activity_logs(since=since, type=type, channel_id=channel_id, page=page, page_size=page_size)

    def log_activity(
        self,
        type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> ActivityLog:
        return self.repo.create_activity_log(type=type, message=message, details=details, user=user, channel_id=channel_id)

    def cleanup_old_logs(self, retention_days: int = 7) -> int:
        if retention_days <= 0:
            return 0
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        return self.repo.delete_logs_older_than(cutoff)
