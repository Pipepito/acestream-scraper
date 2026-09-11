"""Global API exception handlers and error envelope helpers."""
import logging
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas.errors import ErrorResponse

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Explicit application error with stable API metadata."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.context = context or {}


def _correlation_id(request: Request) -> str:
    existing = getattr(request.state, "correlation_id", None)
    if existing:
        return existing
    generated = str(uuid4())
    request.state.correlation_id = generated
    return generated


def _error_response(
    request: Request,
    *,
    code: str,
    message: str,
    status_code: int,
    context: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error={
            "code": code,
            "message": message,
            "correlation_id": _correlation_id(request),
            "context": context or None,
        }
    )
    response = JSONResponse(status_code=status_code, content=payload.model_dump())
    response.headers["X-Correlation-ID"] = payload.error.correlation_id
    return response


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    logger.error(
        "APIError code=%s message=%s context=%s correlation_id=%s",
        exc.code,
        exc.message,
        exc.context,
        _correlation_id(request),
    )
    return _error_response(
        request,
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        context=exc.context,
    )


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception path=%s correlation_id=%s",
        request.url.path,
        _correlation_id(request),
    )
    return _error_response(
        request,
        code="INTERNAL_ERROR",
        message="Unexpected server error",
        status_code=500,
        context={"path": request.url.path, "error": str(exc)},
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
