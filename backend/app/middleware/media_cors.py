"""Keep receiver media CORS independent from credentialed application CORS."""
import re
from starlette.middleware.cors import CORSMiddleware
from app.utils.request_path import route_path

_VIEWER_MEDIA = re.compile(r'/api/v1/viewers/[0-9a-f]{32}/media/[^/]+')


class ApplicationCORSMiddleware(CORSMiddleware):
    async def __call__(self, scope, receive, send):
        if (scope['type'] == 'http' and scope['method'] in ('GET', 'HEAD', 'OPTIONS')
                and _VIEWER_MEDIA.fullmatch(route_path(scope))):
            # Media handlers own a read-only wildcard policy without cookies.
            # The application policy must not intercept receiver preflights or
            # add Access-Control-Allow-Credentials to media responses.
            await self.app(scope, receive, send)
            return
        await super().__call__(scope, receive, send)
