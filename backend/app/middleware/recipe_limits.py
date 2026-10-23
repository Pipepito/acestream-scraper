"""Admit and bound preview uploads before Starlette buffers or parses JSON."""
import asyncio
import threading
import tempfile
from fastapi import HTTPException, Request
from starlette.responses import JSONResponse
from app.api.auth import require_api_token

# JSON escaping can double normal source text; allow envelope/rules overhead.
MAX_PREVIEW_BODY_BYTES = 64 * 1024 * 1024 + 128 * 1024
_PREVIEWS = threading.BoundedSemaphore(2)


class RecipeRequestLimits:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        path = scope.get('path', '').rstrip('/')
        event_write = (path == '/api/v1/events' or path.startswith('/api/v1/events/')) and scope.get('method') in ('POST', 'PATCH')
        catalogue_preview = path == '/api/v1/catalogues/preview'
        event_write = event_write or (path.startswith('/api/v1/catalogues/') and path.endswith('/events/preview') and scope.get('method') == 'POST')
        if scope['type'] != 'http' or (path != '/api/v1/scrapers/recipes/preview' and not event_write and not catalogue_preview):
            await self.app(scope, receive, send)
            return
        body_limit = (2 * 1024 * 1024 if event_write else
                      8 * 1024 * 1024 + 4096 if catalogue_preview else MAX_PREVIEW_BODY_BYTES)
        async def error(status, message, headers=None):
            await JSONResponse({'detail': message}, status_code=status, headers=headers)(scope, receive, send)
        try:
            await require_api_token(Request(scope))
        except HTTPException as exc:
            await error(exc.status_code, exc.detail, exc.headers)
            return
        if not _PREVIEWS.acquire(blocking=False):
            await error(503, 'Two preview requests are already running; try again shortly')
            return
        try:
            headers = dict(scope.get('headers', []))
            encoding = headers.get(b'content-encoding', b'identity').lower()
            if encoding != b'identity':
                await error(415, 'Send an uncompressed JSON preview request')
                return
            length = headers.get(b'content-length')
            if length is not None:
                try:
                    size = int(length)
                except ValueError:
                    await error(400, 'Invalid Content-Length')
                    return
                if size < 0 or size > body_limit:
                    await error(413, 'Preview request is too large; reduce JSON escaping or use a smaller sample')
                    return
            total = 0
            deadline = asyncio.get_running_loop().time() + 30
            # Spill large uploads to a private temporary file, then replay to FastAPI.
            # Admission and length checks finish before JSON parsing begins.
            with tempfile.SpooledTemporaryFile(max_size=1024 * 1024) as body:
                while True:
                    try:
                        message = await asyncio.wait_for(receive(), timeout=max(0, deadline - asyncio.get_running_loop().time()))
                    except asyncio.TimeoutError:
                        await error(408, 'Preview upload timed out')
                        return
                    if message['type'] == 'http.disconnect':
                        return
                    chunk = message.get('body', b'')
                    total += len(chunk)
                    if total > body_limit:
                        await error(413, 'Preview request is too large; reduce JSON escaping or use a smaller sample')
                        return
                    await asyncio.to_thread(body.write, chunk)
                    if not message.get('more_body', False):
                        break
                message = chunk = None
                await asyncio.to_thread(body.seek, 0)
                replayed = 0
                delivered = False
                async def replay():
                    nonlocal replayed, delivered
                    if delivered:
                        return await receive()
                    chunk = await asyncio.to_thread(body.read, 65536)
                    replayed += len(chunk)
                    delivered = replayed >= total
                    return {'type': 'http.request', 'body': chunk, 'more_body': replayed < total}
                await self.app(scope, replay, send)
        finally:
            _PREVIEWS.release()
