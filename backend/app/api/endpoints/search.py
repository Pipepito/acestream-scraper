from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.search import SearchResponse, AddChannelRequest, AddMultipleRequest
from app.services.search_service import SearchService
from app.services.config_service import ConfigService

router = APIRouter(tags=["search"])

def get_config_service(db: Session = Depends(get_db)):
    """Get config service dependency."""
    from app.repositories.settings_repository import SettingsRepository
    settings_repo = SettingsRepository(db)
    return ConfigService(settings_repo)

def get_search_service(db: Session = Depends(get_db), config_service: ConfigService = Depends(get_config_service)):
    """Get search service dependency with DB and config."""
    return SearchService(config_service, db)

@router.get("", response_model=SearchResponse)
async def search_channels(
    query: str = Query("", description="Search query string (optional)"),
    page: int = Query(1, ge=1, description="Page number (default: 1, must be >= 1)"),
    page_size: int = Query(
        10,
        ge=1,
        alias="per_page",
        description="Results per page (default: 10, must be >= 1, alias: per_page)"
    ),
    category: Optional[str] = Query(None, description="Filter by category (optional)"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    Search for Acestream channels via engine API
    """
    # Cap page_size at 100
    if page_size > 100:
        page_size = 100
    return await search_service.search(query, page, page_size, category or "")

@router.post("/add")
async def add_channel(
    channel: AddChannelRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Add a channel from search results to the database (delegated to service)
    """
    return await search_service.add_channel(channel)

@router.post("/add_multiple")
async def add_multiple_channels(
    request: AddMultipleRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Add multiple channels from search results to the database (delegated to service)
    """
    return await search_service.add_multiple_channels(request)
