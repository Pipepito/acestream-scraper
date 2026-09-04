"""Shared errors/client for Jellyfin and Plex adapters (spec 7.3)."""
from __future__ import annotations

from typing import Any, Optional

import httpx

from app.utils.url_guard import BlockedURLError, validate_lan_target

CLIENT_TIMEOUT = httpx.Timeout(10.0, connect=3.0)


class MediaServerUnreachable(RuntimeError):
    """No usable HTTP answer from the media server."""


class MediaServerAuthError(RuntimeError):
    """The server answered but rejected the API key/token."""


class MediaServerError(RuntimeError):
    """The server answered with an error we cannot act on."""

    def __init__(self, status_code: Optional[int], message: str):
        super().__init__(message)
        self.status_code = status_code


def new_client() -> httpx.Client:
    return httpx.Client(follow_redirects=False, timeout=CLIENT_TIMEOUT)


def guard(host: str) -> None:
    """Refuse metadata/link-local/multicast targets right before each request."""
    try:
        validate_lan_target(host, resolve=True)
    except BlockedURLError as exc:
        raise MediaServerUnreachable(str(exc)) from exc


def raise_for(response: httpx.Response, what: str) -> None:
    if response.status_code in (401, 403):
        raise MediaServerAuthError(f"{what}: the server rejected the API key/token (HTTP {response.status_code})")
    if response.status_code >= 400:
        raise MediaServerError(response.status_code, f"{what}: HTTP {response.status_code} {response.text[:200]}")


def decode_json(response: httpx.Response, what: str) -> Any:
    """Decode a JSON body, keeping a non-JSON answer inside the error contract.

    A wrong port or path answers 200 with HTML, and a bare ``response.json()``
    would raise ``json.JSONDecodeError`` — a type no caller catches.
    """
    try:
        return response.json()
    except ValueError as exc:
        content_type = response.headers.get("content-type", "no content type")
        raise MediaServerError(
            response.status_code,
            f"{what}: expected JSON but the server answered {content_type}; check the address",
        ) from exc
