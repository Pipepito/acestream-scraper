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


@dataclass
class ResolvedPublicUrl:
    url: str
    source: PublicUrlSource
    warnings: List[str] = field(default_factory=list)


def _host_warnings(url: str) -> List[str]:
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
        warnings = _host_warnings(configured)
        if urlsplit(configured).hostname != request.url.hostname:
            warnings.append("proxied")
        return ResolvedPublicUrl(url=configured.rstrip("/"), source="setting", warnings=warnings)
    origin = request_origin(request)
    forwarded = bool(getattr(request.state, "forwarded", False))
    warnings = _host_warnings(origin) + ["unset"]
    return ResolvedPublicUrl(url=origin, source="forwarded" if forwarded else "request", warnings=warnings)
