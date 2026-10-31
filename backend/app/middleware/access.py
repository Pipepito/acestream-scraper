"""Default-deny management policy, including routes outside the versioned router."""
import re
from fastapi import HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from app.repositories.access_repository import AccessRepository
from app.services.access_service import request_user, require_csrf, playback_allowed, same_origin
from app.utils.request_path import route_path

# Complete playback exceptions; an unlisted route or method remains management.
PLAYBACK_PATHS = {
    '/playlist.m3u', '/playlists/m3u', '/api/playlists/m3u', '/api/playlists/tv-channels/m3u',
    '/api/playlists/all-streams/m3u', '/api/playlists/epg.xml',
    '/api/v1/playlists/m3u', '/api/v1/playlists/playlists/m3u',
    '/api/v1/playlists/tv-channels/m3u', '/api/v1/playlists/all-streams/m3u',
    '/api/v1/epg/xml',
    '/tuner/discover.json', '/tuner/lineup.json', '/tuner/lineup_status.json',
    '/tuner/device.xml', '/tuner/guide.xml', '/tuner/playlist.m3u', '/tuner/epg.xml',
}
MEDIA_PATH = re.compile(r'^/(?:tuner/(?:stream/[0-9a-fA-F]{40}|source/url:[0-9a-f]{40}|channel/\d+)\.ts|live/[a-zA-Z0-9:_-]+(?:\.[a-z0-9]+)?)$')
PUBLIC_PATHS = {'GET': {'/api/v1/health', '/api/v1/auth/status'},
                'POST': {'/api/v1/auth/login', '/api/v1/auth/bootstrap'}}
DELEGATED = {
    'GET': [r'/api/v1/auth/(?:users|policy|sessions|credentials)', r'/api/v1/view/(?:channels|live|guide|events|recordings)',
            r'/api/v1/view/recordings/[0-9a-f]{32}/files/[0-9a-f]{32}', r'/api/v1/viewers/[0-9a-f]{32}(?:/media/[^/]+)?',
            r'/api/v1/view/recordings/[0-9a-f]{32}/playback-sessions/[0-9a-f]{32}', r'/api/v1/cast/(?:capabilities|devices|sessions)'],
    'POST': [r'/api/v1/auth/(?:logout|disable|users|credentials)', r'/api/v1/view/playlists', r'/api/v1/viewers', r'/api/v1/cast/(?:sessions|browser)',
             r'/api/v1/view/recordings/[0-9a-f]{32}/playback-sessions', r'/api/v1/cast/sessions/[0-9a-f]{32}/commands'],
    'PUT': [r'/api/v1/auth/(?:password|policy)', r'/api/v1/auth/users/[0-9a-f]{32}'],
    'DELETE': [r'/api/v1/auth/(?:sessions|credentials)/[0-9a-f]{32,64}', r'/api/v1/viewers/[0-9a-f]{32}',
               r'/api/v1/view/recordings/[0-9a-f]{32}/playback-sessions/[0-9a-f]{32}'],
    'OPTIONS': [r'/api/v1/viewers/[0-9a-f]{32}/media/[^/]+'],
}


def playback_path(path, method):
    return (path == '/tuner/lineup.post' and method in ('GET', 'POST')) or (method in ('GET', 'HEAD') and (path in PLAYBACK_PATHS or bool(MEDIA_PATH.fullmatch(path))))


def authorize(request):
    repo = AccessRepository()
    mode, policy = repo.state()
    request.state.access_mode = mode
    request.state.access_policy = policy
    if mode == 'open':
        return
    request.state.access_checked = True
    request.state.access_user = request_user(request, repo) if mode == 'accounts' else None
    path, method = route_path(request.scope), request.method
    media_read = method in ('GET', 'HEAD', 'OPTIONS') and re.fullmatch(r'/api/v1/viewers/[0-9a-f]{32}/media/[^/]+', path)
    if request.state.access_user and not getattr(request.state, 'header_authenticated', False) and not same_origin(request) and not media_read:
        raise HTTPException(403, 'Open account resources from the application itself')
    if path in PUBLIC_PATHS.get('GET' if method == 'HEAD' else method, set()):
        return
    if path == '/api/v1/startup' and method in ('GET', 'HEAD'):
        return  # The endpoint returns a minimal projection for anonymous callers.
    if any(re.fullmatch(pattern, path) for pattern in DELEGATED.get('GET' if method == 'HEAD' else method, [])):
        # These routers enforce their finer capabilities after identity is established.
        if method not in ('GET', 'HEAD', 'OPTIONS') and request.state.access_user and not getattr(request.state, 'header_authenticated', False):
            require_csrf(request)
        return
    if playback_path(path, method) and mode == 'accounts' and playback_allowed(request, repo):
        request.state.playback_authorized = True
        return
    user = request.state.access_user
    if not user or not user['administrator']:
        raise HTTPException(401 if not user else 403, 'Sign in as an administrator to access this resource')
    if method not in ('GET', 'HEAD', 'OPTIONS') and not getattr(request.state, 'header_authenticated', False):
        require_csrf(request)


class AccessMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = route_path(scope)
        protected_surface = path.startswith(('/api/', '/tuner/', '/live/', '/playlists/', '/docs/', '/redoc/')) or path in ('/playlist.m3u', '/docs', '/redoc', '/openapi.json')
        if scope['type'] != 'http' or not protected_surface:
            await self.app(scope, receive, send)
            return
        request = Request(scope, receive)
        if path == '/api/v1/health':
            await self.app(scope, receive, send)
            return
        try:
            await run_in_threadpool(authorize, request)
        except HTTPException as error:
            await JSONResponse({'detail': error.detail}, status_code=error.status_code, headers={'Cache-Control': 'no-store', **(error.headers or {})})(scope, receive, send)
            return
        except Exception:
            await JSONResponse({'detail': 'Access storage is unavailable. Use local account recovery or restore its backup.'}, status_code=503, headers={'Cache-Control': 'no-store'})(scope, receive, send)
            return

        if getattr(request.state, 'access_mode', 'open') == 'accounts' and path in PLAYBACK_PATHS and (path.endswith('/m3u') or path == '/playlist.m3u') and scope['method'] in ('GET', 'HEAD'):
            from app.services.watch_service import safe_playlist
            from starlette.responses import PlainTextResponse
            try:
                text = await run_in_threadpool(safe_playlist, request)
            except HTTPException as error:
                await JSONResponse({'detail': error.detail}, status_code=error.status_code)(scope, receive, send)
                return
            await PlainTextResponse(text, media_type='application/x-mpegurl', headers={'Cache-Control': 'no-store'})(scope, receive, send)
            return

        async def private_send(message):
            if message['type'] == 'http.response.start' and not playback_path(path, scope['method']):
                message['headers'] = [(k, v) for k, v in message['headers'] if k.lower() != b'cache-control'] + [(b'cache-control', b'no-store')]
            await send(message)
        await self.app(scope, receive, private_send)
