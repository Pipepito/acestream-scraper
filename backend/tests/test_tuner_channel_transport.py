"""What a TV channel GET does, seen from the engine, the sources and the client.

Characterisation at the transport level: a real HTTP server plays the engine
(and another one an HTTP broadcaster), the app is served by uvicorn on a
loopback port, and a real HTTP client asks it for /tuner/channel/<id>.ts.
Each scenario pins the requests the engine and the sources receive, what the
client gets (status, headers, bytes) and the outcomes the relay reports to
the playback history. Nothing here replaces a relay function, so these hold
whatever shape the relay has inside.
"""
import asyncio
import contextlib
import os
import subprocess
import time
from collections import OrderedDict
from datetime import datetime, timezone

import httpx
import pytest
import uvicorn
from aiohttp import web
from aiohttp.test_utils import TestServer

from app.models.models import AcestreamChannel, TVChannel
from app.repositories.settings_repository import SettingsRepository
from app.services import tuner_playback_service as playback
from app.services.tuner_probe_service import tuner_probe_service

A, B, C = 'a' * 40, 'b' * 40, 'c' * 40
HTTP_ID = 'url:' + 'e' * 40
LINGER = 0.3
SETTLE = 1.2          # past the linger, the deferred stop and the hand-over check
CUT_CHUNKS = 3
RELAY_HEADERS = {'content-type': 'video/mp2t', 'cache-control': 'no-store', 'x-accel-buffering': 'no'}


def chunk_of(cid: str) -> bytes:
    """One engine write: whole TS packets marked with the source's letter."""
    return (b'\x47' + cid[0].encode() * 187) * 349


class FakeEngine:
    """An engine over HTTP. ``behave(cid, ...)`` scripts each start of a
    source (the last item repeats): 'play' streams until the client leaves,
    'cut' sends CUT_CHUNKS writes and ends, 'refuse' answers the start with an
    engine error. ``calls`` is what the engine saw, in order:
    (kind, source letter, session token)."""

    def __init__(self):
        self.calls = []
        self.script = {}
        self.sessions = {}
        self.server = None

    def behave(self, cid, *items):
        self.script[cid] = list(items)

    def _next(self, cid):
        items = self.script.get(cid, ['play'])
        return items.pop(0) if len(items) > 1 else items[0]

    async def handle(self, request):
        path = request.path
        if path == '/ace/getstream':
            cid = request.query['id']
            behaviour = self._next(cid)
            if behaviour == 'refuse':
                self.calls.append(('start', cid[0], None))
                return web.json_response({'response': None, 'error': 'refused'})
            token = f's{len(self.sessions) + 1}'
            self.sessions[token] = behaviour
            self.calls.append(('start', cid[0], token))
            base = f'{self.url}/ace'
            return web.json_response({'response': {
                'playback_session_id': token, 'is_live': 1,
                'playback_url': f'{base}/r/{cid}/{token}',
                'stat_url': f'{base}/stat/{cid}/{token}',
                'command_url': f'{base}/cmd/{cid}/{token}',
            }, 'error': None})
        if path.startswith('/ace/r/'):
            cid, token = path.split('/')[3:5]
            self.calls.append(('read', cid[0], token))
            behaviour = self.sessions[token]
            response = web.StreamResponse(headers={'Content-Type': 'video/mp2t'})
            await response.prepare(request)
            writes = CUT_CHUNKS if behaviour == 'cut' else 3000
            with contextlib.suppress(Exception):
                for _ in range(writes):
                    await response.write(chunk_of(cid))
                    await asyncio.sleep(0.02)
                await response.write_eof()
            return response
        if path.startswith('/ace/cmd/'):
            cid, token = path.split('/')[3:5]
            self.calls.append(('stop', cid[0], token))
            return web.json_response({'response': 'ok', 'error': None})
        self.calls.append(('other', path, None))
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


@contextlib.asynccontextmanager
async def served(app):
    """The app on a real loopback port, as a tuner client reaches it."""
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=0, lifespan='off', log_level='warning',
                                           access_log=False, timeout_graceful_shutdown=3))
    task = asyncio.create_task(server.serve())
    while not server.started:
        if task.done():
            task.result()
        await asyncio.sleep(0.01)
    port = server.servers[0].sockets[0].getsockname()[1]
    try:
        yield f'http://127.0.0.1:{port}'
    finally:
        server.should_exit = True
        await task


async def watch(base, tv_id, *, take=None):
    """One GET of the channel: read until ``take`` bytes and leave, or to the end."""
    async with httpx.AsyncClient(timeout=30) as client:
        async with client.stream('GET', f'{base}/tuner/channel/{tv_id}.ts') as response:
            body = b''
            async for data in response.aiter_raw():
                body += data
                if take is not None and len(body) >= take:
                    break
            headers = {key: response.headers.get(key) for key in RELAY_HEADERS}
            if response.status_code != 200:
                headers = {'content-type': response.headers.get('content-type')}
            return response.status_code, headers, body


@pytest.fixture
def tuner(alembic_backend_runtime, alembic_db_session, monkeypatch):
    """The app, its database and the relay's process-wide state, isolated."""
    from app.config.settings import get_settings
    from app.services.tuner_network import get_tuner_gate
    outcomes, refreshes = [], []
    monkeypatch.setattr(playback, '_failures', OrderedDict())
    monkeypatch.setattr(playback, '_openings', {})
    monkeypatch.setattr(playback, 'STOP_LINGER_SECONDS', LINGER)
    monkeypatch.setattr(playback, '_outcome_recorder',
                        lambda cid, tv, outcome, **kw: outcomes.append((cid, outcome)))
    monkeypatch.setattr(tuner_probe_service, 'start', lambda tv_id: refreshes.append(tv_id))
    try:
        with monkeypatch.context() as scoped:
            scoped.setenv('TUNER_ALLOWED_NETWORKS', '*')
            get_settings.cache_clear()
            get_tuner_gate.cache_clear()
            yield alembic_backend_runtime.app, alembic_db_session, outcomes, refreshes
    finally:
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()


def configure(db, engine_url):
    repo = SettingsRepository(db)
    repo.set_setting(repo.ACE_ENGINE_URL, engine_url)
    repo.set_setting(repo.TUNER_SOURCE_START_SECONDS, '5')
    repo.set_setting(repo.TUNER_STARTUP_BUDGET_SECONDS, '5')


def seed(db, rows):
    """rows: (id, is_online, bitrate, stream_url). Checked just now, so the
    relay order is online by bitrate and an offline one is left out of it."""
    tv = TVChannel(name='Example channel', is_active=True)
    db.add(tv)
    db.flush()
    now = datetime.now(timezone.utc)
    for cid, online, bitrate, url in rows:
        db.add(AcestreamChannel(id=cid, name='Example source', tv_channel_id=tv.id, is_active=True,
                                is_online=online, last_checked=now, bitrate_bps=bitrate, stream_url=url))
    db.commit()
    return tv.id


def kinds(calls):
    return [(kind, letter) for kind, letter, _ in calls]


@pytest.mark.asyncio
async def test_first_source_plays(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None)])
        status, headers, body = await watch(base, tv, take=200_000)
        left = len(engine.calls)
        await asyncio.sleep(0.1)
        before_linger = list(engine.calls[left:])
        await asyncio.sleep(SETTLE)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert body[:len(chunk_of(A))] == chunk_of(A)
    assert engine.calls == [('start', 'a', 's1'), ('read', 'a', 's1'), ('stop', 'a', 's1')]
    assert before_linger == []          # the stop waits for a second GET
    assert outcomes == [(A, 'ok')]
    assert refreshes == [tv]


@pytest.mark.asyncio
async def test_first_source_refused_and_second_plays(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        engine.behave(A, 'refuse')
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None)])
        status, headers, body = await watch(base, tv, take=200_000)
        await asyncio.sleep(SETTLE)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert body[:len(chunk_of(B))] == chunk_of(B)
    assert engine.calls == [('start', 'a', None), ('start', 'b', 's1'), ('read', 'b', 's1'), ('stop', 'b', 's1')]
    assert outcomes == [(A, 'engine_refused'), (B, 'ok')]
    assert refreshes == [tv, tv]


@pytest.mark.asyncio
async def test_source_cut_midway_ends_the_response(tuner):
    """Without the midstream switch (off by default) the response ends where
    the source did, and the next source is left for the client's reconnect."""
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        engine.behave(A, 'cut')
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None)])
        status, headers, body = await watch(base, tv)
        await asyncio.sleep(SETTLE)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert body == chunk_of(A) * CUT_CHUNKS
    assert engine.calls == [('start', 'a', 's1'), ('read', 'a', 's1'), ('stop', 'a', 's1')]
    assert outcomes == [(A, 'early_death')]
    assert refreshes == [tv, tv]


@pytest.mark.asyncio
async def test_all_candidates_fail_and_the_last_resort_plays(tuner):
    """C was found offline just now: out of the relay order, in the last resort."""
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        engine.behave(A, 'refuse')
        engine.behave(B, 'refuse')
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None), (C, False, 9000, None)])
        status, headers, body = await watch(base, tv, take=200_000)
        await asyncio.sleep(SETTLE)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert body[:len(chunk_of(C))] == chunk_of(C)
    assert engine.calls == [('start', 'a', None), ('start', 'b', None), ('start', 'c', 's1'), ('read', 'c', 's1'),
                            ('stop', 'c', 's1')]
    assert outcomes == [(A, 'engine_refused'), (B, 'engine_refused'), (C, 'ok')]
    assert refreshes == [tv, tv, tv]


@pytest.mark.asyncio
async def test_every_source_fails_is_a_502(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        engine.behave(A, 'refuse')
        engine.behave(C, 'refuse')
        tv = seed(db, [(A, True, 3000, None), (C, False, 9000, None)])
        status, headers, body = await watch(base, tv)
        await asyncio.sleep(SETTLE)
    assert (status, headers['content-type']) == (502, 'application/json')
    assert b'CHANNEL_STREAM_FAILED' in body
    assert engine.calls == [('start', 'a', None), ('start', 'c', None)]
    assert outcomes == [(A, 'engine_refused'), (C, 'engine_refused')]
    assert refreshes == [tv, tv, tv]


@pytest.mark.asyncio
async def test_kodi_double_get_shares_the_opening(tuner):
    """Kodi leaves its first GET as soon as bytes arrive and sends a second:
    the second goes on with the same source, the first is a hand-over."""
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None), (B, True, 2000, None)])
        first = await watch(base, tv, take=1)
        second = await watch(base, tv, take=200_000)
        await asyncio.sleep(SETTLE)
    assert first[:2] == second[:2] == (200, RELAY_HEADERS)
    assert second[2][:len(chunk_of(A))] == chunk_of(A)
    starts = [call for call in engine.calls if call[0] != 'stop']
    stops = sorted(call for call in engine.calls if call[0] == 'stop')
    assert starts == [('start', 'a', 's1'), ('read', 'a', 's1'), ('start', 'a', 's2'), ('read', 'a', 's2')]
    assert stops == [('stop', 'a', 's1'), ('stop', 'a', 's2')]
    assert sorted(outcomes) == [(A, 'handover'), (A, 'ok')]
    assert refreshes == [tv, tv]


@pytest.mark.asyncio
async def test_client_leaving_stops_the_engine_session_after_the_linger(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None)])
        await watch(base, tv, take=1)
        left = time.monotonic()
        while not any(call[0] == 'stop' for call in engine.calls) and time.monotonic() - left < 3:
            await asyncio.sleep(0.02)
        waited = time.monotonic() - left
        await asyncio.sleep(SETTLE)
    assert engine.calls == [('start', 'a', 's1'), ('read', 'a', 's1'), ('stop', 'a', 's1')]
    assert LINGER - 0.05 <= waited < LINGER + 1.0
    assert outcomes == [(A, 'ok')]


@pytest.mark.asyncio
async def test_channel_without_sources_is_a_503_and_never_reaches_the_engine(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [])
        status, headers, body = await watch(base, tv)
        async with httpx.AsyncClient() as client:
            head = await client.head(f'{base}/tuner/channel/{tv}.ts')
    assert (status, headers['content-type']) == (503, 'application/json')
    assert b'NO_ONLINE_STREAMS' in body
    assert head.status_code == 503
    assert engine.calls == [] and outcomes == [] and refreshes == []


@pytest.mark.asyncio
async def test_head_answers_without_starting_anything(tuner):
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None)])
        async with httpx.AsyncClient() as client:
            head = await client.head(f'{base}/tuner/channel/{tv}.ts')
    assert head.status_code == 200
    assert {key: head.headers.get(key) for key in RELAY_HEADERS} == RELAY_HEADERS
    assert engine.calls == [] and outcomes == [] and refreshes == []


@pytest.mark.asyncio
async def test_source_held_by_a_recording_is_shared_and_stopped_with_it(tuner):
    """A recording holds the source on the same engine: the relay starts its
    own session, and the engine stops nothing until the recording lets go."""
    from app.services.engine_client import EngineClient
    from app.services.recording_capture import CaptureInput
    app, db, outcomes, refreshes = tuner
    async with FakeEngine() as engine, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(A, True, 3000, None)])
        recording = CaptureInput(EngineClient(engine.url))
        await recording.open(A, time.monotonic() + 5)
        try:
            status, headers, body = await watch(base, tv, take=200_000)
            await asyncio.sleep(SETTLE)
            while_recording = list(engine.calls)
        finally:
            await recording.close()
        await asyncio.sleep(0.3)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert body[:len(chunk_of(A))] == chunk_of(A)
    assert while_recording == [('start', 'a', 's1'), ('start', 'a', 's2'), ('read', 'a', 's2')]
    assert sorted(engine.calls[len(while_recording):]) == [('stop', 'a', 's1'), ('stop', 'a', 's2')]
    assert outcomes == [(A, 'ok')]


@pytest.fixture
def media_tools():
    from app.services import tuner_http_source
    from app.services.stream_relay import EngineStreamError
    try:
        ffmpeg = tuner_http_source.ffmpeg_binary()
    except EngineStreamError:
        pytest.skip('FFmpeg required for an HTTP source')
    return os.environ.get('FFMPEG_TEST_TOOL_PATH', ffmpeg)


@pytest.mark.asyncio
async def test_http_source_plays_without_the_engine(tuner, media_tools, tmp_path):
    app, db, outcomes, refreshes = tuner
    media = tmp_path / 'stream.ts'
    made = subprocess.run([media_tools, '-v', 'error', '-f', 'lavfi', '-i', 'testsrc=size=160x90:rate=25',
                           '-f', 'lavfi', '-i', 'sine=frequency=440:sample_rate=48000', '-t', '3',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-g', '25', '-c:a', 'aac',
                           '-f', 'mpegts', str(media)], capture_output=True, timeout=30)
    if made.returncode != 0:
        pytest.skip('An FFmpeg with lavfi and libx264 is required to make the source')
    fetched = []

    async def broadcaster(request):
        fetched.append(request.path)
        return web.FileResponse(media)
    origin = web.Application()
    origin.router.add_get('/{path:.*}', broadcaster)
    async with FakeEngine() as engine, TestServer(origin, host='127.0.0.1') as site, served(app) as base:
        configure(db, engine.url)
        tv = seed(db, [(HTTP_ID, None, 0, f'http://127.0.0.1:{site.port}/live/stream.ts')])
        status, headers, body = await watch(base, tv)
        await asyncio.sleep(SETTLE)
    assert (status, headers) == (200, RELAY_HEADERS)
    assert len(body) > 188 and len(body) % 188 == 0
    assert all(body[i] == 0x47 for i in range(0, len(body), 188))
    # FFmpeg reads the source through the guarded proxy, more than once.
    assert fetched and set(fetched) == {'/live/stream.ts'}
    assert engine.calls == []
    assert outcomes == [(HTTP_ID, 'early_death')]
    assert refreshes == [tv, tv]
