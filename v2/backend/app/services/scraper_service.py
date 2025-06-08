"""
Service for managing scraping operations
"""
from sqlalchemy.orm import Session
from typing import List, Tuple, Dict, Any, Optional
import logging

from app.models.models import ScrapedURL
from app.schemas.scraper import ChannelResult, URLResponse
from app.scrapers import create_scraper_for_url

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for managing scraping operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def scrape_url(self, url: str, url_type: str = 'auto') -> Tuple[List[ChannelResult], str]:
        """
        Scrape a URL for acestream channels
        
        Args:
            url: The URL to scrape
            url_type: The URL type ('auto', 'regular', 'zeronet')
            
        Returns:
            Tuple[List[ChannelResult], str]: Tuple of (channels, status)
        """
        logger.info(f"Scraping URL: {url} (type: {url_type})")
        
        try:
            scraper = create_scraper_for_url(url, url_type)
            raw_channels, status = await scraper.scrape()
            
            # Convert raw channels to ChannelResult objects
            channels = [
                ChannelResult(
                    channel_id=channel_id,
                    name=name,
                    metadata=metadata
                )
                for channel_id, name, metadata in raw_channels
            ]
            
            return channels, status
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return [], f"Error: {str(e)}"
    
    def get_scraped_urls(self, skip: int = 0, limit: int = 100) -> List[URLResponse]:
        """Get list of URLs that have been scraped"""
        urls = self.db.query(ScrapedURL).offset(skip).limit(limit).all()
        return [URLResponse.from_orm(url) for url in urls]
