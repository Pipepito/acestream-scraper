import asyncio
import json
from datetime import datetime, timedelta, timezone
from threading import Event

import pytest
from sqlalchemy import create_engine, inspect, text

from app.schemas.events import EventImport, EventRetention
from app.services.event_source_service import EventSourceService
from migration_test_utils import upgrade_to_revision, downgrade_to_revision, database_url_for
from test_sporting_events import schedule, preview, apply


def source_preview(client):
    response = client.post('/api/v1/events/sources/preview', json={'url': 'https://guide.example/events.json?token=source-secret'})
    assert response.status_code == 200, response.text
    return response.json()


@pytest.fixture
def feed(monkeypatch):
    from app.services import event_source_service
    data = schedule()
    async def fetch(*args, **kwargs):
        return EventImport.model_validate(data)
    monkeypatch.setattr(event_source_service, 'fetch_schedule', fetch)
    return data


def save_source(client, data, selected=None):
    response = client.post('/api/v1/events/apply', json={'token': data['token'],
        'selected_ids': selected or [e['id'] for e in data['events']], 'refresh_source': True})
    assert response.status_code == 200, response.text
    return client.get('/api/v1/events/sources').json()[0]


def test_url_review_is_read_only_selected_refresh_and_failure_preserves(client, db_session, feed, monkeypatch):
    from app.services import event_source_service
    data = source_preview(client)
    assert client.get('/api/v1/events/sources').json() == []
    chosen = data['events'][0]['id']
    source = save_source(client, data, [chosen])
    assert source['reviewed'] == 1 and source['enabled']
    assert 'source-secret' not in json.dumps(source)
    current = client.get('/api/v1/events/' + chosen).json()
    assert client.patch('/api/v1/events/' + chosen, json={'revision': current['revision'], 'followed': True}).status_code == 200
    feed['observations'][0].update(state='postponed', starts_at=None, broadcasts=[])
    service = EventSourceService(db_session)
    result = service.refresh(source['id'])
    assert (result.updated, result.pending, result.status) == (1, 1, 'updated')
    current = client.get('/api/v1/events/' + chosen).json()
    assert current['state'] == 'postponed' and current['followed'] and len(current['broadcasts']) == 4
    assert client.get('/api/v1/events').json()['total'] == 1
    async def fail(*a, **kw):
        raise ValueError('https://private.example/?token=secret')
    monkeypatch.setattr(event_source_service, 'fetch_schedule', fail)
    result = service.refresh(source['id'])
    assert result.status == 'error'
    assert 'secret' not in result.model_dump_json()
    status = client.get('/api/v1/events/sources').json()[0]
    assert status['last_success'] and status['last_result']['status'] == 'error'
    assert client.get('/api/v1/events/' + chosen).json() == current


def test_disable_during_fetch_invalidates_changes(client, db_session, feed, monkeypatch):
    from sqlalchemy.orm import Session
    from app.schemas.events import EventSourceUpdate
    from app.services import event_source_service
    data = source_preview(client)
    source = save_source(client, data)
    old = client.get('/api/v1/events/' + data['events'][0]['id']).json()
    async def fetch(*a, **kw):
        with Session(db_session.bind) as other:
            EventSourceService(other).update(source['id'], EventSourceUpdate(revision=source['revision'], enabled=False))
        feed['observations'][0]['title'] = 'Must not be applied'
        return EventImport.model_validate(feed)
    monkeypatch.setattr(event_source_service, 'fetch_schedule', fetch)
    result = EventSourceService(db_session).refresh(source['id'])
    assert result.status == 'error'
    assert client.get('/api/v1/events/' + old['id']).json() == old
    assert not client.get('/api/v1/events/sources').json()[0]['enabled']


def test_source_stale_review_rolls_back_events_and_never_overwrites_other_url(client, feed):
    data = source_preview(client)
    source = save_source(client, data)
    stale = source_preview(client)
    assert client.patch('/api/v1/events/sources/' + source['id'], json={'revision': source['revision'], 'enabled': False}).status_code == 200
    before = client.get('/api/v1/events').json()
    result = client.post('/api/v1/events/apply', json={'token': stale['token'], 'selected_ids': [e['id'] for e in stale['events']]})
    assert result.status_code == 409
    assert client.get('/api/v1/events').json() == before
    assert client.post('/api/v1/events/sources/preview', json={'url': 'https://other.example/schedule.json'}).status_code == 409


def test_refresh_budget_and_shutdown_defer_without_new_scheduler(client, db_session, feed, monkeypatch):
    from app.services import event_source_service
    source = save_source(client, source_preview(client))
    service = EventSourceService(db_session)
    stop = Event()
    stop.set()
    assert service.refresh_all(shutdown=stop)['deferred'] == 1
    monkeypatch.setattr(event_source_service, 'REFRESH_BUDGET_SECONDS', 0)
    assert service.refresh_all()['deferred'] == 1
    assert service.repo.get(source['id']).last_attempt is None


def test_retention_protects_followed_unknown_ends_archives_and_shared_channels(client, db_session, feed):
    from app.models.models import SportingEvent, EventMedia, EventObservationRecord, AcestreamChannel
    source = save_source(client, source_preview(client))
    now = datetime(2027, 1, 1, tzinfo=timezone.utc)
    service = EventSourceService(db_session)
    assert service.cleanup(now=now)['deleted'] == 0
    service.save_retention(EventRetention(ended_days=7, archived_days=30))
    rows = db_session.query(SportingEvent).order_by(SportingEvent.id).all()
    for row in rows:
        row.fields = {**row.fields, 'state': 'finished', 'starts_at': '2026-10-01T00:00:00Z', 'ends_at': None}
    db_session.commit()
    assert service.cleanup(now=now)['deleted'] == 0  # no invented end
    first, second = rows
    first.fields = {**first.fields, 'ends_at': '2026-10-01T02:00:00Z'}
    first.followed = True
    second.archived = True
    second.archived_at = now - timedelta(days=29)
    db_session.add(AcestreamChannel(id='a' * 40, name='Shared stream', is_active=True))
    db_session.commit()
    assert service.cleanup(now=now)['deleted'] == 0
    first.followed = False
    second.archived_at = now - timedelta(days=31)
    db_session.commit()
    assert service.cleanup(now=now)['deleted'] == 2
    assert db_session.query(EventMedia).count() == db_session.query(EventObservationRecord).count() == 0
    assert db_session.query(AcestreamChannel).count() == 1
    # Retention drops approvals too: a later feed cannot resurrect deleted rows.
    service.refresh(source['id'])
    assert db_session.query(SportingEvent).count() == 0
    assert client.get('/api/v1/events/sources').json()[0]['reviewed'] == 0


def test_archive_clock_only_changes_on_transition(client, db_session):
    from app.models.models import SportingEvent
    event = apply(client, preview(client))[0]
    def patch(revision, **values):
        response = client.patch('/api/v1/events/' + event['id'], json={'revision': revision, **values})
        assert response.status_code == 200
        return response.json()
    event = patch(event['revision'], archived=True)
    first = db_session.get(SportingEvent, event['id']).archived_at
    event = patch(event['revision'], archived=True)
    db_session.expire_all()
    assert db_session.get(SportingEvent, event['id']).archived_at == first
    patch(event['revision'], archived=False)
    db_session.expire_all()
    assert db_session.get(SportingEvent, event['id']).archived_at is None


def test_reviewed_mapping_survives_feed_refresh_and_reset(client, db_session):
    from app.models.models import AcestreamChannel
    db_session.add(AcestreamChannel(id='b' * 40, name='DAZN Spain', is_active=True))
    db_session.commit()
    event = apply(client, preview(client))[0]
    unresolved = next(b for b in event['broadcasts'] if b['label'] == 'DAZN')
    endpoint = '/api/v1/events/' + event['id'] + '/broadcast'
    result = client.patch(endpoint, json={'revision': event['revision'], 'broadcast_id': unresolved['id'], 'channel_id': 'b' * 40})
    assert result.status_code == 200
    mapped = next(b for b in result.json()['broadcasts'] if b['id'] == unresolved['id'])
    assert mapped['manually_mapped'] and mapped['content_id'] == 'b' * 40
    assert client.patch(endpoint, json={'revision': event['revision'], 'broadcast_id': unresolved['id'], 'channel_id': None}).status_code == 409
    refreshed = next(e for e in apply(client, preview(client)) if e['id'] == event['id'])
    assert next(b for b in refreshed['broadcasts'] if b['id'] == unresolved['id'])['manually_mapped']
    result = client.patch(endpoint, json={'revision': refreshed['revision'], 'broadcast_id': unresolved['id'], 'channel_id': None})
    assert next(b for b in result.json()['broadcasts'] if b['id'] == unresolved['id'])['compatibility'] == 'unresolved'


def test_schedule_fetch_bounds_and_private_errors(monkeypatch):
    from app.services import event_source_service
    calls = []
    payload = json.dumps(schedule()).encode()
    class Content:
        async def iter_chunked(self, size):
            yield payload
    class Response:
        content = Content()
        def raise_for_status(self):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
    class Session(Response):
        def get(self, url, **kwargs):
            calls.append(kwargs)
            return Response()
    monkeypatch.setattr(event_source_service, 'source_session', lambda **kw: Session())
    assert asyncio.run(event_source_service.fetch_schedule('https://guide.example')).observations
    assert calls == [{'max_redirects': 5}]
    monkeypatch.setattr(event_source_service, 'MAX_SOURCE_BYTES', 1)
    with pytest.raises(ValueError, match='Existing events were preserved'):
        asyncio.run(event_source_service.fetch_schedule('https://guide.example?token=secret'))
    payload = b'{"private-secret": '
    with pytest.raises(ValueError) as error:
        asyncio.run(event_source_service.fetch_schedule('https://guide.example?token=secret'))
    assert 'secret' not in str(error.value)


def test_migration_keeps_archives_and_supports_prior_head(tmp_path):
    path = tmp_path / 'events.sqlite'
    upgrade_to_revision(path, '20261023_1200')
    engine = create_engine(database_url_for(path))
    with engine.begin() as db:
        db.execute(text("INSERT INTO sporting_events (id, owner_id, revision, fields, followed, archived) VALUES ('old', 'owner', 1, '{}', 0, 1)"))
    upgrade_to_revision(path, 'head')
    with engine.connect() as db:
        assert db.execute(text("SELECT archived_at FROM sporting_events WHERE id = 'old'")).scalar()
    assert 'event_schedule_sources' in inspect(engine).get_table_names()
    downgrade_to_revision(path, '20261023_1200')
    with engine.connect() as db:
        assert db.execute(text('SELECT count(*) FROM sporting_events')).scalar() == 1
    engine.dispose()


def test_artwork_is_private_optional_guarded_and_does_not_block_playback(client, monkeypatch):
    from app.services import event_artwork
    payload = schedule()
    payload['observations'][0]['artwork_url'] = 'https://art.example/poster.png?token=private-art'
    data = preview(client, payload)
    assert 'private-art' not in json.dumps(data)
    event = next(row for row in apply(client, data) if row['has_artwork'])
    calls = []
    async def fetch(url):
        calls.append(url)
        return b'fixture-image', 'image/png'
    monkeypatch.setattr(event_artwork, '_fetch', fetch)
    response = client.get('/api/v1/events/' + event['id'] + '/artwork')
    assert response.status_code == 200 and response.headers['content-type'] == 'image/png'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert calls == ['https://art.example/poster.png?token=private-art']
    async def failed(url):
        raise ValueError(url)
    monkeypatch.setattr(event_artwork, '_fetch', failed)
    response = client.get('/api/v1/events/' + event['id'] + '/artwork')
    assert response.status_code == 409 and 'private-art' not in response.text
    assert client.get('/api/v1/events/' + event['id']).json()['broadcasts']


def test_artwork_rejects_html_svg_and_excessive_dimensions():
    from app.services.event_artwork import raster_type
    def png(w, h):
        return b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\x0dIHDR' + w.to_bytes(4, 'big') + h.to_bytes(4, 'big')
    assert raster_type(png(400, 200)) == 'image/png'
    for invalid in (b'<html>bad</html>', b'<svg onload="bad()"/>', png(5000, 200), png(3000, 3000), b'\xff\xd8\xff'):
        with pytest.raises(ValueError):
            raster_type(invalid)


@pytest.mark.parametrize(('outcome', 'status'), [('triggered', 200), ('already_running', 200), ('unavailable', 503)])
def test_refresh_now_uses_existing_deduplicated_job(client, monkeypatch, outcome, status):
    from app.services.task_service import task_service
    calls = []
    monkeypatch.setattr(task_service, 'run_task_now', lambda name: calls.append(name) or outcome)
    response = client.post('/api/v1/events/sources/refresh')
    assert response.status_code == status
    assert calls == ['url_scraping']
    if status == 200:
        assert response.json()['status'] == outcome
