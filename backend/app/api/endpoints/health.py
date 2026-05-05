from fastapi import APIRouter, Depends

from app.api.dependencies import get_config_service, get_stats_service
from app.services.config_service import ConfigService
from app.services.stats_service import StatsService
from app.schemas.config import HealthResponse

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def check_health(config_service: ConfigService = Depends(get_config_service)):
    """Check the overall system health"""
    health = config_service.check_system_health()
    return health

@router.get("/stats")
async def get_stats(stats_service: StatsService = Depends(get_stats_service)):
    """Get system statistics"""
    return stats_service.get_health_stats()
