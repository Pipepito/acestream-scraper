"""
Schemas for named stream base URLs (#62).
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseUrlBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    pattern: str = Field(..., min_length=1, max_length=1024,
                         description="Prefix, or a mask using {channel_id} and optionally {pid}")
    is_default: bool = False


class BaseUrlCreate(BaseUrlBase):
    pass


class BaseUrlUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    pattern: Optional[str] = Field(None, min_length=1, max_length=1024)
    is_default: Optional[bool] = None


class BaseUrlResponse(BaseUrlBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
