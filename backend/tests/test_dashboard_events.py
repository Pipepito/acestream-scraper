"""Dashboard selection operates across the saved inventory, without writes."""
import json
from datetime import datetime, timedelta, timezone

import pytest
from app.schemas.events import EventFields

NOW = datetime(2026, 10, 25, 0, 30, tzinfo=timezone.utc)


@pytest.fixture
def clock(monkeypatch):
    from app.services import event_service
    current = [NOW]
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return current[0].astimezone(tz) if tz else current[0].replace(tzinfo=None)
    monkeypatch.setattr(event_service, 'datetime', Clock)
    return current


@pytest.fixture
def add_event(db_session):
    from app.models.models import SportingEvent
    def add(identity, *, followed=False, archived=False, correction=None, **fields):
        data = EventFields(title=identity, timezone='UTC', **fields).model_dump(mode='json')
        row = SportingEvent(id=identity, owner_id=identity, revision=1, fields=data,
                            followed=followed, archived=archived, correction=correction)
        db_session.add(row)
        db_session.commit()
        return row
    return add


def read(client, **params):
    response = client.get('/api/v1/events', params={'selection': 'dashboard', 'zone': 'Europe/Madrid', 'limit': 6, **params})
    assert response.status_code == 200, response.text
    return response.json()


def ids(data):
    return [event['id'] for event in data['events']]


def test_full_inventory_rank_before_limit_and_read_only(client, add_event, clock, db_session):
    for number in range(65):
        add_event(f'past-{number}', starts_at=NOW - timedelta(minutes=number + 1), state='scheduled')
    add_event('live', starts_at=NOW - timedelta(hours=2), ends_at=NOW + timedelta(hours=1), state='live')
    for number in reversed(range(8)):
        add_event(f'future-{number}', starts_at=NOW + timedelta(minutes=number + 1), state='scheduled')
    add_event('date-only', scheduled_date=NOW.date())
    result = read(client, upcoming=True)
    assert result['total'] == 10
    assert ids(result) == ['live', *[f'future-{n}' for n in range(5)]]
    assert ids(read(client, offset=6)) == ['future-5', 'future-6', 'future-7', 'date-only']
    from app.models.models import SportingEvent
    assert all(row.revision == 1 for row in db_session.query(SportingEvent))
    # Existing agenda semantics and default selection remain unchanged.
    agenda = client.get('/api/v1/events', params={'upcoming': True, 'zone': 'Europe/Madrid'}).json()
    assert agenda['events'][0]['id'] == 'live'
    assert agenda['total'] > result['total']


def test_live_eligibility_end_times_archives_and_unknown_dates(client, add_event, clock):
    add_event('overnight', starts_at=NOW - timedelta(days=2), ends_at=NOW + timedelta(minutes=1), state='live')
    add_event('fresh-live', starts_at=NOW - timedelta(hours=24), state='live')
    add_event('stale-live', starts_at=NOW - timedelta(hours=24, seconds=1), state='live')
    add_event('expired', starts_at=NOW - timedelta(hours=2), ends_at=NOW, state='live')
    add_event('undated-live', state='live')
    add_event('unknown-date')
    for state in ['finished', 'cancelled']:
        add_event(state, starts_at=NOW + timedelta(hours=1), state=state)
    add_event('archived', starts_at=NOW + timedelta(hours=1), archived=True)
    add_event('earlier-today', starts_at=NOW - timedelta(minutes=1), state='scheduled')
    add_event('future', starts_at=NOW + timedelta(hours=1))
    assert ids(read(client)) == ['overnight', 'fresh-live', 'future']
    assert read(client, archived=True)['events'] == []


def test_following_or_interests_and_reviewed_corrections(client, add_event, clock):
    add_event('sport', starts_at=NOW + timedelta(hours=1), sport='Football')
    add_event('team', starts_at=NOW + timedelta(hours=2), participants=['North United'], followed=True)
    add_event('competition', starts_at=NOW + timedelta(hours=3), competition='Fórmula 1')
    add_event('other', starts_at=NOW + timedelta(hours=4), followed=True)
    add_event('corrected', starts_at=NOW + timedelta(hours=5), sport='Football',
              correction=EventFields(title='Cancelled by operator', timezone='UTC', state='cancelled').model_dump(mode='json'))
    interests = json.dumps({'sports': ['Football'], 'teams': ['North United'], 'competitions': ['Fórmula 1']})
    assert ids(read(client, interests=interests)) == ['sport', 'team', 'competition']
    assert ids(read(client, followed=True)) == ['team', 'other']
    assert ids(read(client, interests=interests, followed=True)) == ['team']
    assert read(client, interests=json.dumps({'sports': ['Tennis']}))['total'] == 0


def test_date_only_order_ties_and_dst_window(client, add_event, clock):
    # Madrid falls back during the first day. The seventh calendar day ends
    # at Oct 31 23:00 UTC, not at now + 7 * 24h.
    add_event('second-hour', starts_at='2026-10-25T02:30:00+01:00')
    add_event('first-hour', starts_at='2026-10-25T02:30:00+02:00')
    add_event('tie-b', starts_at='2026-10-25T02:30:00+02:00')
    add_event('tie-a', starts_at='2026-10-25T02:30:00+02:00')
    add_event('window-last', starts_at='2026-10-31T22:59:59Z')
    add_event('outside', starts_at='2026-10-31T23:00:00Z')
    add_event('tbc-today', scheduled_date='2026-10-25')
    add_event('tbc-next', scheduled_date='2026-10-26')
    add_event('tbc-outside', scheduled_date='2026-11-01')
    add_event('tbc-past', scheduled_date='2026-10-24')
    result = read(client, limit=100)
    assert ids(result) == ['first-hour', 'tie-a', 'tie-b', 'second-hour', 'window-last', 'tbc-today', 'tbc-next']
    assert result['events'][-1]['starts_at'] is None
    assert 'outside' in ids(read(client, zone='UTC', limit=100))


@pytest.mark.parametrize('params', [{'selection': 'invalid'}, {'zone': 'No/Zone'}, {'limit': 0}, {'window_days': 31}])
def test_selection_contract_validation(client, params):
    assert client.get('/api/v1/events', params=params).status_code == 422


def test_spring_dst_calendar_window_and_midnight_refresh(client, add_event, clock):
    clock[0] = datetime(2026, 3, 28, 22, 59, 59, tzinfo=timezone.utc)
    add_event('first-day-tbc', scheduled_date='2026-03-28')
    add_event('spring-last', starts_at='2026-04-03T21:59:59Z')
    add_event('next-window', starts_at='2026-04-03T22:00:00Z')
    assert ids(read(client)) == ['spring-last', 'first-day-tbc']
    clock[0] += timedelta(seconds=1)  # Madrid midnight advances the calendar window.
    assert ids(read(client)) == ['spring-last', 'next-window']


def test_started_scheduled_event_leaves_summary_until_publisher_reports_live(client, add_event, clock):
    add_event('starting', starts_at=NOW, state='scheduled')
    assert ids(read(client)) == ['starting']
    clock[0] += timedelta(seconds=1)
    assert read(client)['total'] == 0
