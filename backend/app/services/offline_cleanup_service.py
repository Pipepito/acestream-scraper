"""Opt-in offline retention, separate from hiding streams for viewers."""
import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.repositories.offline_cleanup_repository import OfflineCleanupRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import OfflineCleanupConfig, OfflineCleanupPreview

KEY = 'offline_stream_cleanup'


class OfflineCleanupService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = SettingsRepository(db)
        self.repository = OfflineCleanupRepository(db)

    def get(self) -> OfflineCleanupConfig:
        raw = self.settings.get_setting(KEY)
        return OfflineCleanupConfig.model_validate_json(raw) if raw else OfflineCleanupConfig()

    def save(self, config: OfflineCleanupConfig) -> bool:
        return self.settings.set_setting(KEY, config.model_dump_json())

    def preview(self, config: OfflineCleanupConfig) -> OfflineCleanupPreview:
        rows = self.repository.candidates(config, datetime.now(timezone.utc))
        return OfflineCleanupPreview(eligible_streams=len(rows), sources=len({row.source_url for row, _ in rows}))

    def run(self) -> dict[str, int | str]:
        config = self.get()
        if not config.enabled:
            return {'deleted': 0, 'status': 'disabled'}
        from app.services import viewing
        if viewing.watching():
            return {'deleted': 0, 'status': 'deferred', 'message': 'Playback or recording is active; cleanup will retry on its next scheduled run.'}
        # Serialize with imports and re-evaluate eligibility under the write claim.
        from app.services.import_exclusion_service import ImportExclusionService
        ImportExclusionService(self.db).snapshot(claim=True)
        rows = self.repository.candidates(config, datetime.now(timezone.utc))
        sources = {(row.source_url, kind) for row, kind in rows}
        self.repository.delete([row for row, _ in rows])
        result = {'deleted': len(rows), 'rescraped': 0, 'rescrape_failures': 0}
        if config.rescrape:
            from app.services.scraper_service import ScraperService
            from app.services.task_service import task_service
            async def refresh() -> None:
                for url, kind in sorted(sources):
                    if task_service.shutdown_event.is_set():
                        result['status'] = 'interrupted'
                        break
                    try:
                        _, status = await ScraperService(self.db).scrape_url(url, kind)
                        if status.lower().startswith('error'):
                            result['rescrape_failures'] += 1
                        else:
                            result['rescraped'] += 1
                    except Exception:
                        self.db.rollback()
                        result['rescrape_failures'] += 1
            asyncio.run(refresh())
        return result


def configure_offline_cleanup(task_service) -> None:
    from app.config.database import SessionLocal
    from app.tasks.offline_cleanup_task import run_offline_cleanup
    with SessionLocal() as db:
        config = OfflineCleanupService(db).get()
    if config.enabled:
        task_service.add_interval_task(run_offline_cleanup, seconds=config.interval_days * 86400, job_id=KEY)
    elif task_service.scheduler.get_job(KEY) is not None:
        task_service.remove_task(KEY)
