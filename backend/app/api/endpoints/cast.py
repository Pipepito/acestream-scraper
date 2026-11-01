from fastapi import APIRouter, Request, HTTPException, Response
from app.schemas.cast import CastDevice, CastCapabilities, CastStart, CastStatus, CastCommand
from app.api.endpoints.viewers import ViewerStatus, status_for
from app.services.access_service import require_permission, require_server_cast
from app.services.cast_service import cast_service
from app.schemas.access import CastSettings
from app.repositories.access_repository import AccessRepository
from app.services.access_service import home_client
from app.services.cast_settings import require_cast_settings, cast_settings, controller, media_base, trust_home_connection
from app.services.cast_scan import cast_scanner

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
        media_url_configured=bool(media_base(request)), message=message,
        home_connection=home_client(request), media_url=media_base(request) if allowed else '')


@router.get('/settings', response_model=CastSettings)
def settings(request: Request):
    require_cast_settings(request)
    return cast_settings(request.state.access_policy)


@router.put('/settings', response_model=CastSettings)
def save_settings(payload: CastSettings, request: Request):
    require_cast_settings(request)
    return cast_settings(AccessRepository().update_policy(payload.model_dump()))


@router.post('/home-connection', response_model=CastSettings)
def home_connection(request: Request):
    return trust_home_connection(request)


@router.get('/devices', response_model=list[CastDevice])
async def devices(request: Request):
    require_server_cast(request)
    await cast_scanner.refresh_known(cast_service.discovery)
    found = await cast_service.devices()
    # The private application URL supplies the LAN when Docker hides multicast
    # and the source address. Keep scans bounded and only scan an empty list.
    from app.services.access_service import private_lan_address
    if not found and private_lan_address(request) is not None:
        try:
            return await cast_scanner.discover(request, cast_service.discovery)
        except TimeoutError:
            return cast_service.discovery.list()
    return found


@router.post('/discover', response_model=list[CastDevice])
async def discover(request: Request):
    require_server_cast(request)
    try:
        return await cast_scanner.discover(request, cast_service.discovery)
    except TimeoutError:
        return cast_service.discovery.list()


@router.get('/sessions', response_model=list[CastStatus])
def sessions(request: Request):
    require_server_cast(request)
    user = controller(request)
    return [cast_service.status(c) for c in cast_service.active.values() if user['administrator'] or c.owner_id == user['id']]


@router.post('/sessions', response_model=CastStatus)
async def start(payload: CastStart, request: Request):
    require_server_cast(request)
    require_permission(request, 'live')
    if not payload.device_id:
        raise HTTPException(422, 'Select a TV')
    await cast_scanner.refresh_known(cast_service.discovery)
    try:
        policy = request.state.access_policy.model_copy(update={'cast_media_url': media_base(request)})
        return await cast_service.start(payload, getattr(request.state, 'access_user', None), policy, controller=controller(request))
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
        await cast_service.command(cast_id, payload, controller(request))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(502, 'The TV did not accept the command') from None
    return Response(status_code=204)
