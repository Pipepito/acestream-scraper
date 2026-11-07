"""Direct JSON startup shares caller budgets and keeps late-session ownership."""
import asyncio
from contextlib import asynccontextmanager
import json
import threading
import time
from urllib.parse import urlsplit

import httpx
import pytest

from app.services import tuner_playback_service as playback
from app.services.engine_client import EngineClient, EngineUnavailableError
from app.services.playback_ownership import source_ownership
from app.services.stream_relay import EngineStreamError, RelayRegistry


@asynccontextmanager
async def slow_engine(json_delay, media_delay=0):
    tasks = set()
    calls = []
    started = asyncio.Event()
    base = ''

    async def serve(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        try:
            request = await reader.readuntil(b'\r\n\r\n')
            path = urlsplit(request.split(b' ')[1].decode()).path
            calls.append(path)
            if path == '/ace/getstream':
                started.set()
                await asyncio.sleep(json_delay)
                body = json.dumps({'response': {
                    'playback_url': base + '/media', 'stat_url': base + '/stat',
                    'command_url': base + '/stop', 'is_live': 1,
                }}).encode()
            elif path == '/media':
                await asyncio.sleep(media_delay)
                body = b'G' + bytes(187)
            else:
                body = b'{}'
            writer.write(b'HTTP/1.1 200 OK\r\nConnection: close\r\nContent-Length: '
                         + str(len(body)).encode() + b'\r\n\r\n' + body)
            await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            await writer.wait_closed()
            tasks.discard(task)

    server = await asyncio.start_server(serve, '127.0.0.1', 0)
    base = 'http://127.0.0.1:%d' % server.sockets[0].getsockname()[1]
    try:
        yield EngineClient(base), calls, started
    finally:
        server.close()
        await server.wait_closed()
        pending = list(tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


def relay_for(engine, *, attempt, total):
    registry = RelayRegistry()
    claim = registry.try_open('cold', 'test', 1)
    relay = playback.relay_ranked_streams(
        engine, ['cold'], 'test', claim, registry=registry,
        attempt_seconds=attempt, startup_budget_seconds=total,
    )
    return relay, registry


@pytest.mark.asyncio
async def test_real_json_start_can_exceed_the_old_fifteen_second_limit():
    # A real socket proves HTTPX accepts the caller's setting, not just that a
    # mocked request received a timeout keyword. No public engine/peers needed.
    async with slow_engine(16) as (engine, calls, _):
        relay, registry = relay_for(engine, attempt=20, total=25)
        try:
            assert await anext(relay) == b'G' + bytes(187)
            with pytest.raises(StopAsyncIteration):
                await anext(relay)
        finally:
            await relay.aclose()
        assert calls.count('/stop') == 1
        assert registry.count_active() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('attempt,total', [(0.1, 1), (1, 0.1)])
async def test_shorter_source_or_total_budget_still_bounds_json_start(attempt, total):
    async with slow_engine(0.5) as (engine, calls, _):
        relay, registry = relay_for(engine, attempt=attempt, total=total)
        before = time.monotonic()
        with pytest.raises(EngineStreamError):
            await anext(relay)
        await relay.aclose()
        assert time.monotonic() - before < 0.45
        assert calls == ['/ace/getstream']
        assert registry.count_active() == 0


@pytest.mark.asyncio
async def test_json_and_first_media_byte_share_one_attempt_budget():
    async with slow_engine(0.1, media_delay=0.5) as (engine, calls, _):
        relay, registry = relay_for(engine, attempt=0.3, total=2)
        with pytest.raises(EngineStreamError):
            await anext(relay)
        await relay.aclose()
        assert calls.count('/stop') == 1
        assert registry.count_active() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('cancellations', [1, 2])
async def test_cancelling_a_pending_json_start_stops_the_late_session_once(monkeypatch, cancellations):
    monkeypatch.setattr(playback, "STOP_LINGER_SECONDS", 0.05)
    async with slow_engine(0.2) as (engine, calls, started):
        relay, registry = relay_for(engine, attempt=1, total=2)
        opening = asyncio.create_task(anext(relay))
        await asyncio.wait_for(started.wait(), 2)
        opening.cancel()
        if cancellations == 2:
            await asyncio.sleep(0.02)
            opening.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(opening, 2)
        await relay.aclose()
        deadline = time.monotonic() + 2
        while '/stop' not in calls and time.monotonic() < deadline:
            await asyncio.sleep(0.01)
        assert calls == ['/ace/getstream', '/stop']
        assert registry.count_active() == 0


def test_expired_deadline_does_not_make_an_engine_request():
    with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail('expired start sent HTTP'))) as client:
        with pytest.raises(EngineUnavailableError, match='deadline expired'):
            EngineClient('http://engine', client=client).start('expired', startup_deadline=time.monotonic() - 1)


def test_source_lock_wait_consumes_the_same_deadline():
    source = source_ownership('http://engine', 'locked')
    held, release = threading.Event(), threading.Event()

    def hold():
        with source.lock:
            held.set()
            release.wait(2)

    thread = threading.Thread(target=hold)
    thread.start()
    try:
        assert held.wait(1)
        with httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail('locked start sent HTTP'))) as client:
            before = time.monotonic()
            with pytest.raises(EngineUnavailableError, match='waiting for the source'):
                EngineClient('http://engine', client=client).start('locked', startup_deadline=before + 0.1)
            assert time.monotonic() - before < 0.5
    finally:
        release.set()
        thread.join(2)


@pytest.mark.asyncio
async def test_late_reply_after_deadline_is_stopped_without_disconnect_linger():
    calls = []

    def respond(request):
        calls.append(request.url.path)
        if request.url.path == '/ace/getstream':
            # Model an engine/transport that returns just after cancellation.
            time.sleep(0.12)
            return httpx.Response(200, json={'response': {
                'playback_url': 'http://engine/media', 'stat_url': 'http://engine/stat',
                'command_url': 'http://engine/stop',
            }})
        return httpx.Response(200)

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        engine = EngineClient('http://engine', client=client)
        relay, registry = relay_for(engine, attempt=0.05, total=1)
        with pytest.raises(EngineStreamError):
            await anext(relay)
        await relay.aclose()
        assert calls == ['/ace/getstream', '/stop']
        assert registry.count_active() == 0


def test_long_start_budget_does_not_extend_stat_or_stop_timeouts():
    calls = []

    def respond(request):
        calls.append(request.extensions['timeout'])
        return httpx.Response(200, json={'response': {
            'playback_url': 'http://engine/media', 'stat_url': 'http://engine/stat',
            'command_url': 'http://engine/stop',
        }})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        engine = EngineClient('http://engine', client=client)
        session = engine.start('long-start', startup_deadline=time.monotonic() + 60)
        engine.stat(session)
        engine.stop(session)
    assert 59 < calls[0]['read'] <= 60
    assert calls[0]['connect'] == 5
    assert [timeout['read'] for timeout in calls[1:]] == [5, 5]


@pytest.mark.asyncio
async def test_cancelled_second_start_does_not_stop_an_existing_viewer():
    async with slow_engine(0.15) as (engine, calls, started):
        viewer = await asyncio.to_thread(engine.start, 'cold', startup_deadline=time.monotonic() + 1)
        started.clear()
        relay, registry = relay_for(engine, attempt=1, total=2)
        opening = asyncio.create_task(anext(relay))
        try:
            await asyncio.wait_for(started.wait(), 2)
            opening.cancel()
            with pytest.raises(asyncio.CancelledError):
                await opening
            await relay.aclose()
            assert calls == ['/ace/getstream', '/ace/getstream']
            assert registry.count_active() == 0
            # relay_ranked_streams closed its owned HTTP client. Final release
            # can use another short-lived client while retaining the same lease.
            with EngineClient(engine.engine_url) as final_client:
                await asyncio.to_thread(final_client.stop, viewer)
            assert calls.count('/stop') == 2
        finally:
            if not viewer.lease.released:
                with EngineClient(engine.engine_url) as final_client:
                    await asyncio.to_thread(final_client.stop, viewer)
