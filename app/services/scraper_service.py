from typing import List, Tuple
from ..repositories import URLRepository, ChannelRepository
import logging
from ..models.url_types import create_url_object

logger = logging.getLogger(__name__)

class ScraperService:
    def __init__(self):
        self.url_repository = URLRepository()
        self.channel_repository = ChannelRepository()

    async def scrape_url(self, url: str, url_type: str = None) -> Tuple[List[Tuple[str, str, dict]], str]:
        """Scrape a URL and update channels."""
        try:
            # If URL type not provided, get it from database
            if url_type is None:
                url_obj = self.url_repository.get_by_url(url)
                url_type = url_obj.url_type if url_obj else 'regular'  # Default to regular if not found
            
            # Skip processing for special URL types that should not be scraped
            non_scrapable_types = ['search', 'manual']
            if url_type in non_scrapable_types:
                logger.info(f"Skipping URL '{url}' with type '{url_type}' (not intended for scraping)")
                # Update status to OK without actually scraping
                self.url_repository.update_status(url, 'ok')
                # Return empty links list and OK status
                return [], "OK"
            
            # Update URL status
            self.url_repository.update_status(url, 'processing')
            
            # Import here to avoid circular dependency
            from ..scrapers import create_scraper_for_url
            
            # Create and execute scraper with explicit URL type
            scraper = create_scraper_for_url(url, url_type)
            links, status = await scraper.scrape()
            
            if status == "OK":
                # Update channels with metadata
                self._update_channels(url, links)
                self.url_repository.update_status(url, status)
                
                # Update URL type in database if needed
                url_obj = create_url_object(url, url_type)
                self.url_repository.update_url_type(url, url_obj.type_name)
            else:
                self.url_repository.update_status(url, status, "Failed to scrape URL")
                
            return links, status
            
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {e}")
            self.url_repository.update_status(url, 'failed', str(e))
            raise

    async def _add_channels_to_database(self, channels: List[Tuple[str, str, dict]], source_url: str):
        """Add channels to the database with their metadata."""
        added_count = 0
        
        for channel_data in channels:
            channel_id, name, metadata = channel_data
            
            try:
                # Get the existing channel or create a new one
                channel = self.channel_repository.update_or_create(channel_id, name, source_url)
                
                # Update metadata fields if provided
                if 'tvg_id' in metadata:
                    channel.tvg_id = metadata['tvg_id']
                if 'tvg_name' in metadata:
                    channel.tvg_name = metadata['tvg_name']
                if 'logo' in metadata:
                    channel.logo = metadata['logo']
                if 'group' in metadata:
                    channel.group = metadata['group']
                
                # Save to database
                self.channel_repository.commit()
                added_count += 1
                
            except Exception as e:
                logger.error(f"Error adding channel {channel_id} to database: {e}")
        
        logger.info(f"Added/updated {added_count} channels in the database")

    def _update_channels(self, url: str, links: List[Tuple[str, str, dict]]):
        """Update channels for a given URL."""
        try:
            # Get current and existing channels
            current_channels = set(channel_id for channel_id, _, _ in links)
            existing_channels = set(
                ch.id for ch in self.channel_repository.get_by_source(url)
            )
            
            # Remove old channels
            channels_to_remove = existing_channels - current_channels
            if channels_to_remove:
                self.channel_repository.delete_by_source(url)
            
            # Add/update new channels with metadata
            for channel_id, channel_name, metadata in links:
                self.channel_repository.update_or_create(
                    channel_id=channel_id,
                    name=channel_name,
                    source_url=url,
                    metadata=metadata or {}
                )
                
            self.channel_repository.commit()
            
        except Exception as e:
            self.channel_repository.rollback()
            raise