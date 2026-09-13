from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.stats_service import StatsService
from app.schemas.stats_schemas import StatsResponse, TVChannelStatsResponse

router = APIRouter(tags=["stats"])

@router.get("/", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.get_stats()

@router.get("/tv-channels/", response_model=TVChannelStatsResponse)
def get_tv_channel_stats(db: Session = Depends(get_db)):
    service = StatsService(db)
    return service.get_tv_channel_stats()
