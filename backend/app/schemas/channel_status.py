"""
Schemas for channel status operations
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class ChannelStatusResponse(BaseModel):
    """Response schema for channel status check"""
    channel_id: str
    network_status: Optional[Literal["found", "not_found", "unknown"]] = None
    is_online: bool
    status: str  # 'online', 'offline', 'error', 'skipped' (in use; previous status retained)
    message: str
    last_checked: datetime
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ChannelStatusSummary(BaseModel):
    """Summary of all channel statuses"""
    total_channels: int
    active_channels: int  # Added to match test expectations
    online: int
    online_channels: int  # Added to match test expectations
    offline: int
    offline_channels: int  # Added to match test expectations
    unknown: int
    recent_checks: int
    last_checked_channels: int  # Added to match test expectations
    online_percentage: float
    checked_percentage: float

    model_config = ConfigDict(from_attributes=True)


class ChannelStatusJobRunResponse(BaseModel):
    status: Literal["triggered", "already_running", "disabled"]
    message: str
