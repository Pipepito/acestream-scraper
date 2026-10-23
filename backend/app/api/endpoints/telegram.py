"""Strictly protected, thin Telegram control plane."""
import asyncio
from contextlib import asynccontextmanager
import ipaddress
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from app.api.auth import require_api_token
from app.config.settings import get_settings
from app.repositories import telegram_repository as repo
from app.schemas.telegram import (TelegramLogin, TelegramCode, TelegramPassword,
    TelegramStatus, TelegramSource, TelegramSourceCreate, TelegramSourceConfig,
    TelegramPreviewRequest, TelegramPreview, TelegramPeer, TelegramResolve)
from app.schemas.extraction import ExtractionRecipe
from app.services.telegram.manager import manager, threaded
from app.services.telegram.extraction import PAIR_RECIPE
from app.services.telegram.errors import TelegramActionError


async def require_telegram_admin(request: Request) -> None:
    await require_api_token(request)
    expected = get_settings().TELEGRAM_ADMIN_TOKEN.get_secret_value()
    if len(expected) < 32:
        raise HTTPException(503, 'Telegram is disabled. Configure a Telegram admin token of at least 32 characters and a separate encryption key.')
    supplied = request.headers.get('X-Telegram-Admin', '')
    if not secrets.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(403, 'Enter the Telegram admin token configured on this server.')
    peer = request.scope.get('state', {}).get('peer', request.scope.get('client', ('', 0)))[0]
    try:
        local = ipaddress.ip_address(peer).is_loopback
    except ValueError:
        local = False
    local = local and request.url.hostname in ('localhost', '127.0.0.1', '::1')
    if request.url.scheme != 'https' and not local:
        raise HTTPException(403, 'Use HTTPS or a localhost connection for Telegram administration.')
    origin = request.headers.get('origin')
    if (origin and origin != f'{request.url.scheme}://{request.url.netloc}') or request.headers.get('sec-fetch-site') == 'cross-site':
        raise HTTPException(403, 'Open Telegram settings from this application origin.')


class PrivateRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()
        async def guarded(request: Request):
            await require_telegram_admin(request)
            # Authenticate before buffering/parsing credentials and bound input.
            body = bytearray()
            try:
                async with asyncio.timeout(10):
                    async for chunk in request.stream():
                        body.extend(chunk)
                        if len(body) > 128 * 1024:
                            raise HTTPException(413, 'Telegram request is too large')
                request._body = bytes(body)
                response = await handler(request)
                response.headers['Cache-Control'] = 'no-store'
                return response
            except RequestValidationError:
                # FastAPI's default detail includes the submitted secret input.
                raise HTTPException(422, 'Invalid Telegram input. Check the fields and limits.') from None
            except TimeoutError:
                raise HTTPException(408, 'Telegram request timed out; retry shortly.') from None
        return guarded


router = APIRouter(route_class=PrivateRoute)


@asynccontextmanager
async def operation(ignore_flood=False):
    try:
        await asyncio.wait_for(manager.lock.acquire(), 2)
    except TimeoutError:
        raise HTTPException(409, 'Telegram is processing a batch. Try again shortly.') from None
    try:
        if manager.retry_at and not ignore_flood:
            from datetime import datetime, timezone
            if manager.retry_at > datetime.now(timezone.utc):
                raise HTTPException(429, 'Telegram rate limit. Wait until the displayed retry time.')
        async with asyncio.timeout(60):
            yield
    except HTTPException:
        raise
    except TelegramActionError as exc:
        raise HTTPException(400, str(exc)) from None
    except ValueError:
        # Application ValueErrors are user-facing, upstream failures are not.
        # Avoid reflecting arbitrary library messages or submitted secrets.
        raise HTTPException(400, 'Telegram action could not complete. Check connection, chat access and source settings.') from None
    except Exception as exc:
        manager.failure(exc)
        raise HTTPException(400, manager.message) from None
    finally:
        manager.lock.release()


@router.get('/status', response_model=TelegramStatus)
async def status():
    return manager.status()


@router.post('/login', response_model=TelegramStatus)
async def login(data: TelegramLogin):
    async with operation():
        await manager.login(data)
    return manager.status()


@router.post('/code', response_model=TelegramStatus)
async def code(data: TelegramCode):
    async with operation():
        await manager.authorize(data.code.get_secret_value())
    return manager.status()


@router.post('/password', response_model=TelegramStatus)
async def password(data: TelegramPassword):
    async with operation():
        await manager.authorize(data.password.get_secret_value(), password=True)
    return manager.status()


@router.post('/disconnect', response_model=TelegramStatus)
async def disconnect():
    async with operation(ignore_flood=True):
        await manager.disconnect()
    return manager.status()


@router.post('/reconnect', response_model=TelegramStatus)
async def reconnect():
    async with operation():
        await manager.resume()
    manager.wake.set()
    return manager.status()


@router.delete('/account', response_model=TelegramStatus)
async def logout():
    async with operation():
        await manager.logout()
    return manager.status()


@router.get('/chats', response_model=list[TelegramPeer])
async def chats():
    async with operation():
        manager.require_connected()
        return await manager.client.chats()


@router.get('/chats/{chat_id}/topics', response_model=list[TelegramPeer])
async def topics(chat_id: str):
    async with operation():
        manager.require_connected()
        entity, _ = await manager.client.member(chat_id)
        return await manager.client.topics(entity)


@router.post('/resolve', response_model=TelegramPeer)
async def resolve(data: TelegramResolve):
    async with operation():
        manager.require_connected()
        return await manager.client.resolve(data.username)


@router.get('/preset', response_model=ExtractionRecipe)
async def preset():
    return PAIR_RECIPE


@router.get('/sources', response_model=list[TelegramSource])
async def sources():
    return await manager.sources()


@router.post('/sources', response_model=TelegramSource)
async def create_source(data: TelegramSourceCreate):
    async with operation():
        return await manager.save_source(data)


@router.put('/sources/{source_id}', response_model=TelegramSource)
async def update_source(source_id: int, data: TelegramSourceConfig):
    async with operation():
        return await manager.save_source(data, source_id)


@router.delete('/sources/{source_id}')
async def delete_source(source_id: int) -> dict[str, bool]:
    async with operation():
        manager.require_connected()
        await threaded(repo.remove, manager.account['id'], source_id)
    return {'removed': True}


@router.post('/sources/{source_id}/scan')
async def scan(source_id: int) -> dict[str, bool]:
    async with operation():
        manager.require_connected()
        found = await threaded(repo.snapshot, source_id, manager.account['id'])
        if found is None or not found[0].enabled:
            raise HTTPException(400, 'Enable an existing source before scanning')
        manager.reconcile.add(source_id)
        manager.wake.set()
    return {'queued': True}


@router.post('/preview', response_model=TelegramPreview)
async def preview(data: TelegramPreviewRequest):
    async with operation():
        return await manager.preview(data)
