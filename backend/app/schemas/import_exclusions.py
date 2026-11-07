"""Bounded public import-policy contracts."""
import re
import unicodedata
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

RuleKind = Literal['name_contains', 'name_equals', 'stream_id_equals']


def normalize_name(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().split())


def normalized_rule(kind: str, value: str) -> str:
    if any(unicodedata.category(c).startswith('C') for c in value):
        raise ValueError('Control characters are not allowed')
    if kind == 'stream_id_equals':
        value = value.strip().lower()
        if not re.fullmatch(r'(?:[a-f0-9]{40}|url:[a-f0-9]{40})', value):
            raise ValueError('Enter a canonical stream ID, not a URL or infohash')
    else:
        value = normalize_name(value)
    if not value:
        raise ValueError('Enter a nonempty pattern')
    return value


class ExclusionInput(BaseModel):
    kind: RuleKind
    value: str = Field(min_length=1, max_length=256)
    enabled: bool = True
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode='after')
    def valid_rule(self):
        normalized_rule(self.kind, self.value)
        return self


class ExclusionUpdate(ExclusionInput):
    expected_revision: int = Field(ge=1)


class ExclusionRule(ExclusionInput):
    model_config = ConfigDict(from_attributes=True)
    id: int
    revision: int
    created_at: datetime
    updated_at: datetime


class ExclusionWrite(BaseModel):
    rule: ExclusionRule
    policy_revision: int


class ExclusionList(BaseModel):
    items: list[ExclusionRule]
    total: int
    policy_revision: int


class ImportCandidate(BaseModel):
    channel_id: str = Field(max_length=44)
    name: str = Field(max_length=512)


class ExclusionPreviewRequest(ExclusionInput):
    candidates: list[ImportCandidate] | None = Field(default=None, max_length=200)

    @model_validator(mode='after')
    def storage_budget(self):
        if len(self.model_dump_json().encode()) > 256 * 1024:
            raise ValueError('Preview samples exceed the 256 KiB budget')
        return self


class ExclusionPreview(BaseModel):
    policy_revision: int
    scanned: int
    matched: int
    complete: bool
    examples: list[ImportCandidate]
