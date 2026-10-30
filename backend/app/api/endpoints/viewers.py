"""Viewer capabilities are separate from administrative player session IDs."""
import re
from urllib.parse import urlencode
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.concurrency import run_in_threadpool
from app.schemas.player import PlayerSessionCreate, PlayerSessionStatus
from app.services.access_service import require_permission
from app.services.viewer_service import viewer_service
from app.api.endpoints.player import _status, segment as player_segment

router = APIRouter(tags=['viewers'])
_RESOURCE = re.compile(r'^(?:index|video|subtitles)\.m3u8$|^(?:seg\d{5}\.ts|index\d+\.vtt)$')
MEDIA_HEADERS = {'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
                 'Access-Control-Allow-Headers': 'Range', 'Access-Control-Expose-Headers': 'Content-Length, Content-Range',
                 'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer'}


class ViewerStatus(PlayerSessionStatus):
    control_token: str | None = None


def status_for(lease, media_token=None, control=None, root_path=''):
    session = viewer_service.player.get(lease.session_id)
    if not session:
        raise HTTPException(410, 'Playback ended')
    data = _status(session).model_dump()
    data['error_message'] = 'Playback could not continue. Retry or choose another channel.' if session.error else ''
    data.update(id=lease.id, viewers=1, stats=None, control_token=control,
                playlist_url=f'{root_path}/api/v1/viewers/{lease.id}/media/index.m3u8' + (f'?cap={media_token}' if media_token else ''))
    return ViewerStatus(**data)


@router.post('', response_model=ViewerStatus)
async def create(payload: PlayerSessionCreate, request: Request):
    require_permission(request, 'live')
    # Viewer playback only accepts imported streams, never arbitrary upstreams.
    from app.services.watch_service import imported_stream
    if not await run_in_threadpool(imported_stream, payload.content_id):
        raise HTTPException(404, 'Channel is not available')
    lease, control, media = await viewer_service.create(payload, getattr(request.state, 'access_user', None))
    return status_for(lease, media, control, request.scope.get('root_path', '').rstrip('/'))


@router.get('/{viewer_id}', response_model=ViewerStatus)
async def status(viewer_id: str, request: Request):
    lease = await viewer_service.authorize(viewer_id, request.headers.get('x-viewer-token', ''))
    return status_for(lease)


@router.delete('/{viewer_id}', status_code=204)
async def release(viewer_id: str, request: Request):
    await viewer_service.authorize(viewer_id, request.headers.get('x-viewer-token', ''))
    viewer_service.release(viewer_id)
    return Response(status_code=204)


@router.options('/{viewer_id}/media/{resource}', include_in_schema=False)
async def options(viewer_id: str, resource: str):
    return Response(status_code=204, headers=MEDIA_HEADERS)


@router.head('/{viewer_id}/media/{resource}', include_in_schema=False)
@router.get('/{viewer_id}/media/{resource}')
async def media(viewer_id: str, resource: str, request: Request):
    if not _RESOURCE.fullmatch(resource):
        raise HTTPException(404, 'Unknown media resource')
    token = request.query_params.get('cap', '')
    lease = await viewer_service.authorize(viewer_id, token, media=True)
    session = viewer_service.player.get(lease.session_id)
    if resource.endswith('.m3u8'):
        suffix = '?' + urlencode({'cap': token})
        if resource == 'index.m3u8' and session.subtitle_index is not None:
            text = ('#EXTM3U\n#EXT-X-VERSION:3\n'
                    '#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="Selected subtitles",DEFAULT=YES,AUTOSELECT=YES,'
                    f'URI="subtitles.m3u8{suffix}"\n#EXT-X-STREAM-INF:BANDWIDTH=10000000,SUBTITLES="subs"\nvideo.m3u8{suffix}\n')
        else:
            path = session.dir / ('index_vtt.m3u8' if resource == 'subtitles.m3u8' else 'index.m3u8')
            try:
                text = await run_in_threadpool(path.read_text)
            except OSError:
                raise HTTPException(404, 'Playlist not ready') from None
            text = '\n'.join(line + suffix if line and not line.startswith('#') else line for line in text.splitlines()) + '\n'
        return Response(text, media_type='application/vnd.apple.mpegurl', headers=MEDIA_HEADERS)
    response = await player_segment(lease.session_id, resource)
    response.headers.update(MEDIA_HEADERS)
    return response
