"""Public W3U contracts deliberately exclude source URLs and header values."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class CataloguePreviewRequest(BaseModel):
    url: str | None = Field(default=None, max_length=2048)
    sample: str | None = Field(default=None, max_length=4 * 1024 * 1024)
    catalogue_id: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def one_input(self):
        if sum(value is not None for value in (self.url, self.sample, self.catalogue_id)) != 1:
            raise ValueError('Choose a URL, a local W3U file, or a saved catalogue')
        return self


class CatalogueEntry(BaseModel):
    id: str
    parent_id: str | None = None
    name: str
    kind: Literal['folder', 'acestream', 'hls', 'mpegts', 'resolver', 'vod', 'unsupported', 'invalid']
    content_type: Literal['live', 'event', 'vod', 'unknown'] = 'unknown'
    reason: str = ''
    description: str = ''
    image: str | None = None
    guide_id: str | None = None
    number: int | None = None
    origin: str = ''
    header_names: list[str] = Field(default_factory=list)
    channel_id: str | None = None
    duplicate: bool = False
    retained: bool = False
    imported: bool = False


class CatalogueCounts(BaseModel):
    accepted: int = 0
    duplicates: int = 0
    invalid: int = 0
    unsupported: int = 0
    failed_fetches: int = 0
    requests: int = 0
    bytes_read: int = Field(default=0, description='Traversal byte budget used, including cached input and failed-read reservations')
    cached_documents: int = 0


class CatalogueView(BaseModel):
    id: int | None = None
    revision: int = 0
    name: str
    origin: str
    entries: list[CatalogueEntry]
    counts: CatalogueCounts
    partial: bool = False
    warnings: list[str] = Field(default_factory=list)
    selected_branches: list[str] = Field(default_factory=lambda: ['root'])
    mode: Literal['compatible', 'acestream'] = 'compatible'
    refresh_enabled: bool = False
    can_refresh: bool = False
    updated_at: datetime | None = None
    preview_token: str | None = None


class CatalogueSaveRequest(BaseModel):
    confirm_live: bool = False
    preview_token: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    selected_branches: list[str] = Field(max_length=10000)
    mode: Literal['compatible', 'acestream'] = 'compatible'
    refresh_enabled: bool = False


class CatalogueSummary(BaseModel):
    id: int
    name: str
    revision: int
    origin: str
    partial: bool
    refresh_enabled: bool
    updated_at: datetime


from app.schemas.events import EventFields


class CatalogueEventPreviewRequest(EventFields):
    revision: int = Field(ge=1)
    entry_ids: list[str] = Field(min_length=1, max_length=50)
    event_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{32}$')
