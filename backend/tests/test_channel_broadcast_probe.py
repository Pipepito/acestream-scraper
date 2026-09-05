import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.models import AcestreamChannel
from app.services.channel_status_service import ChannelStatusService


@pytest.fixture
def probe(db_session):
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine.test:6878'
    service._get_timeout = lambda: 0.015
    service.channel_repository = MagicMock()
    return service


def session_response():
    return {'response': {
        'is_live': 1,
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
async def test_only_increasing_downloads_confirm_broadcast_and_stop_session(probe, monkeypatch):
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    probe._fetch_engine_response = AsyncMock(side_effect=[
        (200, session_response(), None),
        (200, {'response': {'status': 'dl', 'downloaded': 100}}, None),
        (200, {'response': {'status': 'dl', 'downloaded': 200}}, None),
        (200, {'response': 'ok'}, None),
    ])
    result = await probe.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), identifier='infohash', persist=False)
    assert result['is_online'] is True
    calls = probe._fetch_engine_response.call_args_list
    assert calls[0].args[1]['infohash'] == 'a' * 40
    assert 'method' not in calls[0].args[1]
    assert calls[1].args[0] == 'http://engine.test:6878/ace/stat/hash/session'
    assert calls[-1].args[:2] == ('http://engine.test:6878/ace/cmd/hash/session', {'method': 'stop'})
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
        service._fetch_engine_response = AsyncMock(return_value=(200, {'error': 'not found'}, None))
        await service.check_channel_status(AcestreamChannel(id='a' * 40, name='Example'), persist=False)
        ids.append(service._fetch_engine_response.call_args.args[1]['pid'])
    assert ids[0] != ids[1]
