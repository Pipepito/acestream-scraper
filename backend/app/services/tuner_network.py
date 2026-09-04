"""Network allowlist for the token-free /tuner/* routes (spec 4.4)."""
from __future__ import annotations

import ipaddress
import logging
import time
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from typing import Deque, List, Literal, Optional

from fastapi import Request

from app.api.error_handlers import APIError
from app.config.settings import get_settings
from app.middleware.forwarded import TrustedPeers, parse_trusted

logger = logging.getLogger(__name__)

ClientSource = Literal["direct", "forwarded", "docker-gateway", "loopback"]
_DOCKER_DESKTOP = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")
# Denials are logged once per client address; the memo is bounded so a scan
# from many source addresses cannot grow it without limit.
_WARNED_CLIENTS = 64


@dataclass
class Denial:
    client_ip: str
    peer: str
    path: str
    at: float


class TunerNetworkGate:
    """Decides whether an address may use the tuner routes, and remembers refusals."""

    def __init__(self, allowed_spec: str):
        self.allowed_spec = allowed_spec
        self._trusted: TrustedPeers = parse_trusted(allowed_spec)
        self._denials: Deque[Denial] = deque(maxlen=20)
        self._warned: Deque[str] = deque(maxlen=_WARNED_CLIENTS)

    @property
    def allowed_networks(self) -> List[str]:
        return [token.strip() for token in self.allowed_spec.split(",") if token.strip()]

    def is_allowed(self, host: Optional[str]) -> bool:
        return self._trusted.contains(host)

    def record_denial(self, client_ip: str, peer: str, path: str) -> None:
        self._denials.appendleft(Denial(client_ip=client_ip, peer=peer, path=path, at=time.time()))
        if client_ip not in self._warned:
            self._warned.append(client_ip)
            logger.warning(
                "Tuner request from %s (peer %s) denied by TUNER_ALLOWED_NETWORKS=%s", client_ip, peer, self.allowed_spec
            )

    def recent_denials(self) -> List[Denial]:
        """The last 20 denials, newest first."""
        return list(self._denials)

    @staticmethod
    def classify_source(peer: Optional[str], forwarded: bool) -> ClientSource:
        """How this process sees the client. ``docker-gateway`` and ``loopback``
        mean the allowlist cannot tell real clients apart (spec 4.4)."""
        if forwarded:
            return "forwarded"
        try:
            address = ipaddress.ip_address((peer or "").strip("[]"))
        except ValueError:
            return "direct"
        mapped = getattr(address, "ipv4_mapped", None)
        address = mapped if mapped is not None else address
        if address.is_loopback:
            return "loopback"
        if address in _DOCKER_DESKTOP:
            return "docker-gateway"
        if address in _DOCKER_BRIDGE and str(address).endswith(".1"):
            return "docker-gateway"
        return "direct"


@lru_cache(maxsize=1)
def get_tuner_gate() -> TunerNetworkGate:
    """The process-wide gate. Cached so the denial ring buffer survives requests;
    tests drop it with ``get_tuner_gate.cache_clear()`` after changing the env."""
    return TunerNetworkGate(get_settings().TUNER_ALLOWED_NETWORKS)


async def require_tuner_network(request: Request) -> None:
    """Both the raw peer and the (possibly forwarded) client must be allowed:
    a LAN host spoofing X-Forwarded-For fails on the peer, a trusted proxy
    forwarding a public client fails on the forwarded address."""
    gate = get_tuner_gate()
    peer = (getattr(request.state, "peer", None) or (None, 0))[0]
    client_ip = request.client.host if request.client else None
    if gate.is_allowed(peer) and gate.is_allowed(client_ip):
        return
    gate.record_denial(client_ip or "?", peer or "?", request.url.path)
    raise APIError(
        code="TUNER_NETWORK_DENIED",
        message="This address is not allowed to use the tuner routes (TUNER_ALLOWED_NETWORKS)",
        status_code=403,
        context={"client_ip": client_ip, "peer": peer, "allowed_networks": gate.allowed_networks},
    )
