from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET

from sqlalchemy import create_engine, inspect, text

from app.models.models import EPGProgram
from app.services.epg_service import EPGService
from migration_test_utils import upgrade_to_revision, upgrade_to_head, downgrade_to_revision, database_url_for
from test_event_providers import channel_inventory, plain_schedule
from test_sporting_events import preview, apply


def setup_overlay(client, db):
    tv, guide, _ = channel_inventory(db)
    tv.epg_id, tv.epg_source_id = guide.channel_xml_id, guide.epg_source_id
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=1)
    regular = EPGProgram(epg_channel_id=guide.id, start_time=start - timedelta(hours=1),
                         end_time=start + timedelta(hours=4), title='Regular guide')
    db.add(regular)
    db.commit()
    data = plain_schedule()
    data['observations'][0].update(starts_at=start.isoformat(), ends_at=None)
    event = apply(client, preview(client, data))[0]
    request = dict(revision=event['revision'], broadcast_id=event['broadcasts'][0]['id'],
                   ends_at=(start + timedelta(hours=2)).isoformat())
    return event, request, regular, tv


def preview_overlay(client, event, request):
    result = client.post(f"/api/v1/events/{event['id']}/guide-overlays/preview", json=request)
    assert result.status_code == 200, result.text
    return result.json()


def test_overlay_review_clips_only_exports_and_removal_restores_guide(client, db_session):
    event, request, regular, tv = setup_overlay(client, db_session)
    path = f"/api/v1/events/{event['id']}/guide-overlays"
    original = EPGService(db_session).generate_epg_xml()
    reviewed = preview_overlay(client, event, request)
    assert reviewed['affected'][0]['title'] == 'Regular guide'
    assert client.get(path).json() == []
    assert EPGService(db_session).generate_epg_xml() == original
    result = client.post(path, json={**request, 'expected_fingerprint': reviewed['fingerprint']})
    assert result.status_code == 200, result.text
    assert result.json()[0]['active']
    db_session.expire_all()
    xml = EPGService(db_session).generate_epg_xml()
    rows = ET.fromstring(xml).findall('programme')
    assert [p.findtext('title') for p in rows] == ['Regular guide', event['title'], 'Regular guide']
    assert rows[0].get('stop') == rows[1].get('start')
    assert rows[1].get('stop') == rows[2].get('start')
    assert db_session.query(EPGProgram).count() == 1
    assert regular.title == 'Regular guide'
    # Original guide queries and existing recording IDs are preserved.
    assert EPGService(db_session).get_programs(regular.epg_channel_id)[0].id == regular.id
    current = client.get('/api/v1/events/' + event['id']).json()
    assert client.delete(path, params={'revision': current['revision'], 'broadcast_id': request['broadcast_id']}).status_code == 204
    db_session.expire_all()
    assert EPGService(db_session).generate_epg_xml() == original


def test_stale_preview_rejected_and_changed_schedule_suspends(client, db_session):
    event, request, regular, _ = setup_overlay(client, db_session)
    path = f"/api/v1/events/{event['id']}/guide-overlays"
    reviewed = preview_overlay(client, event, request)
    regular.title = 'Changed guide'
    db_session.commit()
    assert client.post(path, json={**request, 'expected_fingerprint': reviewed['fingerprint']}).status_code == 409
    reviewed = preview_overlay(client, event, request)
    assert client.post(path, json={**request, 'expected_fingerprint': reviewed['fingerprint']}).status_code == 200
    current = client.get('/api/v1/events/' + event['id']).json()
    assert client.patch('/api/v1/events/' + event['id'], json={'revision': current['revision'], 'archived': True}).status_code == 200
    assert not client.get(path).json()[0]['active']
    db_session.expire_all()
    assert event['title'] not in EPGService(db_session).generate_epg_xml()


def test_overlay_requires_assigned_target_explicit_end_and_rejects_conflicts(client, db_session):
    event, request, _, tv = setup_overlay(client, db_session)
    path = f"/api/v1/events/{event['id']}/guide-overlays"
    assert client.post(path + '/preview', json={**request, 'ends_at': '2026-10-30T23:00:00'}).status_code == 422
    tv.epg_id = None
    db_session.commit()
    assert client.post(path + '/preview', json=request).status_code == 409
    tv.epg_id = 'sports.es'
    db_session.commit()
    reviewed = preview_overlay(client, event, request)
    assert client.post(path, json={**request, 'expected_fingerprint': reviewed['fingerprint']}).status_code == 200
    data = plain_schedule()
    data['observations'][0].update(external_id='different', title='Other match', starts_at=event['starts_at'], ends_at=None)
    other = apply(client, preview(client, data))[0]
    response = client.post(f"/api/v1/events/{other['id']}/guide-overlays/preview", json={**request,
        'revision': other['revision'], 'broadcast_id': other['broadcasts'][0]['id']})
    assert response.status_code == 409 and 'occupies' in response.text


def test_overlay_migration_preserves_existing_events_and_upgrade_path(tmp_path):
    path = tmp_path / 'overlay.db'
    upgrade_to_revision(path, '20261028_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO sporting_events (id, owner_id, revision, fields, followed, archived) VALUES ('test', 'owner', 3, '{}', 1, 0)"))
    upgrade_to_head(path)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT revision, followed, guide_overlays FROM sporting_events')).one() == (3, 1, None)
    downgrade_to_revision(path, '20261028_1200')
    assert 'guide_overlays' not in {c['name'] for c in inspect(engine).get_columns('sporting_events')}
    upgrade_to_head(path)
    engine.dispose()
    fresh = tmp_path / 'fresh.db'
    upgrade_to_head(fresh)
