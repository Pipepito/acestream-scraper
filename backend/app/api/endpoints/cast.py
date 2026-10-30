from fastapi import APIRouter, Request, HTTPException, Response
from app.schemas.cast import CastDevice, CastCapabilities, CastStart, CastStatus, CastCommand
from app.api.endpoints.viewers import ViewerStatus, status_for
from app.services.access_service import require_permission, require_server_cast
from app.services.cast_service import cast_service

router = APIRouter(tags=['cast'])


@router.get('/capabilities', response_model=CastCapabilities)
def capabilities(request: Request):
    allowed, message = True, ''
    try:
        require_server_cast(request)
    except HTTPException as error:
        allowed, message = False, error.detail
    policy = request.state.access_policy
    return CastCapabilities(server_devices=allowed, compatibility_conversion=policy.compatibility_conversion,
        media_url_configured=bool(policy.cast_media_url), message=message)


@router.get('/devices', response_model=list[CastDevice])
async def devices(request: Request):
    require_server_cast(request)
    return await cast_service.devices()


@router.get('/sessions', response_model=list[CastStatus])
def sessions(request: Request):
    require_server_cast(request)
    user = request.state.access_user
    return [cast_service.status(c) for c in cast_service.active.values() if user['administrator'] or c.owner_id == user['id']]


@router.post('/sessions', response_model=CastStatus)
async def start(payload: CastStart, request: Request):
    require_server_cast(request)
    require_permission(request, 'live')
    if not payload.device_id:
        raise HTTPException(422, 'Select a TV')
    try:
        return await cast_service.start(payload, request.state.access_user, request.state.access_policy)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, 'Could not start playback on the TV. Check receiver connectivity and stream compatibility.') from None


@router.post('/browser', response_model=ViewerStatus)
async def browser(payload: CastStart, request: Request):
    require_permission(request, 'cast')
    require_permission(request, 'live')
    lease, control, media = await cast_service.prepare(payload, getattr(request.state, 'access_user', None), request.state.access_policy, 'cast')
    return status_for(lease, media, control, request.scope.get('root_path', '').rstrip('/'))


@router.post('/sessions/{cast_id}/commands', status_code=204)
async def command(cast_id: str, payload: CastCommand, request: Request):
    require_server_cast(request)
    try:
        await cast_service.command(cast_id, payload, request.state.access_user)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, 'The TV did not accept the command') from None
    return Response(status_code=204)
