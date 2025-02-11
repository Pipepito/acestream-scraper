import asyncio
import logging
from datetime import datetime
from ..models import ScrapedURL
from ..extensions import db
from ..scrapers import create_scraper

class TaskManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 60  # seconds between retries

    async def start(self):
        self.running = True
        self.logger.info("Task Manager started")
        
        while self.running:
            try:
                # Get URLs that need processing
                with db.session() as session:
                    urls = session.query(ScrapedURL).filter(
                        (ScrapedURL.status == 'pending') |
                        ((ScrapedURL.status == 'failed') & 
                         (ScrapedURL.error_count < self.MAX_RETRIES))  # Add retry check
                    ).all()

                for url_obj in urls:
                    if not self.running:
                        break

                    try:
                        scraper = create_scraper(url_obj.url)
                        links = await scraper.scrape(url_obj.url)
                        
                        with db.session() as session:
                            url_record = session.query(ScrapedURL).get(url_obj.id)
                            if links:
                                url_record.status = 'success'
                                url_record.last_processed = datetime.utcnow()
                                # Reset retry count on success
                                url_record.error_count = 0
                            else:
                                # Increment retry count
                                url_record.error_count = (url_record.error_count or 0) + 1
                                if url_record.error_count >= self.MAX_RETRIES:
                                    url_record.status = 'failed'
                                    self.logger.error(f"URL {url_obj.url} failed after {self.MAX_RETRIES} retries")
                                else:
                                    url_record.status = 'pending'
                                url_record.last_processed = datetime.utcnow()
                            session.commit()

                    except Exception as e:
                        self.logger.error(f"Error processing URL {url_obj.url}: {str(e)}")
                        with db.session() as session:
                            url_record = session.query(ScrapedURL).get(url_obj.id)
                            url_record.error_count = (url_record.error_count or 0) + 1
                            if url_record.error_count >= self.MAX_RETRIES:
                                url_record.status = 'failed'
                                self.logger.error(f"URL {url_obj.url} failed after {self.MAX_RETRIES} retries")
                            else:
                                url_record.status = 'pending'
                            url_record.last_processed = datetime.utcnow()
                            session.commit()

            except Exception as e:
                self.logger.error(f"Task Manager error: {str(e)}")

            await asyncio.sleep(self.RETRY_DELAY)

    def stop(self):
        self.running = False
        self.logger.info("Task Manager stopped")