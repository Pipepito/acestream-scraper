"""
API router configuration
"""
from fastapi import APIRouter
from app.api.endpoints import channels, scrapers, epg, playlists

api_router = APIRouter()
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(scrapers.router, prefix="/scrapers", tags=["scrapers"])
api_router.include_router(epg.router, prefix="/epg", tags=["epg"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
