"""Pure-ASGI forwarded-headers middleware (spec 4.3).

The app owns proxy trust: when the raw peer is in FORWARDED_ALLOW_IPS the
X-Forwarded-Proto / X-Forwarded-Host / X-Forwarded-For headers rewrite the
scope once. uvicorn is started with --no-proxy-headers so nothing else
touches these values. The raw peer is always kept in scope["state"]["peer"].
"""
from __future__ import annotations

import ipaddress
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Set

logger = logging.getLogger(__name__)

_ALLOWED_PROTOS = {"http", "https", "ws", "wss"}


def _canonical(host: str) -> Optional[ipaddress._BaseAddress]:
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    mapped = getattr(address, "ipv4_mapped", None)
    return mapped if mapped is not None else address


@dataclass
class TrustedPeers:
    networks: List[ipaddress._BaseNetwork] = field(default_factory=list)
    literals: Set[str] = field(default_factory=set)
    everyone: bool = False

    def contains(self, host: Optional[str]) -> bool:
        if not host:
            return False
        if self.everyone:
            return True
        if host in self.literals:
            return True
        address = _canonical(host)
        if address is None:
            return False
        return any(address in network for network in self.networks)


def parse_trusted(spec: str) -> TrustedPeers:
    """Parse a comma-separated list of IPs, CIDRs, '*' or literal peer names."""
    trusted = TrustedPeers()
    for raw in (spec or "").split(","):
        token = raw.strip()
        if not token:
            continue
        if token == "*":
            trusted.everyone = True
            continue
        try:
            trusted.networks.append(ipaddress.ip_network(token, strict=False))
            continue
        except ValueError:
            pass
        if "/" in token:
            logger.warning("Ignoring malformed trusted network %r", token)
            continue
        trusted.literals.add(token)
    return trusted


def _header(scope, name: bytes) -> Optional[str]:
    for key, value in scope.get("headers", ()):
        if key.lower() == name:
            return value.decode("latin-1")
    return None


def _set_header(scope, name: bytes, value: str) -> None:
    headers = [(k, v) for k, v in scope.get("headers", ()) if k.lower() != name]
    headers.append((name, value.encode("latin-1")))
    scope["headers"] = headers


def _client_from_forwarded_for(value: str, trusted: TrustedPeers, raw_host: str) -> str:
    hops = [hop.strip() for hop in value.split(",") if hop.strip()]
    for hop in reversed(hops):
        if not trusted.contains(hop):
            return hop
    # Every hop is a trusted proxy: keep the raw peer rather than the first
    # entry (which the client itself may have forged).
    return raw_host


class ForwardedHeadersMiddleware:
    def __init__(self, app, trusted: TrustedPeers):
        self.app = app
        self.trusted = trusted

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return
        client = scope.get("client") or (None, 0)
        raw_host = client[0]
        state = scope.setdefault("state", {})
        state["peer"] = (raw_host, client[1] if len(client) > 1 else 0)
        state["forwarded"] = False

        if self.trusted.contains(raw_host):
            proto = _header(scope, b"x-forwarded-proto")
            if proto:
                proto = proto.split(",")[0].strip().lower()
                if proto in _ALLOWED_PROTOS:
                    scope["scheme"] = proto if scope["type"] == "http" else proto.replace("http", "ws")
                    state["forwarded"] = True
            forwarded_host = _header(scope, b"x-forwarded-host")
            if forwarded_host:
                _set_header(scope, b"host", forwarded_host.split(",")[0].strip())
                state["forwarded"] = True
            forwarded_for = _header(scope, b"x-forwarded-for")
            if forwarded_for:
                scope["client"] = (_client_from_forwarded_for(forwarded_for, self.trusted, raw_host), 0)
                state["forwarded"] = True
        await self.app(scope, receive, send)
