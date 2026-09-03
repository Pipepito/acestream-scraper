"""VLC/Kodi remote players (spec 6.1). Sync handlers: the drivers block for up to a few seconds."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.models.models import RemotePlayer
from app.repositories.settings_repository import SettingsRepository
from app.schemas.remote_players import (
    RemotePlayerCommandRequest,
    RemotePlayerCreate,
    RemotePlayerPlayRequest,
    RemotePlayerPlayResponse,
    RemotePlayerProbeResponse,
    RemotePlayerResponse,
    RemotePlayerStatusResponse,
    RemotePlayerTestRequest,
    RemotePlayerUpdate,
    ScanDefaultResponse,
    ScanRequest,
    ScanResultResponse,
    TunerAccessResponse,
)
from app.services.public_url_service import resolve_public_base_url
from app.services.remote_players.base import (
    PlayerAuthError,
    PlayerCommandError,
    PlayerUnreachable,
    new_client,
)
from app.services.remote_players.scan import (
    ScanValidationError,
    default_scan_cidr,
    scan_network,
    validate_scan_request,
)
from app.services.remote_players.service import RemotePlayerService
from app.utils.url_guard import BlockedURLError

router = APIRouter(tags=["remote-players"])

_client_factory = new_client  # tests swap in a MockTransport factory

UNREACHABLE_HINT = (
    "Check the address and port, and that the player is running with its web interface enabled."
)


def _service(db: Session = Depends(get_db)) -> RemotePlayerService:
    return RemotePlayerService(db, client_factory=_client_factory)


def _response(player: RemotePlayer) -> RemotePlayerResponse:
    """Never expose the stored password — only whether there is one."""
    return RemotePlayerResponse(
        id=player.id,
        name=player.name,
        kind=player.kind,
        host=player.host,
        port=player.port,
        username=player.username,
        base_url_id=player.base_url_id,
        has_password=bool(player.password),
        created_at=player.created_at,
        updated_at=player.updated_at,
    )


def _player_or_404(service: RemotePlayerService, player_id: int) -> RemotePlayer:
    player = service.repo.get(player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Remote player not found")
    return player


def _validated_host(service: RemotePlayerService, host: str) -> str:
    try:
        return service.validate_host(host)
    except (BlockedURLError, ValueError) as exc:
        raise APIError(
            code="REMOTE_PLAYER_HOST_FORBIDDEN",
            message=str(exc),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            context={"host": host},
        ) from exc


def _translate(exc: Exception) -> APIError:
    """Driver failures as API errors. 401 stays reserved for the API token."""
    if isinstance(exc, PlayerAuthError):
        return APIError(
            code="REMOTE_PLAYER_AUTH",
            message=str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
            context={"kind": exc.kind},
        )
    if isinstance(exc, PlayerUnreachable):
        return APIError(
            code="REMOTE_PLAYER_UNREACHABLE",
            message=str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    if isinstance(exc, PlayerCommandError):
        return APIError(
            code="REMOTE_PLAYER_COMMAND_FAILED",
            message=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    raise exc


@router.get("", response_model=List[RemotePlayerResponse], summary="Saved remote players")
def list_players(service: RemotePlayerService = Depends(_service)):
    return [_response(p) for p in service.repo.get_all()]


@router.post("", response_model=RemotePlayerResponse, status_code=status.HTTP_201_CREATED)
def create_player(payload: RemotePlayerCreate, service: RemotePlayerService = Depends(_service)):
    host = _validated_host(service, payload.host)
    if service.repo.get_by_name(payload.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Remote player '{payload.name}' already exists",
        )
    player = service.repo.create(
        name=payload.name,
        kind=payload.kind,
        host=host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        base_url_id=payload.base_url_id,
    )
    return _response(player)


@router.patch("/{player_id}", response_model=RemotePlayerResponse)
def update_player(
    player_id: int, payload: RemotePlayerUpdate, service: RemotePlayerService = Depends(_service)
):
    player = _player_or_404(service, player_id)
    if payload.name and payload.name != player.name and service.repo.get_by_name(payload.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Remote player '{payload.name}' already exists",
        )
    host = _validated_host(service, payload.host) if payload.host else None
    player = service.repo.update(
        player,
        name=payload.name,
        kind=payload.kind,
        host=host,
        port=payload.port,
        username=payload.username,
        password=payload.password,
        base_url_id=payload.base_url_id,
    )
    if payload.clear_base_url:
        player = service.repo.clear_base_url(player)
    return _response(player)


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_player(player_id: int, service: RemotePlayerService = Depends(_service)):
    service.repo.delete(_player_or_404(service, player_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _probe(
    service: RemotePlayerService,
    kind: str,
    host: str,
    port: int,
    username: Optional[str],
    password: Optional[str],
    stored_id: Optional[int],
) -> RemotePlayerProbeResponse:
    """A probe reports failure in its body — it is the answer the user asked for,
    not an API error."""
    try:
        probe, access = service.probe(kind, host, port, username, password, stored_id=stored_id)
    except PlayerUnreachable as exc:
        return RemotePlayerProbeResponse(
            reachable=False,
            authenticated=False,
            version=None,
            message=str(exc),
            hint=UNREACHABLE_HINT,
            tuner_access=TunerAccessResponse(addresses=[], allowed=True),
        )
    return RemotePlayerProbeResponse(
        reachable=probe.reachable,
        authenticated=probe.authenticated,
        version=probe.version,
        message=probe.message,
        hint=probe.hint,
        tuner_access=TunerAccessResponse(addresses=access.addresses, allowed=access.allowed),
    )


@router.post(
    "/test", response_model=RemotePlayerProbeResponse, summary="Probe a player before saving it"
)
def test_player(payload: RemotePlayerTestRequest, service: RemotePlayerService = Depends(_service)):
    host = _validated_host(service, payload.host)
    return _probe(service, payload.kind, host, payload.port, payload.username, payload.password, payload.id)


@router.post(
    "/{player_id}/test", response_model=RemotePlayerProbeResponse, summary="Probe a saved player"
)
def test_saved_player(player_id: int, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    return _probe(service, player.kind, player.host, player.port, player.username, player.password, None)


@router.get("/{player_id}/status", response_model=RemotePlayerStatusResponse)
def player_status(player_id: int, service: RemotePlayerService = Depends(_service)):
    player = _player_or_404(service, player_id)
    try:
        status_ = service.status(player)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return RemotePlayerStatusResponse(**status_.__dict__)


@router.post(
    "/{player_id}/play",
    response_model=RemotePlayerPlayResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send a channel to the player",
)
def play_on_player(
    player_id: int,
    payload: RemotePlayerPlayRequest,
    request: Request,
    service: RemotePlayerService = Depends(_service),
):
    player = _player_or_404(service, player_id)
    public = resolve_public_base_url(request, SettingsRepository(service.db)).url
    try:
        url = service.play(player, payload.content_id.lower(), public, payload.title or payload.content_id)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return RemotePlayerPlayResponse(url=url)


@router.post("/{player_id}/command", status_code=status.HTTP_204_NO_CONTENT)
def player_command(
    player_id: int, payload: RemotePlayerCommandRequest, service: RemotePlayerService = Depends(_service)
):
    player = _player_or_404(service, player_id)
    try:
        service.command(player, payload.command, payload.value)
    except (PlayerAuthError, PlayerUnreachable, PlayerCommandError) as exc:
        raise _translate(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/scan",
    response_model=ScanResultResponse,
    summary="Find VLC/Kodi web interfaces on a private network",
)
async def scan(payload: ScanRequest):
    try:
        network, ports = validate_scan_request(payload.cidr, payload.ports)
    except ScanValidationError as exc:
        raise APIError(
            code=exc.code, message=str(exc), status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        ) from exc
    outcome = await scan_network(network, ports, timeout_ms=payload.timeout_ms, client_factory=_client_factory)
    return ScanResultResponse(
        hosts=[h.__dict__ for h in outcome.hits], scanned=outcome.scanned, duration_ms=outcome.duration_ms
    )


@router.get("/scan/default", response_model=ScanDefaultResponse, summary="Suggested network to scan")
def scan_default(request: Request):
    cidr = default_scan_cidr(request.client.host if request.client else None)
    hint = (
        "Your network, guessed from your address."
        if cidr
        else "Type your network, for example 192.168.1.0/24 (this server cannot see it from here)."
    )
    return ScanDefaultResponse(cidr=cidr, hint=hint)
