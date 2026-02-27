"""
Service for managing scraping operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Dict, Any, Optional
import logging

from app.models.models import ScrapedURL, AcestreamChannel
from app.schemas.scraper import ChannelResult, URLResponse, URLCreate, URLUpdate
from app.scrapers import create_scraper_for_url
from app.services.channel_service import ChannelService
from app.services.m3u_service import M3UService
from app.services.epg_service import EPGService
from app.services.tvchannel_service import TVChannelService
from app.repositories.url_repository import URLRepository

logger = logging.getLogger(__name__)


class ScraperService:
    """Service for managing scraping operations"""

    def __init__(self, db: Session):
        self.db = db
        self.url_repository = URLRepository(db)

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
            # Inject db, epg_service, tv_channel_service for robust TV channel creation/association
            epg_service = EPGService(self.db)
            tv_channel_service = TVChannelService(self.db)
            scraper.db = self.db
            scraper.epg_service = epg_service
            scraper.tv_channel_service = tv_channel_service
            raw_channels, status = await scraper.scrape()

            # Auto-create TV channels from EPG and assign tv_channel_id
            m3u_service = M3UService()
            raw_channels = m3u_service.auto_create_tv_channels_from_epg(self.db, raw_channels, epg_service, tv_channel_service)

            # Remove old channels for this source_url
            existing_channels = {ch.id for ch in self.db.query(self.db.query(AcestreamChannel).filter_by(source_url=url).subquery()).all()}
            new_channel_ids = {channel_id for channel_id, _, _ in raw_channels}
            channels_to_remove = existing_channels - new_channel_ids
            if channels_to_remove:
                for ch_id in channels_to_remove:
                    ch = self.db.query(AcestreamChannel).filter(AcestreamChannel.id == ch_id).first()
                    if ch:
                        self.db.delete(ch)
                self.db.commit()

            # Persist channels to DB using ChannelService
            channel_service = ChannelService(self.db)
            persisted_channels = []
            for channel_id, name, metadata in raw_channels:
                persisted = channel_service.create_channel(
                    channel_id=channel_id,
                    name=name,
                    source_url=url,
                    group=metadata.get('group_title') or metadata.get('group') or None,
                    logo=metadata.get('tvg_logo') or metadata.get('logo') or None,
                    tvg_id=metadata.get('tvg_id') or None,
                    tvg_name=metadata.get('tvg_name') or None,
                    is_online=True
                )
                persisted_channels.append(persisted)
            self.db.commit()

            return [
                ChannelResult(
                    channel_id=ch.id,
                    name=ch.name,
                    metadata={
                        'group': ch.group,
                        'logo': ch.logo,
                        'tvg_id': ch.tvg_id,
                        'tvg_name': ch.tvg_name,
                        'source_url': ch.source_url,
                        'tv_channel_id': getattr(ch, 'tv_channel_id', None)
                    }
                ) for ch in persisted_channels
            ], status

        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return [], f"Error: {str(e)}"

    def get_scraped_urls(self, skip: int = 0, limit: int = 100) -> List[URLResponse]:
        """Get list of URLs that have been scraped, including channels_found count"""
        urls = self.url_repository.get_all(skip=skip, limit=limit)
        # Get all source_urls in one query for efficiency
        url_to_count = {}
        if urls:
            url_list = [u.url for u in urls]
            counts = (
                self.db.query(AcestreamChannel.source_url, func.count(AcestreamChannel.id))
                .filter(AcestreamChannel.source_url.in_(url_list))
                .group_by(AcestreamChannel.source_url)
                .all()
            )
            url_to_count = {url: count for url, count in counts}
        responses = []
        for url in urls:
            channels_found = url_to_count.get(url.url, 0)
            data = url.__dict__.copy()
            data['channels_found'] = channels_found
            responses.append(URLResponse(**data))
        return responses

    def get_scraped_url(self, url_id: int) -> Optional[URLResponse]:
        """Get a specific scraped URL by ID"""
        url = self.url_repository.get_by_id(url_id)
        return URLResponse.model_validate(url) if url else None

    def get_scraped_url_entity(self, url_id: int) -> Optional[ScrapedURL]:
        """Get raw scraped URL model for service-internal decisions."""
        return self.url_repository.get_by_id(url_id)

    def create_scraped_url(self, url_data: URLCreate) -> URLResponse:
        """Create a new scraped URL or update existing if duplicate"""
        # Check for existing URL
        url = self.url_repository.get_by_url(url_data.url)
        if url:
            # Update fields if duplicate
            url.url_type = url_data.url_type
            url.enabled = url_data.enabled
            url.status = url_data.status
            url = self.url_repository.update(url)
            return URLResponse.model_validate(url)
        # Create new if not exists
        url = ScrapedURL(
            url=url_data.url,
            url_type=url_data.url_type,
            enabled=url_data.enabled,
            status=url_data.status
        )
        self.url_repository.add(url)
        self.db.refresh(url)
        return URLResponse.model_validate(url)

    def update_scraped_url(self, url_id: int, url_data: URLUpdate) -> Optional[URLResponse]:
        """Update a scraped URL"""
        url = self.url_repository.get_by_id(url_id)
        if not url:
            return None

        update_data = url_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(url, field, value)

        url = self.url_repository.update(url)
        self.db.refresh(url)
        return URLResponse.model_validate(url)

    def delete_scraped_url(self, url_id: int) -> bool:
        """Delete a scraped URL"""
        url = self.url_repository.get_by_id(url_id)
        if not url:
            return False

        self.url_repository.delete(url)
        return True

    def get_enabled_urls(self) -> List[ScrapedURL]:
        """Get all enabled URLs"""
        return self.url_repository.get_enabled()
