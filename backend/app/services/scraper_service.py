"""
Service for managing scraping operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Dict, Any, Optional
import logging

from app.models.models import ScrapedURL, AcestreamChannel
from app.models.url_types import create_url_object
from app.schemas.scraper import ChannelResult, URLResponse, URLCreate, URLUpdate
from app.scrapers import create_scraper_for_url
from app.services.m3u_service import M3UService
from app.services.epg_service import EPGService
from app.services.tvchannel_service import TVChannelService
from app.repositories.channel_repository import ChannelRepository
from app.repositories.url_repository import URLRepository

logger = logging.getLogger(__name__)


class ScrapeOutcome(tuple):
    """Two-value compatibility plus typed admission metadata for summaries."""
    def __new__(cls, channels, status, excluded_count=0):
        result = super().__new__(cls, (channels, status))
        result.excluded_count = excluded_count
        return result


class ScraperService:
    """Service for managing scraping operations"""

    def __init__(self, db: Session):
        self.db = db
        self.url_repository = URLRepository(db)
        self.last_import_exclusions = 0

    async def scrape_url(self, url: str, url_type: str = 'auto') -> Tuple[List[ChannelResult], str]:
        """
        Scrape a URL for acestream channels

        Args:
            url: The URL to scrape
            url_type: The URL type ('auto', 'regular', 'zeronet', 'ipfs')

        Returns:
            Tuple[List[ChannelResult], str]: Tuple of (channels, status)
        """
        logger.info(f"Scraping URL: {url} (type: {url_type})")

        self.last_import_exclusions = 0
        custom_recipe = False
        try:
            scraper = create_scraper_for_url(url, url_type)
            try:
                source_url = scraper.url_obj.get_normalized_url()
            except AttributeError:
                source_url = create_url_object(url, url_type).get_normalized_url()
            # Fetchers may update source status; admission/assignment runs later
            # in a worker-owned persistence session.
            scraper.db = self.db
            scraper.epg_service = None
            scraper.tv_channel_service = None
            url_record = self.url_repository.get_by_url(url) or self.url_repository.get_by_url(source_url)
            scraper.scrape_bare_ids = bool(url_record.scrape_bare_ids) if url_record else False
            if url_record and url_record.extraction_recipe:
                custom_recipe = True
                from starlette.concurrency import run_in_threadpool
                from app.schemas.extraction import ExtractionRecipe
                from app.services.extraction_service import fetch_recipe_sample, preview_recipe
                recipe = ExtractionRecipe.model_validate(url_record.extraction_recipe)
                sample = await fetch_recipe_sample(url, url_type)
                preview = await run_in_threadpool(preview_recipe, recipe, sample)
                if not preview.channels or preview.invalid_count:
                    raise ValueError('Recipe returned missing or invalid records; source channels were preserved. Test the recipe before scraping again.')
                raw_channels = [(item.channel_id, item.name, item.metadata) for item in preview.channels]
                status = "OK"
            else:
                raw_channels, status = await scraper.scrape()

            from starlette.concurrency import run_in_threadpool
            bind = self.db.get_bind()
            self.db.rollback()
            channels, self.last_import_exclusions = await run_in_threadpool(
                _apply_scrape, bind, raw_channels, url, source_url, custom_recipe, status)
            if custom_recipe:
                await scraper.update_url_status(source_url, "OK")
            return ScrapeOutcome(channels, status, self.last_import_exclusions)

        except Exception as e:
            self.db.rollback()
            if custom_recipe:
                await scraper.update_url_status(source_url, "Error: Recipe extraction failed; test the source configuration")
            logger.error(f"Error scraping URL {url}: {str(e)}")
            return [], f"Error: {str(e)}"

    def get_scraped_urls(self, skip: int = 0, limit: int = 100) -> List[URLResponse]:
        """Get list of URLs that have been scraped, including channels_found count"""
        urls = self.url_repository.get_all(skip=skip, limit=limit)
        # Get all source_urls in one query for efficiency
        url_to_count = {}
        if urls:
            normalized_url_map = {}
            for url in urls:
                try:
                    normalized_url_map[url.url] = create_url_object(url.url, url.url_type).get_normalized_url()
                except Exception:
                    normalized_url_map[url.url] = url.url
            url_list = list({*normalized_url_map.keys(), *normalized_url_map.values()})
            counts = (
                self.db.query(AcestreamChannel.source_url, func.count(AcestreamChannel.id))
                .filter(AcestreamChannel.source_url.in_(url_list))
                .group_by(AcestreamChannel.source_url)
                .all()
            )
            raw_counts = {url: count for url, count in counts}
            url_to_count = {}
            for original_url, normalized_url in normalized_url_map.items():
                count_keys = {original_url, normalized_url}
                url_to_count[original_url] = sum(raw_counts.get(key, 0) for key in count_keys)
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
            url.scrape_bare_ids = url_data.scrape_bare_ids
            if "extraction_recipe" in url_data.model_fields_set:
                url.extraction_recipe = url_data.extraction_recipe.model_dump() if url_data.extraction_recipe else None
            url = self.url_repository.update(url)
            return URLResponse.model_validate(url)
        # Create new if not exists
        url = ScrapedURL(
            url=url_data.url,
            url_type=url_data.url_type,
            enabled=url_data.enabled,
            status=url_data.status,
            scrape_bare_ids=url_data.scrape_bare_ids,
            extraction_recipe=url_data.extraction_recipe.model_dump() if url_data.extraction_recipe else None
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


def _apply_scrape(bind, raw_channels, url, source_url, custom_recipe, status):
    """Worker-owned session: no ORM rows cross the fetch/apply thread boundary."""
    with Session(bind=bind) as db:
        # Fetching has finished. Admission, reconciliation and TV assignment
        # share this short transaction and the policy's DB write claim.
        from app.services.import_exclusion_service import ImportExclusionService
        policy = ImportExclusionService(db).snapshot(claim=True)
        observed_ids = {cid for cid, _, _ in raw_channels}
        excluded_ids = {cid for cid, name, _ in raw_channels if policy.matches(cid, name)}
        excluded_count = len(excluded_ids)
        raw_channels = [(cid, name, meta) for cid, name, meta in raw_channels
                        if cid not in excluded_ids]
        source_urls = {url, source_url}
        source_query = db.query(AcestreamChannel).filter(AcestreamChannel.source_url.in_(source_urls))
        protected_ids = excluded_ids | {ch.id for ch in source_query.all() if policy.matches(ch.id, ch.name)}
        # All-excluded, empty, failed and partial snapshots never prune.
        if raw_channels and observed_ids and not custom_recipe and status == 'OK':
            missing = source_query.filter(~AcestreamChannel.id.in_(observed_ids | protected_ids))
            ChannelRepository(db).remove_search_memberships([row.id for row in missing.all()])
            missing.delete(synchronize_session=False)
        m3u_service = M3UService()
        raw_channels = m3u_service.auto_create_tv_channels_from_epg(
            db, raw_channels, EPGService(db), TVChannelService(db))

        # Persist channels to DB using transaction-scoped upserts
        channel_repository = ChannelRepository(db)
        persisted_channels = []
        for channel_id, name, metadata in raw_channels:
            persisted = channel_repository.create_or_update_channel(
                channel_id=channel_id,
                name=name,
                source_url=source_url,
                group=metadata.get('group_title', metadata.get('group', '')),
                logo=metadata.get('tvg_logo', metadata.get('logo', '')),
                tvg_id=metadata.get('tvg_id', ''),
                tvg_name=metadata.get('tvg_name', ''),
                # auto_create_tv_channels_from_epg also handles IDs that
                # have not been persisted yet. Carry its staged
                # association into the INSERT; existing rows are assigned
                # by the repository's conflict-checked UPDATE above.
                tv_channel_id=metadata.get('tv_channel_id'),
                # Set only for streams addressed by URL instead of by an
                # acestream id. See M3UService._looks_like_stream.
                stream_url=metadata.get('stream_url'),
                stream_headers=metadata.get('stream_headers'),
                # Catalogue presence is not evidence of a live signal.
                is_online=None,
                commit=False,
            )
            persisted_channels.append(persisted)
        db.commit()
        # Optional automation must also protect excluded incoming identities,
        # even when their stored operator name does not match the new rule.
        if not status.lower().startswith('error'):
            from app.services.epg_matching_automation import EPGMatchingAutomation
            EPGMatchingAutomation(db).run(import_excluded_ids=protected_ids)
        channels = [ChannelResult(channel_id=ch.id, name=ch.name, metadata={
            'group': ch.group, 'logo': ch.logo, 'tvg_id': ch.tvg_id,
            'tvg_name': ch.tvg_name, 'source_url': ch.source_url,
            'tv_channel_id': ch.tv_channel_id,
        }) for ch in persisted_channels]
        return channels, excluded_count
