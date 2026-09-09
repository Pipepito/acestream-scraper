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
from app.services.tuner_remux import remux_source

STARTUP_BUDGET_SECONDS = 45.0
ATTEMPT_SECONDS = 15.0
STALL_SECONDS = 15.0
HEALTHY_SECONDS = 30.0
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
    engine: EngineClient, content_ids: list[str], client_label: str, claim: RelayInfo,
    *, client_factory: Callable[..., httpx.AsyncClient] | None = None,
    registry: RelayRegistry = relay_registry,
    candidate_provider: Callable[[], Awaitable[tuple[list[str], bool]]] | None = None,
    experimental_transcoding: bool = False,
    on_source_failure: Callable[[str], Awaitable[None]] | None = None,
) -> AsyncIterator[bytes]:
    """Retry startup failures; midstream transcoding recovery is explicit opt-in.

    One 45-second recovery window tries each candidate once. Only a source that
    delivers for 30 seconds resets the failure history, so flapping sources do
    not hold a slot forever. Cancellation never starts another source.
    """
    started = time.monotonic()
    deadline = started + STARTUP_BUDGET_SECONDS
    attempted: set[str] = set()
    candidates = prefer_recovered_sources(content_ids)
    version = 0
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
            raw = relay_engine_stream(engine, content_id, client_label, registry=registry,
                client_factory=client_factory, claim=claim, release_claim=False)
            iterator = remux_source(raw, version=version, offset=time.monotonic() - started) if experimental_transcoding else raw
            version += 1
            first_at = None
            try:
                with anyio.fail_after(min(ATTEMPT_SECONDS, max(.001, deadline - time.monotonic()))):
                    first = await anext(iterator)
                first_at = time.monotonic()
                yield first
                while True:
                    with anyio.fail_after(STALL_SECONDS):
                        chunk = await anext(iterator)
                    yield chunk
            except (EngineRefusedError, EngineUnavailableError, EngineStreamError, StopAsyncIteration, TimeoutError) as exc:
                record_source_failure(content_id)
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
                    'acexy' if engine.use_acexy else 'direct', experimental_transcoding,
                )
            finally:
                with anyio.CancelScope(shield=True):
                    await iterator.aclose()
            if first_at is not None and time.monotonic() - first_at >= HEALTHY_SECONDS:
                attempted = {content_id}
                deadline = time.monotonic() + STARTUP_BUDGET_SECONDS
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
        engine.close()
