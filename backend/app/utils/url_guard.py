"""
Outbound URL guard for user-supplied fetch targets (scrape URLs, EPG
sources) — SSRF protection (#149).

Behavior:
- Only http/https URLs are ever allowed.
- The cloud metadata endpoint (169.254.169.254) is always blocked.
- In strict mode (ALLOW_PRIVATE_SCRAPE_TARGETS=false), destinations that
  resolve to loopback, private, link-local, reserved, multicast or
  unspecified addresses are blocked — except the configured ZERONET_URL
  host, which is a legitimate local dependency.
- The default is permissive (ALLOW_PRIVATE_SCRAPE_TARGETS=true): scraping
  LAN/localhost sources is a first-class use case for self-hosters. Flip it
  to false when exposing the app beyond a trusted network.

The check resolves the destination immediately before the fetch. It does
not pin the resolved IP into the actual connection, so a hostile DNS server
could still rebind between check and fetch in strict deployments; treat
strict mode as hardening, not a sandbox.
"""

import ipaddress
import logging
import os
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

METADATA_ADDRESSES = {"169.254.169.254", "fd00:ec2::254"}


class BlockedURLError(ValueError):
    """Raised when an outbound URL is not allowed to be fetched."""


def _allow_private_targets() -> bool:
    return os.environ.get("ALLOW_PRIVATE_SCRAPE_TARGETS", "true").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _exempt_hosts() -> set:
    hosts = set()
    zeronet = os.environ.get("ZERONET_URL", "")
    if zeronet:
        parsed = urlparse(zeronet if "://" in zeronet else f"http://{zeronet}")
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

    for address in addresses:
        if str(address) in METADATA_ADDRESSES:
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
