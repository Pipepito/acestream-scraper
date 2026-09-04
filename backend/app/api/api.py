"""
API router configuration
"""
from fastapi import APIRouter
from app.api.endpoints import channels, scrapers, epg, playlists, tv_channels, search, config, health, warp, urls, acestream, stats, activity, background_tasks, streams, base_urls, system, player, remote_players, tuner

api_router = APIRouter()
api_router.include_router(channels.router, prefix="/acestream-channels", tags=["channels"])
# Backward-compatible alias retained for parity and existing test expectations.
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(tv_channels.router, prefix="/tv-channels", tags=["tv-channels"])
api_router.include_router(scrapers.router, prefix="/scrapers", tags=["scrapers"])
api_router.include_router(epg.router, prefix="/epg", tags=["epg"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(warp.router, prefix="/warp", tags=["warp"])
api_router.include_router(urls.router, prefix="/urls", tags=["urls"])
api_router.include_router(acestream.router, prefix="/acestream", tags=["acestream"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(activity.router, prefix="/activity", tags=["activity"])
api_router.include_router(background_tasks.router, tags=["background-tasks"])
api_router.include_router(streams.router, tags=["streams"])
api_router.include_router(base_urls.router, prefix="/base-urls", tags=["base-urls"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(player.router, prefix="/player", tags=["player"])
api_router.include_router(remote_players.router, prefix="/remote-players", tags=["remote-players"])
# Operator-facing tuner settings/status. The token-free HDHomeRun routes are
# tuner.hdhr_router, mounted on the app itself in main.py.
api_router.include_router(tuner.router, prefix="/tuner", tags=["tuner"])
