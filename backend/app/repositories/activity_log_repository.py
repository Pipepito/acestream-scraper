from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.models import ActivityLog
from sqlalchemy import desc

class ActivityLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, entry: ActivityLog):
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_recent(self, days: int = 7, limit: int = 100, type: Optional[str] = None) -> List[ActivityLog]:
        query = self.db.query(ActivityLog)
        if type:
            query = query.filter(ActivityLog.type == type)
        if days > 0:
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=days)
            query = query.filter(ActivityLog.timestamp >= cutoff)
        return query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()

    def delete_older_than(self, days: int):
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        self.db.query(ActivityLog).filter(ActivityLog.timestamp < cutoff).delete()
        self.db.commit()

    def get_activity_logs(self, since, type: Optional[str] = None, channel_id: Optional[str] = None, page: int = 1, page_size: int = 50) -> Dict[str, Any]:
        query = self.db.query(ActivityLog)
        if type:
            query = query.filter(ActivityLog.type == type)
        if channel_id:
            query = query.filter(ActivityLog.channel_id == channel_id)
        if since:
            query = query.filter(ActivityLog.timestamp >= since)
        total = query.count()
        items = (
            query.order_by(desc(ActivityLog.timestamp))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._to_dict(item) for item in items],
        }

    def _to_dict(self, entry: ActivityLog) -> Dict[str, Any]:
        return {
            "id": entry.id,
            "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
            "type": entry.type,
            "message": entry.message,
            "details": entry.details,
            "user": entry.user,
        }

    def create_activity_log(self, type: str, message: str, details: Optional[Dict[str, Any]] = None, user: Optional[str] = None, channel_id: Optional[str] = None) -> ActivityLog:
        entry = ActivityLog(type=type, message=message, details=details, user=user, channel_id=channel_id)
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete_logs_older_than(self, cutoff):
        result = self.db.query(ActivityLog).filter(ActivityLog.timestamp < cutoff).delete()
        self.db.commit()
        return result
