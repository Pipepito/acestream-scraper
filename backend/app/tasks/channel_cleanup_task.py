"""
Periodic task for removing stale channels.

A channel the user hid from the playlist (is_active=False) is kept: hiding is
a choice, not a deletion. It is removed only once it is stale (no scrape has
seen it for CHANNEL_CLEANUP_DAYS days) and no TV channel links to it.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.settings import get_settings
from app.models.models import AcestreamChannel

logger = logging.getLogger("channel_cleanup_task")


def cleanup_hidden_channels(db: Session, *, days: int, now: Optional[datetime] = None) -> Dict[str, object]:
    """Delete hidden, unlinked channels not seen for ``days`` days. Returns a summary."""
    moment = now or datetime.now(timezone.utc)
    cutoff = moment - timedelta(days=days)
    stale = (
        db.query(AcestreamChannel)
        .filter(AcestreamChannel.is_active.is_(False))
        .filter(AcestreamChannel.tv_channel_id.is_(None))
        .filter((AcestreamChannel.last_seen.is_(None)) | (AcestreamChannel.last_seen < cutoff))
        .all()
    )
    for channel in stale:
        db.delete(channel)
    db.commit()
    return {"deleted": len(stale), "days": days, "cutoff": cutoff.isoformat()}


def run_channel_cleanup_task():
    db = SessionLocal()
    try:
        days = int(get_settings().CHANNEL_CLEANUP_DAYS)
        result = cleanup_hidden_channels(db, days=days)
        logger.info("Channel cleanup task completed: %s stale hidden channels deleted (older than %s days).", result["deleted"], days)
        return result
    except Exception as e:
        logger.error(f"Channel cleanup task failed: {e}")
        raise
    finally:
        db.close()
