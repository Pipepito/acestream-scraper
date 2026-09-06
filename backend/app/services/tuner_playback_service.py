"""Bounded startup failover; one viewer keeps one tuner slot across attempts."""
from __future__ import annotations

import time
from typing import AsyncIterator, Callable

import anyio
import httpx

from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError
from app.services.stream_relay import EngineStreamError, RelayInfo, RelayRegistry, relay_engine_stream, relay_registry

STARTUP_BUDGET_SECONDS = 45.0
ATTEMPT_SECONDS = 15.0


async def relay_ranked_streams(
    engine: EngineClient, content_ids: list[str], client_label: str, claim: RelayInfo,
    *, client_factory: Callable[..., httpx.AsyncClient] | None = None,
    registry: RelayRegistry = relay_registry,
) -> AsyncIterator[bytes]:
    """Try each online candidate once until bytes arrive, highest bitrate first.

    Once bytes have been emitted, errors end the response: concatenating feeds
    with unrelated timestamps/codecs is not a safe MPEG-TS failover strategy.
    Reopening the stable channel URL resolves the latest candidates again.
    """
    deadline = time.monotonic() + STARTUP_BUDGET_SECONDS
    try:
        for content_id in content_ids:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            registry.select_stream(claim.id, content_id)
            iterator = relay_engine_stream(engine, content_id, client_label,
                client_factory=client_factory, registry=registry, claim=claim, release_claim=False)
            try:
                try:
                    with anyio.fail_after(min(ATTEMPT_SECONDS, remaining)):
                        first = await anext(iterator)
                except (EngineRefusedError, EngineUnavailableError, EngineStreamError, StopAsyncIteration, TimeoutError):
                    continue
                yield first
                async for chunk in iterator:
                    yield chunk
                return
            finally:
                with anyio.CancelScope(shield=True):
                    await iterator.aclose()
        raise EngineStreamError("No online source delivered video within the startup budget")
    finally:
        registry.close(claim.id)
        engine.close()
