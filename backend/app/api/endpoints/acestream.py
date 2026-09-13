from fastapi import APIRouter, Depends
from app.services.acestream_status_service import AcestreamStatusService
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from sqlalchemy.orm import Session
from app.config.database import get_db
from app.repositories.settings_repository import SettingsRepository

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
def get_acestream_status(db: Session = Depends(get_db)):
    service = AcestreamStatusService(engine_url=SettingsRepository(db).get_setting("ace_engine_url") or "")
    status = service.check_status()
    return status
