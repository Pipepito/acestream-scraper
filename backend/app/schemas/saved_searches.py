"""Saved definitions, bounded preview and truthful run outcomes."""
import unicodedata
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.schemas.search import SearchImportOutcome


class SavedSearchInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    query: str = Field(min_length=1, max_length=256)
    category: str = Field(default='', max_length=100)
    refresh_enabled: bool = False

    @field_validator('name', 'query', 'category')
    @classmethod
    def safe_text(cls, value, info):
        if any(unicodedata.category(c).startswith('C') for c in value):
            raise ValueError('Control characters are not allowed')
        value = value.strip()
        if info.field_name != 'category' and not value:
            raise ValueError('Enter a nonempty value')
        return value


class SavedSearchUpdate(SavedSearchInput):
    expected_revision: int = Field(ge=1)


class SavedSearchRunRequest(BaseModel):
    expected_revision: int = Field(ge=1)
    preview_token: str | None = Field(default=None, max_length=100)


Outcome = Literal['complete', 'partial', 'failed', 'skipped', 'interrupted']


class SavedSearchResult(BaseModel):
    schema_version: int = 1
    outcome: Outcome
    stop_reason: str | None = None
    pages_fetched: int = 0
    candidates_seen: int = 0
    unique_infohashes: int = 0
    resolved_content_ids: int = 0
    added: int = 0
    existing: int = 0
    excluded_candidates: int = 0
    unresolved_candidates: int = 0
    duplicates: int = 0
    deferred_candidates: int = 0
    duration_seconds: float = 0
    policy_revision: int
    definition_revision: int
    started_at: datetime
    finished_at: datetime
    samples: list[SearchImportOutcome] = Field(default_factory=list, max_length=100)
    samples_truncated: bool = False


class SavedSearchView(SavedSearchInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    revision: int
    created_at: datetime
    updated_at: datetime
    last_attempt_at: datetime | None = None
    last_started_at: datetime | None = None
    last_finished_at: datetime | None = None
    last_success_at: datetime | None = None
    last_outcome: Outcome | None = None
    last_result: SavedSearchResult | None = None
    error_code: str | None = None
    error_message: str | None = None
    run_id: str | None = None
    run_state: Literal['waiting', 'running'] | None = None


class SavedSearchList(BaseModel):
    items: list[SavedSearchView]
    total: int


class SavedSearchPreviewRequest(BaseModel):
    definition: SavedSearchInput | None = None
    saved_search_id: int | None = Field(default=None, ge=1)
    expected_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode='after')
    def one_definition(self):
        if (self.definition is None) == (self.saved_search_id is None):
            raise ValueError('Choose a saved search or a proposed definition')
        if self.saved_search_id is not None and self.expected_revision is None:
            raise ValueError('Expected revision is required')
        return self


class SavedSearchPreview(BaseModel):
    preview_token: str
    result: SavedSearchResult
    expires_in_seconds: int = 300
