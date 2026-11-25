"""What the stream check sends to the engine, seen from the engine's side.

Characterisation at the transport level: a real HTTP server plays the engine
and records every request, so these hold whatever client the check uses.
"""
import asyncio

import httpx
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.models.models import AcestreamChannel
from app.repositories.settings_repository import SettingsRepository
from app.services.channel_status_service import GROWTH_CONFIRM_BYTES, ChannelStatusService
from app.services.engine_client import EngineClient

CID = 'a' * 40
LIVE = {'signal_verified': True, 'bitrate_bps': 1000}


@pytest.fixture(autouse=True)
def isolated_queue(monkeypatch):
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))


class FakeEngine:
    """An engine over HTTP. Each route answers from a list of scripted replies;
    the last one repeats. A reply is a dict (JSON 200), an int (bare status) or
    a float (seconds to stall before answering the next item)."""

    def __init__(self, advertised_host='localhost:6878'):
        self.requests = []
        self.advertised = f'http://{advertised_host}'
        self.status = [{'result': {'version': {'version': '3.2'}}}]
        self.start = [self.session()]
        self.stat = [{'response': {'status': 'dl', 'downloaded': 1_000_000}}]
        self.server = None

    def session(self, token='s1'):
        base = f'{self.advertised}/ace'
        return {'response': {
            'is_live': 1, 'playback_session_id': token,
            'playback_url': f'{base}/r/{CID}/{token}',
            'stat_url': f'{base}/stat/{CID}/{token}',
            'command_url': f'{base}/cmd/{CID}/{token}?token=kept-by-playback-only',
        }, 'error': None}

    @staticmethod
    async def _reply(script):
        item = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(item, float):
            await asyncio.sleep(item)
            item = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(item, int):
            return web.Response(status=item)
        return web.json_response(item)

    async def handle(self, request):
        self.requests.append((request.path, list(request.query.items())))
        if request.path == '/server/api':
            return await self._reply(self.status)
        if request.path == '/ace/getstream':
            return await self._reply(self.start)
        if request.path.startswith('/ace/stat/'):
            return await self._reply(self.stat)
        if request.path.startswith('/ace/cmd/'):
            return web.json_response({'response': 'ok', 'error': None})
        return web.Response(status=404)

    async def __aenter__(self):
        app = web.Application()
        app.router.add_route('GET', '/{tail:.*}', self.handle)
        self.server = TestServer(app, host='127.0.0.1')
        await self.server.start_server()
        self.url = f'http://127.0.0.1:{self.server.port}'
        return self

    async def __aexit__(self, *exc):
        await self.server.close()

    def paths(self):
        return [path for path, _ in self.requests]


def growing(*totals):
    return [{'response': {'status': 'dl', 'downloaded': total}} for total in totals]


def service(db_session, engine_url, *, timeout='2', dedicated=None, monkeypatch=None):
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, engine_url)
    repo.set_setting(repo.ACESTREAM_CHECK_TIMEOUT, timeout)
    if monkeypatch is not None:
        from app.config.settings import settings
        monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', dedicated or '')
    return ChannelStatusService(db_session)


@pytest.fixture
def media(monkeypatch):
    seen = []

    async def probe(engine_url, playback_url, *, timeout):
        seen.append((engine_url, playback_url, timeout))
        return LIVE

    monkeypatch.setattr('app.services.channel_status_service.probe_media', probe)
    return seen


def start_query(engine, index=0):
    starts = [query for path, query in engine.requests if path == '/ace/getstream']
    return starts[index]


def channel():
    return AcestreamChannel(id=CID, name='Example')


@pytest.mark.asyncio
async def test_found_live_source(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.stat = growing(1_000_000, 1_000_000 + GROWTH_CONFIRM_BYTES + 1)
        result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)

    assert (result['is_online'], result['network_status']) == (True, 'found')
    assert engine.paths() == ['/server/api', '/ace/getstream', f'/ace/stat/{CID}/s1', f'/ace/stat/{CID}/s1',
                              f'/ace/cmd/{CID}/s1']
    assert engine.requests[0][1] == [('api_version', '3'), ('method', 'get_status')]
    query = start_query(engine)
    assert [key for key, _ in query] == ['id', 'format', 'pid']
    assert dict(query)['id'] == CID and dict(query)['format'] == 'json' and len(dict(query)['pid']) == 32
    assert engine.requests[2][1] == []
    # The session URLs are re-rooted on the configured engine, and the stop
    # carries only method=stop: the advertised query is dropped.
    assert engine.requests[-1][1] == [('method', 'stop')]
    assert media == [(engine.url, f'{engine.url}/ace/r/{CID}/s1', 2.0)]


@pytest.mark.asyncio
async def test_infohash_identifier_is_the_start_key(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.start = [{'error': 'not found'}]
        await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(
            channel(), identifier='infohash', persist=False)
    assert [key for key, _ in start_query(engine)] == ['infohash', 'format', 'pid']


@pytest.mark.asyncio
async def test_not_found(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.start = [{'error': 'Not found'}]
        result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)

    assert (result['is_online'], result['network_status']) == (False, 'not_found')
    assert result['message'] == 'Engine reports this content ID was not found'
    # No session to stop; health asked again before recording offline.
    assert engine.paths() == ['/server/api', '/ace/getstream', '/server/api']
    assert media == []


@pytest.mark.asyncio
async def test_start_timeout_retries_once_with_the_same_pid(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.start = [1.0, {'error': 'not found'}]
        result = await service(db_session, engine.url, timeout='0.4', monkeypatch=monkeypatch).check_channel_status(
            channel(), persist=False)

    assert result['network_status'] == 'not_found'
    assert engine.paths() == ['/server/api', '/ace/getstream', '/server/api', '/ace/getstream', '/server/api']
    assert start_query(engine, 0) == start_query(engine, 1)


@pytest.mark.asyncio
async def test_engine_waking_up_is_waited_for(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.status = [503, {'result': {}}]
        engine.start = [{'error': 'not found'}]
        await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)
    assert engine.paths() == ['/server/api', '/server/api', '/ace/getstream', '/server/api']


@pytest.mark.asyncio
async def test_engine_dying_during_the_probe_keeps_the_previous_status(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.status = [{'result': {}}, 500]
        engine.start = [502]
        probe = service(db_session, engine.url, monkeypatch=monkeypatch)
        result = await probe.check_channel_status(channel(), persist=False)

    assert result['status'] == 'skipped'
    assert probe.engine_unavailable is True
    assert engine.paths() == ['/server/api', '/ace/getstream', '/server/api']


@pytest.mark.asyncio
async def test_stalled_prebuffer_is_offline_and_stopped(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.stat = [{'response': {'status': 'stopped', 'downloaded': 0}}]
        result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)

    assert (result['is_online'], result['network_status']) == (False, 'found')
    assert result['message'] == 'Stream is not broadcasting'
    assert engine.paths() == ['/server/api', '/ace/getstream', f'/ace/stat/{CID}/s1', f'/ace/cmd/{CID}/s1',
                              '/server/api']


@pytest.mark.asyncio
async def test_session_url_outside_engine_routes_is_never_requested(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.start = [{'response': {'stat_url': 'http://elsewhere.example.com/private',
                                      'command_url': 'file:///etc/passwd'}, 'error': None}]
        result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(channel(), persist=False)

    assert result['message'] == 'Engine did not provide a verifiable playback session'
    assert engine.paths() == ['/server/api', '/ace/getstream', '/server/api']


@pytest.mark.asyncio
async def test_source_in_use_is_never_sent_to_the_engine(db_session, media, monkeypatch):
    from app.services.stream_relay import relay_registry
    async with FakeEngine() as engine:
        relay = relay_registry.open(CID, 'test')
        try:
            result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(
                channel(), persist=False)
        finally:
            relay_registry.close(relay.id)
    assert result['status'] == 'skipped'
    assert engine.requests == []


@pytest.mark.asyncio
async def test_probe_ending_while_playback_holds_the_source_is_parked_not_stopped(db_session, media, monkeypatch):
    async with FakeEngine() as engine:
        engine.stat = growing(1_000_000, 1_000_000 + GROWTH_CONFIRM_BYTES + 1)
        played = []

        def playback_engine(request):
            played.append(str(request.url))
            return httpx.Response(200, json={'response': {
                'playback_url': f'{engine.url}/ace/r/{CID}/viewer',
                'stat_url': f'{engine.url}/ace/stat/{CID}/viewer',
                'command_url': f'{engine.url}/ace/cmd/{CID}/viewer'}, 'error': None})

        client = EngineClient(engine.url, client=httpx.Client(transport=httpx.MockTransport(playback_engine)))
        viewer = client.start(CID)
        try:
            result = await service(db_session, engine.url, monkeypatch=monkeypatch).check_channel_status(
                channel(), persist=False)
            assert result['is_online'] is True
            assert '/ace/cmd/' not in ' '.join(engine.paths())
        finally:
            client.stop(viewer)
    # The final playback stop also stops the parked probe session, by the
    # re-rooted command URL with method=stop.
    assert played[1:] == [f'{engine.url}/ace/cmd/{CID}/viewer?method=stop',
                          f'{engine.url}/ace/cmd/{CID}/s1?method=stop']


@pytest.mark.asyncio
async def test_dedicated_checker_is_the_only_engine_asked(db_session, media, monkeypatch):
    async with FakeEngine() as playback, FakeEngine() as checker:
        checker.status = [{'result': {}}, 500]
        checker.start = [500]
        probe = service(db_session, playback.url, dedicated=checker.url, monkeypatch=monkeypatch)
        result = await probe.check_channel_status(channel(), persist=False)

    assert result['status'] == 'skipped' and probe.engine_unavailable is True
    assert checker.paths() == ['/server/api', '/ace/getstream', '/server/api']
    assert playback.requests == []

