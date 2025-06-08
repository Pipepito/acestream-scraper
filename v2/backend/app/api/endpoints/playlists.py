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
    include_groups: Optional[List[str]] = Query(None),
    exclude_groups: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Generate M3U playlist with specified filters
    
    - **search**: Optional search term for channel names
    - **group**: Optional specific group to filter by
    - **only_online**: Whether to include only online channels (default: True)
    - **include_groups**: List of groups to include (if specified, only these groups will be included)
    - **exclude_groups**: List of groups to exclude
    """
    playlist_service = PlaylistService(db)
    
    try:
        m3u_content = await playlist_service.generate_playlist(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups
        )
        
        # Return the M3U content with proper headers
        return m3u_content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate playlist: {str(e)}"
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
