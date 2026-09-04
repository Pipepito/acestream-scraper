"""Web player sessions (spec 5.1). Session create runs its blocking work in
the threadpool; HLS file handlers are async and touch no DB."""
from __future__ import annotations

import re
import stat as stat_module
from datetime import datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.error_handlers import APIError
from app.config.database import get_db
from app.repositories.channel_repository import ChannelRepository
from app.schemas.player import (
    ActiveStream,
    ActiveStreamListResponse,
    PlayerCapabilities,
    PlayerCodecs,
    PlayerSessionCreate,
    PlayerSessionListResponse,
    PlayerSessionStatus,
    PlayerStats,
)
from app.services.player_service import PlayerLimitReached, PlayerSession, player_service
from app.services.stream_relay import relay_registry

router = APIRouter(tags=["player"])
_SEGMENT = re.compile(r"^seg\d{5}\.ts$")


def _status(session: PlayerSession) -> PlayerSessionStatus:
    stats = session.stats
    return PlayerSessionStatus(
        id=session.id,
        content_id=session.content_id,
        state=session.state,
        error=session.error,
        error_message=session.error_message,
        codecs=PlayerCodecs(**session.codecs),
        stats=PlayerStats(
            status=stats.status, peers=stats.peers, speed_down=stats.speed_down, speed_up=stats.speed_up
        ) if stats else None,
        viewers=session.viewers,
        playlist_url=f"/api/v1/player/sessions/{session.id}/index.m3u8",
        hls_ready=player_service.hls_ready(session),
    )


def _session_or_404(session_id: str) -> PlayerSession:
    session = player_service.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player session not found")
    return session


@router.get(
    "/capabilities",
    response_model=PlayerCapabilities,
    summary="Whether the server can prepare streams for browsers",
)
async def capabilities() -> PlayerCapabilities:
    return PlayerCapabilities(**player_service.capabilities())


@router.get("/sessions", response_model=PlayerSessionListResponse, summary="Active player sessions")
async def list_sessions() -> PlayerSessionListResponse:
    return PlayerSessionListResponse(sessions=[_status(s) for s in player_service.list_sessions()])


@router.get(
    "/streams",
    response_model=ActiveStreamListResponse,
    summary="Everything the server is streaming right now",
)
def active_streams(db: Session = Depends(get_db)) -> ActiveStreamListResponse:
    """Browser sessions and raw relays in one list, named where we know the name.

    Declared ``def``, not ``async def``: it reads the database, so FastAPI runs
    it in the threadpool instead of blocking the event loop that is feeding the
    relays this very endpoint reports.
    """
    sessions = player_service.list_sessions()
    relays = relay_registry.active()
    names = ChannelRepository(db).names_by_id(
        [session.content_id for session in sessions] + [relay.content_id for relay in relays]
    )
    streams = [
        ActiveStream(
            kind="browser",
            id=session.id,
            content_id=session.content_id,
            channel_name=names.get(session.content_id.lower()),
            state=session.state,
            viewers=session.viewers,
            peers=session.stats.peers if session.stats else None,
        )
        for session in sessions
    ]
    streams += [
        ActiveStream(
            kind="relay",
            id=relay.id,
            content_id=relay.content_id,
            channel_name=names.get(relay.content_id.lower()),
            state="streaming",
            viewers=1,
            client_label=relay.client_label,
            started_at=datetime.fromtimestamp(relay.started_at, tz=timezone.utc),
        )
        for relay in relays
    ]
    return ActiveStreamListResponse(streams=streams)


@router.post("/sessions", response_model=PlayerSessionStatus, summary="Start (or join) playback of a channel")
async def create_session(payload: PlayerSessionCreate) -> PlayerSessionStatus:
    try:
        session = await player_service.open_session(payload.content_id.lower())
    except PlayerLimitReached as exc:
        raise APIError(
            code="PLAYER_LIMIT_REACHED",
            message="Too many channels are playing at once",
            status_code=status.HTTP_409_CONFLICT,
            context={"limit": exc.limit, "active": exc.active},
        ) from exc
    return _status(session)


@router.get("/sessions/{session_id}", response_model=PlayerSessionStatus, summary="Session status (heartbeat)")
async def get_session(session_id: str) -> PlayerSessionStatus:
    session = _session_or_404(session_id)
    player_service.touch(session_id)
    return _status(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Leave a session")
async def leave_session(session_id: str) -> Response:
    player_service.leave(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions/{session_id}/index.m3u8", summary="HLS playlist", response_class=Response)
async def playlist(session_id: str, request: Request) -> Response:
    session = _session_or_404(session_id)
    player_service.touch(session_id)
    path = player_service.playlist_path(session)
    try:
        # Read instead of exists()+read: ffmpeg swaps the playlist in with
        # os.replace, and a teardown can remove the directory in between.
        text = path.read_text()
    except OSError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Playlist not ready") from None
    # Native (Safari/iOS) players cannot send headers and drop the playlist's
    # query when resolving relative segment URIs: carry ?token= onto each one.
    token = request.query_params.get("token")
    if token:
        suffix = "?" + urlencode({"token": token})
        text = "\n".join(line + suffix if line and not line.startswith("#") else line for line in text.splitlines()) + "\n"
    return Response(content=text, media_type="application/vnd.apple.mpegurl", headers={"Cache-Control": "no-store"})


@router.get("/sessions/{session_id}/{segment}", summary="HLS segment", response_class=FileResponse)
async def segment(session_id: str, segment: str) -> FileResponse:
    session = _session_or_404(session_id)
    if not _SEGMENT.match(segment):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown segment")
    player_service.touch(session_id)
    path = session.dir / segment
    try:
        # Stat once and hand the result to FileResponse. Segment deletion is
        # routine here (ffmpeg's delete_segments, teardown's rmtree); without
        # stat_result Starlette re-stats at send time and raises RuntimeError,
        # which would surface as a 500 instead of this 404.
        file_stat = path.stat()
    except OSError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not ready") from None
    if not stat_module.S_ISREG(file_stat.st_mode):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not ready")
    return FileResponse(
        path, media_type="video/mp2t", headers={"Cache-Control": "no-store"}, stat_result=file_stat
    )
