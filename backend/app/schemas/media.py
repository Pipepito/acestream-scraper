"""Measured source media metadata shared by channel and player APIs."""
from typing import Optional
from pydantic import BaseModel, Field


class AudioTrack(BaseModel):
    index: int = Field(ge=0, description="Zero-based audio track index (ffmpeg 0:a:index)")
    language: Optional[str] = None
    title: Optional[str] = None
    codec: Optional[str] = None
    channels: Optional[int] = None
    channel_layout: Optional[str] = None
