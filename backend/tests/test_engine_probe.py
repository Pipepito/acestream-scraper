"""The real ProbeEngine adapter: how a check session is stopped."""
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
