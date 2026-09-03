"""Find VLC/Kodi web interfaces on a private network (spec 6.1)."""
from __future__ import annotations

import asyncio
import ipaddress
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Union

import httpx

PRIVATE_SCAN_NETWORKS = tuple(
    ipaddress.ip_network(n)
    for n in ("10.0.0.0/8", "100.64.0.0/10", "172.16.0.0/12", "192.168.0.0/16", "fc00::/7")
)
MAX_ADDRESSES = 1024
MAX_PORTS = 8
_DOCKER_DESKTOP = ipaddress.ip_network("192.168.65.0/24")
_DOCKER_BRIDGE = ipaddress.ip_network("172.16.0.0/12")
_PROBE_TIMEOUT = httpx.Timeout(2.0, connect=1.0)
OUT_OF_TIME_HINT = "port is open, but the scan ran out of time before identifying it"


class ScanValidationError(ValueError):
    """A scan request the app refuses to run. ``code`` is the API error code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class ScanHit:
    host: str
    port: int
    kind: str  # vlc | kodi | unknown
    hint: str


@dataclass
class ScanOutcome:
    hits: List[ScanHit] = field(default_factory=list)
    scanned: int = 0
    duration_ms: int = 0


IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]


def validate_scan_request(cidr: str, ports: List[int]) -> Tuple[IPNetwork, List[int]]:
    try:
        network = ipaddress.ip_network(cidr.strip(), strict=False)
    except ValueError as exc:
        raise ScanValidationError("SCAN_CIDR_NOT_PRIVATE", f"{cidr!r} is not a valid network") from exc
    if not any(network.subnet_of(private) for private in PRIVATE_SCAN_NETWORKS if private.version == network.version):
        raise ScanValidationError(
            "SCAN_CIDR_NOT_PRIVATE",
            "Only private networks can be scanned (10/8, 100.64/10, 172.16/12, 192.168/16, fc00::/7)",
        )
    if network.num_addresses > MAX_ADDRESSES:
        raise ScanValidationError(
            "SCAN_TOO_LARGE", f"Scan at most {MAX_ADDRESSES} addresses at a time (a /22 or smaller)"
        )
    unique_ports = list(dict.fromkeys(int(p) for p in ports))
    if not unique_ports or len(unique_ports) > MAX_PORTS or any(p < 1 or p > 65535 for p in unique_ports):
        raise ScanValidationError("SCAN_TOO_LARGE", f"ports must be 1-65535, at most {MAX_PORTS}")
    return network, unique_ports


def default_scan_cidr(client_ip: Optional[str]) -> Optional[str]:
    """The /24 around the caller, when that address says anything useful.
    Loopback and Docker gateways say nothing about the user's LAN."""
    try:
        address = ipaddress.ip_address((client_ip or "").strip("[]"))
    except ValueError:
        return None
    mapped = getattr(address, "ipv4_mapped", None)
    address = mapped if mapped is not None else address
    if address.version != 4 or address.is_loopback or address in _DOCKER_DESKTOP:
        return None
    if address in _DOCKER_BRIDGE and str(address).endswith(".1"):
        return None
    if not any(address in n for n in PRIVATE_SCAN_NETWORKS if n.version == 4):
        return None
    return str(ipaddress.ip_network(f"{address}/24", strict=False))


def _out_of_time(deadline: Optional[float]) -> bool:
    return deadline is not None and time.monotonic() >= deadline


async def _tcp_open(host: str, port: int, timeout: float) -> bool:
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=timeout)
    except (OSError, asyncio.TimeoutError):
        return False
    writer.close()
    return True


def classify(host: str, port: int, client: httpx.Client, deadline: Optional[float] = None) -> ScanHit:
    """VLC answers 401/403/JSON on /requests/status.json; Kodi answers 401 or a
    JSON-RPC body on /jsonrpc. Kodi's Basic realm keeps it out of the VLC branch.

    ``deadline`` is a ``time.monotonic()`` stamp: once it has passed, the port is
    reported as unidentified instead of spending more HTTP requests on it."""
    if _out_of_time(deadline):
        return ScanHit(host=host, port=port, kind="unknown", hint=OUT_OF_TIME_HINT)
    base = f"http://{host}:{port}"
    try:
        response = client.get(f"{base}/requests/status.json")
        looks_like_vlc_auth = (
            response.status_code in (401, 403)
            and "kodi" not in response.headers.get("WWW-Authenticate", "").lower()
        )
        if looks_like_vlc_auth or (response.status_code == 200 and "apiversion" in response.text):
            if response.status_code == 403:
                hint = "web interface has no password"
            elif response.status_code == 401:
                hint = "password required"
            else:
                hint = "open"
            return ScanHit(host=host, port=port, kind="vlc", hint=hint)
    except httpx.HTTPError:
        pass
    if _out_of_time(deadline):
        return ScanHit(host=host, port=port, kind="unknown", hint=OUT_OF_TIME_HINT)
    try:
        response = client.post(
            f"{base}/jsonrpc", json={"jsonrpc": "2.0", "id": 1, "method": "JSONRPC.Ping"}
        )
        if response.status_code == 401 or (response.status_code == 200 and '"pong"' in response.text):
            return ScanHit(
                host=host,
                port=port,
                kind="kodi",
                hint="password required" if response.status_code == 401 else "open",
            )
    except httpx.HTTPError:
        pass
    return ScanHit(host=host, port=port, kind="unknown", hint="something answers on this port")


async def scan_network(
    network: IPNetwork,
    ports: List[int],
    timeout_ms: int = 400,
    concurrency: int = 128,
    budget_s: float = 30.0,
    client_factory: Optional[Callable[[], httpx.Client]] = None,
) -> ScanOutcome:
    started = time.monotonic()
    deadline = started + budget_s
    semaphore = asyncio.Semaphore(concurrency)
    timeout = max(0.05, timeout_ms / 1000)
    hosts = [
        str(a) for a in (network.hosts() if network.num_addresses > 2 else [network.network_address])
    ]
    outcome = ScanOutcome()

    async def check(host: str, port: int):
        # The deadline is checked after the semaphore, not before: every queued
        # coroutine runs its first step in the same loop iteration, so a check
        # ahead of the semaphore is always made while the budget is still whole.
        async with semaphore:
            if _out_of_time(deadline):
                return None
            outcome.scanned += 1
            return (host, port) if await _tcp_open(host, port, timeout) else None

    results = await asyncio.gather(*(check(h, p) for h in hosts for p in ports))
    open_ports = [r for r in results if r]
    factory = client_factory or (
        lambda: httpx.Client(follow_redirects=False, timeout=_PROBE_TIMEOUT)
    )
    if open_ports:
        with factory() as client:
            outcome.hits = list(
                await asyncio.gather(
                    *(asyncio.to_thread(classify, h, p, client, deadline) for h, p in open_ports)
                )
            )
    outcome.duration_ms = int((time.monotonic() - started) * 1000)
    return outcome
