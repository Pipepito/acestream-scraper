"""Latest bounded engine observation, separate from verified media metadata."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class StreamStats(BaseModel):
    observed_at: datetime
    peers: Optional[int] = Field(None, ge=0, le=2147483647)
    download_speed_kbytes_sec: Optional[float] = Field(None, ge=0, le=1e12, description="Engine speed_down in Kbytes/sec; not encoded media bitrate")
    upload_speed_kbytes_sec: Optional[float] = Field(None, ge=0, le=1e12, description="Engine speed_up in Kbytes/sec")
