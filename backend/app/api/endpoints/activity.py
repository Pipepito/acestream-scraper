from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ...services.activity_log_service import ActivityLogService
from app.config.database import get_db
from typing import Optional

router = APIRouter()  # Removed prefix here

@router.get("/recent")
def get_recent_activity(
    days: int = Query(7, ge=0, le=30, description="Number of days to look back"),
    type: Optional[str] = Query(None, description="Filter by activity type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db)
):
    service = ActivityLogService(db)
    try:
        result = service.get_recent_activity(days=days, type=type, page=page, page_size=page_size)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/channels/{channel_id}/activity_log")
def get_channel_activity_log(
    channel_id: str,
    days: int = Query(7, ge=0, le=30, description="Number of days to look back"),
    type: Optional[str] = Query(None, description="Filter by activity type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db)
):
    service = ActivityLogService(db)
    try:
        result = service.get_recent_activity(days=days, type=type, channel_id=channel_id, page=page, page_size=page_size)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
