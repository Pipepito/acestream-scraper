"""Kodi's second GET finds the source still running.

Kodi opens a channel with two GETs and closes the first. The relay stopped
the engine session as the first closed, so the second started cold: 1.8 s
more on an amd64 bench and 3.2 s on an ARM box. When the client leaves, the
TV relay now defers the final stop; a start of the same source within the
delay cancels it. A source that fails is still stopped at once.
"""
import asyncio
import threading
from unittest.mock import Mock

import httpx
import pytest

from app.services import engine_client as engine_module
from app.services.engine_client import EngineClient, EngineRefusedError

CID = "c" * 40
stops = []


@pytest.fixture
def engine(monkeypatch):
    """An engine that records starts; stops are recorded wherever they come from."""
    log = []
    stops.clear()
    stopped = threading.Event()

    def handler(request):
        if request.url.path == "/ace/getstream":
            log.append(("start", request.url.params["pid"]))
            if log and getattr(handler, "refuse", False):
                return httpx.Response(200, json={"response": None, "error": "refused"})
            return httpx.Response(200, json={"response": {
                "playback_url": "http://engine:6878/ace/r/x/tok", "stat_url": "http://engine:6878/ace/stat/x/s",
                "command_url": "http://engine:6878/ace/cmd/x/" + request.url.params["pid"], "is_live": 1}, "error": None})
        log.append(("stop", request.url.params.get("method")))
        stops.append(str(request.url.copy_remove_param("method")))
        stopped.set()
        return httpx.Response(200, json={"response": "ok", "error": None})

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client
    # The deferred stop opens its own client: route it to the same fake engine.
    monkeypatch.setattr(engine_module.httpx, "Client", lambda *a, **k: real_client(transport=transport))
    client = EngineClient("http://engine-linger-%d:6878" % id(log), client=real_client(transport=transport))
    return client, log, stopped, handler


def test_without_linger_the_stop_is_immediate(engine):
    client, log, _stopped, _ = engine
    client.stop(client.start(CID))
    assert [kind for kind, _ in log] == ["start", "stop"]


def test_with_linger_the_stop_comes_later(engine):
    client, log, stopped, _ = engine
    client.stop(client.start(CID), linger_seconds=0.05)
    assert [kind for kind, _ in log] == ["start"]
    assert stopped.wait(2)
    assert [kind for kind, _ in log] == ["start", "stop"]


def test_a_start_within_the_linger_cancels_the_stop_and_leaves_no_orphan(engine):
    """The first session is stopped too, with the final stop: measured with
    Kodi, its stop never came otherwise."""
    client, log, stopped, _ = engine
    first = client.start(CID)
    client.stop(first, linger_seconds=0.1)
    second = client.start(CID)
    assert not stopped.wait(0.3)          # nothing stopped while the second plays
    client.stop(second)
    assert [kind for kind, _ in log] == ["start", "start", "stop", "stop"]
    assert stops == [second.command_url, first.command_url]


def test_a_deferred_final_stop_stops_both_sessions(engine):
    client, log, stopped, _ = engine
    first = client.start(CID)
    client.stop(first, linger_seconds=0.05)
    second = client.start(CID)
    client.stop(second, linger_seconds=0.05)
    deadline = __import__('time').monotonic() + 2
    while len(stops) < 2 and __import__('time').monotonic() < deadline:
        stopped.wait(0.05)
    assert stops == [second.command_url, first.command_url]


def test_a_failed_restart_leaves_no_session_running(engine):
    client, log, stopped, handler = engine
    client.stop(client.start(CID), linger_seconds=5)
    handler.refuse = True
    with pytest.raises(EngineRefusedError):
        client.start(CID)
    assert [kind for kind, _ in log] == ["start", "start", "stop"]


def test_cancelled_timer_cannot_consume_a_newer_pending_stop(engine, monkeypatch):
    """A cancelled timer may already be waiting for the source lock."""
    timers = []

    def timer_factory(delay, callback, args):
        timer = Mock(args=args, function=callback)
        timers.append(timer)
        return timer

    monkeypatch.setattr(engine_module, "Timer", timer_factory)
    client, _log, _stopped, _handler = engine
    first = client.start(CID)
    client.stop(first, linger_seconds=5)
    second = client.start(CID)
    client.stop(second, linger_seconds=5)

    # Simulate the first timer entering its callback after cancellation and
    # after the replacement session has also been released.
    timers[0].function(*timers[0].args)
    assert stops == []
    assert second.lease.source.pending_stop is timers[1]
    timers[1].function(*timers[1].args)
    assert stops == [second.command_url, first.command_url]


@pytest.mark.asyncio
@pytest.mark.parametrize("ending", ["client_cancels", "client_closes", "source_stalls"])
async def test_the_relay_lingers_only_when_the_client_leaves(monkeypatch, ending):
    """How Kodi really leaves: the server cancels the response task while the
    engine reader is waiting for data, so the cancellation reaches the reader
    BEFORE the relay (measured with Kodi: the stop came 18 ms after its GET,
    with no linger). The fake reader asks, like the real one,
    only when it is cancelled or closed."""
    import app.services.tuner_playback_service as playback
    from app.services.stream_relay import EngineStreamError, RelayRegistry
    lingers = []
    waiting = asyncio.Event()

    async def relay(_engine, content_id, _label, *, stop_linger, **kwargs):
        try:
            yield b"a"
            waiting.set()
            await asyncio.sleep(10)
            yield b"b"
        except (GeneratorExit, asyncio.CancelledError):
            lingers.append(stop_linger())
            raise
    monkeypatch.setattr(playback, "relay_engine_stream", relay)
    monkeypatch.setattr(playback, "STALL_SECONDS", 0.05 if ending == "source_stalls" else 5)
    registry = RelayRegistry()
    claim = registry.try_open("one", "viewer", 1)
    monkeypatch.setattr(playback, "ATTEMPT_SECONDS", 1)
    monkeypatch.setattr(playback, "STARTUP_BUDGET_SECONDS", 1)
    iterator = playback.relay_ranked_streams(Mock(), ["one"], "viewer", claim, registry=registry)
    assert await anext(iterator) == b"a"
    if ending == "client_cancels":
        task = asyncio.ensure_future(anext(iterator))
        await waiting.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert lingers == [playback.STOP_LINGER_SECONDS]
    elif ending == "client_closes":
        await iterator.aclose()
        assert lingers == [playback.STOP_LINGER_SECONDS]
    else:
        with pytest.raises((EngineStreamError, StopAsyncIteration)):
            await anext(iterator)
        assert lingers == [0]


def test_the_engine_reader_passes_the_linger_to_the_engine(monkeypatch):
    """relay_engine_stream hands the linger to EngineClient.stop."""
    import anyio
    from app.services.stream_relay import RelayRegistry, relay_engine_stream
    engine = Mock()
    engine.engine_url = "http://engine:6878"
    engine.start.return_value = Mock(playback_url="http://engine:6878/ace/r/x/tok")

    def factory(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"ts")), **kwargs)

    async def main():
        stream = relay_engine_stream(engine, CID, "viewer", client_factory=factory, registry=RelayRegistry(),
                                     stop_linger=lambda: 5.0)
        assert await anext(stream) == b"ts"
        await stream.aclose()
    anyio.run(main)
    engine.stop.assert_called_once_with(engine.start.return_value, linger_seconds=5.0)


def test_a_normal_end_stops_at_once():
    """The source ended (not cancelled): no linger, whatever the caller says."""
    import anyio
    from app.services.stream_relay import RelayRegistry, relay_engine_stream
    engine = Mock()
    engine.engine_url = "http://engine:6878"
    engine.start.return_value = Mock(playback_url="http://engine:6878/ace/r/x/tok")

    def factory(**kwargs):
        return httpx.AsyncClient(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"ts")), **kwargs)

    async def main():
        stream = relay_engine_stream(engine, CID, "viewer", client_factory=factory, registry=RelayRegistry(),
                                     stop_linger=lambda: 5.0)
        assert [chunk async for chunk in stream] == [b"ts"]
    anyio.run(main)
    engine.stop.assert_called_once_with(engine.start.return_value)
