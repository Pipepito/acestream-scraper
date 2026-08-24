"""
API endpoints for playlist management and generation
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.services.playlist_service import PlaylistService
from app.services.task_service import task_service

router = APIRouter()

M3U_DOWNLOAD_HEADERS = {"Content-Disposition": "attachment; filename=playlist.m3u"}


def trigger_url_scrape_refresh() -> None:
    """Kick off the URL-scraping background task for playlist refresh=true.

    Matches v1 semantics: the scrape is fire-and-forget and the playlist is
    generated from current data. Skipped when a scrape is already running or
    the scheduler is unavailable (e.g. under tests); never fails the request.
    """
    import logging
    try:
        outcome = task_service.run_task_now("url_scraping")
        logging.getLogger("app.api.playlists").info(
            "playlist refresh requested url_scraping trigger=%s", outcome
        )
    except Exception as exc:
        logging.getLogger("app.api.playlists").warning(
            "playlist refresh trigger failed error=%s", exc
        )


@router.get("/m3u", response_class=PlainTextResponse)
async def get_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    favorites_only: bool = False,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate M3U playlist with specified filters

    - **search**: Optional search term for channel names
    - **group**: Optional specific group to filter by
    - **only_online**: Whether to include only online channels (default: True)
    - **include_groups**: Comma-separated list of groups to include
    - **exclude_groups**: Comma-separated list of groups to exclude
    - **refresh**: Trigger a background rescrape of all enabled URLs
    """
    if refresh:
        trigger_url_scrape_refresh()

    playlist_service = PlaylistService(db)

    try:
        # Parse comma-separated strings into lists
        include_groups_list = include_groups.split(",") if include_groups else None
        exclude_groups_list = exclude_groups.split(",") if exclude_groups else None

        m3u_content = await playlist_service.generate_playlist(
            search=search,
            group=group,
            only_online=only_online,
            favorites_only=favorites_only,
            include_groups=include_groups_list,
            exclude_groups=exclude_groups_list,
            base_url=base_url,
            format=format
        )

        headers = {
            "Content-Disposition": "attachment; filename=playlist.m3u"
        }
        # Return the M3U content with proper headers
        return PlainTextResponse(m3u_content, headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate playlist: {str(e)}"
        )


@router.get("/playlists/m3u", response_class=PlainTextResponse)
async def get_m3u_playlist_compat(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    favorites_only: bool = False,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Compatibility route for M3U playlist generation

    This route exists to support legacy URLs. It behaves identically to the
    /m3u endpoint.
    """
    return await get_m3u_playlist(
        search=search,
        group=group,
        only_online=only_online,
        favorites_only=favorites_only,
        include_groups=include_groups,
        exclude_groups=exclude_groups,
        base_url=base_url,
        format=format,
        refresh=refresh,
        db=db
    )


@router.get("/tv-channels/m3u", response_class=PlainTextResponse)
async def get_tv_channels_playlist(
    search: Optional[str] = None,
    favorites_only: bool = False,
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate a curated M3U playlist of TV channels with their assigned
    acestreams, ordered by channel number then name.

    - **search**: Optional search term for TV channel names
    - **favorites_only**: Only include favorite TV channels
    - **refresh**: Trigger a background rescrape of all enabled URLs
    """
    if refresh:
        trigger_url_scrape_refresh()

    playlist_service = PlaylistService(db)
    try:
        m3u_content = await playlist_service.generate_tv_channels_playlist(
            search=search,
            favorites_only=favorites_only,
            base_url=base_url,
            format=format
        )
        return PlainTextResponse(m3u_content, headers=M3U_DOWNLOAD_HEADERS)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate TV channels playlist: {str(e)}"
        )


@router.get("/all-streams/m3u", response_class=PlainTextResponse)
async def get_all_streams_playlist(
    search: Optional[str] = None,
    include_unassigned: bool = True,
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate an M3U playlist of numbered TV channels followed by unassigned
    acestreams (numbered from 9000).

    - **search**: Optional search term for channel names
    - **include_unassigned**: Append streams not assigned to any TV channel
    - **refresh**: Trigger a background rescrape of all enabled URLs
    """
    if refresh:
        trigger_url_scrape_refresh()

    playlist_service = PlaylistService(db)
    try:
        m3u_content = await playlist_service.generate_all_streams_playlist(
            search=search,
            include_unassigned=include_unassigned,
            base_url=base_url,
            format=format
        )
        return PlainTextResponse(m3u_content, headers=M3U_DOWNLOAD_HEADERS)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate all-streams playlist: {str(e)}"
        )


@router.get("/groups", response_model=List[str])
async def get_channel_groups(
    db: Session = Depends(get_db)
):
    """
    Get list of all available channel groups
    """
    playlist_service = PlaylistService(db)

    try:
        groups = await playlist_service.get_channel_groups()
        return groups
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve channel groups: {str(e)}"
        )
