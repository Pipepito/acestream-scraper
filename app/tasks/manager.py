import asyncio
import logging
import time
from datetime import datetime, timedelta, timezone
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..scrapers import create_scraper
from flask import current_app
from sqlalchemy.exc import OperationalError
from contextlib import contextmanager
from ..services import ScraperService
from ..repositories import URLRepository
from ..utils.config import Config
from .workers import EPGRefreshWorker
from app.services.epg_service import EPGService, refresh_epg_data
from app.services.tv_channel_service import TVChannelService

class TaskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.MAX_RETRIES = 3
        self.config = Config()
        self.RETRY_DELAY = 60  # seconds between retries
        self.app = None
        self._processing_urls = set()
        self.scraper_service = ScraperService()
        self.url_repository = URLRepository()
        self.epg_refresh_worker = EPGRefreshWorker()
        self.tv_channel_service = TVChannelService()
        # Setting last_epg_refresh to None will force an initial refresh
        # This will be updated after the first refresh
        self.last_epg_refresh = None
        # Track if channels were updated during current cycle
        self.channels_updated_in_cycle = False
    
    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        self.running = True

    @contextmanager
    def database_retry(self, max_retries=3):
        """Context manager for handling SQLite disk I/O errors with retries."""
        retry_count = 0
        while True:
            try:
                yield
                break
            except OperationalError as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
                self.logger.warning(f"SQLite error, retrying ({retry_count}/{max_retries}): {e}")
                db.session.rollback()
                time.sleep(1)
    
    async def process_url(self, url: str):
        if url in self._processing_urls:
            self.logger.info(f"URL {url} is already being processed")
            return
            
        self._processing_urls.add(url)        
        try:
            if self.app and not current_app._get_current_object():
                with self.app.app_context():
                    links, status = await self.scraper_service.scrape_url(url)
                    # Track if channels were actually updated (not just checked)
                    if status == "OK" and links:
                        self.channels_updated_in_cycle = True
            else:
                links, status = await self.scraper_service.scrape_url(url)
                # Track if channels were actually updated (not just checked)
                if status == "OK" and links:
                    self.channels_updated_in_cycle = True
        finally:
            self._processing_urls.remove(url)
    
    def should_refresh_epg(self):
        """Check if EPG data needs to be refreshed."""
        if self.last_epg_refresh is None:
            self.logger.info("Initial EPG refresh needed (no previous refresh recorded)")
            return True
        
        config = Config()
        refresh_interval = timedelta(hours=config.epg_refresh_interval)
        time_since_refresh = datetime.now(timezone.utc) - self.last_epg_refresh
        should_refresh = time_since_refresh >= refresh_interval
        
        if should_refresh:
            self.logger.info(f"EPG refresh needed (last refresh: {self.last_epg_refresh}, interval: {config.epg_refresh_interval} hours)")
        else:
            self.logger.debug(f"EPG refresh not needed yet (last refresh: {self.last_epg_refresh}, next in: {refresh_interval - time_since_refresh})")
            
        return should_refresh

    async def refresh_epg_if_needed(self):
        """Refresh EPG data if the refresh interval has passed."""
        if self.should_refresh_epg():
            try:
                self.logger.info("Starting EPG refresh")
                await self.epg_refresh_worker.refresh_epg_data()
                self.last_epg_refresh = datetime.now(timezone.utc)
                self.logger.info("EPG refresh completed successfully")
            except Exception as e:
                self.logger.error(f"EPG refresh failed: {str(e)}")

    async def start(self):
        """Main task loop."""
        if not self.app:
            raise RuntimeError("TaskManager not initialized with Flask app. Call init_app() first.")
            
        self.running = True
        self.logger.info("Task Manager started")
        while self.running:
            try:
                with self.app.app_context():
                    # Check and refresh EPG data if needed
                    await self.refresh_epg_if_needed()

                    config = Config()                    
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=config.rescrape_interval)
                    urls = ScrapedURL.query.filter(
                        (ScrapedURL.status != 'disabled') &  # Skip disabled URLs
                        ((ScrapedURL.status == 'pending') |
                         ((ScrapedURL.status == 'failed') & 
                          (ScrapedURL.error_count < self.MAX_RETRIES)) |
                         (ScrapedURL.last_processed < cutoff_time))
                    ).all()
                    
                    if urls:
                        self.logger.info(f"Found {len(urls)} URLs to process")
                        # Reset the update tracking flag at the start of a new cycle
                        self.channels_updated_in_cycle = False
                        
                        # Process all URLs
                        for url_obj in urls:
                            if url_obj.url not in self._processing_urls:
                                if url_obj.status == 'OK':
                                    url_obj.status = 'pending'
                                    db.session.commit()
                                await self.process_url(url_obj.url)
                        
                        # After all URLs are processed, associate channels if any were updated
                        if self.channels_updated_in_cycle:
                            self.logger.info("URLs processed, re-associating channels by EPG ID...")
                            await self.associate_channels_by_epg()
            except Exception as e:
                self.logger.error(f"Task Manager error: {str(e)}")
            await asyncio.sleep(self.RETRY_DELAY)

    def stop(self):
        self.running = False
        self.logger.info("Task Manager stopped")

    async def associate_channels_by_epg(self):
        """Associate acestream channels with TV channels based on EPG IDs."""
        try:
            self.logger.info("Starting automatic EPG association after scraping")
            stats = self.tv_channel_service.associate_by_epg_id()
            
            # Log meaningful results
            matched = stats.get('matched', 0)
            created = stats.get('created', 0)
            unmatched = stats.get('unmatched', 0)
            
            if matched > 0 or created > 0:
                self.logger.info(f"EPG association completed: {created} TV channels created, {matched} acestreams matched, {unmatched} remain unmatched")
            else:
                self.logger.debug("EPG association completed: No new associations made")
                
        except Exception as e:
            self.logger.error(f"Error during automatic EPG association: {str(e)}")

def initialize_app():
    """Initialize the application on startup"""
    logger = logging.getLogger(__name__)
    logger.info("Task Manager started")
    
    # Check if EPG refresh is needed
    epg_service = EPGService()
    if epg_service.should_refresh_epg():
        logger.info("Initial EPG refresh needed")
        logger.info("Starting EPG refresh")
        refresh_epg_data()
    else:
        logger.info("EPG data is up to date, skipping refresh")