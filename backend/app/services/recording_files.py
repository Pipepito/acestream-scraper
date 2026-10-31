"""Authenticated descriptor-backed single-range responses, including disconnect cleanup."""
import asyncio
import os
import re
import time
from starlette.responses import StreamingResponse
from app.api.error_handlers import APIError
from app.services.recording_storage import RecordingStorage, reader
from app.services.recording_service import check


class RecordingFileResponse(StreamingResponse):
    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.release()


def file_response(service, rid, fid, request, download=False):
    recording = check(service.repo.get(rid))
    artifact = check(service.repo.file(rid, fid))
    if recording.state in ('deleting', 'deleted') or artifact.state != 'ready':
        raise APIError('RECORDING_FILE_NOT_READY', 'Recording file is not available.', 409)
    storage = RecordingStorage(artifact.root_id)
    lease = reader(storage, artifact.filename)
    try:
        fd = lease.__enter__()
    except APIError:
        storage.close()
        raise
    except OSError:
        storage.close()
        raise APIError('RECORDING_FILE_MISSING', 'Recording file is missing or unavailable.', 404) from None
    released = False

    def release():
        nonlocal released
        if not released:
            released = True
            lease.__exit__(None, None, None)
            storage.close()

    size = os.fstat(fd).st_size
    start, end, status = 0, size-1, 200
    headers = {'Accept-Ranges': 'bytes', 'Cache-Control': 'private, no-store',
               'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer'}
    value = request.headers.get('range')
    if value:
        match = re.fullmatch(r'bytes=(\d*)-(\d*)', value) if len(value) <= 200 else None
        if not match or not any(match.groups()):
            release()
            raise APIError('RECORDING_RANGE_INVALID', 'Only one byte range is supported.', 416)
        a, b = match.groups()
        if a:
            start, end = int(a), min(size-1, int(b)) if b else size-1
        else:
            start = max(0, size-int(b))
        if start > end or start >= size or (not a and int(b) == 0):
            release()
            from starlette.responses import Response
            return Response(status_code=416, headers={**headers, 'Content-Range': f'bytes */{size}'})
        status = 206
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
    headers['Content-Length'] = str(max(0, end-start+1))
    extension = 'mp4' if artifact.kind == 'derivative' else 'ts'
    headers['Content-Disposition'] = f'{"attachment" if download else "inline"}; filename="recording-{rid}-{fid}.{extension}"'

    async def chunks():
        offset = start
        deadline = time.monotonic()+3600
        if request.method == 'HEAD':
            return
        while offset <= end and time.monotonic() < deadline:
            chunk = await asyncio.to_thread(os.pread, fd, min(64*1024, end-offset+1), offset)
            if not chunk:
                break
            offset += len(chunk)
            yield chunk
    response = RecordingFileResponse(chunks(), status_code=status, headers=headers,
        media_type='video/mp4' if extension == 'mp4' else 'video/mp2t')
    response.release = release
    return response
