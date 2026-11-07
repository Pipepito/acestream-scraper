"""Offline retention and explicit linking must preserve uncertain/user-owned data."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, inspect, text

from app.models.models import AcestreamChannel, ScrapedURL, TVChannel
from app.repositories.channel_repository import ChannelRepository
from app.repositories.settings_repository import SettingsRepository
from app.schemas.config import OfflineCleanupConfig
from app.services.offline_cleanup_service import OfflineCleanupService
from app.services.tv_matching_service import normalize_name, similar_name_score
from migration_test_utils import database_url_for, upgrade_to_revision


def test_offline_streak_requires_confirmed_checks_and_resets(db_session):
    channel = AcestreamChannel(id='a' * 40, name='Stream', is_online=False)
    db_session.add(channel); db_session.commit()
    repository = ChannelRepository(db_session)
    repository.update_channel_status(channel.id, False, 'Request timeout')
    assert channel.offline_since is None
    repository.update_channel_status(channel.id, False, 'No packets', network_status='found')
    first = channel.offline_since
    assert first is not None
    repository.update_channel_status(channel.id, False, 'Not found', network_status='not_found')
    assert channel.offline_since == first
    repository.update_channel_status(channel.id, True, network_status='found')
    assert channel.offline_since is None


def test_cleanup_is_opt_in_previewed_and_only_removes_observed_offline_sources(db_session, monkeypatch):
    now = datetime.now(timezone.utc)
    source = ScrapedURL(url='https://example.com/playlist', enabled=True)
    tv = TVChannel(name='Keep this channel')
    db_session.add_all([source, tv]); db_session.flush()
    def stream(key, **changes):
        values = dict(id=key * 40, name=key, source_url=source.url, is_online=False,
                      network_status='found', offline_since=now - timedelta(days=20),
                      last_checked=now - timedelta(hours=1))
        values.update(changes)
        row = AcestreamChannel(**values); db_session.add(row)
        return row
    stream('a')
    stream('b', is_online=True)
    stream('c', offline_since=None)
    stream('d', last_checked=now - timedelta(days=2))
    stream('e', tv_channel_id=tv.id)
    stream('f', source_url=None)
    stream('1', network_status='unknown')
    stream('2', last_checked=now + timedelta(days=1))
    stream('3', offline_since=now - timedelta(days=1))
    db_session.commit()
    service = OfflineCleanupService(db_session)
    assert service.run()['status'] == 'disabled'
    config = OfflineCleanupConfig(enabled=True, rescrape=True)
    assert service.preview(config).eligible_streams == 1
    assert db_session.query(AcestreamChannel).count() == 9
    service.save(config)
    monkeypatch.setattr('app.services.viewing.watching', lambda: 'web player')
    assert service.run()['status'] == 'deferred'
    monkeypatch.setattr('app.services.viewing.watching', lambda: None)
    scrape = AsyncMock(return_value=([], 'OK'))
    monkeypatch.setattr('app.services.scraper_service.ScraperService.scrape_url', scrape)
    from app.services.task_service import task_service
    monkeypatch.setattr(task_service.shutdown_event, 'is_set', lambda: False)
    assert service.run() == {'deleted': 1, 'rescraped': 1, 'rescrape_failures': 0}
    scrape.assert_awaited_once_with(source.url, source.url_type)
    assert db_session.get(AcestreamChannel, 'a' * 40) is None
    assert db_session.get(TVChannel, tv.id) is not None
    assert db_session.get(AcestreamChannel, 'e' * 40).tv_channel_id == tv.id


def test_cleanup_schema_upgrade_keeps_unknown_age(tmp_path):
    path = tmp_path / 'offline.db'
    upgrade_to_revision(path, '20261102_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO acestream_channels (id, name, is_online) VALUES ('old', 'Old offline', 0)"))
    upgrade_to_revision(path, 'head')
    try:
        assert 'offline_since' in {column['name'] for column in inspect(engine).get_columns('acestream_channels')}
        with engine.connect() as connection:
            assert connection.execute(text("SELECT offline_since FROM acestream_channels WHERE id='old'")).scalar() is None
    finally:
        engine.dispose()


def test_manual_add_and_link_is_atomic_and_preserves_existing_assignment(client, db_session):
    tv, other = TVChannel(name='Target'), TVChannel(name='Existing')
    db_session.add_all([tv, other]); db_session.commit()
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
    tv = TVChannel(name='Target'); db_session.add(tv); db_session.commit()
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
    db_session.add_all([tv, row]); db_session.commit()
    endpoint = '/api/v1/tv-channels/automatch/'
    assert client.post(endpoint + 'preview', json={}).json()['candidates'] == []
    candidates = client.post(endpoint + 'preview', json={'include_similar': True}).json()['candidates']
    assert len(candidates) == 1 and candidates[0]['recommended'] is False
    request = {'include_similar': True, 'assignments': [{'acestream_channel_id': row.id, 'tv_channel_id': tv.id}]}
    row.name = 'Different station 2'; db_session.commit()
    assert client.post(endpoint + 'apply', json=request).json()['assigned_count'] == 0
    row.name = 'National Geographik HD'; db_session.commit()
    assert client.post(endpoint + 'apply', json=request).json()['assigned_count'] == 1
