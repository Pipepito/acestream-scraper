"""Relay engine MPEG-TS bytes to a client (spec 4.2).

- ClosingStreamingResponse guarantees the body generator's ``finally`` runs
  as soon as the client goes away (Starlette itself never calls aclose()).
- relay_engine_stream starts an engine session, follows the engine's own
  302 (only while the stream stays on the engine host -- every loopback
  spelling and port being one host), streams 64 KiB chunks and stops the
  session on every exit path.
"""
from __future__ import annotations

import ipaddress
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Dict, List, Optional
from urllib.parse import urlsplit

import anyio
import httpx
from fastapi.concurrency import run_in_threadpool
from starlette.responses import StreamingResponse
from starlette.types import Receive, Scope, Send

from app.services.engine_client import EngineClient, EngineSession

logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024
RELAY_HEADERS = {"Content-Type": "video/mp2t", "Cache-Control": "no-store", "X-Accel-Buffering": "no"}
RELAY_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)


class EngineStreamError(RuntimeError):
    """The engine session started but its byte stream failed.

    Covers a refused stream (wrong host, non-200) and any transport failure
    while opening or reading it, so the route has one engine-stream error to
    map onto 502 instead of a bare ``httpx`` exception.
    """


class ClosingStreamingResponse(StreamingResponse):
    """StreamingResponse that always closes its body generator.

    Starlette drops the iterator when the client disconnects, so a relay's
    ``finally`` (which stops the engine session) would only run whenever the
    garbage collector got round to it. Closing it here — shielded, so a
    cancellation in flight cannot interrupt the cleanup — makes the stop
    deterministic.
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        try:
            await super().__call__(scope, receive, send)
        finally:
            aclose = getattr(self.body_iterator, "aclose", None)
            if aclose is not None:
                with anyio.CancelScope(shield=True):
                    try:
                        await aclose()
                    except Exception:  # noqa: BLE001 - cleanup must never raise into the server
                        logger.exception("Relay generator close failed")


@dataclass
class RelayInfo:
    id: str
    content_id: str
    client_label: str
    started_at: float
    bytes_sent: int = 0
    finished_at: Optional[float] = None


class RelayRegistry:
    """In-memory book of the relays this process is serving."""

    def __init__(self) -> None:
        self._relays: Dict[str, RelayInfo] = {}

    def open(self, content_id: str, client_label: str) -> RelayInfo:
        info = RelayInfo(id=uuid.uuid4().hex, content_id=content_id, client_label=client_label, started_at=time.time())
        self._relays[info.id] = info
        return info

    def close(self, relay_id: str) -> None:
        info = self._relays.get(relay_id)
        if info is not None and info.finished_at is None:
            info.finished_at = time.time()

    def active(self) -> List[RelayInfo]:
        # Snapshot first: relays open and close on the event loop while the
        # reaper may run from a scheduler thread.
        return [info for info in list(self._relays.values()) if info.finished_at is None]

    def count_active(self) -> int:
        return len(self.active())

    def reap_finished(self, older_than_seconds: float = 30.0) -> int:
        """Forget relays that finished more than ``older_than_seconds`` ago."""
        cutoff = time.time() - older_than_seconds
        stale = [rid for rid, info in list(self._relays.items()) if info.finished_at is not None and info.finished_at <= cutoff]
        return sum(1 for rid in stale if self._relays.pop(rid, None) is not None)


relay_registry = RelayRegistry()


_LOOPBACK = "<loopback>"


def _host_identity(host: Optional[str]) -> str:
    """Normalise a host for the engine-host guard.

    Every loopback spelling is one identity: the engine reports its playback
    URL on its own loopback address and, on the ARM (Android) build, on its
    own port -- ``http://127.0.0.1:36879/ace/r/...`` while ``ACE_ENGINE_URL``
    is ``http://localhost:6878``. Comparing the literal host strings would
    refuse every relay of the default deployment. Any other host is compared
    by name (case- and trailing-dot-insensitive), IP literals by value, so a
    redirect that leaves the engine is still refused -- including one that
    points at *our own* loopback when the engine is a remote host.
    """
    if not host:
        return ""
    name = host.strip().strip("[]").rstrip(".").lower()
    if name == "localhost":
        return _LOOPBACK
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        return name
    return _LOOPBACK if address.is_loopback else address.compressed


def _default_client_factory(**kwargs: Any) -> httpx.AsyncClient:
    return httpx.AsyncClient(**kwargs)


async def relay_engine_stream(
    engine: EngineClient,
    content_id: str,
    client_label: str,
    *,
    client_factory: Optional[Callable[..., httpx.AsyncClient]] = None,
    registry: Optional[RelayRegistry] = None,
) -> AsyncIterator[bytes]:
    """Yield MPEG-TS bytes for ``content_id``.

    The first iteration raises before a byte is written: EngineUnavailableError
    / EngineRefusedError from the session start, EngineStreamError when the
    stream is refused (off-host, non-200) or fails at the transport level
    (connect refused, read timeout, redirect loop). A transport failure later
    in the stream raises EngineStreamError as well. The engine session is
    stopped on every exit path.
    """
    registry = registry or relay_registry
    factory = client_factory or _default_client_factory
    session: EngineSession = await run_in_threadpool(engine.start, content_id)
    info = registry.open(content_id, client_label)
    engine_host = _host_identity(urlsplit(engine.engine_url).hostname)
    try:
        try:
            async with factory(follow_redirects=True, max_redirects=3, timeout=RELAY_TIMEOUT) as client:
                async with client.stream("GET", session.playback_url) as response:
                    if _host_identity(response.url.host) != engine_host:
                        raise EngineStreamError(f"Engine stream left the engine host: {response.url.host}")
                    if response.status_code != 200:
                        raise EngineStreamError(f"Engine stream returned HTTP {response.status_code}")
                    async for chunk in response.aiter_bytes(CHUNK_SIZE):
                        info.bytes_sent += len(chunk)
                        yield chunk
        except (httpx.HTTPError, httpx.InvalidURL) as exc:
            # Connect refused, read timeout, too many redirects, an unusable
            # playback_url: the route needs EngineStreamError to answer 502.
            raise EngineStreamError(f"Engine stream failed: {exc}") from exc
    finally:
        registry.close(info.id)
        with anyio.CancelScope(shield=True):
            await run_in_threadpool(engine.stop, session)
