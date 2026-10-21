"""Thin client for the AceStream engine playback API (spec 4.1).

Used by the stream relay (tuner, remote players) and the web player. The
engine URL is the DB setting ``ace_engine_url`` read at call time.
"""
from __future__ import annotations

import asyncio
import logging
import time
from threading import Timer
import uuid
from dataclasses import dataclass, field
from types import TracebackType
from typing import Callable, Optional, TypeVar
from urllib.parse import urlsplit

import anyio
import httpx
from fastapi.concurrency import run_in_threadpool

from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import PlaybackRouting
from app.services.playback_ownership import PlaybackLease, source_ownership

logger = logging.getLogger(__name__)

_Result = TypeVar("_Result")

START_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
STAT_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


class EngineUnavailableError(RuntimeError):
    """The engine could not be reached or answered with a transport/5xx error."""


class EngineRefusedError(RuntimeError):
    """The engine answered but refused (its JSON carried an ``error``)."""


@dataclass(frozen=True)
class EngineSession:
    content_id: str
    pid: str
    playback_url: str
    stat_url: str
    command_url: str
    is_live: bool
    managed_by_acexy: bool = False
    lease: Optional[PlaybackLease] = field(default=None, compare=False, repr=False)


@dataclass(frozen=True)
class EngineStats:
    status: str
    peers: int
    speed_down: int
    speed_up: int


def new_pid() -> str:
    return uuid.uuid4().hex


def _engine_target(value: object, field: str) -> str:
    """One absolute http(s) URL out of the engine's start response.

    The engine is trusted infrastructure and stays trusted for *where* it
    serves a stream from -- which host may answer is the relay's check, made on
    the final post-redirect URL where it can actually be enforced. What is
    checked here is the shape: these three strings are handed to ffmpeg's -i
    and to httpx verbatim, and ffmpeg's input is not limited to HTTP
    ("file:", "concat:", "subfile:"), so a wrong or tampered-with engine answer
    could turn playback into a local-file read re-streamed to the viewer. A
    non-http(s) value is also simply unusable, so refusing it names the fault
    instead of leaving ffmpeg to fail obscurely a moment later.
    """
    url = str(value)
    try:
        parts = urlsplit(url)
    except ValueError as exc:  # e.g. an unbalanced IPv6 bracket
        raise EngineUnavailableError(f"Engine returned an unusable {field}: {url!r}") from exc
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise EngineUnavailableError(f"Engine returned a {field} that is not an http(s) URL: {url!r}")
    return url


def engine_url_from_settings(settings_repo: SettingsRepository) -> str:
    url = (settings_repo.get_setting(SettingsRepository.ACE_ENGINE_URL) or "").strip()
    if not url:
        raise EngineUnavailableError("Acestream Engine URL is not configured")
    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"
    return url.rstrip("/")


def playback_client_from_settings(settings_repo: SettingsRepository) -> "EngineClient":
    routing = PlaybackRouting.model_validate_json(settings_repo.get_setting(SettingsRepository.PLAYBACK_ROUTING))
    if routing.use_acexy:
        return EngineClient(routing.acexy_url, use_acexy=True)
    return EngineClient(engine_url_from_settings(settings_repo))


class EngineClient:
    """Talks to one engine over HTTP.

    When no ``client`` is injected the instance creates — and therefore owns —
    an :class:`httpx.Client`; use it as a context manager (or call
    :meth:`close`) so its connection pool is released. An injected client is
    never closed here: whoever opened it closes it.
    """

    def __init__(self, engine_url: str, client: Optional[httpx.Client] = None, *, use_acexy: bool = False):
        self.engine_url = engine_url.rstrip("/")
        self.use_acexy = use_acexy
        self._owns_client = client is None
        self._client = client or httpx.Client(timeout=START_TIMEOUT)

    def close(self) -> None:
        """Release the connection pool, but only if this instance created it."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "EngineClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def _get_json(self, url: str, params: Optional[dict] = None, timeout: httpx.Timeout = START_TIMEOUT) -> dict:
        try:
            response = self._client.get(url, params=params, timeout=timeout)
        except httpx.HTTPError as exc:
            raise EngineUnavailableError(f"Engine request failed: {exc}") from exc
        if response.status_code >= 500:
            raise EngineUnavailableError(f"Engine returned HTTP {response.status_code}")
        try:
            payload = response.json()
        except ValueError as exc:
            raise EngineUnavailableError("Engine returned a non-JSON response") from exc
        error = payload.get("error") if isinstance(payload, dict) else None
        if error:
            raise EngineRefusedError(str(error))
        body = payload.get("response") if isinstance(payload, dict) else None
        if not isinstance(body, dict):
            raise EngineUnavailableError("Engine response has no 'response' object")
        return body

    def start(self, content_id: str, pid: Optional[str] = None, *, startup_deadline: Optional[float] = None) -> EngineSession:
        if self.use_acexy:
            # Acexy owns multiplexing and engine sessions. Reading/closing this
            # stream is its lifecycle; never send JSON/start/stop or a PID.
            url = str(httpx.URL(f"{self.engine_url}/ace/getstream", params={"id": content_id}))
            return EngineSession(content_id, "", url, "", "", True, managed_by_acexy=True)
        source = source_ownership(self.engine_url, content_id)
        remaining = _remaining_start_seconds(startup_deadline)
        if not source.lock.acquire(timeout=remaining):
            raise EngineUnavailableError("Engine startup deadline expired waiting for the source")
        try:
            # A stop deferred by the TV relay is cancelled: the engine is
            # still running this source. Its session is parked and stopped
            # with the source's final stop.
            deferred, source.pending_stop = source.pending_stop, None
            if deferred is not None:
                deferred.cancel()
                source.parked.append(deferred.args[1])
            lease = PlaybackLease(source)
            try:
                session = self._start_direct(content_id, pid or new_pid(), lease, startup_deadline)
            except BaseException:
                if not source.leases:
                    _stop_parked(source, self._client)
                raise
            source.leases.add(lease)
            if startup_deadline is not None and time.monotonic() >= startup_deadline:
                # HTTP phase timeouts can finish just after the overall budget.
                # Own and release the handle before reporting the expired start.
                self.stop(session)
                raise EngineUnavailableError("Engine startup deadline expired")
            return session
        finally:
            source.lock.release()

    def _start_direct(self, content_id: str, pid: str, lease: PlaybackLease, startup_deadline: Optional[float]) -> EngineSession:
        remaining = _remaining_start_seconds(startup_deadline)
        body = self._get_json(
            f"{self.engine_url}/ace/getstream",
            params={"id": content_id, "pid": pid, "format": "json"},
            timeout=httpx.Timeout(remaining, connect=min(START_TIMEOUT.connect, remaining)),
        )
        try:
            return EngineSession(
                content_id=content_id,
                pid=pid,
                lease=lease,
                playback_url=_engine_target(body["playback_url"], "playback_url"),
                stat_url=_engine_target(body["stat_url"], "stat_url"),
                command_url=_engine_target(body["command_url"], "command_url"),
                is_live=bool(int(body.get("is_live") or 0)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EngineUnavailableError(f"Engine start response is incomplete: {body}") from exc

    def stop(self, session: EngineSession, *, linger_seconds: float = 0) -> None:
        """Release the session; the engine stops with the last lease.

        ``linger_seconds`` defers that final stop: Kodi opens a channel with
        two GETs and closes the first, and stopping in between made the
        second start cold (measured: 1.8 s on an amd64 bench, 3.2 s on an ARM box).
        A start of the same source within the delay cancels the stop.
        """
        if session.managed_by_acexy:
            return
        if session.lease is None:
            # Compatibility for injected clients / pre-existing session handles.
            self._stop_direct(session)
            return
        lease = session.lease
        source = lease.source
        with source.lock:
            if lease.released:
                return
            lease.released = True
            source.leases.discard(lease)
            if source.leases:
                # Another client still plays this source: its session stays
                # until then, and is stopped with the source's final stop.
                # Dropped here, it was never stopped at all (Kodi's two GETs
                # overlapping).
                source.parked.append(session)
                return
            if linger_seconds <= 0:
                self._stop_direct(session)
                _stop_parked(source, self._client)
                return
            timer = Timer(linger_seconds, _deferred_stop, args=(source, session))
            timer.daemon = True
            source.pending_stop = timer
            timer.start()

    def _stop_direct(self, session: EngineSession) -> None:
        _send_stop(self._client, session)

    def stat(self, session: EngineSession) -> Optional[EngineStats]:
        if session.managed_by_acexy:
            return None
        body = self._get_json(session.stat_url, timeout=STAT_TIMEOUT)
        return EngineStats(
            status=str(body.get("status") or "unknown"),
            peers=int(body.get("peers") or 0),
            speed_down=int(body.get("speed_down") or 0),
            speed_up=int(body.get("speed_up") or 0),
        )


def _remaining_start_seconds(deadline: Optional[float]) -> float:
    if deadline is None:
        return START_TIMEOUT.read
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise EngineUnavailableError("Engine startup deadline expired")
    return remaining


async def start_engine_session(
    start: Callable[[], EngineSession], stop: Callable[[EngineSession], None],
) -> EngineSession:
    """Keep ownership of a blocking start even if its consumer is cancelled.

    A worker cannot be interrupted safely. Wait for its bounded request and
    release any late session before the caller closes its client/relay slot.
    Both callbacks run off the event loop; stop uses the original session lease.
    """
    async def finish(task: asyncio.Task[_Result]) -> _Result:
        # A native asyncio cancellation can arrive again during shielded
        # cleanup (disconnect followed by shutdown). Keep the worker owned.
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
        return task.result()

    worker = asyncio.create_task(run_in_threadpool(start))
    try:
        return await asyncio.shield(worker)
    except asyncio.CancelledError:
        with anyio.CancelScope(shield=True):
            try:
                session = await finish(worker)
            except Exception:
                pass  # Preserve the caller's cancellation if startup also failed.
            else:
                cleanup = asyncio.create_task(run_in_threadpool(stop, session))
                try:
                    await finish(cleanup)
                except Exception:
                    # Never convert a disconnect into a retryable start failure.
                    logger.warning("Engine session cleanup failed after cancelled startup")
        raise


def _deferred_stop(source, session: EngineSession) -> None:
    """The final stop a TV relay deferred, unless the source was started again."""
    with source.lock:
        # Timer.cancel() cannot recall a callback already waiting on this lock.
        # It must still own the pending session, not a replacement's timer.
        if (source.pending_stop is None or source.leases
                or source.pending_stop.args[1] is not session):
            return
        source.pending_stop = None
        _stop_now(session)
        _stop_parked(source)


def _stop_parked(source, client: Optional[httpx.Client] = None) -> None:
    parked, source.parked = source.parked, []
    for session in parked:
        if client is None:
            _stop_now(session)
        else:
            _send_stop(client, session)


def _stop_now(session: EngineSession) -> None:
    # The client that started the session may be closed by now.
    with httpx.Client(timeout=STAT_TIMEOUT) as client:
        _send_stop(client, session)


def _send_stop(client: httpx.Client, session: EngineSession) -> None:
    # Merge rather than replace: the engine may hand back a command_url
    # that already carries a token or session id in its query.
    url = httpx.URL(session.command_url).copy_merge_params({"method": "stop"})
    try:
        client.get(url, timeout=STAT_TIMEOUT)
    except httpx.HTTPError as exc:
        logger.warning("Engine stop for %s failed: %s", session.content_id, exc)
