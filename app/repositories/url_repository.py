from datetime import datetime, timezone
from typing import List, Optional
from ..models import ScrapedURL
from .base import BaseRepository

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