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
                    await self.scraper_service.scrape_url(url)
            else:
                await self.scraper_service.scrape_url(url)
        finally:
            self._processing_urls.remove(url)

    async def start(self):
        """Main task loop."""
        if not self.app:
            raise RuntimeError("TaskManager not initialized with Flask app. Call init_app() first.")
            
        self.running = True
        self.logger.info("Task Manager started")
        
        while self.running:
            try:
                with self.app.app_context():
                    config = Config()
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=config.rescrape_interval)
                    
                    urls = ScrapedURL.query.filter(
                        (ScrapedURL.status != 'disabled') &  # Skip disabled URLs
                        ((ScrapedURL.status == 'pending') |
                         (ScrapedURL.status == 'failed') & 
                         (ScrapedURL.error_count < self.MAX_RETRIES) |
                         (ScrapedURL.last_processed < cutoff_time))
                    ).all()

                    if urls:
                        self.logger.info(f"Found {len(urls)} URLs to process")
                        for url_obj in urls:
                            if url_obj.url not in self._processing_urls:
                                if url_obj.status == 'OK':
                                    url_obj.status = 'pending'
                                    db.session.commit()
                                await self.process_url(url_obj.url)

            except Exception as e:
                self.logger.error(f"Task Manager error: {str(e)}")

            await asyncio.sleep(self.RETRY_DELAY)

    def stop(self):
        self.running = False
        self.logger.info("Task Manager stopped")