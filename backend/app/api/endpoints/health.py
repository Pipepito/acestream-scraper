from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool

from app.api.dependencies import get_config_service, get_stats_service
from app.services.config_service import ConfigService
from app.services.stats_service import StatsService
from app.schemas.config import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def check_health(config_service: ConfigService = Depends(get_config_service)):
    """Check the overall system health"""
    # The engine probe is a blocking HTTP call (up to 1 s); keep it off the
    # event loop so a slow engine does not stall every other request.
    health = await run_in_threadpool(config_service.check_system_health)
    return health

@router.get("/stats")
async def get_stats(stats_service: StatsService = Depends(get_stats_service)):
    """Get system statistics"""
    return stats_service.get_health_stats()
