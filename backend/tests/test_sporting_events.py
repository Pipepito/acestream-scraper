import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy import inspect, create_engine, text

from app.schemas.events import EventImport, EventFields
from migration_test_utils import database_url_for, upgrade_to_revision, downgrade_to_revision

FIXTURE = Path(__file__).parent / 'fixtures/events/schedule.json'


def schedule():
    return json.loads(FIXTURE.read_text())


def preview(client, payload=None):
    response = client.post('/api/v1/events/preview', json=payload or schedule())
    assert response.status_code == 200, response.text
    return response.json()


def apply(client, data, ids=None):
    response = client.post('/api/v1/events/apply', json={'token': data['token'],
        'selected_ids': ids or [e['id'] for e in data['events']]})
    assert response.status_code == 200, response.text
    return response.json()


def test_review_replay_postponement_and_private_media(alembic_client, alembic_db_session):
    client, db_session = alembic_client, alembic_db_session
    from app.models.models import AcestreamChannel, TVChannel, SportingEvent
    from app.services.player_http_source import stored_http_source
    data = preview(client)
    assert db_session.query(SportingEvent).count() == 0
    assert 'private-fixture' not in json.dumps(data)
    assert 'https://guide.example/' not in json.dumps(data)
    events = apply(client, data)
    match = next(e for e in events if e['title'].startswith('North'))
    assert match['starts_at'] == '2026-10-24T21:30:00Z'
    assert match['ends_at'] is None and match['state'] == 'scheduled'
    assert [b['compatibility'] for b in match['broadcasts']] == ['playable', 'playable', 'unresolved', 'unsupported']
    assert all(b['is_online'] is None for b in match['broadcasts'])
    assert db_session.query(AcestreamChannel).count() == db_session.query(TVChannel).count() == 0
    source = stored_http_source(match['broadcasts'][1]['content_id'])
    assert source.url.endswith('token=private-fixture')
    assert source.headers == {'referer': 'https://guide.example/'}
    payload = schedule()
    payload['observations'][0].update(state='postponed', starts_at='2026-10-26T00:30:00+01:00', broadcasts=[])
    refreshed = apply(client, preview(client, payload))
    updated = next(e for e in refreshed if e['id'] == match['id'])
    assert updated['state'] == 'postponed' and updated['starts_at'] == '2026-10-25T23:30:00Z'
    assert len(updated['broadcasts']) == 4
    assert client.get('/api/v1/events').json()['total'] == 2
    local = client.get('/api/v1/events', params={'day': '2026-10-26', 'zone': 'Europe/Madrid'}).json()
    assert [e['id'] for e in local['events']] == [match['id']]
    assert client.get('/api/v1/events', params={'day': '2026-10-25', 'zone': 'Europe/Madrid'}).json()['total'] == 0


@pytest.mark.parametrize('value', ['2026-03-29T02:30:00', '2026-10-25T02:30:00'])
def test_ambiguous_and_nonexistent_local_times_rejected(value):
    with pytest.raises(ValidationError, match='ambiguous or does not exist'):
        EventFields(title='Match', timezone='Europe/Madrid', starts_at=value)


@pytest.mark.parametrize(('value', 'expected'), [
    ('2026-10-25T02:30:00+02:00', '2026-10-25T00:30:00+00:00'),
    ('2026-10-25T02:30:00+01:00', '2026-10-25T01:30:00+00:00'),
    ('2026-10-24T23:30:00', '2026-10-24T21:30:00+00:00'),
])
def test_explicit_offsets_and_unambiguous_local_times(value, expected):
    result = EventFields(title='Match', timezone='Europe/Madrid', starts_at=value)
    assert result.starts_at.isoformat() == expected
    assert result.state == 'unknown' and result.ends_at is None


def test_corrections_survive_refresh_and_stale_previews_rejected(client):
    event = apply(client, preview(client))[0]
    stale = preview(client)
    correction = EventFields(title='Reviewed title', timezone='UTC', state='cancelled').model_dump(mode='json')
    response = client.patch('/api/v1/events/' + event['id'], json={'revision': event['revision'], 'correction': correction, 'followed': True})
    assert response.status_code == 200
    conflict = client.post('/api/v1/events/apply', json={'token': stale['token'], 'selected_ids': [event['id']]})
    assert conflict.status_code == 409
    refreshed = apply(client, preview(client))
    current = next(e for e in refreshed if e['id'] == event['id'])
    assert current['title'] == 'Reviewed title' and current['followed'] and current['corrected']
    reverted = client.patch('/api/v1/events/' + event['id'], json={'revision': current['revision'], 'correction': None}).json()
    assert not reverted['corrected'] and reverted['title'] != 'Reviewed title'


def test_shared_contract_linked_w3u_and_telegram_do_not_duplicate_or_override(client):
    event = apply(client, preview(client))[0]
    original = client.get('/api/v1/events/' + event['id']).json()
    for kind in ('w3u', 'telegram'):
        observation = dict(source_id=kind, source_name=kind, source_kind=kind, external_id='same-publisher-event',
            event_id=event['id'], title='Alternate spelling', timezone='UTC', state='live',
            broadcasts=[{'id': 'es', 'label': 'Sports Uno', 'url': 'acestream://' + 'a' * 40}])
        apply(client, preview(client, {'observations': [observation]}))
        apply(client, preview(client, {'observations': [observation]}))
    current = client.get('/api/v1/events/' + event['id']).json()
    assert current['title'] == original['title'] and current['state'] == original['state']
    assert len(current['provenance']) == 3
    assert client.get('/api/v1/events').json()['total'] == 2
    # Identical titles from another identity remain separate unless reviewed.
    observation.pop('event_id')
    observation['external_id'] = 'different-fixture'
    apply(client, preview(client, {'observations': [observation]}))
    assert client.get('/api/v1/events').json()['total'] == 3


def test_selection_expiry_invalid_import_and_archive(client, monkeypatch):
    from app.services import event_service
    data = preview(client)
    chosen = data['events'][0]['id']
    apply(client, data, [chosen])
    assert client.get('/api/v1/events').json()['total'] == 1
    assert client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': [chosen]}).status_code == 409
    data = preview(client)
    cached = event_service._PREVIEWS[data['token']]
    event_service._PREVIEWS[data['token']] = (0, *cached[1:])
    assert client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': [chosen]}).status_code == 409
    invalid = schedule()
    invalid['observations'][0]['broadcasts'][0]['headers'] = {'Authorization': 'super-secret'}
    result = client.post('/api/v1/events/preview', json=invalid)
    assert result.status_code == 422 and 'super-secret' not in result.text
    current = client.get('/api/v1/events/' + chosen).json()
    archived = client.patch('/api/v1/events/' + chosen, json={'revision': current['revision'], 'archived': True})
    assert archived.status_code == 200
    assert client.get('/api/v1/events').json()['total'] == 0
    assert client.get('/api/v1/events?archived=true').json()['total'] == 1


def test_invalid_times_and_input_limits(client):
    for change in ({'timezone': 'Not/AZone'}, {'starts_at': 'today'},
                   {'ends_at': '2026-01-01T00:00:00Z'}):
        payload = schedule()
        payload['observations'][0].update(change)
        assert client.post('/api/v1/events/preview', json=payload).status_code == 422
    response = client.post('/api/v1/events/preview', content=b' ' * (2 * 1024 * 1024 + 1), headers={'content-type': 'application/json'})
    assert response.status_code == 413
    assert client.get('/api/v1/events?zone=Invalid').status_code == 422


def test_broadcaster_mapping_requires_exact_reviewed_channel(client, db_session):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id='b' * 40, name='DAZN', is_active=True, is_online=True,
        last_checked=datetime(2026, 10, 22, tzinfo=timezone.utc)))
    db_session.commit()
    data = preview(client)
    assert data['events'][0]['broadcasts'][2]['content_id'] is None
    payload = schedule()
    payload['observations'][0]['broadcasts'][2]['channel_id'] = 'b' * 40
    mapped = preview(client, payload)['events'][0]['broadcasts'][2]
    assert mapped['content_id'] == 'b' * 40 and mapped['is_online'] is True


def test_migration_upgrade_and_downgrade_preserve_channels(tmp_path):
    path = tmp_path / 'events.sqlite'
    upgrade_to_revision(path, '20261021_1200')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as db:
            db.execute(text("INSERT INTO acestream_channels (id,name) VALUES ('existing','Existing')"))
        upgrade_to_revision(path, '20261023_1200')
        assert {'sporting_events', 'event_observations', 'event_media'} <= set(inspect(engine).get_table_names())
        downgrade_to_revision(path, '20261021_1200')
        with engine.connect() as db:
            assert db.execute(text('SELECT name FROM acestream_channels')).scalar() == 'Existing'
        upgrade_to_revision(tmp_path / 'fresh.sqlite', 'head')
    finally:
        engine.dispose()


def test_event_api_auth_and_invalid_selection(client, monkeypatch):
    monkeypatch.setenv('API_TOKEN', 'event-test-token')
    assert client.get('/api/v1/events').status_code == 401
    assert client.post('/api/v1/events/preview', json=schedule()).status_code == 401
    headers = {'X-Api-Token': 'event-test-token'}
    data = client.post('/api/v1/events/preview', json=schedule(), headers=headers).json()
    result = client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': ['unknown']}, headers=headers)
    assert result.status_code == 409
    assert client.get('/api/v1/events', headers=headers).json()['total'] == 0


def test_new_concurrent_previews_cannot_duplicate_source_identity(client):
    first, second = preview(client), preview(client)
    apply(client, first)
    result = client.post('/api/v1/events/apply', json={'token': second['token'],
        'selected_ids': [e['id'] for e in second['events']]})
    assert result.status_code == 409
    assert client.get('/api/v1/events').json()['total'] == 2


def test_apply_rechecks_inventory_limit_after_other_imports(client, monkeypatch):
    from app.services import event_service
    monkeypatch.setattr(event_service, '_MAX_EVENTS', 2)
    first = preview(client)
    payload = schedule()
    payload['observations'][0]['external_id'] = 'another-match'
    payload['observations'] = payload['observations'][:1]
    second = preview(client, payload)
    apply(client, first)
    result = client.post('/api/v1/events/apply', json={'token': second['token'],
        'selected_ids': [e['id'] for e in second['events']]})
    assert result.status_code == 409
    assert client.get('/api/v1/events').json()['total'] == 2
