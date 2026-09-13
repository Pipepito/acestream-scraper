"""Repository for statistics-focused read operations."""
from typing import Dict, List, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.models import AcestreamChannel, EPGChannel, EPGProgram, EPGSource, ScrapedURL, TVChannel


class StatsRepository:
    """Encapsulates database queries used by stats/health services."""

    def __init__(self, db: Session):
        self.db = db

    def get_urls(self) -> List[ScrapedURL]:
        result = self.db.execute(select(ScrapedURL))
        return result.scalars().all()

    def get_channels(self) -> List[AcestreamChannel]:
        result = self.db.execute(select(AcestreamChannel))
        return result.scalars().all()

    def get_channel_counts_by_source_url(self, source_urls: List[str]) -> Dict[str, int]:
        if not source_urls:
            return {}
        query = (
            self.db.query(AcestreamChannel.source_url, func.count(AcestreamChannel.id))
            .filter(AcestreamChannel.source_url.in_(source_urls))
            .group_by(AcestreamChannel.source_url)
        )
        return {source_url: count for source_url, count in query.all()}

    def get_tv_channel_rollup(self) -> Tuple[int, int, int, int]:
        total = self.db.query(TVChannel).count()
        active = self.db.query(TVChannel).filter(TVChannel.is_active == True).count()
        with_epg = self.db.query(TVChannel).filter(TVChannel.epg_id.isnot(None)).count()
        acestreams = self.db.query(AcestreamChannel).filter(AcestreamChannel.tv_channel_id.isnot(None)).count()
        return total, active, with_epg, acestreams

    def get_health_rollup(self) -> Dict[str, int]:
        return {
            "channels": self.db.query(AcestreamChannel).count(),
            # Same buckets as ChannelStatusService.get_status_summary: a channel is
            # online/offline once checked, unknown until then.
            "channels_online": self.db.query(AcestreamChannel).filter(AcestreamChannel.is_online.is_(True)).count(),
            "channels_offline": self.db.query(AcestreamChannel).filter(AcestreamChannel.is_online.is_(False)).count(),
            "channels_unknown": self.db.query(AcestreamChannel).filter(AcestreamChannel.is_online.is_(None)).count(),
            "scraped_urls_active": self.db.query(ScrapedURL).filter(ScrapedURL.enabled.is_(True)).count(),
            "scraped_urls_error": self.db.query(ScrapedURL).filter(ScrapedURL.status.ilike("error%")).count(),
            "tv_channels": self.db.query(TVChannel).count(),
            "epg_sources": self.db.query(EPGSource).count(),
            "epg_channels": self.db.query(EPGChannel).count(),
            "epg_programs": self.db.query(EPGProgram).count(),
            "scraped_urls": self.db.query(ScrapedURL).count(),
        }
