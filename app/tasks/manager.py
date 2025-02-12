import asyncio
import logging
from datetime import datetime
from ..models import ScrapedURL, AcestreamChannel
from ..extensions import db
from ..scrapers import create_scraper
from flask import current_app

class TaskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 60  # seconds between retries
        self.app = None
        self._processing_urls = set()  # Track URLs being processed

    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        self.running = True
        # Push an application context
        self.app.app_context().push()

    async def process_url(self, url: str):
        """Process a specific URL immediately."""
        if url in self._processing_urls:
            self.logger.info(f"URL {url} is already being processed")
            return
            
        self._processing_urls.add(url)
        try:
            url_obj = ScrapedURL.query.filter_by(url=url).first()
            if not url_obj:
                self.logger.error(f"URL {url} not found in database")
                return
                
            # Skip disabled URLs
            if url_obj.status == 'disabled':
                self.logger.info(f"Skipping disabled URL {url}")
                return
            
            # Update status to processing and timestamp
            url_obj.status = 'processing'
            url_obj.last_processed = datetime.utcnow()
            db.session.commit()
            
            scraper = create_scraper(url)
            self.logger.info(f"Processing URL {url}")
            
            links, status = await scraper.scrape(url)
            
            with db.session.begin():
                url_obj.status = status
                url_obj.last_processed = datetime.utcnow()
                
                if status == "OK":
                    url_obj.error_count = 0
                    url_obj.last_error = None
                    self.logger.info(f"Found {len(links)} channels from {url}")
                    
                    # Get current channel IDs from this URL
                    current_channels = set(channel_id for channel_id, _ in links)
                    
                    # Get existing channels from this URL
                    existing_channels = set(
                        ch.id for ch in AcestreamChannel.query.filter_by(source_url=url).all()
                    )
                    
                    # Remove channels that no longer exist in the source
                    channels_to_remove = existing_channels - current_channels
                    if channels_to_remove:
                        self.logger.info(f"Removing {len(channels_to_remove)} old channels from {url}")
                        AcestreamChannel.query.filter(
                            AcestreamChannel.source_url == url,
                            AcestreamChannel.id.in_(channels_to_remove)
                        ).delete(synchronize_session=False)
                    
                    # Update or add new channels
                    for channel_id, channel_name in links:
                        channel = db.session.get(AcestreamChannel, channel_id) or AcestreamChannel(id=channel_id)
                        channel.name = channel_name
                        channel.last_processed = datetime.utcnow()
                        channel.status = 'active'
                        channel.source_url = url
                        db.session.merge(channel)
                else:
                    url_obj.error_count = (url_obj.error_count or 0) + 1
                    url_obj.last_error = "Failed to scrape URL"
                    
                db.session.merge(url_obj)
                
        except Exception as e:
            self.logger.error(f"Error processing URL {url}: {str(e)}")
            if url_obj:
                url_obj.status = 'failed'
                url_obj.last_error = str(e)
                url_obj.error_count = (url_obj.error_count or 0) + 1
                db.session.commit()
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
                    urls = ScrapedURL.query.filter(
                        (ScrapedURL.status != 'disabled') &  # Skip disabled URLs
                        ((ScrapedURL.status == 'pending') |
                         (ScrapedURL.status == 'failed') & 
                         (ScrapedURL.error_count < self.MAX_RETRIES))
                    ).all()

                    if urls:
                        self.logger.info(f"Found {len(urls)} URLs to process")
                        for url_obj in urls:
                            if url_obj.url not in self._processing_urls:
                                await self.process_url(url_obj.url)

            except Exception as e:
                self.logger.error(f"Task Manager error: {str(e)}")

            await asyncio.sleep(self.RETRY_DELAY)

    def stop(self):
        self.running = False
        self.logger.info("Task Manager stopped")