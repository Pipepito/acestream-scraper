import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import AcestreamChannel
from app.services.channel_status_service import ChannelStatusService


@pytest.fixture(autouse=True)
def isolated_queue(monkeypatch):
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))


@pytest.fixture
def probe(db_session):
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine.test:6878'
    service._get_timeout = lambda: 0.015
    service._engine_ready = AsyncMock(return_value=True)
    service.channel_repository = MagicMock()
    return service


def session_response():
    return {'response': {
        'is_live': 1,
        'playback_url': 'http://127.0.0.1:6878/ace/r/hash/session',
        'stat_url': 'http://127.0.0.1:6878/ace/stat/hash/session',
        'command_url': 'http://127.0.0.1:6878/ace/cmd/hash/session',
    }, 'error': None}


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [
    {'response': {'is_live': 1}},
    {'error': 'got newer download'},
    {'response': {'is_live': 1, 'peers': 12}},
    {'response': None},
])
async def test_metadata_and_errors_do_not_mean_online(probe, payload):
    probe._fetch_engine_response = AsyncMock(return_value=(200, payload, None))
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['is_online'] is False
    probe.channel_repository.update_channel_status.assert_called_once()
    assert probe.channel_repository.update_channel_status.call_args.args[1] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("dedicated", [False, True])
async def test_media_packets_confirm_broadcast_and_stop_session(probe, monkeypatch, dedicated):
    engine_url = "http://checker.test:6880" if dedicated else "http://engine.test:6878"
    if dedicated:
        from app.config.settings import settings
        monkeypatch.setattr(settings, "ACE_CHECK_ENGINE_URL", engine_url)
        probe._get_engine_url = ChannelStatusService._get_engine_url.__get__(probe)
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    media_probe = AsyncMock(return_value={'signal_verified': True})
    monkeypatch.setattr('app.services.channel_status_service.probe_media', media_probe)
    probe._fetch_engine_response = AsyncMock(side_effect=[
        (200, session_response(), None),
        (200, {'response': {'status': 'dl', 'downloaded': 100}}, None),
        (200, {'response': {'status': 'dl', 'downloaded': 200}}, None),
        (200, {'response': 'ok'}, None),
    ])
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), identifier='infohash', persist=False)
    assert result['is_online'] is True
    assert result['network_status'] == 'found'
    media_probe.assert_awaited_once_with(engine_url, f'{engine_url}/ace/r/hash/session')
    calls = probe._fetch_engine_response.call_args_list
    assert calls[0].args[1]['infohash'] == 'a' * 40
    assert 'method' not in calls[0].args[1]
    assert calls[1].args[0] == f'{engine_url}/ace/stat/hash/session'
    assert calls[-1].args[:2] == (f'{engine_url}/ace/cmd/hash/session', {'method': 'stop'})
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.asyncio
async def test_cached_total_and_peers_never_confirm_broadcast(probe):
    calls = []

    async def fetch(url, params, timeout):
        calls.append((url, params))
        if '/getstream' in url:
            return 200, session_response(), None
        return 200, {'response': {'status': 'dl', 'downloaded': 100, 'peers': 10, 'is_live': 1}}, None

    probe._fetch_engine_response = fetch
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['is_online'] is False
    assert calls[-1][1] == {'method': 'stop'}


@pytest.mark.asyncio
@pytest.mark.parametrize('error', [asyncio.TimeoutError(), asyncio.CancelledError(), ValueError('invalid JSON')])
async def test_session_cleanup_on_timeout_cancellation_and_failure(probe, error):
    probe._fetch_engine_response = AsyncMock(side_effect=[
        (200, session_response(), None), error, (200, {'response': 'ok'}, None),
    ])
    channel = AcestreamChannel(id='a' * 40, name='Example')
    if isinstance(error, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await probe.check_channel_status(channel)
    else:
        assert (await probe.check_channel_status(channel))['is_online'] is False
    assert probe._fetch_engine_response.call_args.args[1] == {'method': 'stop'}


@pytest.mark.parametrize('url', ['http://evil.test/private', 'http://engine/ace/stat/../private', 'file:///etc/passwd'])
def test_session_links_cannot_escape_engine_routes(url):
    assert ChannelStatusService._session_url('http://engine:6878', url, 'stat') is None


@pytest.mark.asyncio
async def test_probe_player_ids_are_unique_between_service_instances(db_session):
    ids = []
    for _ in range(2):
        service = ChannelStatusService(db_session)
        service._get_engine_url = lambda: 'http://engine:6878'
        service._engine_ready = AsyncMock(return_value=True)
        service._fetch_engine_response = AsyncMock(return_value=(200, {'error': 'not found'}, None))
        await service.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), persist=False)
        ids.append(service._fetch_engine_response.call_args.args[1]['pid'])
    assert ids[0] != ids[1]


@pytest.mark.asyncio
async def test_downloads_without_verified_media_are_not_online(probe, monkeypatch):
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    for metadata in [None, {'signal_verified': False, 'bitrate_bps': None, 'audio_tracks': []}, {'signal_verified': True, 'bitrate_bps': 8_000_000, 'audio_tracks': [{'index': 0, 'language': 'spa'}]}]:
        monkeypatch.setattr('app.services.channel_status_service.probe_media', AsyncMock(return_value=metadata))
        probe._fetch_engine_response = AsyncMock(side_effect=[
            (200, session_response(), None),
            (200, {'response': {'status': 'dl', 'downloaded': 100}}, None),
            (200, {'response': {'status': 'dl', 'downloaded': 200}}, None),
            (200, {'response': 'ok'}, None),
        ])
        result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
        assert result['is_online'] is bool(metadata and metadata['signal_verified'])
        assert result['network_status'] == 'found'
        assert probe.channel_repository.update_channel_status.call_args.kwargs['bitrate_bps'] == (metadata['bitrate_bps'] if metadata else None)
        assert probe.channel_repository.update_channel_status.call_args.kwargs['audio_tracks'] == (metadata['audio_tracks'] if metadata else None)


@pytest.mark.asyncio
async def test_probes_use_distinct_pids_but_timeout_retry_reuses_pid(probe):
    probe._fetch_engine_response = AsyncMock(side_effect=[
        asyncio.TimeoutError(), (500, None, None), (500, None, None),
    ])
    channel = AcestreamChannel(id='a' * 40, name='Example')
    await probe.check_channel_status(channel, persist=False)
    await probe.check_channel_status(channel, persist=False)
    params = [call.args[1] for call in probe._fetch_engine_response.call_args_list]
    assert len(params[0]['pid']) == 32
    assert params[0]['pid'] == params[1]['pid']
    assert params[0]['pid'] != params[2]['pid']


@pytest.mark.asyncio
async def test_active_relay_is_not_probed_or_marked_offline(probe):
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example', is_online=True)
    claim = relay_registry.open(channel.id, 'test')
    probe._fetch_engine_response = AsyncMock()
    try:
        result = await probe.check_channel_status(channel)
        assert result['status'] == 'skipped'
        assert result['is_online'] is True
        probe._fetch_engine_response.assert_not_called()
        probe.channel_repository.update_channel_status.assert_not_called()
    finally:
        relay_registry.close(claim.id)


@pytest.mark.asyncio
async def test_playback_started_during_probe_prevents_stop_and_status_overwrite(probe):
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example', is_online=True)
    claim = None
    async def fetch(url, params, timeout):
        nonlocal claim
        if '/ace/getstream' in url:
            claim = relay_registry.open(channel.id, 'test')
            return 200, session_response(), None
        if '/ace/stat/' in url:
            return 200, {'response': {'status': 'error'}}, None
        pytest.fail('Must not stop the source now owned by playback')
    probe._fetch_engine_response = fetch
    try:
        assert (await probe.check_channel_status(channel))['status'] == 'skipped'
        probe.channel_repository.update_channel_status.assert_not_called()
    finally:
        if claim:
            relay_registry.close(claim.id)


@pytest.mark.asyncio
async def test_probe_limit_and_same_source_serialization(probe, monkeypatch):
    running = set()
    peak = 0
    calls = []
    async def check(channel, **kwargs):
        nonlocal peak
        assert channel.id not in running
        running.add(channel.id)
        peak = max(peak, len(running))
        calls.append(channel.id)
        await asyncio.sleep(.01)
        running.remove(channel.id)
        return {'channel_id': channel.id}
    monkeypatch.setattr(probe, '_check_channel_status', check)
    channels = [AcestreamChannel(id=key * 40, name=key) for key in ('a', 'a', 'b', 'c')]
    await asyncio.gather(*(probe.check_channel_status(channel, persist=False) for channel in channels))
    assert peak == 1
    assert len(calls) == 4
    assert running == set()


@pytest.mark.asyncio
async def test_engine_recovery_precedes_channel_start(probe, monkeypatch):
    events = []
    readiness = iter([False, False, True, True])
    async def ready(url):
        events.append('health')
        return next(readiness)
    async def fetch(*args):
        events.append('stream')
        return 200, {'error': 'no peers'}, None
    probe._engine_ready = ready
    probe._fetch_engine_response = fetch
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    await probe.check_channel_status(AcestreamChannel(id='b' * 40, name='Example'))
    assert events[:4] == ['health', 'health', 'health', 'stream']


@pytest.mark.asyncio
async def test_engine_down_preserves_last_known_status(probe):
    probe._wait_for_engine = AsyncMock(return_value=False)
    probe._fetch_engine_response = AsyncMock()
    result = await probe.check_channel_status(AcestreamChannel(id='c' * 40, name='Example', is_online=True))
    assert result['status'] == 'skipped'
    assert result['is_online'] is True
    probe._fetch_engine_response.assert_not_called()
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.asyncio
async def test_engine_crash_during_probe_does_not_mark_channel_offline(probe):
    probe._engine_ready = AsyncMock(side_effect=[True, False])
    probe._fetch_engine_response = AsyncMock(side_effect=ConnectionError())
    result = await probe.check_channel_status(AcestreamChannel(id='d' * 40, name='Example', is_online=True))
    assert result['status'] == 'skipped'
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize('payload,expected', [({'result': {'version': {}}}, True), ({'response': {}}, False), ({'result': None}, False), ({'error': 'starting'}, False)])
async def test_readiness_requires_engine_status_response(probe, payload, expected):
    probe._fetch_engine_response = AsyncMock(return_value=(200, payload, None))
    assert await ChannelStatusService._engine_ready(probe, 'http://engine.test:6878') is expected
    assert probe._fetch_engine_response.call_args.args[0].endswith('/server/api')


@pytest.mark.asyncio
@pytest.mark.parametrize('http_status,payload,expected', [
    (200, {'error': 'not found'}, 'not_found'),
    (200, {'error': 'content not found'}, 'not_found'),
    (200, {'error': 'no peers'}, 'unknown'),
    (404, None, 'unknown'),  # an absent API route is not an absent content ID
    (500, None, 'unknown'),
])
async def test_lookup_failure_is_separate_from_signal(probe, http_status, payload, expected):
    probe._fetch_engine_response = AsyncMock(return_value=(http_status, payload, None))
    result = await probe.check_channel_status(AcestreamChannel(id='f' * 40, name='Example'))
    assert result['network_status'] == expected
    assert result['is_online'] is False
    assert probe.channel_repository.update_channel_status.call_args.kwargs['network_status'] == expected


def test_catalogue_upsert_does_not_claim_or_overwrite_signal(db_session):
    from app.repositories.channel_repository import ChannelRepository
    repo = ChannelRepository(db_session)
    channel = repo.create_or_update_channel(channel_id='f' * 40, name='Example')
    assert channel.is_online is None
    repo.update_channel_status(channel.id, False, 'No signal', network_status='found')
    channel = repo.create_or_update_channel(channel_id=channel.id, name='Listed again')
    assert channel.is_online is False
    assert channel.network_status == 'found'


@pytest.mark.asyncio
async def test_dedicated_checker_down_never_falls_back_to_playback(db_session, monkeypatch):
    from app.config.settings import settings
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', 'http://checker.test:6879')
    service = ChannelStatusService(db_session)
    service.channel_repository = MagicMock()
    service._wait_for_engine = AsyncMock(return_value=False)
    service._fetch_engine_response = AsyncMock()
    result = await service.check_channel_status(AcestreamChannel(id='f' * 40, name='Example'))
    service._wait_for_engine.assert_awaited_once_with('http://checker.test:6879')
    service._fetch_engine_response.assert_not_awaited()
    service.channel_repository.update_channel_status.assert_not_called()
    assert result['status'] == 'skipped'


def test_probe_endpoint_uses_explicit_route_or_saved_engine(db_session, monkeypatch):
    from app.config.settings import settings
    service = ChannelStatusService(db_session)
    service.settings_repo.set_setting('ace_engine_url', 'http://playback.test:6878')
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', ' checker.test:6879/ ')
    assert service._get_engine_url() == 'http://checker.test:6879'
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', '')
    assert service._get_engine_url() == 'http://playback.test:6878'
