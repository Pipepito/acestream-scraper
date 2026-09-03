"""DTOs for the web player (/api/v1/player)."""
from __future__ import annotations

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
