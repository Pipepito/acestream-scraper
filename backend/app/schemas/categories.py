"""Additive contracts for stable categories, live genres and reviewed assignment."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CategoryView(BaseModel):
    id: str
    label: str
    label_es: str
    artwork: str
    artwork_status: Literal['specific', 'parent', 'neutral']
    parent: str | None = None
    count: int = 0


class CategoryInventory(BaseModel):
    basis: Literal['channel', 'now']
    as_of: datetime
    taxonomy_version: int
    total: int
    items: list[CategoryView]
    next_change_at: datetime | None = None


class CategorySuggestion(BaseModel):
    channel_id: int
    name: str
    current_category: str | None
    category_origin: str
    category_revision: int
    suggested_category: str | None
    reason: str
    evidence: list[str]
    fingerprint: str


class CategoryPreviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    channel_ids: list[int] = Field(min_length=1, max_length=500)

    @field_validator('channel_ids')
    @classmethod
    def unique_ids(cls, value):
        if len(set(value)) != len(value) or any(item <= 0 for item in value):
            raise ValueError('Choose unique positive channel IDs')
        return value


class CategoryApplyItem(BaseModel):
    model_config = ConfigDict(extra='forbid')
    channel_id: int = Field(gt=0)
    fingerprint: str = Field(min_length=64, max_length=64)
    category_id: str = Field(max_length=100)


class CategoryApplyRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    items: list[CategoryApplyItem] = Field(min_length=1, max_length=500)


class CategoryApplyResult(BaseModel):
    updated: int


class CategoryAssignment(BaseModel):
    model_config = ConfigDict(extra='forbid')
    category: str | None = Field(None, max_length=255)
    mode: Literal['manual', 'automatic'] = 'manual'
    expected_revision: int = Field(ge=0)


class CategoryCoverageRow(BaseModel):
    label: str
    source_id: int
    programme_count: int
    guide_channel_count: int
    genre_ids: list[str]
    artwork_status: Literal['specific', 'parent', 'neutral', 'unmapped']


class CategoryCoverage(BaseModel):
    taxonomy_version: int
    total_labels: int
    items: list[CategoryCoverageRow]
    catalogue: list[CategoryView]
