from typing import Dict, Any, Optional
import logging
import asyncio
from fastapi import HTTPException

from app.repositories.channel_repository import ChannelRepository
from app.repositories.url_repository import URLRepository
from app.services.channel_service import ChannelService
from app.schemas.search import AddChannelRequest, AddMultipleRequest
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class SearchService:
    """Service for searching Acestream channels via the engine API."""

    def __init__(self, config_service=None, db: Session = None):
        """Initialize search service with engine URL from config service."""
        self.config_service = config_service
        self._engine_url = None
        self.db = db
        if db:
            self.channel_repo = ChannelRepository(db)
            self.url_repo = URLRepository(db)
            self.channel_service = ChannelService(db)
        else:
            self.channel_repo = None
            self.url_repo = None
            self.channel_service = None

    def _get_engine_url(self) -> str:
        """Get the configured engine URL without inventing a fallback."""
        if self._engine_url:
            return self._engine_url

        if self.config_service:
            engine_url = self.config_service.get_ace_engine_url()
        else:
            engine_url = ''
        if not (engine_url or '').strip():
            raise HTTPException(status_code=503, detail='AceStream Engine URL is not configured')

        # If URL doesn't start with a protocol, assume http://
        if not engine_url.startswith('http'):
            engine_url = f"http://{engine_url}"

        # Ensure the URL doesn't end with a slash
        engine_url = engine_url.rstrip('/')

        self._engine_url = engine_url
        logger.debug(f"Acestream Search Service initialized with engine URL: {engine_url}")
        return engine_url

    async def search(self, query: str = "", page: int = 1, page_size: int = 10, category: str = "") -> Dict[str, Any]:
        from app.services.search_catalogue_client import SearchCatalogueClient, CatalogueReadError, flatten_results
        from app.api.error_handlers import APIError
        url = self.config_service.get_ace_engine_url() if self.config_service else ''
        if self.db:
            self.db.rollback()
        def read():
            with SearchCatalogueClient(url) as client:
                payload = client.get('/search', dict(query=query.strip(), category=category, page=page - 1, page_size=page_size))
                return flatten_results(payload)
        try:
            items, total, invalid, capped = await asyncio.to_thread(read)
        except CatalogueReadError as exc:
            raise APIError(exc.code, 'Configure a reachable AceStream engine in Settings → Playback.', 503) from None
        return dict(success=True, message='Search partial: invalid or excess entries were omitted' if invalid or capped else 'Search successful',
            results=[dict(item, id=item['infohash']) for item in items],
            pagination=dict(page=page, page_size=page_size, total_results=total,
                            total_pages=(total + page_size - 1) // page_size))

    async def check_broadcast(self, infohash: str) -> Dict[str, Any]:
        from app.models.models import AcestreamChannel
        from app.services.channel_status_service import ChannelStatusService

        # Search IDs are infohashes, not transport-file content IDs. This
        # preview must not add a channel or overwrite an inventory record.
        service = ChannelStatusService(self.db)
        return await service.check_channel_status(
            AcestreamChannel(id=infohash, name=infohash), identifier='infohash', persist=False
        )

    async def resolve_content_id(self, infohash: str) -> str:
        from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError

        # Resolve against the catalogue/playback engine, never the checker or
        # Acexy. Do not start playback or persist anything during this lookup.
        if self.config_service and not (self.config_service.get_ace_engine_url() or "").strip():
            raise HTTPException(status_code=503, detail="AceStream Engine URL is not configured")
        engine_url = self._get_engine_url()

        def resolve():
            with EngineClient(engine_url) as engine:
                return engine.resolve_content_id(infohash)

        try:
            return await asyncio.to_thread(resolve)
        except EngineRefusedError:
            raise HTTPException(status_code=502, detail="The engine could not resolve this search result. Try again later.") from None
        except EngineUnavailableError:
            raise HTTPException(status_code=502, detail="Could not resolve the search result. Check the AceStream engine and try again.") from None

    def extract_acestream_id(self, url: str) -> Optional[str]:
        """
        Extract acestream ID from a URL.

        Args:
            url: Acestream URL

        Returns:
            Extracted ID or None if not found
        """
        if url.startswith('acestream://'):
            return url.split('acestream://')[1]
        return None

    async def add_channel(self, channel: AddChannelRequest):
        from app.schemas.search import SearchImportItem, SearchImportRequest
        # Legacy IDs explicitly mean catalogue infohashes, just like /import.
        request = SearchImportRequest(items=[SearchImportItem(infohash=channel.id or '',
            name=channel.name, category=channel.category or '')])
        return await self._import_in_worker(request)

    async def add_multiple_channels(self, request: AddMultipleRequest):
        from app.schemas.search import SearchImportItem, SearchImportRequest
        items = SearchImportRequest(items=[SearchImportItem(infohash=c.id or '', name=c.name,
            category=c.category or '') for c in request.channels])
        return await self._import_in_worker(items)

    async def _import_in_worker(self, request):
        from starlette.concurrency import run_in_threadpool
        from app.services.search_import_service import SearchImportService
        bind = self.db.get_bind()
        self.db.rollback()
        def import_items():
            with Session(bind=bind) as db:
                return SearchImportService(db).import_items(request)
        return await run_in_threadpool(import_items)
