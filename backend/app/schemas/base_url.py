"""
Schemas for named stream base URLs (#62).
"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_pattern(pattern: str) -> str:
    # {pid} only renders inside a mask; without {channel_id} the pattern
    # falls back to prefix mode and would glue the channel id onto a
    # literal placeholder.
    if "{pid}" in pattern and "{channel_id}" not in pattern:
        raise ValueError("A pattern using {pid} must also contain {channel_id}")
    return pattern


class BaseUrlBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    pattern: str = Field(..., min_length=1, max_length=1024,
                         description="Prefix, or a mask using {channel_id} and optionally {pid}")
    is_default: bool = False

    @field_validator("pattern")
    @classmethod
    def check_pattern(cls, value: str) -> str:
        return _validate_pattern(value)


class BaseUrlCreate(BaseUrlBase):
    pass


class BaseUrlUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    pattern: Optional[str] = Field(None, min_length=1, max_length=1024)
    is_default: Optional[bool] = None

    @field_validator("pattern")
    @classmethod
    def check_pattern(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return _validate_pattern(value)


class BaseUrlResponse(BaseUrlBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
