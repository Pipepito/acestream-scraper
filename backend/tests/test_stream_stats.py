from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.models.models import AcestreamChannel
from app.services.channel_status_service import ChannelStatusService
from app.services.stream_stats import stream_stats_sample


@pytest.mark.parametrize('value', [None, True, False, '12', -1, float('nan'), float('inf'), {}, 10**400])
def test_invalid_metrics_are_unknown(value):
    assert stream_stats_sample({'peers': value, 'speed_down': value, 'speed_up': value}) is None


def test_zero_fractional_speeds_and_independent_missing_values():
    sample = stream_stats_sample({'peers': 0, 'speed_down': 2.5})
    assert sample['peers'] == 0
    assert sample['download_speed_kbytes_sec'] == 2.5
    assert sample['upload_speed_kbytes_sec'] is None
    assert datetime.fromisoformat(sample['observed_at']).tzinfo is not None
    assert stream_stats_sample({'peers': 1.5}) is None


def test_migration_preserves_rows_and_fresh_schema(tmp_path):
    from sqlalchemy import create_engine, inspect, text
    from migration_test_utils import upgrade_to_revision, upgrade_to_head, downgrade_to_revision, database_url_for
    path = tmp_path / 'stats.db'
    upgrade_to_revision(path, '20260914_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO acestream_channels (id, name, bitrate_bps) VALUES ('existing', 'Existing', 8000000)"))
    upgrade_to_head(path)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT name, bitrate_bps, stream_stats FROM acestream_channels')).one() == ('Existing', 8000000, None)
    downgrade_to_revision(path, '20260914_1200')
    assert 'stream_stats' not in {c['name'] for c in inspect(engine).get_columns('acestream_channels')}
    upgrade_to_head(path)
    engine.dispose()
    fresh = tmp_path / 'fresh.db'
    upgrade_to_head(fresh)
    engine = create_engine(database_url_for(fresh))
    assert 'stream_stats' in {c['name'] for c in inspect(engine).get_columns('acestream_channels')}
    engine.dispose()


@pytest.mark.asyncio
async def test_probe_persists_atomic_latest_sample_and_api_exposes_it(db_session, client, monkeypatch):
    from app.repositories.channel_repository import ChannelRepository
    from app.services.probe_queue import ProbeQueue
    monkeypatch.setattr('app.services.channel_status_service.probe_queue', ProbeQueue(cooldown=0, outage_backoff=0))
    monkeypatch.setattr('app.services.channel_status_service.asyncio.sleep', AsyncMock())
    monkeypatch.setattr('app.services.channel_status_service.probe_media', AsyncMock(return_value={'signal_verified': True, 'bitrate_bps': 8_000_000}))
    channel = AcestreamChannel(id='a' * 40, name='Stats stream')
    db_session.add(channel)
    db_session.commit()
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine:6878'
    service._engine_ready = AsyncMock(return_value=True)
    service._fetch_engine_response = AsyncMock(side_effect=[
        (200, {'response': {'stat_url': '/ace/stat/a/b', 'command_url': '/ace/cmd/a/b', 'playback_url': '/ace/r/a/b'}}, None),
        (200, {'response': {'status': 'dl', 'downloaded': 100, 'peers': 12, 'speed_down': 900, 'speed_up': 10}}, None),
        (200, {'response': {'status': 'dl', 'downloaded': 200, 'peers': 0, 'speed_down': 0}}, None),
        (200, {'response': 'ok'}, None),
    ])
    result = await service.check_channel_status(channel)
    db_session.refresh(channel)
    assert channel.stream_stats == result['stream_stats']
    assert channel.stream_stats['peers'] == 0
    assert channel.stream_stats['download_speed_kbytes_sec'] == 0
    assert channel.stream_stats['upload_speed_kbytes_sec'] is None  # not retained from earlier poll
    assert channel.bitrate_bps == 8_000_000
    assert result['is_online'] is True  # verified media, independent of instantaneous speed
    response = client.get(f'/api/v1/channels/{channel.id}')
    assert response.status_code == 200
    assert response.json()['stream_stats'] == channel.stream_stats
    previous = dict(channel.stream_stats)
    ChannelRepository(db_session).update_channel_status(channel.id, False, 'No sample')
    assert channel.stream_stats == previous  # its original age remains visible
    service._wait_for_engine = AsyncMock(return_value=False)
    skipped = await service.check_channel_status(channel, persist=False)
    assert skipped['status'] == 'skipped'
    assert skipped['stream_stats'] == previous
    db_session.refresh(channel)
    assert channel.stream_stats == previous


@pytest.mark.asyncio
async def test_peers_without_transfer_are_sampled_but_not_online(db_session):
    channel = AcestreamChannel(id='b' * 40, name='No transfer')
    service = ChannelStatusService(db_session)
    service._get_engine_url = lambda: 'http://engine:6878'
    service._engine_ready = AsyncMock(return_value=True)
    service._get_timeout = lambda: 0.01
    async def fetch(url, params, timeout):
        if '/getstream' in url:
            return 200, {'response': {'stat_url': '/ace/stat/a/b', 'command_url': '/ace/cmd/a/b'}}, None
        return 200, {'response': {'status': 'dl', 'downloaded': 100, 'peers': 10, 'speed_down': 0}}, None
    service._fetch_engine_response = fetch
    result = await service._check_channel_status(channel, persist=False)
    assert result['is_online'] is False
    assert result['stream_stats']['peers'] == 10
    assert result['stream_stats']['download_speed_kbytes_sec'] == 0
