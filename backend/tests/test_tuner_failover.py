"""Online-only channel resolution and startup failover lifecycle."""
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.engine_client import EngineRefusedError
from functools import partial
from app.services.tuner_playback_service import relay_ranked_streams as default_relay_ranked_streams
relay_ranked_streams = partial(default_relay_ranked_streams, experimental_transcoding=True)
from app.services.tuner_service import TunerService


@pytest.fixture(autouse=True)
def remux_test_transport(monkeypatch):
    monkeypatch.setattr('app.services.tuner_playback_service._failures', __import__('collections').OrderedDict())
    # Lifecycle tests use byte markers; real media remuxing is tested separately.
    async def identity(source, **kwargs):
        try:
            async for chunk in source:
                yield chunk
        finally:
            await source.aclose()
    monkeypatch.setattr('app.services.tuner_playback_service.remux_source', identity)
    monkeypatch.setattr('app.api.endpoints.tuner.ffmpeg_binary', lambda: '/test/ffmpeg')


async def collect_until_exhausted(iterator):
    chunks = []
    try:
        async for chunk in iterator:
            chunks.append(chunk)
    except EngineStreamError:
        if not chunks:
            raise
    return chunks


def test_online_sources_rank_by_measured_bitrate_with_unknown_last(db_session):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='F1', is_active=True)
    db_session.add(tv)
    db_session.flush()
    rows = [('a', True, True, 8_000_000), ('b', True, True, 16_000_000),
            ('c', False, True, 32_000_000), ('d', None, True, 64_000_000),
            ('e', True, False, 128_000_000), ('f', True, True, None)]
    for key, online, active, bitrate in rows:
        db_session.add(AcestreamChannel(id=key * 40, name=key, tv_channel_id=tv.id,
            is_online=online, is_active=active, bitrate_bps=bitrate))
    db_session.commit()
    service = TunerService(db_session)
    assert service.online_stream_ids(tv.id) == ['b' * 40, 'a' * 40, 'f' * 40]
    tv.is_active = False
    db_session.commit()
    assert service.online_stream_ids(tv.id) == []


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['refused', 'empty', 'transport', 'timeout'])
async def test_retry_holds_one_slot_and_cleans_attempts(monkeypatch, failure):
    registry = RelayRegistry()
    claim = registry.try_open('high', 'viewer', 1)
    engine = Mock()
    attempts, cleaned = [], []
    async def relay(_engine, content_id, _label, **kwargs):
        assert kwargs['release_claim'] is False
        assert registry.try_open('other', 'viewer2', 1) is None
        attempts.append(content_id)
        try:
            if content_id == 'high':
                if failure == 'refused':
                    raise EngineRefusedError('refused')
                if failure == 'transport':
                    raise EngineStreamError('no bytes')
                if failure == 'timeout':
                    await asyncio.sleep(10)
                return
            yield b'video'
        finally:
            cleaned.append(content_id)
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    monkeypatch.setattr('app.services.tuner_playback_service.ATTEMPT_SECONDS', 0.01)
    data = b''.join(await collect_until_exhausted(relay_ranked_streams(engine, ['high', 'low'], 'viewer', claim, registry=registry)))
    assert data == b'video'
    assert attempts == cleaned == ['high', 'low']
    assert registry.count_active() == 0
    engine.close.assert_called_once()


@pytest.mark.asyncio
async def test_exhaustion_is_an_error_not_empty_success(monkeypatch):
    async def empty(*args, **kwargs):
        if False:
            yield b''
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', empty)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    engine = Mock()
    with pytest.raises(EngineStreamError):
        await anext(relay_ranked_streams(engine, ['one'], 'viewer', claim, registry=registry))
    assert registry.count_active() == 0
    engine.close.assert_called_once()


@pytest.mark.asyncio
async def test_midstream_failure_advances_to_remuxed_backup(monkeypatch):
    attempts = []
    async def relay(_engine, content_id, *args, **kwargs):
        attempts.append(content_id)
        yield b'first'
        raise EngineStreamError('stalled')
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    iterator = relay_ranked_streams(Mock(), ['one', 'two'], 'viewer', claim, registry=registry)
    assert await anext(iterator) == b'first'
    assert await anext(iterator) == b'first'
    with pytest.raises(EngineStreamError):
        await anext(iterator)
    assert attempts == ['one', 'two']
    assert registry.count_active() == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("experimental", [False, True])
async def test_cancel_does_not_start_backup_and_releases_slot(monkeypatch, experimental):
    cleaned = asyncio.Event()
    entered = asyncio.Event()
    async def relay(*args, **kwargs):
        try:
            entered.set()
            await asyncio.sleep(10)
            yield b'never'
        finally:
            cleaned.set()
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    engine = Mock()
    iterator = default_relay_ranked_streams(engine, ['one', 'two'], 'viewer', claim, registry=registry, experimental_transcoding=experimental)
    task = asyncio.create_task(anext(iterator))
    await asyncio.wait_for(entered.wait(), timeout=2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cleaned.is_set()
    assert registry.count_active() == 0
    engine.close.assert_called_once()


def test_channel_url_resolves_current_sources_and_head_never_starts_engine(alembic_client, alembic_db_session, monkeypatch):
    from app.api.endpoints import tuner
    from app.models.models import AcestreamChannel, TVChannel
    from app.services.tuner_network import get_tuner_gate
    from app.config.settings import get_settings
    monkeypatch.setenv('TUNER_ALLOWED_NETWORKS', '*')
    get_settings.cache_clear(); get_tuner_gate.cache_clear()
    try:
        tv = TVChannel(name='F1', is_active=True)
        alembic_db_session.add(tv); alembic_db_session.flush()
        row = AcestreamChannel(id='a' * 40, name='feed', is_online=True, is_active=True, tv_channel_id=tv.id)
        alembic_db_session.add(row); alembic_db_session.commit()
        engine = Mock()
        monkeypatch.setattr(tuner, '_engine', engine)
        url = f'/tuner/channel/{tv.id}.ts'
        assert alembic_client.head(url).status_code == 200
        engine.assert_not_called()
        assert alembic_client.get('/tuner/lineup.json').json()[0]['URL'].endswith(url)
        row.is_online = False; tv.is_active = False; alembic_db_session.commit()
        assert alembic_client.get(url).json()['error']['code'] == 'NO_ONLINE_STREAMS'
        engine.assert_not_called()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear(); get_tuner_gate.cache_clear()


@pytest.mark.asyncio
async def test_real_relay_stops_failed_session_before_starting_backup():
    import httpx
    from app.services.engine_client import EngineClient
    events = []
    def handler(request):
        if request.url.path == '/ace/getstream':
            cid = request.url.params['id']
            events.append(('start', cid))
            return httpx.Response(200, json={'response': {
                'playback_url': f'http://engine/media/{cid}',
                'stat_url': f'http://engine/stat/{cid}', 'command_url': f'http://engine/stop/{cid}', 'is_live': 1}})
        if request.url.path.startswith('/stop/'):
            events.append(('stop', request.url.path.split('/')[-1]))
            return httpx.Response(200)
        if request.url.path == '/media/high':
            return httpx.Response(503)
        return httpx.Response(200, content=b'video bytes')
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        engine = EngineClient('http://engine', client=client)
        registry = RelayRegistry()
        claim = registry.try_open('high', 'viewer', 1)
        def factory(**kwargs):
            return httpx.AsyncClient(transport=httpx.MockTransport(handler), **kwargs)
        output = b''.join(await collect_until_exhausted(relay_ranked_streams(engine, ['high', 'low'], 'viewer', claim,
            registry=registry, client_factory=factory)))
        assert output == b'video bytes'
        assert events == [('start', 'high'), ('stop', 'high'), ('start', 'low'), ('stop', 'low')]
        assert registry.count_active() == 0


@pytest.mark.asyncio
async def test_newly_verified_source_is_used_during_same_startup(monkeypatch):
    attempts = []
    async def relay(_engine, content_id, *args, **kwargs):
        attempts.append(content_id)
        if content_id == 'stale':
            raise EngineStreamError('offline')
        yield b'backup'
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    provider = AsyncMock(side_effect=[([], True), (['stale', 'recovered'], False), (['recovered'], False), (['recovered'], False)])
    registry = RelayRegistry()
    claim = registry.try_open('stale', 'viewer', 1)
    data = b''.join(await collect_until_exhausted(relay_ranked_streams(Mock(), ['stale'], 'viewer', claim,
        registry=registry, candidate_provider=provider)))
    assert data == b'backup'
    assert attempts == ['stale', 'recovered']
    assert registry.count_active() == 0


@pytest.mark.asyncio
async def test_no_stored_online_sources_waits_for_refresh(monkeypatch):
    async def relay(*args, **kwargs):
        yield b'recovered'
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    registry = RelayRegistry()
    claim = registry.try_open('offline', 'viewer', 1)
    provider = AsyncMock(return_value=(['recovered'], False))
    assert b''.join(await collect_until_exhausted(relay_ranked_streams(Mock(), [], 'viewer', claim,
        registry=registry, candidate_provider=provider))) == b'recovered'


@pytest.mark.asyncio
async def test_refresh_wait_stays_inside_startup_budget(monkeypatch):
    monkeypatch.setattr('app.services.tuner_playback_service.STARTUP_BUDGET_SECONDS', 0.01)
    registry = RelayRegistry()
    claim = registry.try_open('offline', 'viewer', 1)
    provider = AsyncMock(return_value=([], True))
    with pytest.raises(EngineStreamError):
        await anext(relay_ranked_streams(Mock(), [], 'viewer', claim, registry=registry, candidate_provider=provider))
    assert registry.count_active() == 0


def test_channel_get_starts_quiet_refresh_and_recovers_offline_source(alembic_client, alembic_db_session, monkeypatch):
    from app.api.endpoints import tuner
    from app.config.database import SessionLocal
    from app.models.models import AcestreamChannel, TVChannel
    from app.services.tuner_network import get_tuner_gate
    from app.config.settings import get_settings
    monkeypatch.setenv('TUNER_ALLOWED_NETWORKS', '*')
    get_settings.cache_clear()
    get_tuner_gate.cache_clear()
    try:
        tv = TVChannel(name='Recoverable', is_active=True)
        alembic_db_session.add(tv)
        alembic_db_session.flush()
        cid = 'b' * 40
        alembic_db_session.add(AcestreamChannel(id=cid, name='Backup', tv_channel_id=tv.id,
                                              is_active=True, is_online=False))
        alembic_db_session.commit()
        def refresh(channel_id):
            assert channel_id == tv.id
            with SessionLocal() as db:
                db.get(AcestreamChannel, cid).is_online = True
                db.commit()
            return None
        start = Mock(side_effect=refresh)
        monkeypatch.setattr(tuner.tuner_probe_service, 'start', start)
        engine = Mock()
        monkeypatch.setattr(tuner, '_engine', lambda: engine)
        async def relay(_engine, content_id, *args, **kwargs):
            assert content_id == cid
            yield b'recovered video'
        async def ranked(*args, candidate_provider, **kwargs):
            candidates, _ = await candidate_provider()
            assert candidates == [cid]
            yield b'recovered video'
            engine.close()
        monkeypatch.setattr(tuner, 'relay_ranked_streams', ranked)
        url = f'/tuner/channel/{tv.id}.ts'
        assert alembic_client.head(url).status_code == 200
        start.assert_not_called()
        response = alembic_client.get(url)
        assert response.status_code == 200
        assert response.content == b'recovered video'
        start.assert_called_once_with(tv.id)
        engine.close.assert_called_once()
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()

@pytest.mark.asyncio
@pytest.mark.parametrize('ending', ['eof', 'stalled'])
async def test_eof_or_stalled_feed_uses_next_source_without_releasing_slot(monkeypatch, ending):
    attempts = []
    async def relay(_engine, cid, *args, **kwargs):
        attempts.append(cid)
        yield cid.encode()
        if ending == 'stalled':
            await asyncio.Event().wait()
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    monkeypatch.setattr('app.services.tuner_playback_service.STALL_SECONDS', .01)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    engine = Mock()
    iterator = relay_ranked_streams(engine, ['one', 'two'], 'viewer', claim, registry=registry)
    assert await anext(iterator) == b'one'
    assert await anext(iterator) == b'two'
    assert registry.count_active() == 1
    await iterator.aclose()
    assert attempts == ['one', 'two']
    assert registry.count_active() == 0
    engine.close.assert_called_once()


@pytest.mark.asyncio
async def test_long_lived_source_gets_new_recovery_budget(monkeypatch):
    monkeypatch.setattr('app.services.tuner_playback_service.STARTUP_BUDGET_SECONDS', .01)
    monkeypatch.setattr('app.services.tuner_playback_service.HEALTHY_SECONDS', .01)
    async def relay(_engine, cid, *args, **kwargs):
        yield cid.encode()
        if cid == 'one':
            await asyncio.sleep(.03)
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    iterator = relay_ranked_streams(Mock(), ['one', 'two'], 'viewer', claim, registry=registry)
    assert await anext(iterator) == b'one'
    assert await anext(iterator) == b'two'
    await iterator.aclose()


@pytest.mark.asyncio
async def test_channel_monitor_repeats_only_while_response_is_open(monkeypatch):
    from starlette.requests import Request
    from app.api.endpoints import tuner
    registry = RelayRegistry()
    monkeypatch.setattr(tuner, 'relay_registry', registry)
    monkeypatch.setattr(tuner, '_channel_candidates', lambda *args, **kwargs: ['one'])
    monkeypatch.setattr(tuner, '_tuner_count', lambda: 1)
    engine = Mock()
    monkeypatch.setattr(tuner, '_engine', lambda: engine)
    monkeypatch.setattr(tuner, 'SOURCE_REFRESH_SECONDS', .01)
    refresh = Mock(return_value=None)
    monkeypatch.setattr(tuner.tuner_probe_service, 'start', refresh)
    async def relay(_engine, _candidates, _label, claim, **kwargs):
        try:
            yield b'video'
            await asyncio.Event().wait()
        finally:
            registry.close(claim.id)
            engine.close()
    monkeypatch.setattr(tuner, 'relay_ranked_streams', relay)
    response = await tuner.tuner_channel(1, Request({'type': 'http', 'method': 'GET', 'client': ('127.0.0.1', 1)}))
    assert await anext(response.body_iterator) == b'video'
    await asyncio.sleep(.03)
    assert refresh.call_count >= 2
    await response.body_iterator.aclose()
    calls = refresh.call_count
    await asyncio.sleep(.03)
    assert refresh.call_count == calls
    assert registry.count_active() == 0
    engine.close.assert_called_once()


@pytest.mark.asyncio
async def test_default_reconnect_uses_backup_without_ffmpeg(monkeypatch):
    opened = []
    closed = []
    async def raw(engine, cid, *args, **kwargs):
        opened.append(cid)
        try:
            yield cid.encode()
            raise EngineStreamError('lost signal')
        finally:
            closed.append(cid)
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', raw)
    remux = Mock(side_effect=AssertionError('Default must not encode'))
    monkeypatch.setattr('app.services.tuner_playback_service.remux_source', remux)
    registry = RelayRegistry()
    for expected in ('one', 'two'):
        engine = Mock()
        claim = registry.try_open('one', 'viewer', 1)
        iterator = default_relay_ranked_streams(engine, ['one', 'two'], 'viewer', claim, registry=registry)
        assert b''.join([chunk async for chunk in iterator]) == expected.encode()
        assert registry.count_active() == 0
        engine.close.assert_called_once()
    assert opened == closed == ['one', 'two']
    remux.assert_not_called()


@pytest.mark.asyncio
async def test_default_retries_startup_failure_without_encoding(monkeypatch):
    async def raw(engine, cid, *args, **kwargs):
        if cid == 'one':
            raise EngineRefusedError('unavailable')
        yield b'backup'
    monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', raw)
    monkeypatch.setattr('app.services.tuner_playback_service.remux_source', Mock(side_effect=AssertionError('No encoding')))
    registry = RelayRegistry()
    claim = registry.try_open('one', 'viewer', 1)
    assert b''.join([chunk async for chunk in default_relay_ranked_streams(Mock(), ['one', 'two'], 'viewer', claim, registry=registry)]) == b'backup'
    assert registry.count_active() == 0


def test_failed_source_cooldown_expires(monkeypatch):
    from app.services import tuner_playback_service as service
    now = [100.0]
    monkeypatch.setattr(service.time, 'monotonic', lambda: now[0])
    service.record_source_failure('one')
    assert service.prefer_recovered_sources(['one', 'two']) == ['two', 'one']
    now[0] += service.FAILURE_COOLDOWN_SECONDS
    assert service.prefer_recovered_sources(['one', 'two']) == ['one', 'two']
