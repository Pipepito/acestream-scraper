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

    def init_app(self, app):
        """Initialize with Flask app context"""
        self.app = app
        # Push an application context
        self.app.app_context().push()

    async def start(self):
        if not self.app:
            raise RuntimeError("TaskManager not initialized with Flask app. Call init_app() first.")
            
        self.running = True
        self.logger.info("Task Manager started")
        
        while self.running:
            try:
                with self.app.app_context():
                    # Get URLs that need processing
                    urls = ScrapedURL.query.filter(
                        (ScrapedURL.status == 'pending') |
                        ((ScrapedURL.status == 'failed') & 
                         (ScrapedURL.error_count < self.MAX_RETRIES))
                    ).all()

                    if urls:
                        self.logger.info(f"Processing {len(urls)} URLs")

                    for url_obj in urls:
                        if not self.running:
                            break

                        try:
                            scraper = create_scraper(url_obj.url)
                            scraper_name = scraper.__class__.__name__
                            self.logger.info(f"Processing URL {url_obj.url} with {scraper_name}")
                            
                            links, status = await scraper.scrape(url_obj.url)
                            
                            with db.session.begin():
                                url_obj.status = status
                                url_obj.last_processed = datetime.utcnow()
                                
                                if status == "OK":
                                    url_obj.error_count = 0
                                    self.logger.info(f"Found {len(links)} channels from {url_obj.url}")
                                    
                                    for channel_id, channel_name in links:
                                        channel = db.session.get(AcestreamChannel, channel_id) or AcestreamChannel(id=channel_id)
                                        channel.name = channel_name
                                        channel.last_processed = datetime.utcnow()
                                        channel.status = 'active'
                                        channel.source_url = url_obj.url  # Add this line
                                        db.session.merge(channel)
                                else:
                                    url_obj.error_count = (url_obj.error_count or 0) + 1
                                    if url_obj.error_count >= self.MAX_RETRIES:
                                        self.logger.error(f"URL {url_obj.url} failed after {self.MAX_RETRIES} retries")
                                
                                db.session.merge(url_obj)

                        except Exception as e:
                            self.logger.error(f"Error processing URL {url_obj.url}: {str(e)}")
                            with db.session.begin():
                                url_obj.error_count = (url_obj.error_count or 0) + 1
                                url_obj.status = 'failed' if url_obj.error_count >= self.MAX_RETRIES else 'pending'
                                url_obj.last_processed = datetime.utcnow()
                                db.session.merge(url_obj)

            except Exception as e:
                self.logger.error(f"Task Manager error: {str(e)}")

            await asyncio.sleep(self.RETRY_DELAY)

    def stop(self):
        self.running = False
        self.logger.info("Task Manager stopped")