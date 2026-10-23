"""Catalogue/event boundaries exercised through the public reviewed API."""
import json
import pytest
from sqlalchemy import create_engine, inspect, text
from migration_test_utils import database_url_for, upgrade_to_revision, upgrade_to_head

A = 'a' * 40


def save_catalogue(client, stations, **options):
    preview = client.post('/api/v1/catalogues/preview', json={'sample': json.dumps({'stations': stations})})
    assert preview.status_code == 200, preview.text
    saved = client.post('/api/v1/catalogues', json={'preview_token': preview.json()['preview_token'],
        'name': 'Mixed catalogue', 'selected_branches': ['root'], **options})
    assert saved.status_code == 200, saved.text
    return saved.json()


def event_preview(client, catalogue, **fields):
    return client.post(f"/api/v1/catalogues/{catalogue['id']}/events/preview", json={
        'revision': catalogue['revision'], 'entry_ids': [catalogue['entries'][1]['id']],
        'title': 'Reviewed match', 'timezone': 'Europe/Madrid', **fields})


def apply(client, preview):
    assert preview.status_code == 200, preview.text
    return client.post('/api/v1/events/apply', json={'token': preview.json()['token'],
        'selected_ids': [preview.json()['events'][0]['id']]})


def test_reviewed_classification_precedes_transport_and_refresh(client, db_session, monkeypatch):
    from app.models.models import AcestreamChannel
    from app.services.catalogue_service import CatalogueService
    from app.utils.bounded_source import SourceResponse
    rows = [{'name': 'Movie', 'type': 'movie', 'url': f'acestream://{A}'},
            {'name': 'Match', 'type': 'event', 'url': f'acestream://{A}'},
            {'name': 'Live', 'url': 'acestream://' + 'b' * 40}]
    saved = save_catalogue(client, rows, confirm_live=True)
    assert [e['imported'] for e in saved['entries'][1:]] == [False, False, True]
    assert db_session.query(AcestreamChannel).count() == 1
    unreviewed = save_catalogue(client, [{'name': 'Unknown', 'url': f'acestream://{A}'}])
    assert not unreviewed['entries'][1]['imported']
    async def fetch(*args, **kwargs):
        return SourceResponse(200, json.dumps({'stations': rows}).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', fetch)
    preview = client.post('/api/v1/catalogues/preview', json={'url': 'https://example.test/list'}).json()
    saved = client.post('/api/v1/catalogues', json={'preview_token': preview['preview_token'],
        'name': 'Remote', 'selected_branches': ['root'], 'confirm_live': True}).json()
    rows.append({'name': 'New unknown', 'url': 'acestream://' + 'c' * 40})
    refreshed = CatalogueService(db_session).refresh(saved['id'])
    assert not refreshed.entries[-1].imported
    assert db_session.query(AcestreamChannel).count() == 1


def test_catalogue_event_uses_private_shared_media_and_checks_revision(client, db_session):
    from app.models.models import AcestreamChannel, TVChannel, EventMedia
    saved = save_catalogue(client, [{'id': 'fixture-match', 'type': 'event', 'name': 'Match',
        'url': 'https://media.test/match.m3u8?token=PRIVATE', 'referer': 'https://page.test/?key=SECRET'}])
    preview = event_preview(client, saved, starts_at='2026-10-24T19:00:00')
    assert 'PRIVATE' not in preview.text and 'SECRET' not in preview.text
    event = apply(client, preview).json()[0]
    assert event['starts_at'] == '2026-10-24T17:00:00Z'
    assert event['provenance'][0]['source_kind'] == 'w3u'
    assert event['broadcasts'][0]['compatibility'] == 'playable'
    media = db_session.get(EventMedia, event['broadcasts'][0]['content_id'])
    assert media.url.endswith('token=PRIVATE') and media.headers['referer'].endswith('key=SECRET')
    assert db_session.query(AcestreamChannel).count() == db_session.query(TVChannel).count() == 0
    assert event_preview(client, saved).status_code == 422
    current = client.get(f"/api/v1/catalogues/{saved['id']}").json()
    stale = event_preview(client, current)
    client.delete(f"/api/v1/catalogues/{saved['id']}")
    rejected = apply(client, stale)
    assert rejected.status_code == 409
    assert client.get('/api/v1/events/' + event['id']).json()['revision'] == event['revision']
    # Reusing the integer catalogue ID after removal must not overwrite an event.
    replacement = save_catalogue(client, [{'id': 'fixture-match', 'name': 'Other', 'url': f'acestream://{A}'}])
    other = apply(client, event_preview(client, replacement)).json()[0]
    assert other['id'] != event['id']


def test_catalogue_event_requires_timezone_and_rejects_vod(client):
    saved = save_catalogue(client, [{'name': 'Match', 'url': f'acestream://{A}'}])
    assert event_preview(client, saved, starts_at='2026-10-25T02:30:00').status_code == 422
    vod = save_catalogue(client, [{'type': 'movie', 'name': 'Movie', 'url': f'acestream://{A}'}])
    assert event_preview(client, vod).status_code == 422


@pytest.mark.parametrize('revision', ['20261021_1200', '20261022_1200', '20261023_1200', '20261023_1300', '20261023_1400'])
def test_merge_migration_preserves_both_histories(tmp_path, revision):
    path = tmp_path / f'{revision}.db'
    upgrade_to_revision(path, revision)
    engine = create_engine(database_url_for(path))
    try:
        tables = inspect(engine).get_table_names()
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO acestream_channels (id, name) VALUES ('existing', 'Manual')"))
            if 'w3u_catalogues' in tables:
                conn.execute(text("INSERT INTO w3u_catalogues (name, revision, snapshot, selected_branches, mode, refresh_enabled, updated_at) VALUES ('Saved', 3, '{}', '[]', 'compatible', 0, '2026-10-23')"))
            if 'sporting_events' in tables:
                conn.execute(text("INSERT INTO sporting_events (id, owner_id, revision, fields, followed, archived) VALUES ('fixture', 'source', 2, '{}', 1, 0)"))
        upgrade_to_head(path)
        upgrade_to_head(path)
        assert {'w3u_catalogues', 'sporting_events', 'event_schedule_sources', 'telegram_sources', 'telegram_observations'} <= set(inspect(engine).get_table_names())
        with engine.connect() as conn:
            assert conn.execute(text('SELECT version_num FROM alembic_version')).scalars().all() == ['20261023_1500']
            assert conn.execute(text('SELECT name FROM acestream_channels')).scalar() == 'Manual'
            if 'w3u_catalogues' in tables:
                assert conn.execute(text('SELECT revision FROM w3u_catalogues')).scalar() == 3
            if 'sporting_events' in tables:
                assert conn.execute(text('SELECT followed FROM sporting_events')).scalar() == 1
    finally:
        engine.dispose()


def test_removed_catalogue_id_reuse_cannot_apply_stale_event_preview(client):
    saved = save_catalogue(client, [{'id': 'event', 'name': 'First', 'url': f'acestream://{A}'}])
    preview = event_preview(client, saved)
    client.delete(f"/api/v1/catalogues/{saved['id']}")
    replacement = save_catalogue(client, [{'id': 'event', 'name': 'Replacement', 'url': f'acestream://{A}'}])
    assert replacement['id'] == saved['id'] and replacement['revision'] == saved['revision']
    assert apply(client, preview).status_code == 409
    assert client.get('/api/v1/events').json()['total'] == 0


def test_reviewed_w3u_update_keeps_event_identity_and_manual_state(client, db_session, monkeypatch):
    from app.services.catalogue_service import CatalogueService
    from app.utils.bounded_source import SourceResponse
    from app.models.models import AcestreamChannel, EventMedia
    signed = 'first'
    async def fetch(*args, **kwargs):
        return SourceResponse(200, json.dumps({'stations': [{'id': 'stable-match', 'type': 'event',
            'name': 'Publisher title', 'url': f'https://media.test/live.m3u8?token={signed}'}]}).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', fetch)
    raw = client.post('/api/v1/catalogues/preview', json={'url': 'https://example.test/list'}).json()
    saved = client.post('/api/v1/catalogues', json={'preview_token': raw['preview_token'], 'name': 'Remote',
        'selected_branches': ['root'], 'confirm_live': True}).json()
    event = apply(client, event_preview(client, saved)).json()[0]
    old_content = event['broadcasts'][0]['content_id']
    client.patch('/api/v1/events/' + event['id'], json={'revision': event['revision'], 'followed': True,
        'correction': {'title': 'Manual title', 'timezone': 'UTC', 'state': 'postponed'}})
    signed = 'rotated'
    current = CatalogueService(db_session).refresh(saved['id']).model_dump(mode='json')
    # Catalogue refresh alone must not change the reviewed event's observation.
    assert client.get('/api/v1/events/' + event['id']).json()['broadcasts'][0]['content_id'] == old_content
    updated = apply(client, event_preview(client, current)).json()[0]
    assert updated['id'] == event['id'] and updated['title'] == 'Manual title'
    assert updated['followed'] and updated['state'] == 'postponed'
    assert updated['broadcasts'][0]['content_id'] != old_content
    assert db_session.get(EventMedia, old_content) is None
    assert db_session.query(AcestreamChannel).count() == 0
