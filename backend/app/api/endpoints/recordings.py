"""Thin DVR API. All endpoints inherit the application's optional API token."""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.schemas.recordings import (RecordingCreate, RecordingEdit, RecordingView, RecordingList,
    RecordingSettings, RecordingCapabilities, RecordingConversion, RecordingFile, RecordingState)
from app.services.recording_service import RecordingService
from app.services.recording_files import file_response

router = APIRouter()
config_router = APIRouter()


def service(db: Session = Depends(get_db)):
    return RecordingService(db)


@router.get('/capabilities', response_model=RecordingCapabilities)
def capabilities(svc: RecordingService = Depends(service)):
    return svc.capabilities()


@config_router.get('/recordings', response_model=RecordingSettings)
def settings(svc: RecordingService = Depends(service)):
    return svc.settings()


@config_router.put('/recordings', response_model=RecordingSettings)
def configure(data: RecordingSettings, svc: RecordingService = Depends(service)):
    return svc.configure(data)


@router.post('', response_model=RecordingView, status_code=201)
def create(data: RecordingCreate, svc: RecordingService = Depends(service)):
    return svc.create(data)


@router.get('', response_model=RecordingList)
def listing(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
            state: RecordingState | None = None, search: str | None = Query(None, max_length=200),
            tv_channel_id: int | None = None, svc: RecordingService = Depends(service)):
    return svc.list(offset, limit, state=state, search=search, tv_channel_id=tv_channel_id)


from app.schemas.recordings import ProgrammeSelection
from app.models.models import _utcnow


@router.get('/current-programme', response_model=ProgrammeSelection | None)
def current_programme(tv_channel_id: int, svc: RecordingService = Depends(service)):
    return svc.repo.current_programme(tv_channel_id, _utcnow())


@router.get('/upcoming', response_model=RecordingList)
def upcoming(svc: RecordingService = Depends(service)):
    rows = svc.repo.pending()
    return RecordingList(items=[svc.get(row.id) for row in rows[:20]], total=len(rows))


@router.get('/{rid}', response_model=RecordingView)
def detail(rid: str, svc: RecordingService = Depends(service)):
    return svc.get(rid)


@router.patch('/{rid}', response_model=RecordingView)
def edit(rid: str, data: RecordingEdit, svc: RecordingService = Depends(service)):
    return svc.edit(rid, data)


@router.post('/{rid}/stop', response_model=RecordingView, status_code=202)
def stop(rid: str, svc: RecordingService = Depends(service)):
    return svc.stop(rid)


@router.post('/{rid}/cancel', response_model=RecordingView, status_code=202)
def cancel(rid: str, svc: RecordingService = Depends(service)):
    return svc.stop(rid, cancel=True)


@router.delete('/{rid}', response_model=RecordingView, status_code=202)
def delete(rid: str, svc: RecordingService = Depends(service)):
    return svc.delete(rid)


@router.post('/{rid}/conversions', response_model=RecordingFile, status_code=202)
def convert(rid: str, data: RecordingConversion, svc: RecordingService = Depends(service)):
    return svc.convert(rid, data)


@router.get('/{rid}/files/{fid}')
@router.head('/{rid}/files/{fid}')
def file(rid: str, fid: str, request: Request, download: bool = False, svc: RecordingService = Depends(service)):
    return file_response(svc, rid, fid, request, download)


from app.schemas.recordings import RecordingPlaybackRequest, RecordingPlaybackView
from app.services import recording_playback
from app.api.auth import authenticated_player_url


def playback_url(view, request):
    if view.media_url:
        view.media_url = authenticated_player_url(request, request.scope.get('root_path', '').rstrip('/') + view.media_url)
    return view


@router.post('/{rid}/playback-sessions', response_model=RecordingPlaybackView, status_code=201)
def open_playback(rid: str, data: RecordingPlaybackRequest, request: Request, svc: RecordingService = Depends(service)):
    return playback_url(recording_playback.create(svc, rid, data.file_id), request)


@router.get('/{rid}/playback-sessions/{sid}', response_model=RecordingPlaybackView)
def playback_status(rid: str, sid: str, request: Request, svc: RecordingService = Depends(service)):
    return playback_url(recording_playback.status(svc, rid, sid), request)


@router.delete('/{rid}/playback-sessions/{sid}', status_code=204)
def close_playback(rid: str, sid: str):
    recording_playback.close(rid, sid)
