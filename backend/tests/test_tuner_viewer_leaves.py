"""When the viewer of a TV channel leaves, the channel's background refresh
is told to stop (``tuner_probe_service.stop_channel``), so it does not go on
checking sources, each with its own engine session, for a channel nobody
watches. This holds whether the viewer leaves while the video plays or while
the channel is still opening.
"""
import asyncio

import pytest
from aiohttp import web

from app.services.stream_relay import relay_registry
from app.services.tuner_probe_service import tuner_probe_service
from tests.test_tuner_channel_transport import A, B, FakeEngine, chunk_of, configure, seed, served, tuner, watch  # noqa: F401

FIRST_BYTE_DELAY = 1.5


class SlowEngine(FakeEngine):
    """The read sends its first bytes only after FIRST_BYTE_DELAY."""

    async def handle(self, request):
        if request.path.startswith('/ace/r/'):
            cid, token = request.path.split('/')[3:5]
            self.calls.append(('read', cid[0], token))
            response = web.StreamResponse(headers={'Content-Type': 'video/mp2t'})
            await response.prepare(request)
            try:
                await asyncio.sleep(FIRST_BYTE_DELAY)
                for _ in range(3000):
                    await response.write(chunk_of(cid))
                    await asyncio.sleep(0.02)
            except Exception:
                pass
            return response
        return await super().handle(request)


async def leave_while_opening(base, tv_id, after):
    """A GET that hangs up before any byte of the body arrives."""
    host, port = base.split('//')[1].split(':')
    reader, writer = await asyncio.open_connection(host, int(port))
    writer.write(f'GET /tuner/channel/{tv_id}.ts HTTP/1.1\r\nHost: example\r\n\r\n'.encode())
    await writer.drain()
    await asyncio.sleep(after)
    writer.transport.abort()


async def wait_for(condition, seconds):
    deadline = asyncio.get_running_loop().time() + seconds
    while not condition() and asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.05)
    return condition()


@pytest.fixture
def stops(monkeypatch):
    calls = []
    monkeypatch.setattr(tuner_probe_service, 'stop_channel', calls.append)
    return calls


@pytest.mark.asyncio
async def test_viewer_leaving_while_it_plays_stops_the_channel_refresh(tuner, stops):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None)])
        await watch(base, tv, take=1)
        assert await wait_for(lambda: stops, 3)
        assert await wait_for(lambda: not relay_registry.active(), 3)
    assert stops == [tv]


@pytest.mark.asyncio
async def test_viewer_leaving_while_the_channel_opens_stops_the_channel_refresh(tuner, stops):
    app, db, outcomes, refreshes = tuner
    async with SlowEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None)])
        await leave_while_opening(base, tv, after=0.5)
        assert await wait_for(lambda: stops, FIRST_BYTE_DELAY + 3)
        assert await wait_for(lambda: not relay_registry.active(), 3)
    assert stops == [tv]
