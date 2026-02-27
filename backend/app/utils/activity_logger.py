import logging
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.activity_log import ActivityLog

def log_activity(db: Session, type: str, message: str, details: Optional[Any] = None, user: Optional[str] = None):
    entry = ActivityLog(
        timestamp=datetime.utcnow(),
        type=type,
        message=message,
        details=details,
        user=user
    )
    db.add(entry)
    db.commit()
    logging.info(f"Activity logged: {type} - {message}")
