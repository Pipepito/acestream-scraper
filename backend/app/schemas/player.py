"""DTOs for the web player (/api/v1/player)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

PlayerStateValue = Literal["starting", "ready", "error", "stopped"]
PlayerErrorValue = Literal["engine_unavailable", "engine_refused", "engine_stalled", "ffmpeg_missing", "ffmpeg_failed"]


class PlayerSessionCreate(BaseModel):
    content_id: str = Field(..., pattern=r"^[0-9a-fA-F]{40}$", description="AceStream content id (40 hex)")


class PlayerCodecs(BaseModel):
    video: Optional[str] = None
    audio: Optional[str] = None


class PlayerStats(BaseModel):
    status: str
    peers: int
    speed_down: int
    speed_up: int


class PlayerSessionStatus(BaseModel):
    id: str
    content_id: str
    state: PlayerStateValue
    error: Optional[PlayerErrorValue] = None
    error_message: str = ""
    codecs: PlayerCodecs
    stats: Optional[PlayerStats] = None
    viewers: int
    playlist_url: str
    hls_ready: bool


class PlayerSessionListResponse(BaseModel):
    sessions: List[PlayerSessionStatus]


class PlayerCapabilities(BaseModel):
    ffmpeg_available: bool
    ffmpeg_path: Optional[str] = None
    max_sessions: int
    hls_dir: str


class ActiveStream(BaseModel):
    """One thing the server is streaming right now.

    ``browser`` is an ffmpeg/HLS player session; ``relay`` is a raw MPEG-TS
    relay of ``/tuner/stream/<id>.ts`` — what a media server's tuner and a
    remote player on the server-relay link format pull.
    """

    kind: Literal["browser", "relay"]
    id: str
    content_id: str
    #: Name of the acestream channel, when one with this id is known here.
    channel_name: Optional[str] = None
    state: Literal["starting", "ready", "error", "stopped", "streaming"]
    viewers: int = 1
    #: Engine peers, when the session has read stats (browser sessions only).
    peers: Optional[int] = None
    #: Who is pulling the relay, e.g. "tuner:192.168.1.5" (relays only).
    client_label: Optional[str] = None
    started_at: Optional[datetime] = None


class ActiveStreamListResponse(BaseModel):
    streams: List[ActiveStream]
