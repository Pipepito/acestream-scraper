"""DTOs for /api/v1/remote-players (spec 6.1)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PlayerKind = Literal["vlc", "kodi"]
PlayerCommand = Literal["pause", "resume", "stop", "volume"]


class RemotePlayerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    kind: PlayerKind
    host: str = Field(..., min_length=1, max_length=255, description="Hostname or IP, no scheme")
    port: int = Field(8080, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255, description="Kodi only; default kodi")
    base_url_id: Optional[int] = Field(None, description="Stream link format; null = server relay URL")


class RemotePlayerCreate(RemotePlayerBase):
    password: Optional[str] = Field(None, max_length=1024)


class RemotePlayerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    kind: Optional[PlayerKind] = None
    host: Optional[str] = Field(None, min_length=1, max_length=255)
    port: Optional[int] = Field(None, ge=1, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, max_length=1024, description="omit = keep, empty string = clear")
    base_url_id: Optional[int] = None
    clear_base_url: bool = False


class RemotePlayerResponse(RemotePlayerBase):
    id: int
    has_password: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RemotePlayerTestRequest(BaseModel):
    kind: PlayerKind
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(8080, ge=1, le=65535)
    username: Optional[str] = None
    password: Optional[str] = None
    id: Optional[int] = Field(None, description="Use this saved player's password when none is given")


class TunerAccessResponse(BaseModel):
    addresses: List[str]
    allowed: bool


class RemotePlayerProbeResponse(BaseModel):
    reachable: bool
    authenticated: bool
    version: Optional[str] = None
    message: str
    hint: Optional[str] = None
    tuner_access: TunerAccessResponse


class RemotePlayerStatusResponse(BaseModel):
    state: Literal["playing", "paused", "stopped"]
    title: Optional[str] = None
    position_s: Optional[int] = None
    length_s: Optional[int] = None
    volume_pct: Optional[int] = None
    message: Optional[str] = None


class RemotePlayerPlayRequest(BaseModel):
    content_id: str = Field(..., pattern=r"^[0-9a-fA-F]{40}$")
    title: Optional[str] = None


class RemotePlayerPlayResponse(BaseModel):
    url: str


class RemotePlayerCommandRequest(BaseModel):
    command: PlayerCommand
    value: Optional[int] = Field(None, ge=0, le=200, description="Percent, volume only")

    @model_validator(mode="after")
    def _volume_needs_a_value(self) -> "RemotePlayerCommandRequest":
        """Without this the driver call raises and the caller sees a 500."""
        if self.command == "volume" and self.value is None:
            raise ValueError("volume needs a value between 0 and 200")
        return self


class ScanRequest(BaseModel):
    cidr: str
    ports: List[int] = Field(default_factory=lambda: [8080])
    timeout_ms: int = Field(400, ge=50, le=5000)


class ScanHitResponse(BaseModel):
    host: str
    port: int
    kind: Literal["vlc", "kodi", "unknown"]
    hint: str


class ScanResultResponse(BaseModel):
    hosts: List[ScanHitResponse]
    scanned: int
    duration_ms: int


class ScanDefaultResponse(BaseModel):
    cidr: Optional[str] = None
    hint: str
