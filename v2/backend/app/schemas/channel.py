"""
Pydantic schemas for channel data
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ChannelBase(BaseModel):
    """Base model for channel data"""
    channel_id: str
    name: str
    

class ChannelCreate(ChannelBase):
    """Schema for channel creation"""
    source_url: Optional[str] = None


class ChannelResponse(ChannelBase):
    """Schema for channel response"""
    id: int
    source_url: Optional[str] = None
    last_seen: datetime
    is_active: bool
    tv_channel_id: Optional[int] = None

    class Config:
        orm_mode = True


class TVChannelBase(BaseModel):
    """Base model for TV channel data"""
    name: str
    logo_url: Optional[str] = None


class TVChannelCreate(TVChannelBase):
    """Schema for TV channel creation"""
    pass


class TVChannelResponse(TVChannelBase):
    """Schema for TV channel response"""
    id: int
    acestream_channels: List[ChannelResponse] = []

    class Config:
        orm_mode = True
