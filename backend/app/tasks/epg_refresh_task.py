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
        summary = {
            "sources": len(results),
            "successful": sum(1 for item in results if item.get("success")),
            "failed": sum(1 for item in results if not item.get("success")),
        }
        logger.info("EPG refresh task completed summary=%s results=%s", summary, results)
        return summary
    except Exception as exc:
        logger.exception("EPG refresh task failed error=%s", exc)
        raise
    finally:
        db.close()
