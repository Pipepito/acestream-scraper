"""Bounded retention candidates; only configured, enabled sources are recoverable."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import AcestreamChannel, ScrapedURL
from app.repositories.channel_repository import ChannelRepository
from app.schemas.config import OfflineCleanupConfig
from app.services.source_health import removable_clause


class OfflineCleanupRepository:
    def __init__(self, db: Session):
        self.db = db

    def enabled_sources(self):
        return self.db.query(ScrapedURL.url, ScrapedURL.url_type).filter(ScrapedURL.enabled.is_(True)).order_by(ScrapedURL.id).all()

    def candidates(self, config: OfflineCleanupConfig, now: datetime, source_urls: list[str]) -> list[AcestreamChannel]:
        """Sources ``source_health`` says may go (``removable``), of configured
        enabled lists and checked within the last day, after their streak began."""
        query = self.db.query(AcestreamChannel).filter(
                AcestreamChannel.source_url.in_(source_urls),
                removable_clause(now, config.offline_days),
                AcestreamChannel.last_checked > AcestreamChannel.failing_since,
                AcestreamChannel.last_checked >= now - timedelta(hours=24),
                AcestreamChannel.last_checked <= now)
        if not config.remove_linked:
            query = query.filter(AcestreamChannel.tv_channel_id.is_(None))
        return query.order_by(AcestreamChannel.failing_since, AcestreamChannel.id).limit(500).all()

    def delete(self, rows: list[AcestreamChannel]) -> None:
        ChannelRepository(self.db).remove_search_memberships([row.id for row in rows])
        for row in rows:
            self.db.delete(row)
        self.db.commit()
