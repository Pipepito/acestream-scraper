"""Resolve the origin external clients (tuners, players, copied links) must use (spec 4.3)."""
from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from typing import List, Literal
from urllib.parse import urlsplit

from fastapi import Request

from app.repositories.settings_repository import SettingsRepository

PublicUrlSource = Literal["setting", "forwarded", "request"]

_DOCKER_DESKTOP_GATEWAY = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")


class InvalidPublicBaseUrl(ValueError):
    """A candidate public base URL is not a bare http(s)://host[:port] origin."""


def normalize_public_base_url(value: str) -> str:
    """Accept http(s)://host[:port] only; strip a trailing slash; '' clears.

    Raises InvalidPublicBaseUrl for anything else. Request-facing callers map that
    onto HTTP 422 (ConfigService.normalize_public_base_url); the env seed in
    SettingsRepository logs it and falls back to '' so a typo cannot be stored.
    """
    candidate = (value or "").strip()
    if not candidate:
        return ""
    try:
        parts = urlsplit(candidate)
        _ = parts.port  # property access validates the port, raising ValueError
    except ValueError as exc:  # e.g. "http://[::1" -> Invalid IPv6 URL
        raise InvalidPublicBaseUrl("public_base_url must be http(s)://host[:port]") from exc
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise InvalidPublicBaseUrl("public_base_url must be http(s)://host[:port]")
    if parts.path not in ("", "/") or parts.query or parts.fragment or parts.username or parts.password:
        raise InvalidPublicBaseUrl(
            "public_base_url must not contain a path, query, fragment or credentials"
        )
    return f"{parts.scheme}://{parts.netloc}"


@dataclass
class ResolvedPublicUrl:
    url: str
    source: PublicUrlSource
    warnings: List[str] = field(default_factory=list)


def host_warnings(url: str) -> List[str]:
    """Codes for an origin other devices cannot reach: it names this machine
    ("localhost") or a Docker-internal address. Shared with the remote-player
    play response, which warns about the link it hands a player."""
    host = urlsplit(url).hostname or ""
    if host in ("localhost", "0.0.0.0", "::", "::1") or host.startswith("127."):
        return ["localhost"]
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return []
    if address in _DOCKER_DESKTOP_GATEWAY or address in _DOCKER_BRIDGE:
        return ["docker-internal"]
    return []


def request_origin(request: Request) -> str:
    """scheme://netloc of the (already forwarded-corrected) request."""
    return f"{request.url.scheme}://{request.url.netloc}"


def resolve_public_base_url(request: Request, settings_repo: SettingsRepository) -> ResolvedPublicUrl:
    configured = (settings_repo.get_setting(SettingsRepository.PUBLIC_BASE_URL) or "").strip()
    if configured:
        warnings = host_warnings(configured)
        if urlsplit(configured).hostname != request.url.hostname:
            warnings.append("proxied")
        return ResolvedPublicUrl(url=configured.rstrip("/"), source="setting", warnings=warnings)
    origin = request_origin(request)
    forwarded = bool(getattr(request.state, "forwarded", False))
    warnings = host_warnings(origin) + ["unset"]
    return ResolvedPublicUrl(url=origin, source="forwarded" if forwarded else "request", warnings=warnings)
