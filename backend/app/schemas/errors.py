"""API error response schemas."""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    """Structured error payload for API responses."""

    code: str
    message: str
    correlation_id: str
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Top-level API error envelope."""

    error: ErrorPayload


class HTTPErrorCodeHeader(BaseModel):
    """Optional response metadata for legacy detail-based HTTP errors."""

    error_code: str = Field(alias='X-Error-Code', pattern=r'^[A-Z][A-Z0-9_]{0,99}$',
                           description='Stable application reason code, when available; select localized guidance by this code, not the detail sentence.')
