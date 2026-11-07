"""Runs inside the shared maintenance FIFO; no nested job acquisition."""
from app.config.database import SessionLocal
from app.services.offline_cleanup_service import OfflineCleanupService


def run_offline_cleanup():
    with SessionLocal() as db:
        return OfflineCleanupService(db).run()
