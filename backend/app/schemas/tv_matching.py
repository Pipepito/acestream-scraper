"""Contracts for reviewed, non-destructive TV channel automatching."""
from typing import Literal
from pydantic import BaseModel, Field


class TVMatchOptions(BaseModel):
    assumed_country: Literal['ES', 'PT', 'FR', 'DE', 'IT', 'GB', 'US', 'NL', 'PL', 'TR', 'BE', 'AR', 'RU'] | None = Field(
        default=None, description='Matching-only country for unlabelled streams and TV channels; explicit countries take precedence.'
    )


class TVMatchCandidate(BaseModel):
    acestream_channel_id: str
    acestream_name: str
    tv_channel_id: int
    tv_channel_name: str
    score: float
    reason: str
    recommended: bool


class TVMatchPreview(BaseModel):
    tv_channels: int
    unassigned_streams: int
    ambiguous_streams: int
    unmatched_streams: int
    candidates: list[TVMatchCandidate]


class TVMatchAssignment(BaseModel):
    acestream_channel_id: str = Field(min_length=1, max_length=100)
    tv_channel_id: int = Field(gt=0)


class TVMatchApplyRequest(TVMatchOptions):
    assignments: list[TVMatchAssignment] = Field(min_length=1, max_length=10000)


class TVMatchApplyResponse(BaseModel):
    assigned_count: int
    skipped_count: int
