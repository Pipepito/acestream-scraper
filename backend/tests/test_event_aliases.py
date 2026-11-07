"""Broadcaster aliases: one manual link applies to every event of a source with that broadcaster."""
from datetime import datetime, timezone
import json

from sqlalchemy import create_engine, inspect, text

from migration_test_utils import database_url_for, upgrade_to_revision, downgrade_to_revision
from test_event_providers import plain_schedule
from test_sporting_events import preview, apply


def test_alias_migration_upgrade_and_downgrade(tmp_path):
    path = tmp_path / 'aliases.sqlite'
    upgrade_to_revision(path, '20261103_1200')
    engine = create_engine(database_url_for(path))
    try:
        columns = {c['name'] for c in inspect(engine).get_columns('event_broadcaster_aliases')}
        assert {'id', 'source_id', 'label', 'normalized_label', 'target', 'created_at', 'updated_at'} <= columns
        now = datetime.now(timezone.utc).isoformat()
        with engine.begin() as conn:
            conn.execute(text('INSERT INTO event_broadcaster_aliases (id, source_id, label, normalized_label, target, created_at, updated_at) '
                              "VALUES (:id, 's', 'DAZN', 'dazn', :target, :now, :now)"),
                         {'id': 'a' * 32, 'target': json.dumps({'kind': 'tv', 'id': 1, 'name': 'DAZN 1', 'country': ''}), 'now': now})
        downgrade_to_revision(path, '20261030_1300')
        assert 'event_broadcaster_aliases' not in inspect(engine).get_table_names()
        upgrade_to_revision(tmp_path / 'fresh.sqlite', 'head')
    finally:
        engine.dispose()


def two_event_schedule():
    data = plain_schedule()
    second = json.loads(json.dumps(data['observations'][0]))
    second['external_id'] = 'second'
    second['title'] = 'Second match'
    data['observations'].append(second)
    for obs in data['observations']:
        obs['broadcasts'] = [{'id': 'dz', 'label': 'DAZN', 'country': 'es'}]
    return data


def link(client, event, broadcast_index=0, **payload):
    broadcast = event['broadcasts'][broadcast_index]
    response = client.patch(f"/api/v1/events/{event['id']}/broadcast",
                            json={'revision': event['revision'], 'broadcast_id': broadcast['id'], **payload})
    assert response.status_code == 200, response.text
    return response.json()


def test_alias_applies_to_sibling_and_future_events(client, db_session):
    from app.models.models import TVChannel
    tv = TVChannel(name='DAZN 1', country='es', is_active=True)
    db_session.add(tv)
    db_session.commit()
    first, second = apply(client, preview(client, two_event_schedule()))
    assert first['broadcasts'][0]['target'] is None
    linked = link(client, first, target_kind='tv', target_id=tv.id)
    assert linked['broadcasts'][0]['via_alias'] is True and linked['broadcasts'][0]['manually_mapped'] is True
    sibling = client.get('/api/v1/events/' + second['id']).json()
    assert sibling['broadcasts'][0]['target']['id'] == tv.id and sibling['broadcasts'][0]['manually_mapped']
    data = two_event_schedule()
    data['observations'][1]['external_id'] = 'third'
    third = apply(client, preview(client, data))[1]
    assert third['broadcasts'][0]['target']['id'] == tv.id
    links = client.get('/api/v1/events/broadcaster-links').json()
    assert [(row['label'], row['target']['id'], row['event_count']) for row in links] == [('DAZN', tv.id, 3)]
    assert client.delete(f"/api/v1/events/broadcaster-links/{links[0]['id']}").status_code == 204
    assert client.delete(f"/api/v1/events/broadcaster-links/{links[0]['id']}").status_code == 404
    assert client.get('/api/v1/events/' + second['id']).json()['broadcasts'][0]['target'] is None


def test_event_only_choices_and_none_marker(client, db_session):
    from app.models.models import TVChannel, SportingEvent
    one = TVChannel(name='DAZN 1', country='es', is_active=True)
    two = TVChannel(name='DAZN 2', country='es', is_active=True)
    db_session.add_all([one, two])
    db_session.commit()
    first, second = apply(client, preview(client, two_event_schedule()))
    link(client, first, target_kind='tv', target_id=one.id)
    second = client.get('/api/v1/events/' + second['id']).json()
    # This event only wins over the alias; the alias is untouched.
    only = link(client, second, target_kind='tv', target_id=two.id, apply_to_source=False)
    assert only['broadcasts'][0]['target']['id'] == two.id and only['broadcasts'][0]['via_alias'] is False
    assert client.get('/api/v1/events/' + first['id']).json()['broadcasts'][0]['target']['id'] == one.id
    # Clearing this event only writes an explicit marker; the alias still applies elsewhere.
    cleared = link(client, only, apply_to_source=False)
    assert cleared['broadcasts'][0]['target'] is None and cleared['broadcasts'][0]['compatibility'] == 'unresolved'
    assert client.get('/api/v1/events/' + first['id']).json()['broadcasts'][0]['target']['id'] == one.id
    # Saving with the checkbox on sweeps per-event entries for that broadcaster across the source.
    first = client.get('/api/v1/events/' + first['id']).json()
    link(client, first, target_kind='tv', target_id=two.id)
    assert client.get('/api/v1/events/' + second['id']).json()['broadcasts'][0]['target']['id'] == two.id
    assert all(not (row.broadcast_mappings or {}) for row in db_session.query(SportingEvent).all())
    # Clearing with the checkbox on removes the alias for every event.
    first = client.get('/api/v1/events/' + first['id']).json()
    assert link(client, first)['broadcasts'][0]['target'] is None
    assert client.get('/api/v1/events/broadcaster-links').json() == []


def test_alias_target_rename_is_unavailable_not_rematched(client, db_session):
    from app.models.models import TVChannel
    tv = TVChannel(name='DAZN 1', country='es', is_active=True)
    db_session.add(tv)
    db_session.commit()
    first, _ = apply(client, preview(client, two_event_schedule()))
    link(client, first, target_kind='tv', target_id=tv.id)
    tv.name = 'DAZN'
    db_session.commit()
    current = client.get('/api/v1/events/' + first['id']).json()['broadcasts'][0]
    assert current['target'] is None and current['compatibility'] == 'unavailable'


def test_alias_stream_mapping_applies_to_source(client, db_session):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id='b' * 40, name='DAZN Spain', is_active=True))
    db_session.commit()
    first, second = apply(client, preview(client, two_event_schedule()))
    link(client, first, channel_id='b' * 40)
    sibling = client.get('/api/v1/events/' + second['id']).json()['broadcasts'][0]
    assert sibling['content_id'] == 'b' * 40 and sibling['compatibility'] == 'playable' and sibling['via_alias'] is True
    links = client.get('/api/v1/events/broadcaster-links').json()
    assert links[0]['target'] is None and links[0]['content_id'] == 'b' * 40
