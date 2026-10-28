"""Bounded VOD subscriptions over low-priority local MP4 preparation.

No engine sessions, source requests or recording lifetime heartbeats. Closing
one subscriber never cancels preparation used by another subscriber.
"""
import threading
import time
from uuid import uuid4
from app.api.error_handlers import APIError
from app.schemas.recordings import RecordingConversion, RecordingPlaybackView
from app.services.recording_service import check

_lock = threading.Lock()
_sessions = {}
TTL = 60


def create(service, rid, fid):
    recording = check(service.repo.get(rid))
    file = check(service.repo.file(rid, fid))
    if recording.state not in ('completed', 'partial') or file.state != 'ready':
        raise APIError('RECORDING_FILE_NOT_READY', 'Playback is available after recording finishes.', 409)
    if file.kind == 'original':
        file = service.convert(rid, RecordingConversion(file_id=fid, profile='aac'))
    with _lock:
        now = time.monotonic()
        for key, session in list(_sessions.items()):
            if session['expires'] < now:
                del _sessions[key]
        if len(_sessions) >= 16:
            raise APIError('RECORDING_PLAYBACK_LIMIT', 'Too many recording playback sessions.', 409)
        sid = uuid4().hex
        _sessions[sid] = dict(recording=rid, file=file.id, expires=now+TTL)
    return status(service, rid, sid)


def status(service, rid, sid):
    with _lock:
        session = _sessions.get(sid)
        if session is None or session['recording'] != rid or session['expires'] < time.monotonic():
            _sessions.pop(sid, None)
            raise APIError('RECORDING_PLAYBACK_EXPIRED', 'Playback session expired. Open the recording again.', 404)
        session['expires'] = time.monotonic()+TTL
        fid = session['file']
    recording = check(service.repo.get(rid))
    artifact = check(service.repo.file(rid, fid))
    state = 'ready' if artifact.state == 'ready' else 'preparing' if artifact.state in ('queued','converting') else 'failed'
    if recording.state in ('deleted','deleting'):
        state = 'failed'
    return RecordingPlaybackView(id=sid, state=state, file_id=fid,
        media_url=f'/api/v1/recordings/{rid}/files/{fid}' if state == 'ready' else None,
        message='Ready' if state == 'ready' else 'Preparing browser playback; capture takes priority.' if state == 'preparing'
        else 'This recording cannot be prepared for this browser. Download the original.')


def close(rid, sid):
    with _lock:
        if _sessions.get(sid, {}).get('recording') == rid:
            del _sessions[sid]
