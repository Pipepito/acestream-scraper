"""
Pydantic schemas for scraper data
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


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
    """Result model for scraper response"""
    message: str
    channels: List[ChannelResult]
    url: str


class URLResponse(BaseModel):
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
    added_at: datetime


    channels_found: int = 0  # Number of acestream channels found for this URL

    class Config:
        from_attributes = True


class URLCreate(BaseModel):
    """Schema for creating a scraped URL"""
    url: str
    url_type: str = "regular"
    enabled: bool = True
    status: str = "active"


class URLUpdate(BaseModel):
    """Schema for updating a scraped URL"""
    url: Optional[str] = None
    url_type: Optional[str] = None
    enabled: Optional[bool] = None
    status: Optional[str] = None
