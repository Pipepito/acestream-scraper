import logging
from typing import Optional, List
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from ..models import ScrapedURL
from .base import BaseRepository

logger = logging.getLogger(__name__)

class URLRepository(BaseRepository[ScrapedURL]):
    def __init__(self):
        super().__init__(ScrapedURL)

    def get_pending(self, max_retries: int) -> List[ScrapedURL]:
        return self.model.query.filter(
            (ScrapedURL.status != 'disabled') & 
            ((ScrapedURL.status == 'pending') |
             (ScrapedURL.status == 'failed') & 
             (ScrapedURL.error_count < max_retries))
        ).all()
        
    def get_by_url(self, url: str) -> Optional[ScrapedURL]:
        return self.model.query.filter_by(url=url).first()

    def get_by_id(self, id: str) -> Optional[ScrapedURL]:
        """Get a URL by its ID."""
        return self.model.query.filter_by(id=id).first()
        
    def update_status(self, url: str, status: str, error: str = None):
        url_obj = self.get_by_url(url)
        if url_obj:
            url_obj.status = status
            url_obj.last_processed = datetime.now(timezone.utc)
            if error:
                url_obj.error_count = (url_obj.error_count or 0) + 1
                url_obj.last_error = error
            else:
                url_obj.error_count = 0
                url_obj.last_error = None
            self.commit()

    def get_enabled(self):
        return self.model.query.filter_by(enabled=True).all()
        
    def update(self, url_obj):
        """Update a URL object in the database"""
        self._db.session.add(url_obj)
        self._db.session.commit()
        return url_obj

    def add(self, url: str, url_type: str = 'regular') -> ScrapedURL:
        """Add a new URL to scrape."""
        try:
            url_obj = ScrapedURL(url=url, url_type=url_type)
            self._db.session.add(url_obj)
            self._db.session.commit()
            return url_obj
        except Exception as e:
            self._db.session.rollback()
            logger.error(f"Error adding URL to database: {str(e)}", exc_info=True)
            raise

    def delete(self, url_obj_or_id):
        """Delete a URL."""
        try:
            if isinstance(url_obj_or_id, str):
                # Assume it's an ID
                url_obj = self.get_by_id(url_obj_or_id)
            else:
                # Assume it's a URL object
                url_obj = url_obj_or_id
                
            if url_obj:
                self._db.session.delete(url_obj)
                self._db.session.commit()
                return True
            return False
        except Exception as e:
            self._db.session.rollback()
            logger.error(f"Error deleting URL: {e}", exc_info=True)
            return False

    def update_enabled(self, url: str, enabled: bool) -> Optional[ScrapedURL]:
        """Enable or disable a URL."""
        url_obj = self.get_by_url(url)
        if url_obj:
            url_obj.enabled = enabled
            self._db.session.commit()
            return url_obj
        return None
        
    def update_url_type(self, url: str, url_type: str) -> Optional[ScrapedURL]:
        """Update the URL type."""
        url_obj = self.get_by_url(url)
        if url_obj:
            url_obj.url_type = url_type
            self._db.session.commit()
            return url_obj
        return None

    def get_or_create_by_type_and_url(self, url_type: str, url: str, enabled: bool = True, trigger_scrape: bool = False) -> ScrapedURL:
        """Get a URL by type and URL, or create it if it doesn't exist."""
        try:
            # Try to find existing URL
            scraped_url = self.model.query.filter_by(url=url, url_type=url_type).first()
            
            # If it doesn't exist, create it
            if not scraped_url:
                from datetime import datetime, timezone
                scraped_url = self.model(
                    url=url,
                    url_type=url_type,
                    added_at=datetime.now(timezone.utc),
                    enabled=enabled,
                    status='pending' if trigger_scrape else 'ok'
                )
                self._db.session.add(scraped_url)
                self._db.session.commit()
                logger.info(f"Created new {url_type} URL: {url}")
            
            return scraped_url
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error getting or creating URL by type {url_type} and URL {url}: {e}")
            raise
    
    def get_or_create_manual_url(self, base_url: str) -> ScrapedURL:
        """Get or create a special URL for manually added channels.
        
        Args:
            base_url: The base URL of the application (e.g., http://localhost:8000)
            
        Returns:
            A ScrapedURL object for manually added channels
        """
        try:
            # Try to find existing manual URL
            manual_url = self.model.query.filter_by(url_type='manual').first()
            
            # If it doesn't exist, create it
            if not manual_url:
                from datetime import datetime, timezone
                manual_url = self.model(
                    url=base_url,
                    url_type='manual',
                    added_at=datetime.now(timezone.utc),
                    enabled=False,  # Disabled so we don't try to scrape our own service
                    status='ok',
                    channel_count=0
                )
                self._db.session.add(manual_url)
                self._db.session.commit()
                logger.info(f"Created new manual URL entry: {base_url}")
            
            return manual_url
        except SQLAlchemyError as e:
            self._db.session.rollback()
            logger.error(f"Error getting or creating manual URL: {e}")
            raise