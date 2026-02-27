"""
Periodic task for refreshing EPG data.
"""
from app.config.database import SessionLocal
from app.services.epg_service import EPGService
import logging

def run_epg_refresh_task():
    db = SessionLocal()
    logger = logging.getLogger("epg_refresh_task")
    try:
        service = EPGService(db)
        results = service.refresh_all_sources()
        logger.info("EPG refresh task completed results=%s", results)
    except Exception as e:
        logger.error("EPG refresh task failed error=%s", e)
    finally:
        db.close()
