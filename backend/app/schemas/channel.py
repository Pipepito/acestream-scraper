"""Pydantic schemas for channel data."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field



class AcestreamChannelBase(BaseModel):
    """Base model for Acestream channel data"""
    id: str = Field(..., description="Acestream channel ID (required, GUID string)")
    name: str = Field(..., min_length=1)



class AcestreamChannelCreate(AcestreamChannelBase):
    """Schema for Acestream channel creation"""
    source_url: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    is_online: Optional[bool] = True  # Default to True



class AcestreamChannelUpdate(BaseModel):
    """Schema for Acestream channel update"""
    name: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    source_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_online: Optional[bool] = None  # Added for test compatibility
    tv_channel_id: Optional[int] = None
    epg_update_protected: Optional[bool] = None



class AcestreamChannelResponse(AcestreamChannelBase):
    """Schema for Acestream channel response"""
    source_url: Optional[str] = None
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    last_seen: datetime
    is_active: bool
    is_online: Optional[bool] = None
    last_checked: Optional[datetime] = None
    check_error: Optional[str] = None
    tv_channel_id: Optional[int] = None
    tv_channel_name: Optional[str] = None
    tv_channel_is_favorite: Optional[bool] = None
    epg_update_protected: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)


class TVChannelBase(BaseModel):
    """Base model for TV channel data"""
    name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    website: Optional[str] = None
    epg_id: Optional[str] = None
    channel_number: Optional[int] = None


class TVChannelCreate(TVChannelBase):
    """Schema for TV channel creation"""
    is_active: Optional[bool] = True
    is_favorite: Optional[bool] = False
    epg_source_id: Optional[int] = None


class TVChannelUpdate(BaseModel):
    """Schema for TV channel update"""
    name: Optional[str] = None
    logo_url: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    website: Optional[str] = None
    epg_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None
    channel_number: Optional[int] = None
    epg_source_id: Optional[int] = None



class TVChannelResponse(TVChannelBase):
    """Schema for TV channel response"""
    id: int
    epg_source_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_favorite: bool
    acestream_channels: List[AcestreamChannelResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ChannelStatusCheck(BaseModel):
    """Schema for channel status check results"""
    total_channels: int
    online_count: int
    offline_count: int
    status_details: Dict[str, Any]



class AcestreamChannelListResponse(BaseModel):
    """Schema for paginated acestream channel results"""
    items: List[AcestreamChannelResponse]
    total: int


class TVChannelListResponse(BaseModel):
    """Schema for paginated TV channel results"""
    items: List[TVChannelResponse]
    total: int


class BulkChannelEditRequest(BaseModel):
    """Schema for bulk channel field updates"""
    acestreamchannel_ids: List[str]
    fields: AcestreamChannelUpdate


class BulkChannelActivateRequest(BaseModel):
    """Schema for bulk channel activation/deactivation"""
    acestreamchannel_ids: List[str]
    active: bool = True


class TVChannelAssociationRequest(BaseModel):
    """Schema for asociating one acestream channel with a TV channel"""
    acestream_channel_id: str


class TVChannelBatchAssignmentItem(BaseModel):
    """Schema for one TV channel assignment row"""
    tv_channel_id: int
    acestream_channel_id: str


class TVChannelBatchAssignRequest(BaseModel):
    """Schema for batch TV channel assignments"""
    assignments: List[TVChannelBatchAssignmentItem]


class TVChannelBatchAssignResponse(BaseModel):
    """Schema for batch assignment operation results"""
    success_count: int
    failure_count: int
    details: Dict[str, Dict[str, List[str]]]


class TVChannelCreateFromEPGRequest(BaseModel):
    epg_channel_ids: List[int]


class TVChannelCreateFromEPGResponse(BaseModel):
    created_count: int
    skipped_count: int
    associated_count: int
    items: List[TVChannelResponse]


MatchStrictness = Literal["loose", "balanced", "strict"]


class EPGMatchAnalysisRequest(BaseModel):
    strictness: MatchStrictness
    source_id: Optional[int] = None


class EPGMatchCandidateResponse(BaseModel):
    acestream_channel_id: str
    name: str
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    score: float
    match_stage: str


class EPGMatchRowResponse(BaseModel):
    epg_channel_id: int
    epg_channel_xml_id: str
    epg_channel_name: str
    epg_source_id: int
    epg_source_name: Optional[str] = None
    existing_tv_channel_id: Optional[int] = None
    existing_tv_channel_count: int = 0
    has_duplicate_existing_conflict: bool = False
    candidate_count: int
    candidates: List[EPGMatchCandidateResponse]
    best_match_type: Optional[str] = None
    best_match_confidence: Optional[str] = None
    is_creatable: bool


class EPGMatchAnalysisSummaryResponse(BaseModel):
    epg_channels_analyzed: int
    matched_epg_channels: int
    matched_acestream_channels: int
    creatable_rows: int
    skipped_existing_tv_channels: int


class EPGMatchAnalysisResponse(BaseModel):
    summary: EPGMatchAnalysisSummaryResponse
    rows: List[EPGMatchRowResponse]


class TVChannelCreateFromEPGAnalysisRowOutcome(BaseModel):
    epg_channel_id: int
    status: str
    reason: Optional[str] = None
    tv_channel_id: Optional[int] = None
    associated_count: int = 0


class TVChannelCreateFromEPGAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strictness: MatchStrictness
    epg_channel_ids: List[int] = Field(..., min_length=1)


class TVChannelCreateFromEPGAnalysisResponse(BaseModel):
    created_count: int
    skipped_count: int
    associated_count: int
    failure_count: int
    row_outcomes: List[TVChannelCreateFromEPGAnalysisRowOutcome]


class TVChannelBulkEPGUpdateItem(BaseModel):
    """Schema for one EPG update row"""
    tv_channel_id: int
    epg_id: str


class TVChannelBulkEPGUpdateRequest(BaseModel):
    """Schema for bulk EPG updates"""
    updates: List[TVChannelBulkEPGUpdateItem]


class TVChannelBulkEPGUpdateDetail(BaseModel):
    """Schema for one bulk EPG update result detail"""
    tv_channel_id: int | str
    status: str
    reason: Optional[str] = None
    old_epg_id: Optional[str] = None
    new_epg_id: Optional[str] = None


class TVChannelBulkEPGUpdateResponse(BaseModel):
    """Schema for bulk EPG update operation results"""
    success_count: int
    failure_count: int
    details: List[TVChannelBulkEPGUpdateDetail]


class MessageResponse(BaseModel):
    """Generic operation message response"""
    message: str
