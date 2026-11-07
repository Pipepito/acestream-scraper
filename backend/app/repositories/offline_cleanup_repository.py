"""Bounded retention candidates; only configured, enabled sources are recoverable."""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.models import AcestreamChannel, ScrapedURL
from app.models.stream_attempts import StreamAttempt
from app.repositories.channel_repository import ChannelRepository
from app.schemas.config import OfflineCleanupConfig


class OfflineCleanupRepository:
    def __init__(self, db: Session):
        self.db = db

    def enabled_sources(self):
        return self.db.query(ScrapedURL.url, ScrapedURL.url_type).filter(ScrapedURL.enabled.is_(True)).order_by(ScrapedURL.id).all()

    def candidates(self, config: OfflineCleanupConfig, now: datetime, source_urls: list[str]) -> list[AcestreamChannel]:
        # Playback can prove a stale probe wrong without rewriting its status.
        played_since = self.db.query(StreamAttempt.id).filter(
            StreamAttempt.content_id == AcestreamChannel.id,
            StreamAttempt.created_at >= now - timedelta(days=config.offline_days),
            StreamAttempt.created_at <= now,
            StreamAttempt.outcome.in_(['ok', 'ended', 'stall']),
            StreamAttempt.seconds > 0,
        ).exists()
        query = self.db.query(AcestreamChannel).filter(
                AcestreamChannel.source_url.in_(source_urls), AcestreamChannel.stream_url.is_(None),
                AcestreamChannel.is_online.is_(False),
                AcestreamChannel.offline_since <= now - timedelta(days=config.offline_days),
                AcestreamChannel.last_checked > AcestreamChannel.offline_since,
                AcestreamChannel.last_checked >= now - timedelta(hours=24),
                AcestreamChannel.last_checked <= now,
                AcestreamChannel.network_status.in_(['found', 'not_found']), ~played_since)
        if not config.remove_linked:
            query = query.filter(AcestreamChannel.tv_channel_id.is_(None))
        return query.order_by(AcestreamChannel.offline_since, AcestreamChannel.id).limit(500).all()

    def delete(self, rows: list[AcestreamChannel]) -> None:
        ChannelRepository(self.db).remove_search_memberships([row.id for row in rows])
        for row in rows:
            self.db.delete(row)
        self.db.commit()
