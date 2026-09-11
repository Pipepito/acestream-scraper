"""Scheduler job: push channel/guide changes to Jellyfin/Plex (spec 7.3)."""
import logging

from app.config.database import SessionLocal
from app.services.media_servers.service import MediaServerService

logger = logging.getLogger(__name__)


def run_media_server_sync_task() -> dict:
    db = SessionLocal()
    try:
        service = MediaServerService(db)
        summary = {"checked": 0, "refreshed": 0, "manual": 0, "errors": 0}
        for server in service.repo.get_all():
            if not server.enabled or not server.auto_refresh:
                continue
            summary["checked"] += 1
            try:
                result = service.sync_if_changed(server)
            except Exception as exc:  # noqa: BLE001 - one server must not stop the others
                logger.exception("Media server sync failed for %s", server.name)
                server.last_sync_status = "error"
                server.last_error = str(exc)
                service.repo.save(server)
                summary["errors"] += 1
                continue
            if result is None:
                continue
            summary["refreshed" if result.status == "ok" else "manual" if result.status == "manual" else "errors"] += 1
        return summary
    finally:
        db.close()
