"""
API endpoints for playlist management and generation
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.services.playlist_service import PlaylistService

router = APIRouter()


@router.get("/m3u", response_class=PlainTextResponse)
async def get_m3u_playlist(
    search: Optional[str] = None,
    group: Optional[str] = None,
    only_online: bool = True,
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    print("[DEBUG] /api/v1/playlists/m3u endpoint called")
    """
    Generate M3U playlist with specified filters

    - **search**: Optional search term for channel names
    - **group**: Optional specific group to filter by
    - **only_online**: Whether to include only online channels (default: True)
    - **include_groups**: Comma-separated list of groups to include
    - **exclude_groups**: Comma-separated list of groups to exclude
    """
    playlist_service = PlaylistService(db)

    try:
        # Parse comma-separated strings into lists
        include_groups_list = include_groups.split(",") if include_groups else None
        exclude_groups_list = exclude_groups.split(",") if exclude_groups else None

        # TEMP: Test if endpoint is hit
        if search == "__test__":
            return PlainTextResponse("#EXTM3U\n#EXTINF:-1,Test Channel\nacestream://TEST_ID\n", headers={"Content-Disposition": "attachment; filename=playlist.m3u"})

        m3u_content = await playlist_service.generate_playlist(
            search=search,
            group=group,
            only_online=only_online,
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
    include_groups: Optional[str] = Query(None),
    exclude_groups: Optional[str] = Query(None),
    base_url: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
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
        include_groups=include_groups,
        exclude_groups=exclude_groups,
        base_url=base_url,
        format=format,
        db=db
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
