"""Stable presentation metadata without changing HTTP error bodies or policy."""
from fastapi import HTTPException


def coded_http_error(status_code: int, code: str, detail: str, *, headers: dict[str, str] | None = None) -> HTTPException:
    """Keep legacy detail/headers while giving clients a language-independent code."""
    return HTTPException(status_code, detail, headers={**(headers or {}), 'X-Error-Code': code})
