"""Bounded retention candidates; only configured, enabled sources are recoverable."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import AcestreamChannel, ScrapedURL
from app.repositories.channel_repository import ChannelRepository
from app.schemas.config import OfflineCleanupConfig


class OfflineCleanupRepository:
    def __init__(self, db: Session):
        self.db = db

    def candidates(self, config: OfflineCleanupConfig, now: datetime):
        query = self.db.query(AcestreamChannel, ScrapedURL.url_type).join(
            ScrapedURL, ScrapedURL.url == AcestreamChannel.source_url).filter(
                ScrapedURL.enabled.is_(True), AcestreamChannel.stream_url.is_(None),
                AcestreamChannel.is_online.is_(False),
                AcestreamChannel.offline_since <= now - timedelta(days=config.offline_days),
                AcestreamChannel.last_checked > AcestreamChannel.offline_since,
                AcestreamChannel.last_checked >= now - timedelta(hours=24),
                AcestreamChannel.last_checked <= now,
                AcestreamChannel.network_status.in_(['found', 'not_found']))
        if not config.remove_linked:
            query = query.filter(AcestreamChannel.tv_channel_id.is_(None))
        return query.order_by(AcestreamChannel.offline_since, AcestreamChannel.id).limit(500).all()

    def delete(self, rows: list[AcestreamChannel]) -> None:
        ChannelRepository(self.db).remove_search_memberships([row.id for row in rows])
        for row in rows:
            self.db.delete(row)
        self.db.commit()
