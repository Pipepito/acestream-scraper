from fastapi import APIRouter, Depends
from app.services.acestream_status_service import AcestreamStatusService
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(tags=["acestream"])

class AcestreamStatusResponse(BaseModel):
    enabled: bool
    is_internal: bool
    engine_url: str
    available: bool
    message: str
    version: str | None = None
    platform: str | None = None
    playlist_loaded: bool | None = None
    connected: bool | None = None

@router.get("/status", response_model=AcestreamStatusResponse, summary="Get Acestream Engine status")
def get_acestream_status():
    service = AcestreamStatusService()
    status = service.check_status()
    return status
