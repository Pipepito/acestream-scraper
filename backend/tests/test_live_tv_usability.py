"""Offline retention and explicit linking must preserve uncertain/user-owned data."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, inspect

from app.models.models import AcestreamChannel, ScrapedURL, TVChannel
from app.repositories.channel_repository import ChannelRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import OfflineCleanupConfig
from app.services.offline_cleanup_service import OfflineCleanupService
from app.services.tv_matching_service import normalize_name, similar_name_score
from migration_test_utils import database_url_for, upgrade_to_revision


def test_the_repository_only_stores_what_the_checker_saw_and_health_decides(db_session):
    channel = AcestreamChannel(id='a' * 40, name='Stream', is_online=False)
    db_session.add(channel)
    db_session.commit()
    repository = ChannelRepository(db_session)
    repository.update_channel_status(channel.id, False, 'Request timeout')
    assert (channel.failed_checks, channel.failing_since) == (0, None)
    repository.update_channel_status(channel.id, False, 'No packets', network_status='found')
    first = channel.failing_since
    assert first is not None and channel.failed_checks == 1
    # The streak starts at the very check that is stored, so a later check must come after it.
    assert channel.last_checked == first
    repository.update_channel_status(channel.id, False, 'Not found', network_status='not_found')
    assert channel.failing_since == first and channel.failed_checks == 2
    repository.update_channel_status(channel.id, True, network_status='found')
    assert (channel.failed_checks, channel.failing_since) == (0, None)


def test_an_http_check_counts_without_an_engine_lookup(db_session):
    channel = AcestreamChannel(id='url:' + 'a' * 40, name='Stream', stream_url='https://example.com/a.m3u8')
    db_session.add(channel)
    db_session.commit()
    ChannelRepository(db_session).update_channel_status(channel.id, False, 'HTTP 404', http=True)
    assert channel.failed_checks == 1 and channel.failing_since is not None


def test_cleanup_is_opt_in_previewed_and_only_removes_observed_offline_sources(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    source = ScrapedURL(url='https://example.com/playlist', enabled=True)
    tv = TVChannel(name='Keep this channel')
    db_session.add_all([source, tv])
    db_session.flush()
    def stream(key, **changes):
        values = dict(id=key * 40, name=key, source_url=source.url, is_online=False,
                      network_status='found', failed_checks=6, failing_since=now - timedelta(days=20),
                      last_checked=now - timedelta(hours=1))
        values.update(changes)
        row = AcestreamChannel(**values)
        db_session.add(row)
        return row
    stream('a')
    stream('b', is_online=True, failed_checks=0, failing_since=None)
    stream('c', failing_since=None)
    stream('d', last_checked=now - timedelta(days=2))
    stream('e', tv_channel_id=tv.id)
    stream('f', source_url=None)
    stream('1', network_status='unknown')                                                         # last check inconclusive: still counts
    stream('2', last_checked=now + timedelta(days=1))
    stream('3', failing_since=now - timedelta(days=1))
    stream('4', last_worked_at=now - timedelta(hours=2), failed_checks=0, failing_since=None)    # played since
    stream('5', failed_checks=4)                                                                  # not discarded
    stream('6', last_worked_at=now - timedelta(days=3))                                           # worked this week
    stream('7', network_status='unknown', stream_url='https://example.com/a.m3u8')                # HTTP: counts too
    db_session.commit()
    service = OfflineCleanupService(db_session)
    assert service.run()['status'] == 'disabled'
    config = OfflineCleanupConfig(enabled=True, rescrape=True)
    assert service.preview(config).eligible_streams == 3
    assert db_session.query(AcestreamChannel).count() == 13
    service.save(config)
    monkeypatch.setattr('app.services.viewing.watching', lambda: 'web player')
    assert service.run()['status'] == 'deferred'
    monkeypatch.setattr('app.services.viewing.watching', lambda: None)
    scrape = AsyncMock(return_value=([], 'OK'))
    monkeypatch.setattr('app.services.scraper_service.ScraperService.scrape_url', scrape)
    from app.services.task_service import task_service
    monkeypatch.setattr(task_service.shutdown_event, 'is_set', lambda: False)
    assert service.run() == {'deleted': 3, 'rescraped': 1, 'rescrape_failures': 0}
    scrape.assert_awaited_once_with(source.url, source.url_type)
    assert db_session.get(AcestreamChannel, 'a' * 40) is None
    assert db_session.get(AcestreamChannel, '7' * 40) is None
    assert db_session.get(AcestreamChannel, '1' * 40) is None
    assert db_session.get(AcestreamChannel, '5' * 40) is not None and db_session.get(AcestreamChannel, '6' * 40) is not None
    assert db_session.get(TVChannel, tv.id) is not None
    assert db_session.get(AcestreamChannel, 'e' * 40).tv_channel_id == tv.id


def test_the_second_streak_column_is_gone_after_the_upgrade_and_comes_back_on_downgrade(tmp_path):
    from migration_test_utils import downgrade_to_revision
    path = tmp_path / 'offline.db'
    upgrade_to_revision(path, '20261113_1400')
    engine = create_engine(database_url_for(path))
    try:
        assert 'offline_since' in {column['name'] for column in inspect(engine).get_columns('acestream_channels')}
        upgrade_to_revision(path, 'head')
        assert 'offline_since' not in {column['name'] for column in inspect(engine).get_columns('acestream_channels')}
        downgrade_to_revision(path, '20261113_1400')
        columns = {column['name']: column for column in inspect(engine).get_columns('acestream_channels')}
        assert columns['offline_since']['nullable'] is True
    finally:
        engine.dispose()


def test_cleanup_recognizes_normalized_sources_and_protects_disabled_sources(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    source = ScrapedURL(url='http://127.0.0.1:43110/example/playlist', url_type='auto', enabled=True)
    row = AcestreamChannel(id='9' * 40, name='Normalized source', source_url='zero://example/playlist',
                           is_online=False, network_status='not_found', failed_checks=6,
                           failing_since=now - timedelta(days=20), last_checked=now - timedelta(hours=1))
    db_session.add_all([source, row])
    db_session.commit()
    service = OfflineCleanupService(db_session)
    config = OfflineCleanupConfig(enabled=True, rescrape=True)
    assert service.preview(config).eligible_streams == 1
    source.enabled = False
    db_session.commit()
    assert service.preview(config).eligible_streams == 0
    source.enabled = True
    db_session.commit()
    service.save(config)
    monkeypatch.setattr('app.services.viewing.watching', lambda: None)
    scrape = AsyncMock(return_value=([], 'OK'))
    monkeypatch.setattr('app.services.scraper_service.ScraperService.scrape_url', scrape)
    from app.services.task_service import task_service
    monkeypatch.setattr(task_service.shutdown_event, 'is_set', lambda: False)
    assert service.run()['deleted'] == 1
    scrape.assert_awaited_once_with(source.url, 'auto')


def test_manual_add_and_link_is_atomic_and_preserves_existing_assignment(client, db_session):
    tv, other = TVChannel(name='Target'), TVChannel(name='Existing')
    db_session.add_all([tv, other])
    db_session.commit()
    payload = {'id': 'a' * 40, 'name': 'Stream', 'tv_channel_id': tv.id}
    response = client.post('/api/v1/acestream-channels/', json=payload)
    assert response.status_code == 201, response.text
    assert response.json()['tv_channel_id'] == tv.id
    payload.update(tv_channel_id=other.id, name='Should roll back')
    assert client.post('/api/v1/acestream-channels/', json=payload).status_code == 409
    db_session.expire_all()
    assert db_session.get(AcestreamChannel, payload['id']).name == 'Stream'
    payload.update(id='b' * 40, tv_channel_id=999999)
    assert client.post('/api/v1/acestream-channels/', json=payload).status_code == 404
    assert db_session.get(AcestreamChannel, payload['id']) is None


def test_search_add_and_link_resolves_then_links(client, db_session, monkeypatch):
    from app.services.search_catalogue_client import SearchCatalogueClient
    SettingsRepository(db_session).set_setting('ace_engine_url', 'http://engine')
    tv = TVChannel(name='Target')
    db_session.add(tv)
    db_session.commit()
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', lambda self, value: 'b' * 40)
    response = client.post('/api/v1/search/import', json={'items': [{'infohash': 'a' * 40, 'name': 'Found'}], 'tv_channel_id': tv.id})
    assert response.status_code == 200
    assert db_session.get(AcestreamChannel, 'a' * 40) is None
    assert db_session.get(AcestreamChannel, 'b' * 40).tv_channel_id == tv.id


@pytest.mark.parametrize('target,candidate', [('DAZN 1', 'DAZN 2'), ('DAZN 1', 'DAZN 1 BAR'), ('FR | Sport 1', 'ES | Sport 1')])
def test_review_hints_keep_number_and_edition_boundaries(target, candidate):
    assert similar_name_score(normalize_name(target), normalize_name(candidate)) is None


def test_similar_names_are_opt_in_and_apply_rechecks_metadata(client, db_session):
    tv = TVChannel(name='National Geographic')
    row = AcestreamChannel(id='c' * 40, name='National Geographik HD')
    db_session.add_all([tv, row])
    db_session.commit()
    endpoint = '/api/v1/tv-channels/automatch/'
    assert client.post(endpoint + 'preview', json={}).json()['candidates'] == []
    candidates = client.post(endpoint + 'preview', json={'include_similar': True}).json()['candidates']
    assert len(candidates) == 1 and candidates[0]['recommended'] is False
    request = {'include_similar': True, 'assignments': [{'acestream_channel_id': row.id, 'tv_channel_id': tv.id}]}
    row.name = 'Different station 2'
    db_session.commit()
    assert client.post(endpoint + 'apply', json=request).json()['assigned_count'] == 0
    row.name = 'National Geographik HD'
    db_session.commit()
    assert client.post(endpoint + 'apply', json=request).json()['assigned_count'] == 1
