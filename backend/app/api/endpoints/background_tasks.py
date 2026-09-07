from fastapi import APIRouter
from app.models.background_task_status import BackgroundTaskStatus
import logging

from app.api.error_handlers import APIError
from app.services.background_task_status_service import BackgroundTaskStatusService

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
