"""Sidecar service status and restart (/api/v1/system)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.schemas.system import ServiceRestartResponse, ServicesStatusResponse, ServiceStatus
from app.services.system_services_service import (
    ServiceNotFoundError,
    ServiceNotManagedError,
    SystemServicesService,
)

router = APIRouter(tags=["system"])


def _service(db: Session) -> SystemServicesService:
    # The external engine the app really talks to is the DB setting, not the env default.
    engine_url = SettingsRepository(db).get_setting("ace_engine_url") or None
    return SystemServicesService(external_engine_url=engine_url)


@router.get("/services", response_model=ServicesStatusResponse, summary="Status of the sidecar services")
def list_services(db: Session = Depends(get_db)):
    """Sync endpoint on purpose: the probes block for up to a couple of seconds each."""
    return _service(db).list_services()


@router.get("/services/{name}", response_model=ServiceStatus, summary="Status of one sidecar service")
def get_service(name: str, db: Session = Depends(get_db)):
    try:
        return _service(db).get_service(name)
    except ServiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown service: {name}")


@router.post(
    "/services/{name}/restart",
    response_model=ServiceRestartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Restart a service supervised by this container",
)
def restart_service(name: str, db: Session = Depends(get_db)):
    try:
        return _service(db).restart(name)
    except ServiceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown service: {name}")
    except ServiceNotManagedError as exc:
        raise APIError(
            code="SERVICE_NOT_MANAGED",
            message=str(exc),
            status_code=status.HTTP_409_CONFLICT,
            context={"service": name},
        ) from exc
