"""
Main application entry point for Acestream Scraper v2 backend.
"""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import Depends, FastAPI, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.api import api_router
from app.api.endpoints.playlists import (
    get_all_streams_playlist,
    get_m3u_playlist,
    get_tv_channels_playlist,
    trigger_url_scrape_refresh,
)
from app.api.error_handlers import register_error_handlers
from app.config.database import get_db
from app.config.settings import get_env_compat_events, settings
from app.services.epg_service import EPGService
from app.services.playlist_service import PlaylistService
from app.services.task_service import task_service
from app.tasks.activity_log_cleanup import run_activity_log_cleanup
from app.tasks.channel_cleanup_task import run_channel_cleanup_task
from app.tasks.channel_status_task import run_channel_status_task
from app.tasks.epg_refresh_task import run_epg_refresh_task
from app.tasks.url_scraping_task import run_url_scraping_task
from app.utils.logging import setup_logging

# Setup logging before anything else
setup_logging()
logging.getLogger().warning("[MAIN] Root logger active at startup")

for event in get_env_compat_events():
    logging.getLogger("app.config.settings").warning(
        "env_compat_event kind=%s legacy_key=%s new_key=%s selected=%s window=%s",
        event.get("kind"),
        event.get("legacy_key"),
        event.get("new_key"),
        event.get("selected"),
        event.get("window"),
    )


def _run_alembic_upgrade() -> None:
    from alembic import command
    from alembic.config import Config

    # When deployed in Docker, main.py lives at /app/main.py; migrations/ is
    # a sibling directory.  During local dev/tests, main.py is at
    # backend/main.py so migrations/ is also a sibling.  parent.parent would
    # give the repo root only when the CWD happens to equal backend/, which is
    # fragile — derive the path relative to __file__ instead.
    app_dir = Path(__file__).resolve().parent
    ini_path = app_dir / "migrations" / "alembic.ini"
    alembic_config = Config(str(ini_path))
    # Override script_location to an absolute path so Alembic can find the
    # env.py and versions/ regardless of the process CWD.
    alembic_config.set_main_option("script_location", str(app_dir / "migrations"))
    command.upgrade(alembic_config, "head")


def initialize_database():
    """Initialize database with migration check."""
    from migrate_database import DatabaseMigrator

    migrator = DatabaseMigrator()

    # Only run migration if acestream.db exists and hasn't been migrated yet.
    if migrator.should_migrate():
        print("Found v1 database, running migration...")
        migrated = migrator.run_migration()
        if migrated:
            print("Migration completed successfully!")
        return

    # Fresh v2 databases should be provisioned through Alembic so startup uses
    # the same schema path as tests and deployments.
    if not os.path.exists(migrator.v2_db_path):
        print("Creating fresh v2 database via Alembic...")
        _run_alembic_upgrade()
        print("Fresh v2 database created!")
    else:
        print("V2 database ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: provision the database, start the scheduler, and
    register periodic tasks on startup; tear the scheduler down on shutdown.
    Replaces the deprecated ``@app.on_event("startup"|"shutdown")`` hooks.
    """
    initialize_database()
    task_service.start()
    task_service.add_interval_task(run_activity_log_cleanup, seconds=86400, job_id="activity_log_cleanup")  # daily
    task_service.add_interval_task(run_epg_refresh_task, seconds=3600, job_id="epg_refresh")  # every hour
    task_service.add_interval_task(run_url_scraping_task, seconds=900, job_id="url_scraping")  # every 15 min
    task_service.add_interval_task(run_channel_cleanup_task, seconds=86400, job_id="channel_cleanup")  # daily
    task_service.add_interval_task(run_channel_status_task, seconds=600, job_id="channel_status")  # every 10 min
    try:
        yield
    finally:
        task_service.shutdown()


app = FastAPI(
    title="Acestream Scraper API",
    description="API for scraping and managing Acestream channels",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API routes with versioning
app.include_router(api_router, prefix="/api/v1")
register_error_handlers(app)

# Static files serving
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.FRONTEND_BUILD_PATH)
os.makedirs(frontend_dir, exist_ok=True)  # Ensure directory exists

# Check what static directories exist in the frontend build
static_dirs = []
for dirname in ["static", "assets"]:
    if os.path.isdir(os.path.join(frontend_dir, dirname)):
        static_dirs.append(dirname)

# Mount static files directories that exist
for dirname in static_dirs:
    app.mount(f"/{dirname}", StaticFiles(directory=os.path.join(frontend_dir, dirname)), name=dirname)

# Public playlist route for user-friendly URLs (no /api prefix)
@app.get("/playlists/m3u", response_class=PlainTextResponse)
async def public_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Public route for M3U playlist (no /api prefix)
    """
    if refresh:
        trigger_url_scrape_refresh()

    playlist_service = PlaylistService(db)
    try:
        include_groups_list = include_groups.split(",") if include_groups else None
        exclude_groups_list = exclude_groups.split(",") if exclude_groups else None
        m3u_content = await playlist_service.generate_playlist(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups_list,
            exclude_groups=exclude_groups_list,
            base_url=base_url,
            format=format
        )
        headers = {"Content-Disposition": "attachment; filename=playlist.m3u"}
        return PlainTextResponse(m3u_content, headers=headers)
    except Exception as e:
        return PlainTextResponse(f"#EXTM3U\n#EXTINF:-1,Error: {str(e)}\n", status_code=500)

# Legacy v1 playlist route. v1 served the playlist at /playlist.m3u and IPTV
# players are configured with that exact URL; without this route the SPA
# fallback would answer with index.html and HTTP 200, silently breaking them.
@app.get("/playlist.m3u", response_class=PlainTextResponse)
async def legacy_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Legacy v1 playlist URL. Behaves identically to /playlists/m3u.
    """
    return await public_m3u_playlist(
        search=search,
        group=group,
        only_online=only_online,
        include_groups=include_groups,
        exclude_groups=exclude_groups,
        base_url=base_url,
        format=format,
        refresh=refresh,
        db=db
    )

# Legacy v1 playlist API routes. v1 served these under /api/playlists/*;
# the canonical v2 routes live under /api/v1/playlists/*.
@app.get("/api/playlists/m3u", response_class=PlainTextResponse)
async def legacy_api_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Legacy v1 playlist API URL. Behaves identically to /api/v1/playlists/m3u
    (API error contract, unlike the player-facing /playlists/m3u route).
    """
    return await get_m3u_playlist(
        search=search,
        group=group,
        only_online=only_online,
        include_groups=include_groups,
        exclude_groups=exclude_groups,
        base_url=base_url,
        format=format,
        refresh=refresh,
        db=db
    )

@app.get("/api/playlists/tv-channels/m3u", response_class=PlainTextResponse)
async def legacy_tv_channels_playlist(
    search: Optional[str] = None,
    favorites_only: bool = False,
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Legacy v1 TV-channels playlist URL. Behaves identically to
    /api/v1/playlists/tv-channels/m3u.
    """
    return await get_tv_channels_playlist(
        search=search,
        favorites_only=favorites_only,
        base_url=base_url,
        format=format,
        refresh=refresh,
        db=db
    )

@app.get("/api/playlists/all-streams/m3u", response_class=PlainTextResponse)
async def legacy_all_streams_playlist(
    search: Optional[str] = None,
    include_unassigned: bool = True,
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Legacy v1 all-streams playlist URL. Behaves identically to
    /api/v1/playlists/all-streams/m3u.
    """
    return await get_all_streams_playlist(
        search=search,
        include_unassigned=include_unassigned,
        base_url=base_url,
        format=format,
        refresh=refresh,
        db=db
    )

# Legacy v1 EPG XML route. v1 served XMLTV data at /api/playlists/epg.xml and
# that URL is configured once in players/XMLTV grabbers; in v2 the canonical
# route moved to /api/v1/epg/xml, so keep the old URL answering.
@app.get("/api/playlists/epg.xml")
async def legacy_epg_xml(
    search_term: Optional[str] = None,
    favorites_only: bool = False,
    days_back: int = 1,
    days_forward: int = 7,
    db: Session = Depends(get_db)
):
    """
    Legacy v1 EPG XML URL. Behaves identically to /api/v1/epg/xml.
    """
    epg_service = EPGService(db)
    xml_content = epg_service.generate_epg_xml(
        search_term=search_term,
        favorites_only=favorites_only,
        days_back=days_back,
        days_forward=days_forward
    )
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": "attachment; filename=epg.xml"
        }
    )

# Serve React app - handle all other routes to support client-side routing
@app.exception_handler(StarletteHTTPException)
async def spa_server(request: Request, exc: StarletteHTTPException):
    """Serve SPA for all non-API routes."""
    # Only handle 404s for non-API routes (client-side routing)
    if exc.status_code == 404 and not request.url.path.startswith("/api"):
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    # For API routes or other status codes, return the exception as an HTTP response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the React frontend index page."""
    try:
        with open(os.path.join(frontend_dir, "index.html"), "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        # If frontend build doesn't exist yet, return a placeholder
        return HTMLResponse(content="<html><body><h1>Acestream Scraper</h1><p>Frontend not built yet. Please run 'npm run build' in the frontend directory.</p></body></html>")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
