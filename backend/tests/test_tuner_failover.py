"""Online-only channel resolution and startup failover lifecycle."""
import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.stream_relay import EngineStreamError, RelayRegistry
from app.services.engine_client import EngineRefusedError
from app.services.tuner_playback_service import relay_ranked_streams
from app.services.tuner_service import TunerService


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
    data = b''.join([chunk async for chunk in relay_ranked_streams(engine, ['high', 'low'], 'viewer', claim, registry=registry)])
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
async def test_midstream_failure_does_not_splice_in_another_feed(monkeypatch):
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
    with pytest.raises(EngineStreamError):
        await anext(iterator)
    assert attempts == ['one']
    assert registry.count_active() == 0


@pytest.mark.asyncio
async def test_cancel_does_not_start_backup_and_releases_slot(monkeypatch):
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
    iterator = relay_ranked_streams(engine, ['one', 'two'], 'viewer', claim, registry=registry)
    task = asyncio.create_task(anext(iterator))
    await entered.wait()
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
        output = b''.join([chunk async for chunk in relay_ranked_streams(engine, ['high', 'low'], 'viewer', claim,
            registry=registry, client_factory=factory)])
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
    provider = AsyncMock(side_effect=[([], True), (['stale', 'recovered'], False)])
    registry = RelayRegistry()
    claim = registry.try_open('stale', 'viewer', 1)
    data = b''.join([part async for part in relay_ranked_streams(Mock(), ['stale'], 'viewer', claim,
        registry=registry, candidate_provider=provider)])
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
    assert b''.join([part async for part in relay_ranked_streams(Mock(), [], 'viewer', claim,
        registry=registry, candidate_provider=provider)]) == b'recovered'


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
        monkeypatch.setattr('app.services.tuner_playback_service.relay_engine_stream', relay)
        url = f'/tuner/channel/{tv.id}.ts'
        assert alembic_client.head(url).status_code == 200
        start.assert_not_called()
        response = alembic_client.get(url)
        assert response.status_code == 200
        assert response.content == b'recovered video'
        start.assert_called_once_with(tv.id)
        engine.close.assert_called_once()
    finally:
        get_settings.cache_clear()
        get_tuner_gate.cache_clear()
