"""The real ProbeEngine adapter: how a check session is stopped."""
import asyncio

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.services.engine_probe import AiohttpProbeEngine, ProbeSession

CID = 'a' * 40


@pytest_asyncio.fixture
async def engine():
    seen = []

    async def handle(request):
        seen.append((request.path, list(request.query.items())))
        return web.json_response({'response': 'ok', 'error': None})

    app = web.Application()
    app.router.add_route('GET', '/{tail:.*}', handle)
    server = TestServer(app, host='127.0.0.1')
    await server.start_server()
    url = f'http://127.0.0.1:{server.port}'
    yield url, seen
    await server.close()


@pytest.mark.asyncio
async def test_stop_sends_only_method_stop_to_the_session_command(engine):
    url, seen = engine
    session = ProbeSession(CID, stat_url=f'{url}/ace/stat/{CID}/s1', command_url=f'{url}/ace/cmd/{CID}/s1',
                           playback_url=None)
    await AiohttpProbeEngine(url).stop(session)
    assert seen == [(f'/ace/cmd/{CID}/s1', [('method', 'stop')])]


async def _server(handler):
    app = web.Application()
    app.router.add_route('GET', '/{tail:.*}', handler)
    server = TestServer(app, host='127.0.0.1')
    await server.start_server()
    return server


@pytest.mark.asyncio
async def test_ready_is_true_only_for_an_engine_status_answer():
    answers = iter([web.json_response({'result': {'version': {'version': '3.2'}}}), web.Response(status=503)])

    async def handle(request):
        return next(answers)

    server = await _server(handle)
    url = f'http://127.0.0.1:{server.port}'
    try:
        assert await AiohttpProbeEngine(url).ready() is True
        assert await AiohttpProbeEngine(url).ready() is False
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_ready_is_false_when_the_engine_refuses_or_hangs(monkeypatch):
    async def hang(request):
        await asyncio.sleep(2)
        return web.json_response({'result': {}})

    server = await _server(hang)
    hung = f'http://127.0.0.1:{server.port}'
    port = server.port
    monkeypatch.setattr('app.services.engine_probe.READY_TIMEOUT', 0.2)
    try:
        assert await AiohttpProbeEngine(hung).ready() is False
    finally:
        await server.close()
    # The same port, now closed: the connection is refused.
    assert await AiohttpProbeEngine(f'http://127.0.0.1:{port}').ready() is False


@pytest.mark.asyncio
async def test_a_probe_whose_statistics_are_unreadable_is_stopped_by_the_real_adapter(db_session, monkeypatch):
    from tests.test_engine_check_transport import FakeEngine, channel, service
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))

    async with FakeEngine() as engine:
        engine.stat = [500]
        result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)

    assert result['message'] == 'Could not read stream statistics'
    assert engine.paths() == ['/server/api', '/ace/getstream', f'/ace/stat/{CID}/s1', f'/ace/cmd/{CID}/s1',
                              '/server/api']
