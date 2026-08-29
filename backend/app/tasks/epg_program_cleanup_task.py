"""
Periodic task that deletes EPG programs which already ended.

Retention is ``EPG_PROGRAM_RETENTION_HOURS`` (default 24 h, negative disables);
the same setting makes the v1 -> v2 migration skip programs that already ended.
"""
import logging

from app.config.database import SessionLocal
from app.services.epg_service import EPGService


def run_epg_program_cleanup_task():
    db = SessionLocal()
    logger = logging.getLogger("epg_program_cleanup_task")
    try:
        result = EPGService(db).purge_expired_programs()
        logger.info("EPG program cleanup task completed result=%s", result)
        return result
    except Exception as exc:
        logger.exception("EPG program cleanup task failed error=%s", exc)
        raise
    finally:
        db.close()
