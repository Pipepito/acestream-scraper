"""Public projections deliberately exclude source provenance and integration metadata."""
from datetime import datetime
from pydantic import BaseModel, Field


class WatchChannel(BaseModel):
    id: str
    name: str
    category: str | None = None
    tv_channel_id: int | None = None
    online: bool | None = None


class WatchChannels(BaseModel):
    items: list[WatchChannel]
    total: int


class WatchProgramme(BaseModel):
    id: int
    channel: str
    title: str
    start: datetime
    end: datetime


class WatchEvent(BaseModel):
    id: str
    title: str
    starts_at: str | None = None
    competition: str = ''
    state: str = ''


class WatchRecording(BaseModel):
    id: str
    title: str
    channel: str
    state: str
    files: list[str] = Field(default_factory=list)


class PlaylistLink(BaseModel):
    url: str
    guide_url: str
