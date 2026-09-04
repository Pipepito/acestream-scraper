"""Jellyfin/Plex media servers (spec 7.3). Sync handlers: the clients block for
up to a few seconds and every handler touches the database."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.models.models import MediaServer
from app.repositories.settings_repository import SettingsRepository
from app.schemas.media_servers import (
    MediaServerCreate,
    MediaServerProbeResponse,
    MediaServerRefreshResponse,
    MediaServerResponse,
    MediaServerStatusResponse,
    MediaServerTestRequest,
    MediaServerUpdate,
)
from app.services.media_servers.base import (
    MediaServerAuthError,
    MediaServerError,
    MediaServerUnreachable,
    new_client,
)
from app.services.media_servers.service import MediaServerService
from app.services.public_url_service import resolve_public_base_url
from app.services.remote_players.service import RemotePlayerService
from app.utils.url_guard import BlockedURLError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["media-servers"])

_client_factory = new_client  # tests swap in a MockTransport factory

CLIENT_ERRORS = (MediaServerAuthError, MediaServerUnreachable, MediaServerError)


def _service(db: Session = Depends(get_db)) -> MediaServerService:
    return MediaServerService(db, client_factory=_client_factory)


def _connected(server: MediaServer) -> bool:
    """Plex is connected once we know its DVR; Jellyfin once both ids are ours."""
    if server.kind == "plex":
        return bool(server.dvr_key)
    return bool(server.tuner_host_id and server.listing_provider_id)


def _response(server: MediaServer) -> MediaServerResponse:
    """Never expose the stored API key/token — only whether there is one."""
    return MediaServerResponse(
        id=server.id,
        kind=server.kind,
        name=server.name,
        base_url=server.base_url,
        tuner_mode=server.tuner_mode,
        enabled=server.enabled,
        auto_refresh=server.auto_refresh,
        has_api_key=bool(server.api_key),
        connected=_connected(server),
        tuner_host_id=server.tuner_host_id,
        listing_provider_id=server.listing_provider_id,
        dvr_key=server.dvr_key,
        last_sync_at=server.last_sync_at,
        last_sync_status=server.last_sync_status,
        last_error=server.last_error,
        server_version=server.server_version,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


def _server_or_404(service: MediaServerService, server_id: int) -> MediaServer:
    server = service.repo.get(server_id)
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media server not found")
    return server


def _validated_base_url(service: MediaServerService, base_url: str) -> str:
    try:
        return service.validate_base_url(base_url)
    except (BlockedURLError, ValueError) as exc:
        raise APIError(
            code="MEDIA_SERVER_URL_FORBIDDEN",
            message=str(exc),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            context={"base_url": base_url},
        ) from exc


def _ensure_unique_name(service: MediaServerService, name: Optional[str], current: Optional[MediaServer] = None) -> None:
    if not name or (current is not None and name == current.name):
        return
    if service.repo.get_by_name(name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Media server '{name}' already exists",
        )


def _translate(exc: Exception) -> APIError:
    """Client failures as API errors. 401 stays reserved for the API token."""
    if isinstance(exc, MediaServerAuthError):
        return APIError(
            code="MEDIA_SERVER_AUTH",
            message=str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    if isinstance(exc, MediaServerUnreachable):
        return APIError(
            code="MEDIA_SERVER_UNREACHABLE",
            message=str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
    if isinstance(exc, MediaServerError):
        return APIError(
            code="MEDIA_SERVER_ERROR",
            message=str(exc),
            status_code=status.HTTP_502_BAD_GATEWAY,
            context={"status": exc.status_code},
        )
    raise exc


@router.get("", response_model=List[MediaServerResponse], summary="Saved media servers")
def list_media_servers(service: MediaServerService = Depends(_service)):
    return [_response(server) for server in service.repo.get_all()]


@router.post("", response_model=MediaServerResponse, status_code=status.HTTP_201_CREATED)
def create_media_server(payload: MediaServerCreate, service: MediaServerService = Depends(_service)):
    base_url = _validated_base_url(service, payload.base_url)
    _ensure_unique_name(service, payload.name)
    server = service.repo.create(
        kind=payload.kind,
        name=payload.name,
        base_url=base_url,
        api_key=payload.api_key or None,
        tuner_mode=payload.tuner_mode,
        enabled=payload.enabled,
        auto_refresh=payload.auto_refresh,
    )
    return _response(server)


@router.patch("/{server_id}", response_model=MediaServerResponse)
def update_media_server(
    server_id: int, payload: MediaServerUpdate, service: MediaServerService = Depends(_service)
):
    server = _server_or_404(service, server_id)
    _ensure_unique_name(service, payload.name, server)
    if payload.base_url is not None:
        server.base_url = _validated_base_url(service, payload.base_url)
    if payload.name is not None:
        server.name = payload.name
    if payload.tuner_mode is not None:
        server.tuner_mode = payload.tuner_mode
    if payload.enabled is not None:
        server.enabled = payload.enabled
    if payload.auto_refresh is not None:
        server.auto_refresh = payload.auto_refresh
    if "api_key" in payload.model_fields_set:
        # Omitted keeps the stored secret; an empty string (or null) clears it.
        server.api_key = payload.api_key or None
    return _response(service.repo.save(server))


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_media_server(server_id: int, service: MediaServerService = Depends(_service)):
    server = _server_or_404(service, server_id)
    if server.kind == "jellyfin" and _connected(server):
        # Leaving a tuner and a listings provider behind would make Jellyfin
        # keep fetching a lineup nobody serves any more. Best effort: an
        # unreachable server must not block the delete the user asked for.
        try:
            service.disconnect(server)
        except CLIENT_ERRORS as exc:
            logger.warning("Could not unregister %s from Jellyfin before deleting it: %s", server.name, exc)
    service.repo.delete(server)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _probe(
    service: MediaServerService,
    kind: str,
    base_url: str,
    api_key: Optional[str],
    stored_id: Optional[int],
) -> MediaServerProbeResponse:
    try:
        probe = service.test(kind, base_url, api_key, stored_id=stored_id)
    except CLIENT_ERRORS as exc:
        raise _translate(exc) from exc
    # Same warning the remote players give: can this host reach our tuner URLs?
    access = RemotePlayerService(service.db).tuner_access(urlsplit(base_url).hostname or "")
    return MediaServerProbeResponse(**probe, tuner_access={"addresses": access.addresses, "allowed": access.allowed})


@router.post(
    "/test", response_model=MediaServerProbeResponse, summary="Probe a media server before saving it"
)
def test_media_server(payload: MediaServerTestRequest, service: MediaServerService = Depends(_service)):
    base_url = _validated_base_url(service, payload.base_url)
    return _probe(service, payload.kind, base_url, payload.api_key, payload.id)


@router.post(
    "/{server_id}/test", response_model=MediaServerProbeResponse, summary="Probe a saved media server"
)
def test_saved_media_server(server_id: int, service: MediaServerService = Depends(_service)):
    server = _server_or_404(service, server_id)
    return _probe(service, server.kind, server.base_url, server.api_key, None)


@router.post("/{server_id}/connect", response_model=MediaServerResponse, summary="Register the tuner and guide")
def connect_media_server(
    server_id: int, request: Request, service: MediaServerService = Depends(_service)
):
    server = _server_or_404(service, server_id)
    public = resolve_public_base_url(request, SettingsRepository(service.db)).url
    try:
        server = service.connect(server, public)
    except CLIENT_ERRORS as exc:
        raise _translate(exc) from exc
    return _response(server)


@router.post("/{server_id}/refresh", response_model=MediaServerRefreshResponse, summary="Refresh the guide now")
def refresh_media_server(server_id: int, service: MediaServerService = Depends(_service)):
    """Bypasses the sync job's debounce — the user asked for it explicitly."""
    server = _server_or_404(service, server_id)
    try:
        result = service.refresh(server)
    except CLIENT_ERRORS as exc:
        server.last_sync_status = "error"
        server.last_error = str(exc)
        service.repo.save(server)
        raise _translate(exc) from exc
    server.last_sync_status = result.status
    server.last_error = result.message if result.status == "error" else None
    if result.status == "ok":
        server.last_sync_at = datetime.now(timezone.utc)
    service.repo.save(server)
    return MediaServerRefreshResponse(
        status=result.status, message=result.message, last_sync_at=server.last_sync_at
    )


@router.post("/{server_id}/disconnect", response_model=MediaServerResponse, summary="Unregister the tuner and guide")
def disconnect_media_server(server_id: int, service: MediaServerService = Depends(_service)):
    server = _server_or_404(service, server_id)
    if not _connected(server):
        raise APIError(
            code="MEDIA_SERVER_NOT_CONNECTED",
            message=f"'{server.name}' is not connected",
            status_code=status.HTTP_409_CONFLICT,
        )
    try:
        server = service.disconnect(server)
    except CLIENT_ERRORS as exc:
        raise _translate(exc) from exc
    return _response(server)


@router.get("/{server_id}/status", response_model=MediaServerStatusResponse)
def media_server_status(server_id: int, service: MediaServerService = Depends(_service)):
    server = _server_or_404(service, server_id)
    return MediaServerStatusResponse(**service.status(server))
