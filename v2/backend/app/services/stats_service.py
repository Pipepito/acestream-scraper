from sqlalchemy.orm import Session

from app.config.settings import settings
from app.repositories.stats_repository import StatsRepository
from app.schemas.stats_schemas import StatsResponse, TVChannelStatsResponse, URLStats
from app.services.task_service import task_service


class StatsService:
    def __init__(self, db: Session):
        self.repository = StatsRepository(db)

    def get_stats(self) -> StatsResponse:
        urls = self.repository.get_urls()
        channels = self.repository.get_channels()
        channel_counts = self.repository.get_channel_counts_by_source_url([url.url for url in urls])
        # URL stats
        url_stats = []
        for url in urls:
            url_stats.append(URLStats(
                id=url.id,
                url=url.url,
                url_type=url.url_type,
                status=url.status,
                last_processed=str(url.last_scraped) if url.last_scraped else None,
                channel_count=channel_counts.get(url.url, 0),
                enabled=url.status != 'disabled',
                error_count=url.error_count or 0,
                last_error=url.last_error
            ))
        # Channel stats
        total_channels = len(channels)
        channels_checked = sum(1 for ch in channels if ch.last_checked is not None)
        channels_online = sum(1 for ch in channels if ch.last_checked is not None and ch.is_online is True)
        channels_offline = sum(1 for ch in channels if ch.last_checked is not None and ch.is_online is False)
        # Config
        base_url = getattr(settings, 'BASE_URL', '')
        ace_engine_url = getattr(settings, 'ACE_ENGINE_URL', '')
        rescrape_interval = getattr(settings, 'RESCRAPE_INTERVAL', 24)
        addpid = getattr(settings, 'ADDPID', False)
        # Task manager status
        try:
            jobs = task_service.get_jobs()
            task_manager_status = 'running' if jobs else 'stopped'
        except Exception:
            task_manager_status = 'unknown'
        return StatsResponse(
            urls=url_stats,
            total_channels=total_channels,
            channels=total_channels,  # Alias for compatibility
            channels_checked=channels_checked,
            channels_online=channels_online,
            channels_offline=channels_offline,
            base_url=base_url,
            ace_engine_url=ace_engine_url,
            rescrape_interval=rescrape_interval,
            addpid=addpid,
            task_manager_status=task_manager_status
        )

    def get_tv_channel_stats(self) -> TVChannelStatsResponse:
        total, active, with_epg, acestreams = self.repository.get_tv_channel_rollup()
        return TVChannelStatsResponse(
            total=total,
            active=active,
            with_epg=with_epg,
            acestreams=acestreams
        )

    def get_health_stats(self):
        """Compact stats payload for /health/stats endpoint."""
        rollup = self.repository.get_health_rollup()
        channels = rollup["channels"]
        return {
            "channels": channels,
            "channels_detail": {
                "total": channels,
                "online": 0,
                "offline": 0,
                "unknown": 0,
            },
            "urls": {
                "total": rollup["scraped_urls"],
                "active": 0,
                "error": 0,
            },
            "epg": {
                "sources": rollup["epg_sources"],
                "channels": rollup["epg_channels"],
                "programs": rollup["epg_programs"],
            },
        }
