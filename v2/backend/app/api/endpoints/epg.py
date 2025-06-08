"""
API endpoints for EPG management
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.config.database import get_db
from app.schemas.epg import (
    EPGSourceCreate, 
    EPGSourceUpdate, 
    EPGSourceResponse, 
    EPGChannelResponse,
    EPGProgramResponse,
    EPGStringMappingResponse,
    EPGRefreshResponse,
    EPGChannelMappingRequest
)
from app.services.epg_service import EPGService

router = APIRouter()


@router.get("/sources", response_model=List[EPGSourceResponse])
def get_epg_sources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all EPG sources
    """
    epg_service = EPGService(db)
    return epg_service.get_sources(skip=skip, limit=limit)


@router.get("/sources/{source_id}", response_model=EPGSourceResponse)
def get_epg_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific EPG source by ID
    """
    epg_service = EPGService(db)
    source = epg_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="EPG source not found")
    return source


@router.post("/sources", response_model=EPGSourceResponse)
def create_epg_source(
    source_data: EPGSourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new EPG source
    """
    epg_service = EPGService(db)
    return epg_service.create_source(source_data)


@router.patch("/sources/{source_id}", response_model=EPGSourceResponse)
def update_epg_source(
    source_id: int,
    source_data: EPGSourceUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an EPG source
    """
    epg_service = EPGService(db)
    source = epg_service.update_source(source_id, source_data)
    if not source:
        raise HTTPException(status_code=404, detail="EPG source not found")
    return source


@router.delete("/sources/{source_id}", status_code=204)
def delete_epg_source(
    source_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an EPG source
    """
    epg_service = EPGService(db)
    if not epg_service.delete_source(source_id):
        raise HTTPException(status_code=404, detail="EPG source not found")
    return None


@router.post("/sources/{source_id}/refresh", response_model=EPGRefreshResponse)
def refresh_epg_source(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Refresh EPG data for a specific source
    """
    epg_service = EPGService(db)
    source = epg_service.get_source(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="EPG source not found")
    
    # Start background task to refresh EPG
    background_tasks.add_task(epg_service.refresh_source, source_id)
    
    return {
        "source_id": source_id,
        "message": f"EPG refresh started for source: {source.name}",
        "success": True
    }


@router.post("/sources/refresh_all", response_model=List[EPGRefreshResponse])
def refresh_all_epg_sources(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Refresh EPG data for all enabled sources
    """
    epg_service = EPGService(db)
    sources = epg_service.get_enabled_sources()
    
    results = []
    for source in sources:
        background_tasks.add_task(epg_service.refresh_source, source.id)
        results.append({
            "source_id": source.id,
            "message": f"EPG refresh started for source: {source.name}",
            "success": True
        })
    
    return results


@router.get("/channels", response_model=List[EPGChannelResponse])
def get_epg_channels(
    source_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get EPG channels, optionally filtered by source ID
    """
    epg_service = EPGService(db)
    return epg_service.get_channels(source_id=source_id, skip=skip, limit=limit)


@router.get("/channels/{channel_id}", response_model=EPGChannelResponse)
def get_epg_channel(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific EPG channel by ID
    """
    epg_service = EPGService(db)
    channel = epg_service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="EPG channel not found")
    return channel


@router.post("/channels/map", status_code=204)
def map_epg_channel_to_tv(
    mapping: EPGChannelMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Map an EPG channel to a TV channel
    """
    epg_service = EPGService(db)
    if not epg_service.map_channel_to_tv(mapping.epg_channel_id, mapping.tv_channel_id):
        raise HTTPException(status_code=404, detail="EPG channel or TV channel not found")
    return None


@router.delete("/channels/map", status_code=204)
def unmap_epg_channel_from_tv(
    mapping: EPGChannelMappingRequest,
    db: Session = Depends(get_db)
):
    """
    Remove a mapping between an EPG channel and a TV channel
    """
    epg_service = EPGService(db)
    if not epg_service.unmap_channel_from_tv(mapping.epg_channel_id, mapping.tv_channel_id):
        raise HTTPException(status_code=404, detail="Mapping not found")
    return None


@router.get("/channels/{channel_id}/programs", response_model=List[EPGProgramResponse])
def get_epg_programs(
    channel_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get programs for an EPG channel, optionally filtered by date range
    """
    epg_service = EPGService(db)
    return epg_service.get_programs(
        channel_id=channel_id, 
        start_date=start_date, 
        end_date=end_date,
        skip=skip, 
        limit=limit
    )


@router.get("/channels/{channel_id}/mappings", response_model=List[EPGStringMappingResponse])
def get_epg_string_mappings(
    channel_id: int,
    db: Session = Depends(get_db)
):
    """
    Get string mappings for an EPG channel
    """
    epg_service = EPGService(db)
    return epg_service.get_string_mappings(channel_id)


@router.post("/channels/{channel_id}/mappings", response_model=EPGStringMappingResponse)
def add_epg_string_mapping(
    channel_id: int,
    mapping_data: dict,
    db: Session = Depends(get_db)
):
    """
    Add a string mapping for an EPG channel
    """
    epg_service = EPGService(db)
    return epg_service.add_string_mapping(
        channel_id=channel_id,
        search_pattern=mapping_data.get("search_pattern"),
        is_exclusion=mapping_data.get("is_exclusion", False)
    )


@router.delete("/mappings/{mapping_id}", status_code=204)
def delete_epg_string_mapping(
    mapping_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a string mapping
    """
    epg_service = EPGService(db)
    if not epg_service.delete_string_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="String mapping not found")
    return None
