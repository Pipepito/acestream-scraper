"""
Outbound URL guard for user-supplied fetch targets (scrape URLs, EPG
sources) — SSRF protection (#149).

Behavior:
- Only http/https URLs are ever allowed.
- The cloud metadata endpoint (169.254.169.254) is always blocked.
- In strict mode (ALLOW_PRIVATE_SCRAPE_TARGETS=false), destinations that
  resolve to loopback, private, link-local, reserved, multicast or
  unspecified addresses are blocked — except the configured ZERONET_URL
  and IPFS_GATEWAY_URL hosts, which are legitimate local dependencies.
- The default is permissive (ALLOW_PRIVATE_SCRAPE_TARGETS=true): scraping
  LAN/localhost sources is a first-class use case for self-hosters. Flip it
  to false when exposing the app beyond a trusted network.

Callers follow HTTP redirects manually and re-validate every hop through
this guard. The check resolves the destination immediately before the
fetch, but does not pin the resolved IP into the actual connection, so a
hostile DNS server could still rebind between check and fetch in strict
deployments; treat strict mode as hardening, not a sandbox.
"""

import ipaddress
import logging
import os
import socket
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

METADATA_ADDRESSES = frozenset(
    ipaddress.ip_address(value) for value in ("169.254.169.254", "fd00:ec2::254")
)


def _canonical_address(address):
    """Unwrap IPv6-mapped IPv4 (::ffff:a.b.c.d) so literal-form tricks can't
    dodge the address checks."""
    mapped = getattr(address, "ipv4_mapped", None)
    return mapped if mapped is not None else address


class BlockedURLError(ValueError):
    """Raised when an outbound URL is not allowed to be fetched."""


def _allow_private_targets() -> bool:
    return os.environ.get("ALLOW_PRIVATE_SCRAPE_TARGETS", "true").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _exempt_hosts() -> set:
    hosts = set()
    for env_name in ("ZERONET_URL", "IPFS_GATEWAY_URL"):
        value = os.environ.get(env_name, "")
        if value:
            parsed = urlparse(value if "://" in value else f"http://{value}")
            if parsed.hostname:
                hosts.add(parsed.hostname.lower())
    return hosts


def _resolve_addresses(host: str):
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise BlockedURLError(f"Cannot resolve host '{host}': {exc}") from exc
    addresses = []
    for info in infos:
        try:
            addresses.append(ipaddress.ip_address(info[4][0]))
        except ValueError:
            continue
    if not addresses:
        raise BlockedURLError(f"Host '{host}' resolved to no usable addresses")
    return addresses


def validate_outbound_url(url: str) -> None:
    """Validate a user-supplied outbound fetch target.

    Raises BlockedURLError when the URL must not be fetched; returns None
    when the fetch may proceed.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise BlockedURLError(f"URL scheme '{parsed.scheme}' is not allowed for outbound fetches")
    host = parsed.hostname
    if not host:
        raise BlockedURLError("URL has no host")

    addresses = _resolve_addresses(host)

    addresses = [_canonical_address(address) for address in addresses]

    for address in addresses:
        if address in METADATA_ADDRESSES:
            raise BlockedURLError(
                f"Refusing to fetch '{url}': resolves to the cloud metadata endpoint"
            )

    if _allow_private_targets():
        return

    if host.lower() in _exempt_hosts():
        return

    for address in addresses:
        if (
            address.is_loopback
            or address.is_private
            or address.is_link_local
            or address.is_reserved
            or address.is_multicast
            or address.is_unspecified
        ):
            raise BlockedURLError(
                f"Refusing to fetch '{url}': resolves to non-public address {address} "
                "(set ALLOW_PRIVATE_SCRAPE_TARGETS=true to permit private targets)"
            )


def _lan_target_reason(address) -> Optional[str]:
    address = _canonical_address(address)
    if address in METADATA_ADDRESSES:
        return "the cloud metadata endpoint"
    if address.is_link_local:
        return "a link-local address"
    if address.is_multicast:
        return "a multicast address"
    if address.is_unspecified:
        return "an unspecified address"
    if address.is_reserved and not address.is_loopback:
        # IPv6 loopback (::1) falls inside the ::/8 IETF-reserved block, but
        # spec 4.4 allows loopback regardless of ALLOW_PRIVATE_SCRAPE_TARGETS.
        return "a reserved address"
    return None


def validate_lan_target(host: str, *, resolve: bool) -> None:
    """Validate a user-supplied LAN target (remote player host, media server).

    Private, loopback and global addresses are allowed regardless of
    ALLOW_PRIVATE_SCRAPE_TARGETS — talking to LAN devices is the feature.
    Metadata, link-local, multicast, unspecified and reserved addresses are
    always refused. With resolve=False only IP literals are checked; with
    resolve=True the host is resolved and every address is checked (call it
    immediately before each outbound request).
    """
    host = (host or "").strip().strip("[]")
    if not host:
        raise BlockedURLError("Target host is empty")
    try:
        candidates = [ipaddress.ip_address(host)]
    except ValueError:
        if not resolve:
            return
        candidates = _resolve_addresses(host)
    for address in candidates:
        reason = _lan_target_reason(address)
        if reason:
            raise BlockedURLError(f"Refusing to contact '{host}': resolves to {reason} ({_canonical_address(address)})")
