from fastapi import APIRouter, HTTPException, Depends
from app.models.background_task_status import BackgroundTaskStatus
import logging

from app.api.error_handlers import APIError
from app.services.background_task_status_service import BackgroundTaskStatusService

from app.services.task_service import task_service
from app.schemas.channel_status import ChannelStatusJobRunResponse

from sqlalchemy.orm import Session
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.services.check_engine_config_service import CheckEngineConfigService

router = APIRouter()
logger = logging.getLogger(__name__)

status_service = BackgroundTaskStatusService()

@router.get("/background-tasks/status", response_model=list[BackgroundTaskStatus], tags=["background-tasks"])
def get_background_tasks_status():
    try:
        return [task.model_dump() for task in status_service.get_all_statuses()]
    except Exception as exc:
        logger.error("Failed to fetch background task status: %s", exc)
        raise APIError(
            code="BACKGROUND_TASK_STATUS_FAILED",
            message="Unable to fetch background task status",
            status_code=500,
            context={"error": str(exc)},
        ) from exc


@router.post("/background-tasks/channel_status/run", response_model=ChannelStatusJobRunResponse, tags=["background-tasks"])
def run_channel_status_job(db: Session = Depends(get_db)):
    if not CheckEngineConfigService(SettingsRepository(db)).effective_url():
        return ChannelStatusJobRunResponse(status="disabled", message="No engine configured. Add a playback or checking engine in Settings to enable stream checks.")
    outcome = task_service.run_task_now("channel_status")
    if outcome == "unavailable":
        raise HTTPException(status_code=503, detail="The stream status job is unavailable. Check the scheduler in Overview.")
    message = (
        "The stream status job is already running or waiting. Follow its progress in Overview."
        if outcome == "already_running" else
        "Stream status job queued for all active streams. Follow its progress in Overview."
    )
    return ChannelStatusJobRunResponse(status=outcome, message=message)
