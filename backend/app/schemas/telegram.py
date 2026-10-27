"""Telegram control-plane DTOs. Account secrets are write-only."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from app.schemas.extraction import ExtractionRecipe, RecipePreview


class TelegramLogin(BaseModel):
    model_config = ConfigDict(extra='forbid')
    api_id: int = Field(gt=0, le=2147483647)
    api_hash: SecretStr = Field(min_length=32, max_length=32)
    phone: SecretStr = Field(min_length=5, max_length=32)


class TelegramCode(BaseModel):
    code: SecretStr = Field(min_length=1, max_length=16)


class TelegramPassword(BaseModel):
    password: SecretStr = Field(min_length=1, max_length=256)


class TelegramStatus(BaseModel):
    state: str
    message: str = ''
    account_label: str = ''
    queue_size: int = 0
    retry_at: datetime | None = None


class TelegramPeer(BaseModel):
    id: str
    label: str
    kind: Literal['user', 'chat', 'channel', 'topic']


class TelegramSourceConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    chat_id: str = Field(pattern=r'^-?[1-9][0-9]{0,18}$')
    topic_id: int | None = Field(None, gt=0)
    enabled: bool = True
    sender_ids: list[str] = Field(default_factory=list, max_length=100)
    sender_rule: Literal['posting', 'original'] = 'posting'
    include_forwards: bool = True
    include: str = Field('', max_length=512)
    exclude: str = Field('', max_length=512)
    filter_mode: Literal['keyword', 'regex'] = 'keyword'
    bare_ids: bool = True
    recipe: ExtractionRecipe | None = None

    @model_validator(mode='after')
    def validate_filters(self):
        import re
        if any(not re.fullmatch(r'-?[1-9][0-9]{0,18}', item) for item in self.sender_ids):
            raise ValueError('Select stable Telegram sender IDs')
        if self.filter_mode == 'regex':
            for pattern in (self.include, self.exclude):
                if pattern:
                    ExtractionRecipe(mode='regex', records=pattern,
                                     fields={'name': {}, 'id': {}})
        return self


class TelegramSourceCreate(TelegramSourceConfig):
    history_count: int = Field(0, ge=0, le=1000)
    history_since: datetime | None = None

    @model_validator(mode='after')
    def aware_history(self):
        if self.history_since and self.history_since.tzinfo is None:
            raise ValueError('History start must include a timezone')
        return self


class TelegramSource(TelegramSourceConfig):
    excluded_count: int = 0
    id: int
    chat_label: str
    sender_labels: dict[str, str] = Field(default_factory=dict)
    cursor: int
    state: str
    last_success: datetime | None = None
    imported_count: int
    message: str


class TelegramPreviewMessage(BaseModel):
    excluded_count: int = 0
    excluded_rule_ids: dict[str, list[int]] = Field(default_factory=dict)
    message_id: int
    sender_id: str | None = None
    outcome: str
    result: RecipePreview


class TelegramPreviewRequest(BaseModel):
    source: TelegramSourceConfig
    limit: int = Field(10, ge=1, le=30)


class TelegramPreview(BaseModel):
    chat_id: str
    messages: list[TelegramPreviewMessage]


class TelegramResolve(BaseModel):
    username: str = Field(pattern=r'^@?[A-Za-z][A-Za-z0-9_]{3,31}$')
