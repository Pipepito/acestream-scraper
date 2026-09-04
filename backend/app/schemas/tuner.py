"""DTOs for /api/v1/tuner (spec 7.2)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TunerSettingsResponse(BaseModel):
    friendly_name: str
    tuner_count: int
    max_channels: int
    only_online: bool


class TunerSettingsUpdate(BaseModel):
    friendly_name: Optional[str] = Field(None, max_length=255)
    tuner_count: Optional[int] = Field(None, ge=1, le=16)
    max_channels: Optional[int] = Field(None, ge=1, le=1000)
    only_online: Optional[bool] = None


class TunerRenumbered(BaseModel):
    tv_channel_id: int
    name: str
    requested_number: int
    assigned_number: int


class TunerUrls(BaseModel):
    tuner: str
    lineup: str
    guide: str
    playlist: str
    epg: str
    stream_template: str


class TunerDenial(BaseModel):
    client_ip: str
    peer: str
    path: str
    at: float


class TunerStatusResponse(BaseModel):
    channel_count: int
    renumbered: List[TunerRenumbered]
    overflow: int
    device_id: str
    urls: TunerUrls
    ffmpeg_available: bool
    allowed_networks: List[str]
    client_ip: Optional[str] = None
    peer: Optional[str] = None
    client_allowed: bool
    client_source: Literal["direct", "forwarded", "docker-gateway", "loopback"]
    warnings: List[str]
    recent_denials: List[TunerDenial]
