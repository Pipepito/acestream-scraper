"""Versioned observations shared by reviewed schedule, W3U and Telegram adapters."""
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EventState = Literal['unknown', 'scheduled', 'live', 'finished', 'postponed', 'cancelled']


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


def event_time(value: datetime | None, zone: str) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc)
    tz = ZoneInfo(zone)
    candidates = {value.replace(tzinfo=tz, fold=fold).astimezone(timezone.utc)
                  for fold in (0, 1)
                  if value.replace(tzinfo=tz, fold=fold).astimezone(timezone.utc)
                  .astimezone(tz).replace(tzinfo=None) == value}
    if len(candidates) != 1:
        raise ValueError('Local time is ambiguous or does not exist; supply an explicit UTC offset')
    return candidates.pop()


class EventFields(StrictModel):
    title: str = Field(min_length=1, max_length=300)
    sport: str = Field(default='', max_length=100)
    competition: str = Field(default='', max_length=200)
    participants: list[str] = Field(default_factory=list, max_length=8)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    timezone: str = Field(max_length=100)
    time_notes: str = Field(default='', max_length=500)
    state: EventState = 'unknown'

    @field_validator('starts_at', 'ends_at', mode='before')
    @classmethod
    def explicit_date_and_time(cls, value):
        if value is not None and not isinstance(value, datetime):
            if not isinstance(value, str) or not any(separator in value for separator in ('T', 't', ' ')) or ':' not in value:
                raise ValueError('Supply a full ISO date and time, or null when unknown')
        return value

    @field_validator('timezone')
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Use an IANA timezone such as Europe/Madrid') from None
        return value

    @field_validator('participants')
    @classmethod
    def bounded_participants(cls, value):
        if any(not name or len(name) > 200 for name in value):
            raise ValueError('Participants must contain 1–200 characters')
        return value

    @model_validator(mode='after')
    def normalize_times(self):
        self.starts_at = event_time(self.starts_at, self.timezone)
        self.ends_at = event_time(self.ends_at, self.timezone)
        if self.ends_at and (not self.starts_at or self.ends_at <= self.starts_at):
            raise ValueError('A known end must follow a known start')
        return self


class EventBroadcast(StrictModel):
    id: str = Field(min_length=1, max_length=160)
    label: str = Field(min_length=1, max_length=200)
    language: str = Field(default='', max_length=80)
    quality: str = Field(default='', max_length=80)
    country: str = Field(default='', max_length=80)
    # Explicit stored channel mappings are reviewed, never guessed from a name.
    channel_id: str | None = Field(default=None, pattern=r'^(?:url:)?[0-9a-fA-F]{40}$')
    url: str | None = Field(default=None, max_length=4096)
    headers: dict[str, str] = Field(default_factory=dict, max_length=3)

    @model_validator(mode='after')
    def safe_input(self):
        if self.url and self.channel_id:
            raise ValueError('Choose a stream URL or an existing channel, not both')
        if self.url:
            p = urlsplit(self.url)
            if p.scheme == 'acestream':
                import re
                if not re.fullmatch(r'acestream://[0-9a-fA-F]{40}', self.url):
                    raise ValueError('Invalid AceStream ID')
            elif p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
                raise ValueError('Use HTTP(S) or an AceStream ID')
            if any(ord(c) < 32 for c in self.url):
                raise ValueError('Invalid source URL')
        if any(k.lower() not in ('user-agent', 'referer', 'origin') or len(v) > 2048
               or any(ord(c) < 32 for c in k + v) for k, v in self.headers.items()):
            raise ValueError('Only bounded User-Agent, Referer and Origin headers are supported')
        self.headers = {k.lower(): v for k, v in self.headers.items()}
        return self


class EventObservation(EventFields):
    artwork_url: str | None = Field(default=None, max_length=4096)

    @field_validator('artwork_url')
    @classmethod
    def artwork_http_url(cls, value):
        if value:
            p = urlsplit(value)
            if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password or any(ord(c) < 32 for c in value):
                raise ValueError('Artwork needs an HTTP(S) URL without embedded credentials')
        return value

    source_id: str = Field(min_length=1, max_length=160, pattern=r'^[\w.:-]+$')
    source_name: str = Field(min_length=1, max_length=200)
    source_kind: Literal['guide', 'w3u', 'telegram', 'manual'] = 'manual'
    external_id: str = Field(min_length=1, max_length=200)
    # Only an explicit reviewed association combines different sources.
    event_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{32}$')
    broadcasts: list[EventBroadcast] = Field(default_factory=list, max_length=50)

    @model_validator(mode='after')
    def unique_broadcasts(self):
        if len({b.id for b in self.broadcasts}) != len(self.broadcasts):
            raise ValueError('Broadcast IDs must be unique within an observation')
        return self


class EventImport(StrictModel):
    version: Literal[1] = 1
    observations: list[EventObservation] = Field(min_length=1, max_length=500)

    @model_validator(mode='after')
    def unique_observations(self):
        if len({(o.source_id, o.external_id) for o in self.observations}) != len(self.observations):
            raise ValueError('Each source/event identity must occur once per import')
        return self


class BroadcastView(StrictModel):
    manually_mapped: bool = False
    id: str
    label: str
    language: str
    quality: str
    country: str
    source_name: str
    origin: str
    content_id: str | None
    compatibility: Literal['playable', 'unresolved', 'unsupported', 'unavailable']
    reason: str
    is_online: bool | None = None
    checked_at: datetime | None = None


class ProvenanceView(StrictModel):
    source_id: str
    source_name: str
    source_kind: str
    external_id: str
    updated_at: datetime


class EventView(EventFields):
    has_artwork: bool = False
    id: str
    revision: int
    corrected: bool
    followed: bool
    archived: bool
    broadcasts: list[BroadcastView]
    provenance: list[ProvenanceView]


class EventList(StrictModel):
    events: list[EventView]
    total: int


class EventPreview(StrictModel):
    token: str
    events: list[EventView]
    warnings: list[str]


class EventApply(StrictModel):
    token: str = Field(min_length=1, max_length=128)
    selected_ids: list[str] = Field(min_length=1, max_length=500)
    refresh_source: bool = False


class EventUpdate(StrictModel):
    revision: int = Field(ge=1)
    correction: EventFields | None = None
    followed: bool | None = None
    archived: bool | None = None


class EventSourcePreviewRequest(StrictModel):
    format: Literal['event_import', 'schema_org'] = 'event_import'
    timezone: str = Field(default='UTC', max_length=100)

    @field_validator('timezone')
    @classmethod
    def valid_zone(cls, value):
        return EventFields.valid_zone(value)

    url: str | None = Field(default=None, max_length=4096)
    source_id: str | None = Field(default=None, pattern=r'^[0-9a-f]{32}$')

    @model_validator(mode='after')
    def one_source(self):
        if bool(self.url) == bool(self.source_id):
            raise ValueError('Choose a schedule URL or a saved source')
        if self.url:
            parsed = urlsplit(self.url)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or any(ord(c) < 32 for c in self.url):
                raise ValueError('Use an HTTP(S) schedule URL without embedded credentials')
        return self


class EventSourceUpdate(StrictModel):
    revision: int = Field(ge=1)
    enabled: bool


class EventRefreshResult(StrictModel):
    updated: int = 0
    pending: int = 0
    status: Literal['updated', 'error', 'unchanged']
    message: str


class EventSourceView(StrictModel):
    format: Literal['event_import', 'schema_org'] = 'event_import'
    timezone: str = 'UTC'
    id: str
    revision: int
    name: str
    origin: str
    enabled: bool
    reviewed: int
    last_attempt: datetime | None
    last_success: datetime | None
    last_result: EventRefreshResult | None


class EventRetention(StrictModel):
    ended_days: int = Field(default=0, ge=0, le=3650)
    archived_days: int = Field(default=0, ge=0, le=3650)


class EventBroadcastMapping(StrictModel):
    revision: int = Field(ge=1)
    broadcast_id: str = Field(min_length=1, max_length=193)
    channel_id: str | None = Field(default=None, pattern=r'^(?:url:)?[0-9a-fA-F]{40}$')


class EventRefreshQueued(StrictModel):
    status: Literal['triggered', 'already_running']
    message: str
