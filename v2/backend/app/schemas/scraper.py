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
    last_scraped: datetime
    status: str
    
    class Config:
        orm_mode = True
