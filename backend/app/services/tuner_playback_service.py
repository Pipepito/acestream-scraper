"""Bounded source selection with opt-in experimental transcoding recovery."""
from __future__ import annotations

from collections import OrderedDict
import threading
import asyncio
import logging
import time
from typing import AsyncIterator, Awaitable, Callable

import anyio
import httpx

from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError
from app.services.stream_relay import EngineStreamError, RelayInfo, RelayRegistry, relay_engine_stream, relay_registry
from app.services.tuner_remux import remux_source, compatible_audio_source
from app.services.tuner_http_source import relay_http_stream

STARTUP_BUDGET_SECONDS = 45.0
ATTEMPT_SECONDS = 15.0
# A healthy source can be silent for over 16 s: the engine hands over whole
# pieces (~1.5 MB), so a low-bitrate source arrives in bursts. Measured on a
# live engine: a source at 97 kB/s had 19 gaps of 12 s or more in 5 minutes,
# the longest 16.4 s, and a 15 s stall timeout cut it; a source at 458 kB/s
# was never silent for more than 4.6 s. 25 s is above the longest gap seen.
STALL_SECONDS = 25.0
HEALTHY_SECONDS = 30.0
# Kodi opens a channel with two GETs and closes the first one; the engine
# session outlives a closed client this long, so the second GET finds the
# source still running instead of starting it cold (measured: 1.8 s more on
# an amd64 bench, 3.2 s on an ARM box).
STOP_LINGER_SECONDS = 5.0
# An engine session that ends with no byte at all this soon is retried once
# before the source counts as failed. Seen with Kodi (intermittent): its
# second GET joined a source whose first reader had just left, the engine
# answered 200 and closed at once, and with a single source the channel
# failed. Only when no other candidate is left: otherwise the next source
# goes first.
EMPTY_START_RETRY_SECONDS = 3.0
logger = logging.getLogger(__name__)

# Short, bounded process-local memory prevents reconnects picking a known failure
# ahead of healthy alternatives. It does not overwrite verified DB probe results.
_failures: OrderedDict[str, float] = OrderedDict()
_failure_lock = threading.Lock()
FAILURE_COOLDOWN_SECONDS = 60.0


def record_source_failure(content_id: str) -> None:
    with _failure_lock:
        _failures[content_id] = time.monotonic()
        _failures.move_to_end(content_id)
        while len(_failures) > 4096:
            _failures.popitem(last=False)


def prefer_recovered_sources(content_ids: list[str]) -> list[str]:
    with _failure_lock:
        now = time.monotonic()
        for cid, failed_at in list(_failures.items()):
            if now - failed_at >= FAILURE_COOLDOWN_SECONDS:
                del _failures[cid]
        return sorted(content_ids, key=lambda cid: (cid in _failures, _failures.get(cid, 0)))



async def relay_ranked_streams(
    engine: EngineClient | None, content_ids: list[str], client_label: str, claim: RelayInfo,
    *, client_factory: Callable[..., httpx.AsyncClient] | None = None,
    registry: RelayRegistry = relay_registry,
    candidate_provider: Callable[[], Awaitable[tuple[list[str], bool]]] | None = None,
    experimental_transcoding: bool = False,
    plex_compatible_audio: bool = False,
    on_source_failure: Callable[[str], Awaitable[None]] | None = None,
    attempt_seconds: float | None = None,
    startup_budget_seconds: float | None = None,
) -> AsyncIterator[bytes]:
    """Retry startup failures; midstream transcoding recovery is explicit opt-in.

    One 45-second recovery window tries each candidate once. Only a source that
    delivers for 30 seconds resets the failure history, so flapping sources do
    not hold a slot forever. Cancellation never starts another source.
    """
    # The tuner settings when the route passes them; the module defaults otherwise.
    attempt_seconds = ATTEMPT_SECONDS if attempt_seconds is None else attempt_seconds
    startup_budget_seconds = STARTUP_BUDGET_SECONDS if startup_budget_seconds is None else startup_budget_seconds
    started = time.monotonic()
    deadline = started + startup_budget_seconds
    attempted: set[str] = set()
    retried_empty: set[str] = set()
    candidates = prefer_recovered_sources(content_ids)
    version = 0
    # The relay's own deadline (start or stall) of the read in progress.
    # When it fires, the engine reader is cancelled just like when the
    # client leaves; only this tells the two apart.
    timer: list = [None]

    def stop_linger() -> float:
        return 0 if timer[0] is not None and timer[0].cancel_called else STOP_LINGER_SECONDS
    try:
        while time.monotonic() < deadline:
            candidates = prefer_recovered_sources(candidates)
            pending = [cid for cid in candidates if cid not in attempted]
            if not pending:
                if candidate_provider is None:
                    break
                with anyio.move_on_after(max(0, deadline - time.monotonic())) as scope:
                    candidates, refreshing = await candidate_provider()
                    candidates = prefer_recovered_sources(candidates)
                if scope.cancel_called:
                    break
                pending = [cid for cid in candidates if cid not in attempted]
                if not pending:
                    if not refreshing:
                        break
                    await asyncio.sleep(min(.25, max(0, deadline - time.monotonic())))
                    continue
            content_id = pending[0]
            attempted.add(content_id)
            registry.select_stream(claim.id, content_id)
            attempt_deadline = min(deadline, time.monotonic() + attempt_seconds)
            is_http = content_id.startswith('url:')

            async def source():
                if is_http:
                    upstream = relay_http_stream(content_id, claim, startup_deadline=attempt_deadline,
                        plex_compatible_audio=plex_compatible_audio and not experimental_transcoding)
                else:
                    if engine is None:
                        raise EngineUnavailableError('Acestream Engine URL is not configured')
                    upstream = relay_engine_stream(engine, content_id, client_label, registry=registry,
                        client_factory=client_factory, claim=claim, release_claim=False,
                        stop_linger=stop_linger, read_seconds=attempt_seconds,
                        startup_deadline=attempt_deadline)
                try:
                    async for chunk in upstream:
                        yield chunk
                finally:
                    with anyio.CancelScope(shield=True):
                        await upstream.aclose()

            raw = source()
            if experimental_transcoding:
                iterator = remux_source(raw, version=version, offset=time.monotonic() - started,
                    plex_compatible_audio=plex_compatible_audio)
            elif plex_compatible_audio and not is_http:
                iterator = compatible_audio_source(raw)
            else:
                iterator = raw
            version += 1
            first_at = last_at = None
            healthy = False
            attempt_started = time.monotonic()
            try:
                with anyio.fail_after(max(0, attempt_deadline - time.monotonic())) as timer[0]:
                    first = await anext(iterator)
                first_at = last_at = time.monotonic()
                yield first
                while True:
                    with anyio.fail_after(STALL_SECONDS) as timer[0]:
                        chunk = await anext(iterator)
                    last_at = time.monotonic()
                    yield chunk
            except (EngineRefusedError, EngineUnavailableError, EngineStreamError, StopAsyncIteration, TimeoutError) as exc:
                empty_start = (isinstance(exc, StopAsyncIteration) and first_at is None
                               and content_id not in retried_empty
                               and time.monotonic() - attempt_started < EMPTY_START_RETRY_SECONDS
                               and not [cid for cid in candidates if cid not in attempted])
                if empty_start:
                    # Empty at once and nothing else left to try: the same
                    # source again, not as a failure.
                    retried_empty.add(content_id)
                    attempted.discard(content_id)
                    logger.info('TV relay source %s ended empty at start; retrying it once', content_id)
                    continue
                record_source_failure(content_id)
                # Count delivery only through the last chunk, regardless of
                # how the source ends. Silence before EOF/transport failure
                # must not renew the budget any more than a stall wait does.
                if first_at is not None:
                    healthy = last_at - first_at >= HEALTHY_SECONDS
                # Do not include upstream exception text: it can contain URLs
                # with credentials. Keep EOF distinct from our read deadline.
                reason = (
                    'read_timeout' if isinstance(exc, TimeoutError) else
                    'upstream_eof' if isinstance(exc, StopAsyncIteration) else
                    'engine_refused' if isinstance(exc, EngineRefusedError) else
                    'engine_unavailable' if isinstance(exc, EngineUnavailableError) else
                    'upstream_error'
                )
                logger.info(
                    'TV relay source ended content_id=%s reason=%s phase=%s route=%s experimental_transcoding=%s',
                    content_id, reason, 'streaming' if first_at is not None else 'starting',
                    'http' if is_http else 'acexy' if engine is not None and engine.use_acexy else 'direct', experimental_transcoding,
                )
            finally:
                with anyio.CancelScope(shield=True):
                    await iterator.aclose()
            if healthy:
                attempted = {content_id}
                deadline = time.monotonic() + startup_budget_seconds
            if on_source_failure is not None:
                await on_source_failure(content_id)
            if first_at is not None and not experimental_transcoding:
                # Headers and media have already been sent. End this response so
                # the client reconnects to the same stable TV URL for a new source.
                return
            # Always use current eligibility after a failure, not the startup snapshot.
            if candidate_provider is not None:
                with anyio.move_on_after(max(0, deadline - time.monotonic())) as scope:
                    candidates, _ = await candidate_provider()
                if scope.cancel_called:
                    break
        raise EngineStreamError('No source could sustain TV channel playback within the recovery budget')
    finally:
        registry.close(claim.id)
        if engine is not None:
            engine.close()
