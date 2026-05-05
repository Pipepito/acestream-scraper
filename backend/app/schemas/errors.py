"""API error response schemas."""
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ErrorPayload(BaseModel):
    """Structured error payload for API responses."""

    code: str
    message: str
    correlation_id: str
    context: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Top-level API error envelope."""

    error: ErrorPayload
