"""Bounded catalogue reads; filters always precede ordering and pagination."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TVBrowseFilters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
    search: str = Field('', max_length=200)
    category: str = Field('', max_length=200)
    country: str = Field('', max_length=200)
    language: str = Field('', max_length=200)
    is_active: bool | None = None
    is_favorite: bool | None = None
    epg: Literal['yes', 'no'] | None = None
    epg_source_id: int | None = Field(None, ge=1)
    streams: Literal['any', 'none', 'multiple'] | None = None
    signal: Literal['verified', 'unverified', 'unknown'] | None = None
    number: Literal['yes', 'no'] | None = None
    min_number: int | None = None
    max_number: int | None = None
    min_streams: int | None = Field(None, ge=0)
    max_streams: int | None = Field(None, ge=0)
    logo_url: Literal['yes', 'no'] | None = None
    website: Literal['yes', 'no'] | None = None
    description: Literal['yes', 'no'] | None = None
    watchable: bool = False
    online_only: bool = False
    sort: Literal['default', 'name', 'channel_number', 'is_favorite', 'category', 'language', 'country', 'acestream_channels', 'is_active', 'logo_url'] = 'default'
    direction: Literal['asc', 'desc'] = 'asc'


class TVInventory(BaseModel):
    total: int
    favorites: int
    with_streams: int
    categories: list[str]
    countries: list[str]
    languages: list[str]
    epg_sources: list[int]
