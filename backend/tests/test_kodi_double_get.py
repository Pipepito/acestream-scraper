"""Kodi opens a channel with a HEAD and two GETs, closing the first early.

Real pieces: EngineClient against a fake engine that records getstream and
stop, relay_engine_stream and relay_ranked_streams; the client leaves through
an anyio cancellation, as the server does, followed by the response's
shielded close (ClosingStreamingResponse). The second GET must keep its
session, and every session must be stopped once the last client is gone.
"""
import asyncio
import time

import anyio
from unittest.mock import Mock
import httpx
import pytest

import app.services.tuner_playback_service as playback
from app.services import engine_client as engine_module
from app.services.engine_client import EngineClient
from app.services.stream_relay import RelayRegistry

CID = "d" * 40


@pytest.fixture
def engine(monkeypatch):
    events = []
    t0 = time.monotonic()
    base = "http://engine:%d" % (20000 + id(events) % 20000)   # own source ownership per test

    def handler(request):
        now = round(time.monotonic() - t0, 3)
        if request.url.path == "/ace/getstream":
            pid = request.url.params["pid"]
            events.append((now, "start", pid))
            return httpx.Response(200, json={"response": {
                "playback_url": f"{base}/ace/r/x/{pid}", "stat_url": f"{base}/ace/stat/x/s",
                "command_url": f"{base}/ace/cmd/x/{pid}", "is_live": 1}, "error": None})
        events.append((now, "stop", request.url.path.rsplit("/", 1)[-1]))
        return httpx.Response(200, json={"response": "ok", "error": None})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    monkeypatch.setattr(engine_module.httpx, "Client", lambda *a, **k: real_client(transport=transport))

    async def video(request):
        # Whole relay chunks: the reader hands on CHUNK_SIZE blocks.
        for _ in range(200):
            yield (b"\x47" + bytes(187)) * 349
            await asyncio.sleep(0.02)

    def factory(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=video(r))), **kwargs)

    def new_engine():
        return EngineClient(base, client=real_client(transport=transport))
    return new_engine, factory, events


async def _kodi_get(new_engine, factory, registry, seconds):
    """One GET as the route serves it, consumed until the client leaves (anyio
    cancellation), then the response's shielded close."""
    claim = registry.try_open(CID, "tuner:kodi", 4)
    stream = playback.relay_ranked_streams(new_engine(), [CID], "tuner:kodi", claim, registry=registry,
                                           client_factory=factory)
    got = 0
    with anyio.move_on_after(seconds):
        async for chunk in stream:
            got += len(chunk)
    with anyio.CancelScope(shield=True):
        await stream.aclose()
    return got


@pytest.mark.asyncio
@pytest.mark.parametrize("order", ["second_opens_after_first_closed", "overlapping"])
async def test_the_second_get_keeps_its_session_and_every_session_is_stopped(engine, monkeypatch, order):
    """Kodi closes the first GET and then opens the second (measured); the
    overlapping order is covered too."""
    new_engine, factory, events = engine
    monkeypatch.setattr(playback, "STOP_LINGER_SECONDS", 0.3)
    registry = RelayRegistry()
    if order == "overlapping":
        first = asyncio.ensure_future(_kodi_get(new_engine, factory, registry, 0.3))
        await asyncio.sleep(0.2)
        second = await _kodi_get(new_engine, factory, registry, 1.5)
        await first
    else:
        await _kodi_get(new_engine, factory, registry, 0.2)
        second = await _kodi_get(new_engine, factory, registry, 1.5)
    await asyncio.sleep(0.6)                       # linger and the deferred stop
    starts = [e for e in events if e[1] == "start"]
    stops = [e for e in events if e[1] == "stop"]
    assert len(starts) == 2
    # Nothing stopped while the second GET was playing...
    assert all(t >= 1.5 for t, _, _ in stops), events
    # ...and both sessions are stopped once it is gone.
    assert {pid for _, _, pid in stops} == {pid for _, _, pid in starts}, events
    assert second > 1_000_000              # the second GET played


# --- an engine session that is empty at once ---------------------------------

def _empty_then(monkeypatch, outcomes, delay=0):
    calls = []

    async def relay(_engine, content_id, _label, **kwargs):
        calls.append(content_id)
        outcome = outcomes[min(len(calls), len(outcomes)) - 1]
        await asyncio.sleep(delay)
        if outcome == 'empty':
            return
        yield b'video'
    monkeypatch.setattr(playback, 'relay_engine_stream', relay)
    monkeypatch.setattr(playback, 'ATTEMPT_SECONDS', 1)
    monkeypatch.setattr(playback, 'STARTUP_BUDGET_SECONDS', 2)
    return calls


@pytest.mark.asyncio
async def test_a_session_empty_at_start_is_retried_once(monkeypatch):
    """Seen with Kodi (intermittent): the engine answered 200 and closed at
    once for the second GET's session; with one source the channel failed."""
    from unittest.mock import Mock
    calls = _empty_then(monkeypatch, ['empty', 'video'])
    registry = RelayRegistry()
    claim = registry.try_open(CID, 'kodi', 1)
    first = await anext(playback.relay_ranked_streams(Mock(), [CID], 'kodi', claim, registry=registry))
    assert first == b'video' and calls == [CID, CID]


@pytest.mark.asyncio
async def test_only_once(monkeypatch):
    from unittest.mock import Mock
    from app.services.stream_relay import EngineStreamError
    calls = _empty_then(monkeypatch, ['empty'])
    registry = RelayRegistry()
    claim = registry.try_open(CID, 'kodi', 1)
    with pytest.raises(EngineStreamError):
        await anext(playback.relay_ranked_streams(Mock(), [CID], 'kodi', claim, registry=registry))
    assert calls == [CID, CID]


@pytest.mark.asyncio
async def test_a_source_that_takes_long_to_end_is_not_retried(monkeypatch):
    from unittest.mock import Mock
    from app.services.stream_relay import EngineStreamError
    monkeypatch.setattr(playback, 'EMPTY_START_RETRY_SECONDS', 0.05)
    calls = _empty_then(monkeypatch, ['empty', 'video'], delay=0.1)
    registry = RelayRegistry()
    claim = registry.try_open(CID, 'kodi', 1)
    with pytest.raises(EngineStreamError):
        await anext(playback.relay_ranked_streams(Mock(), [CID], 'kodi', claim, registry=registry))
    assert calls == [CID]
