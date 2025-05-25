import asyncio
import logging
from typing import List, Tuple
from datetime import datetime, timedelta, timezone
from ..models import AcestreamChannel, ScrapedURL, EPGSource
from ..extensions import db
from ..scrapers import create_scraper_for_url
from ..services.epg_service import EPGService

logger = logging.getLogger(__name__)

class ScrapeWorker:
    """Worker class for executing scraping tasks."""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, url: str) -> Tuple[List[Tuple[str, str, dict]], str]:
        """Execute a scraping task for a single URL."""
        async with self.semaphore:
            # Get URL type from database
            url_obj = ScrapedURL.query.filter_by(url=url).first()
            url_type = url_obj.url_type if url_obj else 'auto'
            
            # Create scraper with the correct URL type
            scraper = create_scraper_for_url(url, url_type)
            return await scraper.scrape()

class ChannelCleanupWorker:
    """Worker class for cleaning up old channels."""
    
    def __init__(self, max_age_days: int = 7):
        self.max_age_days = max_age_days

    async def cleanup_old_channels(self):
        """Remove channels that haven't been seen in a while."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.max_age_days)
        
        try:
            old_channels = AcestreamChannel.query.filter(
                AcestreamChannel.last_processed < cutoff_date
            ).all()
            
            for channel in old_channels:
                db.session.delete(channel)
            
            db.session.commit()
            logger.info(f"Removed {len(old_channels)} old channels")
            
        except Exception as e:
            logger.error(f"Error during channel cleanup: {e}")
            db.session.rollback()


class EPGRefreshWorker:
    """Worker class for refreshing EPG data and programs."""
    
    def __init__(self, cleanup_old_programs_days: int = 7):
        self.cleanup_old_programs_days = cleanup_old_programs_days
        self.epg_service = EPGService()

    async def refresh_epg_data(self):
        """Refresh EPG data from all enabled sources."""
        try:
            # Check if EPG refresh is needed
            if not self.epg_service.should_refresh_epg():
                logger.info("EPG data is up to date, skipping refresh")
                return 0
            
            logger.info("Starting EPG data refresh")
            
            # Fetch fresh EPG data (this includes programs)
            epg_data = self.epg_service.fetch_epg_data()
            
            # Clean up old programs
            await self.cleanup_old_programs()
            
            # No need for separate timestamp update - it's done in fetch_epg_data
            
            logger.info(f"EPG refresh completed: {len(epg_data)} channels processed")
            return len(epg_data)
            
        except Exception as e:
            logger.error(f"Error during EPG refresh: {e}")
            raise

    async def cleanup_old_programs(self):
        """Remove old program data to prevent database bloat."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.cleanup_old_programs_days)
            
            deleted_count = self.epg_service.epg_program_repo.delete_old_programs(cutoff_date)
            logger.info(f"Cleaned up {deleted_count} old EPG programs (older than {self.cleanup_old_programs_days} days)")
            
        except Exception as e:
            logger.error(f"Error during EPG program cleanup: {e}")