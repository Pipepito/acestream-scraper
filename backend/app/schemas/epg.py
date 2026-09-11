"""
Pydantic schemas for EPG
"""
from pydantic import BaseModel, ConfigDict, Field, HttpUrl
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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class EPGChannelListResponse(BaseModel):
    """Paginated EPG channel response."""

    items: List[EPGChannelResponse]
    total: int


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

    model_config = ConfigDict(from_attributes=True)


class EPGStringMappingBase(BaseModel):
    """Base model for EPG string mapping"""
    search_pattern: str
    is_exclusion: bool = False


class EPGStringMappingCreate(EPGStringMappingBase):
    """Schema for creating an EPG string mapping"""
    epg_channel_id: int


class EPGStringMappingUpdate(EPGStringMappingBase):
    """Schema for updating/creating mapping payload in endpoint bodies"""
    pass


class EPGStringMappingResponse(EPGStringMappingBase):
    """Schema for EPG string mapping response"""
    id: int
    epg_channel_id: int

    model_config = ConfigDict(from_attributes=True)


class EPGChannelMappingRequest(BaseModel):
    """Schema for EPG channel to TV channel mapping request"""
    epg_channel_id: int
    tv_channel_id: int


class EPGRefreshResponse(BaseModel):
    """Schema for EPG refresh response"""
    source_id: int
    message: str
    success: bool
    status: str = "success"  # Added status field for compatibility with tests
    channels_found: Optional[int] = None
    programs_found: Optional[int] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


class EPGXmlGenerationRequest(BaseModel):
    """Schema for EPG XML generation request"""
    search_term: Optional[str] = None
    favorites_only: bool = False
    days_back: int = 1
    days_forward: int = 7
