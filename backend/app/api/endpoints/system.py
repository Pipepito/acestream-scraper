"""Sidecar service status and restart (/api/v1/system)."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response
from app.services.diagnostics_service import build_bundle, DiagnosticsBusy
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository
from app.schemas.system import (
    PublicUrlResponse,
    ServiceRestartResponse,
    ServicesStatusResponse,
    ServiceStatus,
)
from app.services.public_url_service import resolve_public_base_url
from app.services.system_services_service import (
    ServiceNotFoundError,
    ServiceNotManagedError,
    SystemServicesService,
)

router = APIRouter(tags=["system"])


@router.get('/diagnostics', response_class=Response,
            responses={200: {'content': {'application/zip': {'schema': {'type': 'string', 'format': 'binary'}}}}},
            summary='Download recent runtime diagnostics')
def download_diagnostics() -> Response:
    try:
        bundle = build_bundle()
    except DiagnosticsBusy:
        raise HTTPException(503, 'Diagnostics are being collected. Try again shortly.', headers={'Retry-After': '2'})
    return Response(bundle, media_type='application/zip', headers={
        'Content-Disposition': 'attachment; filename="acestream-diagnostics.zip"',
        'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
    })


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


def _control_engine(action: str, db: Session, name: str = "acestream") -> dict[str, object]:
    try:
        return _service(db).control_engine(action, name)
    except ServiceNotManagedError as exc:
        raise APIError(code="SERVICE_NOT_MANAGED", message=str(exc),
                       status_code=status.HTTP_409_CONFLICT,
                       context={"service": name}) from exc


@router.post("/services/acestream/start", response_model=ServiceRestartResponse,
             status_code=status.HTTP_202_ACCEPTED, summary="Start the supervised AceStream engine")
def start_engine(db: Session = Depends(get_db)) -> dict[str, object]:
    return _control_engine("start", db)


@router.post("/services/acestream/stop", response_model=ServiceRestartResponse,
             status_code=status.HTTP_202_ACCEPTED, summary="Stop AceStream until Start or container restart")
def stop_engine(db: Session = Depends(get_db)) -> dict[str, object]:
    return _control_engine("stop", db)


@router.post("/services/acestream-check/start", response_model=ServiceRestartResponse,
             status_code=status.HTTP_202_ACCEPTED, summary="Start the supervised checking engine")
def start_check_engine(db: Session = Depends(get_db)) -> dict[str, object]:
    return _control_engine("start", db, "acestream-check")


@router.post("/services/acestream-check/stop", response_model=ServiceRestartResponse,
             status_code=status.HTTP_202_ACCEPTED, summary="Stop channel checks until Start or container restart")
def stop_check_engine(db: Session = Depends(get_db)) -> dict[str, object]:
    return _control_engine("stop", db, "acestream-check")


@router.get("/public-url", response_model=PublicUrlResponse, summary="Origin external clients must use")
def get_public_url(request: Request, db: Session = Depends(get_db)):
    """Sync on purpose: it reads the settings table."""
    resolved = resolve_public_base_url(request, SettingsRepository(db))
    return PublicUrlResponse(url=resolved.url, source=resolved.source, warnings=resolved.warnings)
