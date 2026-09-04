import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog


def log_activity(db: Session, type: str, message: str, details: Optional[Any] = None, user: Optional[str] = None):
    entry = ActivityLog(
        timestamp=datetime.now(timezone.utc),
        type=type,
        message=message,
        details=details,
        user=user
    )
    db.add(entry)
    db.commit()
    logging.info(f"Activity logged: {type} - {message}")
