import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import AcestreamChannel
from app.repositories.settings_repository import SettingsRepository
from app.services.channel_status_service import ChannelStatusService, SustainedGrowth, GROWTH_CONFIRM_BYTES
from app.services.engine_probe import read_ready, read_start
from fake_probe_engine import ENGINE, FakeProbeEngine, session_answer, stat_answer

LIVE_GROWTH = GROWTH_CONFIRM_BYTES + 1
MB = 1_000_000


@pytest.fixture(autouse=True)
def isolated_queue(monkeypatch):
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))


def use_engines(db_session, monkeypatch, *, playback=ENGINE, checker='', timeout='0.015'):
    from app.config.settings import settings
    monkeypatch.setattr(settings, 'ACE_CHECK_ENGINE_URL', checker)
    repo = SettingsRepository(db_session)
    repo.set_setting(repo.ACE_ENGINE_URL, playback)
    repo.set_setting(repo.ACESTREAM_CHECK_TIMEOUT, timeout)


@pytest.fixture
def engine():
    return FakeProbeEngine()


@pytest.fixture
def probe(db_session, monkeypatch, engine):
    use_engines(db_session, monkeypatch)
    service = ChannelStatusService(db_session, probe_engine=engine)
    service.channel_repository = MagicMock()
    return service


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        self.now += max(seconds, 0.001)


@pytest.fixture
def clock(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr('app.services.channel_status_service._clock', clock)
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', clock.sleep)
    return clock


def growing():
    return [stat_answer(downloaded=100), stat_answer(downloaded=100 + LIVE_GROWTH)]


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [
    {'response': {'is_live': 1}},
    {'error': 'got newer download'},
    {'response': {'is_live': 1, 'peers': 12}},
    {'response': None},
])
async def test_metadata_and_errors_do_not_mean_online(probe, engine, payload):
    engine.start_script = [(200, payload)]
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['is_online'] is False
    probe.channel_repository.update_channel_status.assert_called_once()
    assert probe.channel_repository.update_channel_status.call_args.args[1] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("dedicated", [False, True])
async def test_media_packets_confirm_broadcast_and_stop_session(db_session, monkeypatch, dedicated):
    engine_url = "http://checker.test:6880" if dedicated else ENGINE
    use_engines(db_session, monkeypatch, checker=engine_url if dedicated else '')
    engine = FakeProbeEngine(stats=growing())
    probe = ChannelStatusService(db_session, probe_engine=engine)
    probe.channel_repository = MagicMock()
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    media_probe = AsyncMock(return_value={'signal_verified': True})
    monkeypatch.setattr('app.services.channel_status_service.probe_media', media_probe)
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), identifier='infohash', persist=False)
    assert result['is_online'] is True
    assert result['network_status'] == 'found'
    assert engine.requested_url == engine_url
    media_probe.assert_awaited_once_with(engine_url, f'{engine_url}/ace/r/hash/session', timeout=0.015)
    assert [call[:2] for call in engine.asked('open')] == [('a' * 40, 'infohash')]
    assert engine.asked('stats')[0][0] == f'{engine_url}/ace/stat/hash/session'
    assert engine.stopped == [f'{engine_url}/ace/cmd/hash/session']
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.asyncio
async def test_cached_total_and_peers_never_confirm_broadcast(probe, engine):
    engine.stats_script = [(200, {'response': {'status': 'dl', 'downloaded': 100, 'peers': 10, 'is_live': 1}})]
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
    assert result['is_online'] is False
    assert engine.stopped == [f'{ENGINE}/ace/cmd/hash/session']


@pytest.mark.asyncio
@pytest.mark.parametrize('error', [asyncio.TimeoutError(), asyncio.CancelledError(), ValueError('invalid JSON')])
async def test_session_cleanup_on_timeout_cancellation_and_failure(probe, engine, error):
    engine.stats_script = [error]
    channel = AcestreamChannel(id='a' * 40, name='Example')
    if isinstance(error, asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await probe.check_channel_status(channel)
    else:
        assert (await probe.check_channel_status(channel))['is_online'] is False
    assert engine.stopped == [f'{ENGINE}/ace/cmd/hash/session']


@pytest.mark.parametrize('url', ['http://evil.test/private', 'http://engine/ace/stat/../private', 'file:///etc/passwd'])
def test_session_links_cannot_escape_engine_routes(url):
    start = read_start('http://engine:6878', 'a' * 40, 200, {'response': {'stat_url': url, 'command_url': url, 'playback_url': url}})
    assert (start.session.stat_url, start.session.command_url, start.session.playback_url) == (None, None, None)
    assert not start.session.verifiable


@pytest.mark.asyncio
async def test_probe_player_ids_are_unique_between_service_instances(db_session, monkeypatch):
    use_engines(db_session, monkeypatch)
    ids = []
    for _ in range(2):
        engine = FakeProbeEngine(start=(200, {'error': 'not found'}))
        service = ChannelStatusService(db_session, probe_engine=engine)
        await service.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), persist=False)
        ids.append(engine.asked('open')[0][2])
    assert ids[0] != ids[1]


@pytest.mark.asyncio
async def test_downloads_without_verified_media_are_not_online(probe, monkeypatch):
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    for metadata in [None, {'signal_verified': False, 'bitrate_bps': None, 'audio_tracks': []}, {'signal_verified': True, 'bitrate_bps': 8_000_000, 'audio_tracks': [{'index': 0, 'language': 'spa'}]}]:
        monkeypatch.setattr('app.services.channel_status_service.probe_media', AsyncMock(return_value=metadata))
        engine = FakeProbeEngine(stats=growing())
        probe.probe_engine = engine
        result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'))
        assert result['is_online'] is bool(metadata and metadata['signal_verified'])
        assert result['network_status'] == 'found'
        assert probe.channel_repository.update_channel_status.call_args.kwargs['bitrate_bps'] == (metadata['bitrate_bps'] if metadata else None)
        assert probe.channel_repository.update_channel_status.call_args.kwargs['audio_tracks'] == (metadata['audio_tracks'] if metadata else None)
        assert len(engine.stopped) == 1


@pytest.mark.asyncio
async def test_probes_use_distinct_pids_but_timeout_retry_reuses_pid(probe, engine):
    engine.start_script = [asyncio.TimeoutError(), (500, None), (500, None)]
    channel = AcestreamChannel(id='a' * 40, name='Example')
    await probe.check_channel_status(channel, persist=False)
    await probe.check_channel_status(channel, persist=False)
    opens = engine.asked('open')
    pids = [call[2] for call in opens]
    assert len(pids[0]) == 32
    assert pids[0] == pids[1]
    assert pids[0] != pids[2]
    # The retry doubles the start timeout.
    assert [call[3] for call in opens] == [0.015, 0.03, 0.015]


@pytest.mark.asyncio
@pytest.mark.parametrize('starts', [
    [asyncio.TimeoutError(), asyncio.TimeoutError()],
    [(200, None)],
    [asyncio.TimeoutError(), (200, None)],
], ids=['both starts time out', 'answer is not JSON', 'retry answer is not JSON'])
async def test_a_start_without_a_usable_answer_has_its_session_stopped(probe, engine, starts):
    """The engine opens the session even when the check never reads its
    answer; asking again with the same PID hands that session back."""
    engine.start_script = [*starts, (200, session_answer(token='unanswered'))]
    channel = AcestreamChannel(id='a' * 40, name='Example')
    result = await probe.check_channel_status(channel, persist=False)
    assert result['is_online'] is False
    pids = {call[2] for call in engine.asked('open')}
    assert len(pids) == 1
    assert engine.stopped == ['http://engine.test:6878/ace/cmd/hash/unanswered']


@pytest.mark.asyncio
async def test_a_timed_out_start_is_not_stopped_once_playback_holds_the_source(probe, engine):
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example', is_online=True)
    claim = None

    def start(*_args):
        nonlocal claim
        if claim is None:
            claim = relay_registry.open(channel.id, 'test')
            return asyncio.TimeoutError()
        return 200, session_answer(token='unanswered')

    engine.start_script = [start]
    try:
        assert (await probe.check_channel_status(channel, persist=False))['status'] == 'skipped'
        # Distinct PIDs do not isolate a stop of the same source.
        assert engine.stopped == []
    finally:
        if claim:
            relay_registry.close(claim.id)


@pytest.mark.asyncio
async def test_active_relay_is_not_probed_or_marked_offline(probe, engine):
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example', is_online=True)
    claim = relay_registry.open(channel.id, 'test')
    try:
        result = await probe.check_channel_status(channel)
        assert result['status'] == 'skipped'
        assert result['is_online'] is True
        assert engine.calls == []
        probe.channel_repository.update_channel_status.assert_not_called()
    finally:
        relay_registry.close(claim.id)


@pytest.mark.asyncio
async def test_playback_started_during_probe_prevents_stop_and_status_overwrite(probe, engine):
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example', is_online=True)
    claim = None

    def start(*_args):
        nonlocal claim
        claim = relay_registry.open(channel.id, 'test')
        return 200, session_answer()

    engine.start_script = [start]
    engine.stats_script = [stat_answer(status='error')]
    try:
        assert (await probe.check_channel_status(channel))['status'] == 'skipped'
        # The app now plays the source: its session is left to the engine.
        assert engine.stopped == []
        probe.channel_repository.update_channel_status.assert_not_called()
    finally:
        if claim:
            relay_registry.close(claim.id)


@pytest.mark.asyncio
@pytest.mark.parametrize('owner', ['nobody', 'playback lease', 'app relay'])
async def test_probe_session_is_given_back_by_source_ownership(probe, engine, owner):
    """Stopped when nobody plays the source; parked for the final playback stop
    while a lease holds it; left to the engine while the app plays it."""
    import httpx
    from app.services.engine_client import EngineClient
    from app.services.playback_ownership import source_ownership
    from app.services.stream_relay import relay_registry
    channel = AcestreamChannel(id='a' * 40, name='Example')
    probe_stop = f'{ENGINE}/ace/cmd/hash/session'
    played = []

    def playback_engine(request):
        played.append(str(request.url))
        return httpx.Response(200, json={'response': {
            'playback_url': f'{ENGINE}/ace/r/hash/viewer', 'stat_url': f'{ENGINE}/ace/stat/hash/viewer',
            'command_url': f'{ENGINE}/ace/cmd/hash/viewer'}, 'error': None})

    client = EngineClient(ENGINE, client=httpx.Client(transport=httpx.MockTransport(playback_engine)))
    viewer = client.start(channel.id) if owner == 'playback lease' else None
    claim = None

    def start(*_args):
        nonlocal claim
        if owner == 'app relay':
            claim = relay_registry.open(channel.id, 'test')
        return 200, session_answer()

    engine.start_script = [start]
    engine.stats_script = [stat_answer(status='stopped')]
    try:
        await probe.check_channel_status(channel, persist=False)
        if owner == 'nobody':
            assert engine.stopped == [probe_stop]
        elif owner == 'app relay':
            assert engine.stopped == []
        else:
            assert engine.stopped == []
            assert [parked.command_url for parked in source_ownership(ENGINE, channel.id).parked] == [probe_stop]
            client.stop(viewer)
            assert played[1:] == [f'{ENGINE}/ace/cmd/hash/viewer?method=stop', f'{probe_stop}?method=stop']
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
async def test_engine_recovery_precedes_channel_start(probe, engine, clock):
    engine.ready_script = [False, False, True, True]
    engine.start_script = [(200, {'error': 'no peers'})]
    await probe.check_channel_status(AcestreamChannel(id='b' * 40, name='Example'))
    assert [call[0] for call in engine.calls][:4] == ['ready', 'ready', 'ready', 'open']
    # Polled every two seconds.
    assert clock.now == pytest.approx(4.0)


@pytest.mark.asyncio
async def test_engine_down_preserves_last_known_status(probe, engine, clock):
    engine.ready_script = [False]
    result = await probe.check_channel_status(AcestreamChannel(id='c' * 40, name='Example', is_online=True))
    assert result['status'] == 'skipped'
    assert result['is_online'] is True
    assert engine.asked('open') == []
    # Waited about a minute for the engine to come back.
    assert 60.0 <= clock.now < 62.0
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.asyncio
async def test_engine_crash_during_probe_does_not_mark_channel_offline(probe, engine):
    engine.ready_script = [True, False]
    engine.start_script = [ConnectionError()]
    result = await probe.check_channel_status(AcestreamChannel(id='d' * 40, name='Example', is_online=True))
    assert result['status'] == 'skipped'
    probe.channel_repository.update_channel_status.assert_not_called()


@pytest.mark.parametrize('payload,expected', [({'result': {'version': {}}}, True), ({'response': {}}, False), ({'result': None}, False), ({'error': 'starting'}, False)])
def test_readiness_requires_engine_status_response(payload, expected):
    assert read_ready(200, payload) is expected
    assert read_ready(503, None) is False


@pytest.mark.asyncio
@pytest.mark.parametrize('http_status,payload,expected', [
    (200, {'error': 'not found'}, 'not_found'),
    (200, {'error': 'content not found'}, 'not_found'),
    (200, {'error': 'no peers'}, 'unknown'),
    (404, None, 'unknown'),  # an absent API route is not an absent content ID
    (500, None, 'unknown'),
])
async def test_lookup_failure_is_separate_from_signal(probe, engine, http_status, payload, expected):
    engine.start_script = [(http_status, payload)]
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
async def test_dedicated_checker_down_never_falls_back_to_playback(db_session, monkeypatch, clock):
    use_engines(db_session, monkeypatch, checker='http://checker.test:6879')
    engine = FakeProbeEngine(ready=False)
    service = ChannelStatusService(db_session, probe_engine=engine)
    service.channel_repository = MagicMock()
    result = await service.check_channel_status(AcestreamChannel(id='f' * 40, name='Example'))
    assert engine.requested_url == 'http://checker.test:6879'
    assert engine.asked('open') == []
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


@pytest.mark.asyncio
@pytest.mark.parametrize('verified', [True, False])
async def test_outpace_idle_lease_reads_media_and_releases(probe, engine, monkeypatch, verified):
    engine.start_script = [(200, session_answer(playback_session_id='session'))]
    engine.stats_script = [stat_answer(status='idle', downloaded=0, client_session_id=-1, playback_session_id='session')]
    sample = AsyncMock(return_value={'signal_verified': verified})
    monkeypatch.setattr('app.services.channel_status_service.probe_media', sample)
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Test'), persist=False)
    assert result['is_online'] is verified
    sample.assert_awaited_once_with(ENGINE, f'{ENGINE}/ace/r/hash/session', timeout=0.015)
    assert engine.stopped == [f'{ENGINE}/ace/cmd/hash/session']


# Engine stat series measured 2026-11-12 (seconds, status, MB downloaded).
# A stalled source hands its stored prebuffer over in one go and stays flat.
STALLED = [(1, 'prebuf', 0.0), (2, 'prebuf', 1.8)] + [(t, 'dl', 9.44) for t in range(3, 61)]
# Same, but the handover trickles in over 25 s before going flat.
SLOW_HANDOVER = ([(t, 'prebuf', 0.41 * (t - 1)) for t in range(1, 21)]
                 + [(21, 'dl', 8.4), (22, 'dl', 8.7), (23, 'dl', 9.0), (24, 'dl', 9.2)]
                 + [(t, 'dl', 9.44) for t in range(25, 91)])
# Live sources: about 1 MB/s, or a slow one in 1 MB pieces with long gaps.
LIVE = [(1, 'prebuf', 2.6)] + [(t, 'dl', 11.5 + 1.05 * (t - 2)) for t in range(2, 61)]
SLOW_LIVE = ([(1, 'prebuf', 0.0)] + [(t, 'dl', 9.44) for t in range(3, 12)]
             + [(t, 'dl', 10.48) for t in range(12, 30)] + [(t, 'dl', 11.53) for t in range(30, 61)])


def verdict(series):
    growth = SustainedGrowth()
    for t, status, mb in series:
        result = growth.observe(float(t), status, mb * MB)
        if result is not None:
            return result, t
    return None, None


@pytest.mark.parametrize('series, expected, by', [
    (STALLED, False, 28),
    (SLOW_HANDOVER, False, 46),
    (LIVE, True, 6),
    (SLOW_LIVE, True, 12),
])
def test_sustained_growth_tells_live_from_a_prebuffer_handover(series, expected, by):
    result, at = verdict(series)
    assert result is expected
    assert at <= by


def engine_replaying(series, clock):
    def stats(_session, _timeout):
        current = [row for row in series if row[0] <= clock.now + 1] or series[:1]
        _t, status, mb = current[-1]
        return stat_answer(status=status, downloaded=int(mb * MB))
    return FakeProbeEngine(stats=stats)


@pytest.mark.asyncio
@pytest.mark.parametrize('series, online', [(STALLED, False), (SLOW_HANDOVER, False), (LIVE, True), (SLOW_LIVE, True)])
async def test_stalled_sources_are_offline_even_with_media_in_the_handover(probe, db_session, monkeypatch, clock, series, online):
    media_probe = AsyncMock(return_value={'signal_verified': True})  # the handover carries real A/V
    monkeypatch.setattr('app.services.channel_status_service.probe_media', media_probe)
    use_engines(db_session, monkeypatch, timeout='10')
    engine = engine_replaying(series, clock)
    probe.probe_engine = engine
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), persist=False)
    assert result['is_online'] is online
    assert media_probe.await_count == (1 if online else 0)
    assert clock.now < 10.0 + 25.0 + 25.0
    assert len(engine.stopped) == 1
