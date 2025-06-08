"""
Pydantic schemas for EPG
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class EPGSourceBase(BaseModel):
    """Base model for EPG source"""
    url: str
    name: str


class EPGSourceCreate(EPGSourceBase):
    """Schema for creating an EPG source"""
    enabled: bool = True


class EPGSourceUpdate(BaseModel):
    """Schema for updating an EPG source"""
    url: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None


class EPGSourceResponse(EPGSourceBase):
    """Schema for EPG source response"""
    id: int
    enabled: bool
    last_updated: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None

    class Config:
        orm_mode = True


class EPGChannelBase(BaseModel):
    """Base model for EPG channel"""
    epg_source_id: int
    channel_xml_id: str
    name: str
    icon_url: Optional[str] = None
    language: Optional[str] = None


class EPGChannelResponse(EPGChannelBase):
    """Schema for EPG channel response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class EPGProgramBase(BaseModel):
    """Base model for EPG program"""
    epg_channel_id: int
    start_time: datetime
    end_time: datetime
    title: str
    subtitle: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class EPGProgramResponse(EPGProgramBase):
    """Schema for EPG program response"""
    id: int
    program_xml_id: Optional[str] = None

    class Config:
        orm_mode = True


class EPGStringMappingBase(BaseModel):
    """Base model for EPG string mapping"""
    search_pattern: str
    is_exclusion: bool = False


class EPGStringMappingCreate(EPGStringMappingBase):
    """Schema for creating an EPG string mapping"""
    epg_channel_id: int


class EPGStringMappingResponse(EPGStringMappingBase):
    """Schema for EPG string mapping response"""
    id: int
    epg_channel_id: int

    class Config:
        orm_mode = True


class EPGChannelMappingRequest(BaseModel):
    """Schema for EPG channel to TV channel mapping request"""
    epg_channel_id: int
    tv_channel_id: int


class EPGRefreshResponse(BaseModel):
    """Schema for EPG refresh response"""
    source_id: int
    message: str
    success: bool
    channels_found: Optional[int] = None
    programs_found: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
