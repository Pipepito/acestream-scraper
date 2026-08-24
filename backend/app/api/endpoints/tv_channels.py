"""
API endpoints for TV channel management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.services.tvchannel_service import TVChannelService
from app.services.acestreamchannel_service import AcestreamChannelService
from app.services.epg_match_service import EPGMatchService
from app.schemas.channel import (
    AcestreamChannelResponse,
    EPGMatchAnalysisRequest,
    EPGMatchAnalysisResponse,
    MessageResponse,
    TVChannelAssociationRequest,
    TVChannelBatchAssignRequest,
    TVChannelBatchAssignResponse,
    TVChannelBulkEPGUpdateRequest,
    TVChannelBulkEPGUpdateResponse,
    TVChannelCreateFromEPGRequest,
    TVChannelCreateFromEPGAnalysisRequest,
    TVChannelCreateFromEPGAnalysisResponse,
    TVChannelCreateFromEPGResponse,
    TVChannelCreate,
    TVChannelListResponse,
    TVChannelResponse,
    TVChannelUpdate,
)

router = APIRouter()


from fastapi import Query


@router.get("/", response_model=TVChannelListResponse)
async def get_tv_channels(
    skip: int = Query(0, alias="skip"),
    limit: int = Query(100, alias="limit"),
    page: int = Query(None, alias="page"),
    page_size: int = Query(None, alias="page_size"),
    search: str = Query(None),
    favorites: bool = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all TV channels with pagination and total count.
    Optional filters: search (name substring), favorites=true.
    """
    # Convert page/page_size to skip/limit if provided
    if page is not None and page_size is not None:
        skip = (page - 1) * page_size
        limit = page_size
    service = TVChannelService(db)
    items, total = service.get_tv_channels_with_total(
        skip=skip, limit=limit, search=search, favorites_only=bool(favorites)
    )
    items_serialized = [TVChannelResponse.model_validate(item) for item in items]
    return {"items": items_serialized, "total": total}


@router.post("/{tv_channel_id}/favorite", response_model=TVChannelResponse)
async def set_tv_channel_favorite(
    tv_channel_id: int,
    value: bool = Query(None, description="Explicit favorite state; omit to toggle"),
    db: Session = Depends(get_db)
):
    """
    Toggle (or explicitly set, via ?value=) a TV channel's favorite flag.
    """
    service = TVChannelService(db)
    tv_channel = service.set_favorite(tv_channel_id, value)
    if tv_channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TV channel not found")
    return TVChannelResponse.model_validate(tv_channel)


@router.get("/{tv_channel_id}/acestream-matches", response_model=List[AcestreamChannelResponse])
async def get_tv_channel_acestream_matches(
    tv_channel_id: int,
    db: Session = Depends(get_db)
):
    """
    Suggest unassigned acestreams matching this TV channel by EPG id or
    normalized name, for the assign flow.
    """
    service = TVChannelService(db)
    matches = service.find_unassigned_matches(tv_channel_id)
    if matches is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TV channel not found")
    return matches


@router.post(
    "/analyze-epg-matches",
    status_code=status.HTTP_200_OK,
    response_model=EPGMatchAnalysisResponse,
)
async def analyze_epg_matches(request: EPGMatchAnalysisRequest, db: Session = Depends(get_db)):
    service = EPGMatchService(db)
    try:
        return service.analyze_matches(strictness=request.strictness, source_id=request.source_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{tv_channel_id}", response_model=TVChannelResponse)
async def get_tv_channel(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Get a specific TV channel by ID.
    """
    service = TVChannelService(db)
    tv_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not tv_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")
    return tv_channel


@router.post("/from-epg", status_code=status.HTTP_200_OK, response_model=TVChannelCreateFromEPGResponse)
async def create_tv_channels_from_epg(request: TVChannelCreateFromEPGRequest, db: Session = Depends(get_db)):
    service = TVChannelService(db)
    result = service.create_tv_channels_from_epg(request.epg_channel_ids)
    return result


@router.post(
    "/create-from-epg-analysis",
    status_code=status.HTTP_200_OK,
    response_model=TVChannelCreateFromEPGAnalysisResponse,
)
async def create_tv_channels_from_epg_analysis(
    request: TVChannelCreateFromEPGAnalysisRequest,
    db: Session = Depends(get_db),
):
    service = TVChannelService(db)
    try:
        return service.create_tv_channels_from_epg_analysis(
            strictness=request.strictness,
            epg_channel_ids=request.epg_channel_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/", response_model=TVChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_tv_channel(tv_channel: TVChannelCreate, db: Session = Depends(get_db)):
    """
    Create a new TV channel.
    """
    if not tv_channel.name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty"
        )

    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_name(tv_channel.name)
    if existing_channel:
        raise HTTPException(
            status_code=400,
            detail=f"TV Channel with name {tv_channel.name} already exists"
        )

    return service.create_tv_channel(
        name=tv_channel.name,
        logo_url=tv_channel.logo_url,
        description=tv_channel.description,
        category=tv_channel.category,
        country=tv_channel.country,
        language=tv_channel.language,
        website=tv_channel.website,
        epg_id=tv_channel.epg_id,
        epg_source_id=tv_channel.epg_source_id,
        channel_number=tv_channel.channel_number,
        is_active=tv_channel.is_active or True,
        is_favorite=tv_channel.is_favorite or False
    )


@router.put("/{tv_channel_id}", response_model=TVChannelResponse)
async def update_tv_channel(
    tv_channel_id: int,
    tv_channel_update: TVChannelUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing TV channel.
    """
    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    updated_channel = service.update_tv_channel(
        tv_channel_id=tv_channel_id,
        updates=tv_channel_update.dict(exclude_unset=True)
    )
    return updated_channel


@router.delete("/{tv_channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tv_channel(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Delete a TV channel.
    """
    service = TVChannelService(db)
    existing_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not existing_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    service.delete_tv_channel(tv_channel_id)
    return None


@router.get("/{tv_channel_id}/acestreams", response_model=List[AcestreamChannelResponse])
async def get_tv_channel_acestreams(tv_channel_id: int, db: Session = Depends(get_db)):
    """
    Get all acestream channels associated with a TV channel.
    """
    service = TVChannelService(db)
    tv_channel = service.get_tv_channel_by_id(tv_channel_id)
    if not tv_channel:
        raise HTTPException(status_code=404, detail="TV Channel not found")

    return tv_channel.acestream_channels


@router.post(
    "/{tv_channel_id}/acestreams",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def associate_acestream(
    tv_channel_id: int,
    association: TVChannelAssociationRequest,
    db: Session = Depends(get_db)
):
    """
    Associate an acestream channel with a TV channel.
    """
    acestream_id = association.acestream_channel_id
    service = TVChannelService(db)
    success = service.associate_acestream(
        tv_channel_id=tv_channel_id,
        acestream_id=acestream_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="TV Channel or Acestream channel not found"
        )

    return {"message": "Acestream successfully associated with TV channel"}


@router.delete("/{tv_channel_id}/acestreams/{acestream_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_acestream_association(
    tv_channel_id: int,
    acestream_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove association between an acestream channel and a TV channel.
    """
    service = TVChannelService(db)
    success = service.remove_acestream_association(
        tv_channel_id=tv_channel_id,
        acestream_id=acestream_id
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Association between TV channel and Acestream channel not found"
        )

    # Return empty Response with 204 status code
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/batch-assign",
    status_code=status.HTTP_200_OK,
    response_model=TVChannelBatchAssignResponse,
)
async def batch_assign_acestreams(
    assignment_data: TVChannelBatchAssignRequest,
    db: Session = Depends(get_db)
):
    """
    Batch assign acestream channels to TV channels.

    The request body should be a dictionary where keys are TV channel IDs
    and values are lists of acestream channel IDs.

    Example:
    {
        "1": ["acestream1", "acestream2"],
        "2": ["acestream3"]
    }
    """
    service = TVChannelService(db)
    assignments = [item.model_dump() for item in assignment_data.assignments]
    results = service.batch_associate_acestreams(assignments)
    return results


@router.post("/associate-by-epg", status_code=status.HTTP_200_OK)
async def associate_by_epg(db: Session = Depends(get_db)):
    """
    Associate acestream channels with TV channels based on EPG IDs.

    This endpoint attempts to match acestream channels with TV channels
    using EPG IDs and channel names.
    """
    tv_service = TVChannelService(db)
    ace_service = AcestreamChannelService(db)

    # Get all TV channels with EPG IDs
    tv_channels = tv_service.get_all_tv_channels(skip=0, limit=1000)
    tv_channels_with_epg = [tc for tc in tv_channels if tc.epg_id]

    # Get all acestream channels with tvg_id
    acestream_channels = ace_service.get_all_channels(skip=0, limit=10000)
    acestream_channels_with_tvg = [ac for ac in acestream_channels if getattr(ac, 'tvg_id', None)]

    matched_count = 0
    for tv_channel in tv_channels_with_epg:
        for acestream in acestream_channels_with_tvg:
            if tv_channel.epg_id == acestream.tvg_id:
                success = tv_service.associate_acestream(tv_channel.id, acestream.id)
                if success:
                    matched_count += 1
                    break

    return {
        "message": "EPG association completed",
        "matched_count": matched_count,
        "tv_channels_with_epg": len(tv_channels_with_epg),
        "acestreams_with_tvg": len(acestream_channels_with_tvg)
    }


@router.post(
    "/bulk-update-epg",
    status_code=status.HTTP_200_OK,
    response_model=TVChannelBulkEPGUpdateResponse,
)
async def bulk_update_epg(
    update_data: TVChannelBulkEPGUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update EPG IDs for multiple TV channels.

    This endpoint updates EPG IDs for multiple TV channels in a batch.

    Request format:
    {
        "updates": [
            {"tv_channel_id": 1, "epg_id": "new.epg.id1"},
            {"tv_channel_id": 2, "epg_id": "new.epg.id2"}
        ]
    }
    """
    updates = update_data.updates
    service = TVChannelService(db)

    results = {
        "success_count": 0,
        "failure_count": 0,
        "details": []
    }

    for update in updates:
        tv_channel_id = update.tv_channel_id
        epg_id = update.epg_id

        try:
            # Get the TV channel
            tv_channel = service.get_tv_channel_by_id(tv_channel_id)
            if not tv_channel:
                results["failure_count"] += 1
                results["details"].append({
                    "tv_channel_id": tv_channel_id,
                    "status": "failure",
                    "reason": "TV Channel not found"
                })
                continue

            # Update the EPG ID
            updated_channel = service.update_tv_channel(
                tv_channel_id=tv_channel_id,
                updates={"epg_id": epg_id}
            )

            results["success_count"] += 1
            results["details"].append({
                "tv_channel_id": tv_channel_id,
                "status": "success",
                "old_epg_id": tv_channel.epg_id,
                "new_epg_id": epg_id
            })
        except Exception as e:
            results["failure_count"] += 1
            results["details"].append({
                "tv_channel_id": tv_channel_id,
                "status": "failure",
                "reason": str(e)
            })

    return results
