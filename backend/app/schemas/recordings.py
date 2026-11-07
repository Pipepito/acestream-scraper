"""DVR public contracts. No process identities, paths or upstream URLs."""
from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

RecordingState = Literal['scheduled', 'starting', 'recording', 'recovering', 'finalizing',
                         'completed', 'partial', 'failed', 'missed', 'cancelled', 'deleting', 'deleted']


class RecordingSettings(BaseModel):
    enabled: bool = False
    max_concurrent: int = Field(default=1, ge=1, le=4)
    min_free_bytes: int = Field(default=2 * 1024**3, ge=64 * 1024**2)
    max_recording_bytes: int = Field(default=100 * 1024**3, ge=1024**2)
    retention_days: int | None = Field(default=None, ge=1, le=3650)


class ProgrammeSelection(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    epg_channel_id: int
    start_time: AwareDatetime
    end_time: AwareDatetime
    title: str
    subtitle: str | None = None
    description: str | None = None
    category: str | None = None


class RecordingCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tv_channel_id: int = Field(gt=0)
    mode: Literal['now', 'schedule'] = 'schedule'
    start_time: AwareDatetime
    end_time: AwareDatetime
    timezone: str = Field(max_length=64)
    programme: ProgrammeSelection | None = None
    idempotency_key: str = Field(min_length=16, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')

    @field_validator('timezone')
    @classmethod
    def valid_zone(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError('Choose a valid IANA timezone') from None
        return value

    @model_validator(mode='after')
    def times(self):
        if self.end_time <= self.start_time:
            raise ValueError('End must be after start')
        if (self.end_time - self.start_time).total_seconds() > 43200:
            raise ValueError('Maximum recording duration is 12 hours')
        # UTC is the API's canonical wire format. Non-UTC local offsets must
        # round-trip in the explicit zone (detects missing/folded local times).
        for value in (self.start_time, self.end_time):
            if value.utcoffset().total_seconds() and value.astimezone(ZoneInfo(self.timezone)).utcoffset() != value.utcoffset():
                raise ValueError('Time offset does not match the chosen timezone')
        if self.mode == 'schedule' and self.programme is None:
            raise ValueError('Select a programme for one-off scheduling')
        return self


class RecordingEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    expected_revision: int = Field(ge=1)
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    protected: bool | None = None


class RecordingSnapshot(BaseModel):
    title: str
    channel_name: str
    subtitle: str | None = None
    description: str | None = None
    category: str | None = None
    guide_source_uuid: str | None = None
    guide_channel_id: str | None = None
    original_start: datetime | None = None
    original_end: datetime | None = None
    provider_programme_id: str | None = None


class RecordingGap(BaseModel):
    start: datetime
    end: datetime
    reason: str


class RecordingFile(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    kind: str
    state: str
    profile: str | None
    source_artifact_id: str | None
    bytes: int
    duration: float | None
    codecs: list[str]
    reason: str | None


class RecordingAttemptView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    ordinal: int
    source_id: str
    route: str
    started_at: datetime
    ended_at: datetime | None
    exit_code: int | None
    reason: str | None


class RecordingView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tv_channel_id: int | None
    snapshot: RecordingSnapshot
    start_time: datetime
    end_time: datetime
    timezone: str
    state: RecordingState
    revision: int
    protected: bool
    actual_start: datetime | None
    actual_end: datetime | None
    reason: str | None
    gaps: list[RecordingGap]
    created_at: datetime
    files: list[RecordingFile] = Field(default_factory=list)
    attempts: list[RecordingAttemptView] = Field(default_factory=list)


class RecordingList(BaseModel):
    items: list[RecordingView]
    total: int


class RecordingCapabilities(BaseModel):
    enabled: bool
    available: bool
    storage_ready: bool
    message: str
    stream_copy: bool
    mp4_remux: bool
    aac_conversion: bool
    settings: RecordingSettings


class RecordingConversion(BaseModel):
    file_id: str = Field(pattern=r'^[0-9a-f]{32}$')
    profile: Literal['remux', 'aac'] = 'remux'


class RecordingPlaybackRequest(BaseModel):
    file_id: str = Field(pattern=r'^[0-9a-f]{32}$')


class RecordingPlaybackView(BaseModel):
    id: str
    state: Literal['preparing', 'ready', 'failed']
    file_id: str
    media_url: str | None = None
    message: str
