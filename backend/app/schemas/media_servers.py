"""DTOs for /api/v1/media-servers (spec 7.3)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

MediaServerKind = Literal["jellyfin", "plex"]
TunerMode = Literal["hdhomerun", "m3u"]
SyncStatus = Literal["ok", "error", "never", "manual"]


class MediaServerCreate(BaseModel):
    kind: MediaServerKind
    name: str = Field(..., min_length=1, max_length=255)
    base_url: str = Field(..., min_length=1, max_length=1024)
    api_key: Optional[str] = Field(None, description="Jellyfin API key or Plex owner token")
    tuner_mode: TunerMode = "hdhomerun"
    enabled: bool = True
    auto_refresh: bool = True


class MediaServerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_url: Optional[str] = Field(None, min_length=1, max_length=1024)
    api_key: Optional[str] = Field(None, description="omit = keep, empty = clear")
    tuner_mode: Optional[TunerMode] = None
    enabled: Optional[bool] = None
    auto_refresh: Optional[bool] = None


class MediaServerResponse(BaseModel):
    id: int
    kind: MediaServerKind
    name: str
    base_url: str
    tuner_mode: TunerMode
    enabled: bool
    auto_refresh: bool
    has_api_key: bool
    connected: bool
    tuner_host_id: Optional[str] = None
    listing_provider_id: Optional[str] = None
    dvr_key: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    last_sync_status: SyncStatus
    last_error: Optional[str] = None
    server_version: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MediaServerTestRequest(BaseModel):
    kind: MediaServerKind
    base_url: str
    api_key: Optional[str] = None
    id: Optional[int] = None


class MediaServerProbeResponse(BaseModel):
    reachable: bool
    authenticated: bool
    version: Optional[str] = None
    message: str
    tuner_access: Dict[str, Any]


class MediaServerRefreshResponse(BaseModel):
    status: Literal["ok", "error", "manual"]
    message: Optional[str] = None
    last_sync_at: Optional[datetime] = None


class MediaServerStatusResponse(BaseModel):
    connected: bool
    channel_count: Optional[int] = None
    refresh_state: Optional[str] = None
    last_result: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    paste: Dict[str, str] = Field(default_factory=dict)
    error: Optional[str] = None
