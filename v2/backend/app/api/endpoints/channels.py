"""
API endpoints for channel management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.models.models import AcestreamChannel, TVChannel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import ChannelResponse, TVChannelResponse

router = APIRouter()


@router.get("/", response_model=List[ChannelResponse])
async def get_channels(
    skip: int = 0, 
    limit: int = 100,
    active_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all channels with optional filtering.
    """
    repo = ChannelRepository(db)
    channels = repo.get_channels(skip=skip, limit=limit, active_only=active_only, search=search)
    return channels


@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(channel_id: str, db: Session = Depends(get_db)):
    """
    Get a specific channel by ID.
    """
    repo = ChannelRepository(db)
    channel = repo.get_channel_by_id(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel


@router.get("/tv/", response_model=List[TVChannelResponse])
async def get_tv_channels(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all TV channels.
    """
    repo = ChannelRepository(db)
    return repo.get_tv_channels(skip=skip, limit=limit)
