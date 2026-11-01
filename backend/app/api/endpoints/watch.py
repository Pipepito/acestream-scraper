"""Watch-only APIs never reuse administrative response models."""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.repositories.watch_repository import WatchRepository
from app.schemas.watch import WatchChannels, WatchProgramme, WatchEvent, WatchRecording, PlaylistLink
from app.services.access_service import require_permission, playback_allowed
from app.schemas.recordings import RecordingPlaybackRequest, RecordingPlaybackView
from app.services.recording_service import RecordingService
from app.services import recording_playback

router = APIRouter(tags=['watch'])


def recording_owner(request):
    require_permission(request, 'recordings')
    user = getattr(request.state, 'access_user', None)
    return user['id'] if user else None


def recording_media(view, rid, request):
    if view.media_url:
        view.media_url = request.scope.get('root_path', '').rstrip('/') + f'/api/v1/view/recordings/{rid}/files/{view.file_id}'
    return view


@router.post('/recordings/{rid}/playback-sessions', response_model=RecordingPlaybackView, status_code=201)
def start_recording(rid: str, data: RecordingPlaybackRequest, request: Request, db: Session = Depends(get_db)):
    owner = recording_owner(request)
    return recording_media(recording_playback.create(RecordingService(db), rid, data.file_id, owner=owner), rid, request)


@router.get('/recordings/{rid}/playback-sessions/{sid}', response_model=RecordingPlaybackView)
def recording_status(rid: str, sid: str, request: Request, db: Session = Depends(get_db)):
    owner = recording_owner(request)
    return recording_media(recording_playback.status(RecordingService(db), rid, sid, owner=owner), rid, request)


@router.delete('/recordings/{rid}/playback-sessions/{sid}', status_code=204)
def stop_recording(rid: str, sid: str, request: Request):
    recording_playback.close(rid, sid, owner=recording_owner(request))


@router.post('/playlists', response_model=PlaylistLink)
def playlist_link(request: Request, db: Session = Depends(get_db)):
    import secrets
    from urllib.parse import urlencode
    from fastapi import HTTPException
    from app.repositories.access_repository import AccessRepository
    from app.repositories.settings_repository import SettingsRepository
    from app.services.public_url_service import resolve_public_base_url
    repo = AccessRepository()
    if not playback_allowed(request, repo):
        raise HTTPException(403, 'Playlist access is not enabled for this viewer')
    base = resolve_public_base_url(request, SettingsRepository(db)).url
    user = getattr(request.state, 'access_user', None)
    suffix = ''
    if user:
        try:
            issued = repo.issue_credential(user['id'], 'Shared IPTV playlist', 'playback', secrets.token_urlsafe(32))
        except ValueError as error:
            raise HTTPException(409, str(error)) from None
        suffix = '?' + urlencode({'token': issued['token']})
    return PlaylistLink(url=base + '/api/v1/playlists/m3u' + suffix, guide_url=base + '/api/v1/epg/xml' + suffix)


@router.get('/channels', response_model=WatchChannels)
def channels(request: Request, search: str = Query('', max_length=200), offset: int = Query(0, ge=0, le=100000), db: Session = Depends(get_db)):
    require_permission(request, 'channels')
    return WatchRepository(db).channels(search, offset)


@router.get('/live', response_model=WatchChannels)
def live(request: Request, search: str = Query('', max_length=200), offset: int = Query(0, ge=0, le=100000), db: Session = Depends(get_db)):
    require_permission(request, 'live')
    return WatchRepository(db).channels(search, offset)


@router.get('/guide', response_model=list[WatchProgramme])
def guide(request: Request, offset: int = Query(0, ge=0, le=100000), db: Session = Depends(get_db)):
    require_permission(request, 'guide')
    return WatchRepository(db).guide(offset)


@router.get('/events', response_model=list[WatchEvent])
def events(request: Request, offset: int = Query(0, ge=0, le=100000), db: Session = Depends(get_db)):
    require_permission(request, 'events')
    return WatchRepository(db).events(offset)


@router.get('/recordings', response_model=list[WatchRecording])
def recordings(request: Request, offset: int = Query(0, ge=0, le=100000), db: Session = Depends(get_db)):
    require_permission(request, 'recordings')
    return WatchRepository(db).recordings(offset)


@router.head('/recordings/{rid}/files/{fid}', include_in_schema=False)
@router.get('/recordings/{rid}/files/{fid}')
def recording_file(rid: str, fid: str, request: Request, db: Session = Depends(get_db)):
    require_permission(request, 'recordings')
    from app.services.recording_service import RecordingService
    from app.services.recording_files import file_response
    return file_response(RecordingService(db), rid, fid, request)
