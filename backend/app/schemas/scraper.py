"""
Pydantic schemas for scraper data
"""
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.extraction import ExtractionRecipe


class ScraperRequest(BaseModel):
    """Request model for scraping a URL"""
    url: str
    url_type: str = "auto"
    run_async: bool = False


class ChannelResult(BaseModel):
    """Schema for channel result from scraping"""
    channel_id: str
    name: str
    metadata: Dict[str, Any] = {}


class ScraperResult(BaseModel):
    excluded_count: int = 0
    """Result model for scraper response"""
    message: str
    channels: List[ChannelResult]
    url: str


class SourceName(BaseModel):
    name: Optional[str] = Field(None, max_length=255)

    @field_validator('name', mode='before')
    @classmethod
    def clean_name(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class BuiltinProvider(BaseModel):
    id: str
    name: str
    url: str


class URLResponse(SourceName):
    """Schema for scraped URL information"""
    id: int
    url: str
    url_type: str
    status: str
    last_processed: Optional[datetime] = None
    last_scraped: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    error: Optional[str] = None  # Keep for backward compatibility
    enabled: bool = True
    extraction_recipe: Optional[ExtractionRecipe] = None
    scrape_bare_ids: bool = False
    added_at: datetime


    channels_found: int = 0  # Number of acestream channels found for this URL

    model_config = ConfigDict(from_attributes=True)

    @field_validator("scrape_bare_ids", mode="before")
    @classmethod
    def _null_flag_means_off(cls, value: Optional[bool]) -> bool:
        # Rows the pre-2026-08-29 v1 migrator copied into a create_all schema
        # carry NULL here; treat that as the opt-in being off rather than
        # failing the whole listing.
        return False if value is None else value


class URLCreate(SourceName):
    """Schema for creating a scraped URL"""
    url: str
    url_type: str = "regular"
    enabled: bool = True
    status: str = "active"
    extraction_recipe: Optional[ExtractionRecipe] = None
    scrape_bare_ids: bool = False


class URLUpdate(SourceName):
    """Schema for updating a scraped URL"""
    url: Optional[str] = None
    url_type: Optional[str] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
    extraction_recipe: Optional[ExtractionRecipe] = None
    scrape_bare_ids: Optional[bool] = None
