"""The stream check's conversation with the engine (the ``ProbeEngine`` seam).

A check starts a session with its own PID, reads its statistics, and gives the
session back. The answers stay close to the engine's: telling "found" from
"not found", a live download from a prebuffer, or online from offline is the
check's job (``channel_status_service``), not this module's.

``AiohttpProbeEngine`` is the real adapter. Every request is one aiohttp
session with a total timeout and no redirects. Session URLs the engine hands
back are re-rooted on the configured engine (a remote engine advertises
localhost) and must match the engine's own session routes; anything else is
never requested. Tests use an in-memory engine at this seam
(``tests/fake_probe_engine.py``). Whether a session may be stopped at all
is decided by its source's ownership (``playback_ownership``), not here.
"""
from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol
from urllib.parse import urlparse

import aiohttp

from app.utils.engine_url import ENGINE_API_PATH, ENGINE_START_PATH, ENGINE_STATUS_PARAMS

logger = logging.getLogger(__name__)

READY_TIMEOUT = 3.0
STOP_TIMEOUT = 3.0


class StatsUnreadable(Exception):
    """No usable statistics answer: not HTTP 200, not JSON, or not an object."""


class StatsRefused(Exception):
    """The engine answered the statistics request with an ``error`` or no ``response``."""


@dataclass(frozen=True)
class ProbeSession:
    """What the engine handed back for one check session.

    A URL that is not one of the engine's session routes is ``None``. The
    session must be given back whenever ``command_url`` is set, even if the
    rest is unusable.
    """
    content_id: str
    stat_url: Optional[str]
    command_url: Optional[str]
    playback_url: Optional[str]
    playback_session_id: Any = None

    @property
    def verifiable(self) -> bool:
        return bool(self.stat_url and self.command_url)

    @property
    def stat_token(self) -> str:
        return (self.stat_url or '').rsplit('/', 1)[-1]


@dataclass(frozen=True)
class ProbeStart:
    """The engine's answer to a check's start request."""
    http_status: int
    # HTTP 200 with a JSON object. Anything else is answered by status alone.
    readable: bool
    # The engine's ``error`` field, as sent (None when absent or unreadable).
    error: Any = None
    # Present when the answer carried a ``response`` object.
    session: Optional[ProbeSession] = None


class ProbeEngine(Protocol):
    """One engine as the stream check sees it.

    Errors: ``open_probe`` and ``stats`` raise ``asyncio.TimeoutError`` past
    their timeout and let transport errors through; ``stats`` raises
    ``StatsUnreadable``/``StatsRefused`` for an unusable answer. ``ready``
    never raises for a timeout or a transport error: it answers False.
    ``stop`` ends the session unconditionally (the caller has already
    decided, under the source's ownership lock, that it may) and may raise.
    """
    engine_url: str

    async def ready(self) -> bool: ...

    async def open_probe(self, content_id: str, identifier: str, pid: str, timeout: float) -> ProbeStart: ...

    async def stats(self, session: ProbeSession, timeout: float) -> Dict[str, Any]: ...

    async def stop(self, session: ProbeSession) -> None: ...


def session_url(engine_url: str, value: Any, kind: str) -> Optional[str]:
    """Keep session requests on the configured engine, including remote engines
    which advertise localhost URLs. Never follow arbitrary upstream targets.
    """
    if not isinstance(value, str):
        return None
    path = urlparse(value).path
    if not re.fullmatch(rf"/ace/{kind}/(?:cid:[a-fA-F0-9]{{40}}|[a-zA-Z0-9_-]+)/[a-zA-Z0-9_-]+", path):
        return None
    return f"{engine_url}{path}"


def read_start(engine_url: str, content_id: str, http_status: int, payload: Any) -> ProbeStart:
    """A start answer as the check reads it. ``payload`` is the parsed JSON, or
    None when the answer was not HTTP 200 or not JSON."""
    if http_status != 200 or not isinstance(payload, dict):
        return ProbeStart(http_status, readable=False)
    response = payload.get('response')
    session = None
    if isinstance(response, dict):
        session = ProbeSession(
            content_id=content_id,
            stat_url=session_url(engine_url, response.get('stat_url'), 'stat'),
            command_url=session_url(engine_url, response.get('command_url'), 'cmd'),
            playback_url=session_url(engine_url, response.get('playback_url'), 'r'),
            playback_session_id=response.get('playback_session_id'),
        )
    return ProbeStart(http_status, readable=True, error=payload.get('error'), session=session)


def read_stats(http_status: int, payload: Any) -> Dict[str, Any]:
    """The ``response`` object of a statistics answer, or the reason there is none."""
    if http_status != 200 or not isinstance(payload, dict):
        raise StatsUnreadable()
    state = payload.get('response')
    if payload.get('error') or not isinstance(state, dict):
        raise StatsRefused()
    return state


def read_ready(http_status: int, payload: Any) -> bool:
    return (http_status == 200 and isinstance(payload, dict) and isinstance(payload.get('result'), dict)
            and not payload.get('error'))


class AiohttpProbeEngine:
    """The real engine, over aiohttp."""

    def __init__(self, engine_url: str):
        self.engine_url = engine_url

    @staticmethod
    async def _get(url: str, params: Dict[str, str], timeout: float):
        """One request. Returns (http_status, parsed JSON or None). Raises
        asyncio.TimeoutError on timeout."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout),
                allow_redirects=False,
            ) as response:
                if response.status != 200:
                    return response.status, None
                try:
                    return response.status, await response.json()
                except Exception:
                    return response.status, None

    async def ready(self) -> bool:
        try:
            status, payload = await self._get(f"{self.engine_url}{ENGINE_API_PATH}", dict(ENGINE_STATUS_PARAMS), READY_TIMEOUT)
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False
        return read_ready(status, payload)

    async def open_probe(self, content_id: str, identifier: str, pid: str, timeout: float) -> ProbeStart:
        params = {identifier: content_id, 'format': 'json', 'pid': pid}
        status, payload = await self._get(f"{self.engine_url}{ENGINE_START_PATH}", params, timeout)
        return read_start(self.engine_url, content_id, status, payload)

    async def stats(self, session: ProbeSession, timeout: float) -> Dict[str, Any]:
        status, payload = await self._get(session.stat_url, {}, timeout)
        return read_stats(status, payload)

    async def stop(self, session: ProbeSession) -> None:
        await self._get(session.command_url, {'method': 'stop'}, STOP_TIMEOUT)
