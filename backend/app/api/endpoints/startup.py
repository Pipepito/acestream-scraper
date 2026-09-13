"""Startup endpoints deliberately have no database dependencies."""
import secrets
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.schemas.startup import StartupStatus, StartupRecoveryRequest
from app.services.startup_service import startup_service

router = APIRouter(tags=['startup'])


@router.get('', response_model=StartupStatus)
def status():
    return startup_service.snapshot()


@router.get('/diagnostics', response_class=PlainTextResponse)
def diagnostics():
    return PlainTextResponse(startup_service.diagnostics(), headers={
        'Content-Disposition': 'attachment; filename="startup-diagnostics.json"',
        'Cache-Control': 'no-store',
    })


@router.post('/recover', response_model=StartupStatus, status_code=202)
async def recover(payload: StartupRecoveryRequest, request: Request):
    # A per-boot nonce plus JSON POST prevents cross-origin form resets on
    # installations using the historical token-free trusted-network mode.
    with startup_service.lock:
        if not secrets.compare_digest(payload.recovery_token.encode(), startup_service.recovery_token.encode()):
            raise HTTPException(409, 'Startup changed. Refresh before trying again.')
        if startup_service.status != 'failed' or not hasattr(request.app.state, 'retry_startup'):
            raise HTTPException(409, 'Recovery is only available after startup stops.')
        if payload.action != 'retry' and (not payload.confirm or not startup_service.recovery_available):
            raise HTTPException(409, 'Database recovery must be available and confirmed.')
        startup_service.status = 'starting'
        startup_service.recovery_token = secrets.token_urlsafe(32)
        startup_service.guidance = None
        startup_service.record('Retrying startup' if payload.action == 'retry' else 'Preparing database recovery')
        request.app.state.retry_startup(payload.action)
    return startup_service.snapshot()
