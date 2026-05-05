from pydantic import BaseModel
from typing import List, Optional

class URLStats(BaseModel):
    id: int
    url: str
    url_type: str
    status: str
    last_processed: Optional[str] = None
    channel_count: int
    enabled: bool
    error_count: int
    last_error: Optional[str] = None

class StatsResponse(BaseModel):
    urls: List[URLStats]
    total_channels: int
    channels: int  # Alias for total_channels for compatibility
    channels_checked: int
    channels_online: int
    channels_offline: int
    base_url: str
    ace_engine_url: str
    rescrape_interval: int
    addpid: bool
    task_manager_status: str

class TVChannelStatsResponse(BaseModel):
    total: int
    active: int
    with_epg: int
    acestreams: int
