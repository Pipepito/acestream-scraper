from sqlalchemy.orm import Session
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime, timezone

from app.models.models import ScrapedURL

class URLRepository:
    """Repository for ScrapedURL operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ScrapedURL]:
        """Get all ScrapedURLs"""
        result = self.db.execute(select(ScrapedURL).offset(skip).limit(limit))
        return result.scalars().all()

    def get_enabled(self) -> List[ScrapedURL]:
        """Get enabled ScrapedURLs only."""
        result = self.db.execute(select(ScrapedURL).where(ScrapedURL.enabled == True))
        return result.scalars().all()

    def get_by_id(self, url_id: int) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by id"""
        result = self.db.execute(select(ScrapedURL).where(ScrapedURL.id == url_id))
        return result.scalar_one_or_none()

    def get_by_url(self, url: str) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by url"""
        result = self.db.execute(select(ScrapedURL).where(ScrapedURL.url == url))
        return result.scalar_one_or_none()

    def get_by_type_and_url(self, url_type: str, url: str) -> Optional[ScrapedURL]:
        """Get a ScrapedURL by type and url"""
        result = self.db.execute(
            select(ScrapedURL).where(ScrapedURL.url_type == url_type, ScrapedURL.url == url)
        )
        return result.scalar_one_or_none()

    def get_or_create_by_type_and_url(
        self,
        url_type: str,
        url: str,
        trigger_scrape: bool = True
    ) -> ScrapedURL:
        """Get or create a ScrapedURL by type and url"""
        scraped_url = self.get_by_type_and_url(url_type, url)

        if scraped_url:
            return scraped_url

        # Create new ScrapedURL
        scraped_url = ScrapedURL(
            url=url,
            url_type=url_type,
            added_at=datetime.now(timezone.utc),
            last_scraped=None
        )

        self.db.add(scraped_url)
        self.db.flush()
        self.db.commit()

        return scraped_url

    def add(self, scraped_url: ScrapedURL) -> ScrapedURL:
        """Add a new ScrapedURL"""
        self.db.add(scraped_url)
        self.db.flush()
        self.db.commit()
        return scraped_url

    def update(self, scraped_url: ScrapedURL) -> ScrapedURL:
        """Update an existing ScrapedURL"""
        self.db.add(scraped_url)
        self.db.commit()
        return scraped_url

    def delete(self, scraped_url: ScrapedURL) -> None:
        """Delete a ScrapedURL"""
        self.db.delete(scraped_url)
        self.db.commit()

    def refresh_url(self, url_id: int) -> bool:
        """Mark one URL as refreshing and update the last scrape timestamp."""
        updated = (
            self.db.query(ScrapedURL)
            .filter(ScrapedURL.id == url_id)
            .update(
                {
                    "last_scraped": datetime.now(timezone.utc),
                    "status": "refreshing",
                },
                synchronize_session=False,
            )
        )
        if updated:
            self.db.commit()
            return True
        return False

    def refresh_all_urls(self) -> int:
        """Mark all URLs as refreshing and update the last scrape timestamp."""
        now = datetime.now(timezone.utc)
        updated = (
            self.db.query(ScrapedURL)
            .update(
                {
                    "last_scraped": now,
                    "status": "refreshing",
                },
                synchronize_session=False,
            )
        )
        self.db.commit()
        return updated
