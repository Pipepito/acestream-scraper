from datetime import datetime, timedelta, timezone

from test_sporting_events import schedule, preview, apply
from test_event_providers import channel_inventory


def programme(db, epg, **changes):
    from app.models.models import EPGProgram
    values = dict(epg_channel_id=epg.id, title='Copa: NORTH UNITED - South City (Directo)',
        start_time=datetime(2026, 10, 24, 21, 20, tzinfo=timezone.utc),
        end_time=datetime(2026, 10, 24, 23, 30, tzinfo=timezone.utc))
    values.update(changes)
    row = EPGProgram(**values)
    db.add(row)
    db.commit()
    return row


def test_programme_match_adds_source_qualified_tv_link_without_changing_event(client, db_session):
    tv, epg, _ = channel_inventory(db_session)
    tv.epg_source_id, tv.epg_id = epg.epg_source_id, epg.channel_xml_id
    program = programme(db_session, epg)
    data = schedule()
    data['observations'] = data['observations'][:1]
    data['observations'][0]['broadcasts'] = []
    reviewed = preview(client, data)
    match = reviewed['events'][0]['epg_matches'][0]
    assert match['program_id'] == program.id
    assert match['tv_channel']['id'] == tv.id
    saved = apply(client, reviewed)[0]
    assert saved['epg_matches'] == reviewed['events'][0]['epg_matches']
    assert saved['broadcasts'] == []
    assert saved['starts_at'] == '2026-10-24T21:30:00Z'
    # Programme records are rechecked after guide replacement; no reused-ID link.
    program.title = 'Unrelated programme'
    db_session.commit()
    assert client.get('/api/v1/events/' + saved['id']).json()['epg_matches'] == []


def test_ambiguous_repeat_wrong_day_single_team_and_disabled_guide_do_not_match(client, db_session):
    _, epg, _ = channel_inventory(db_session)
    row = programme(db_session, epg, title='North United news')
    assert preview(client)['events'][0]['epg_matches'] == []
    row.title = 'North United - South City'
    row.start_time += timedelta(days=1)
    db_session.commit()
    assert preview(client)['events'][0]['epg_matches'] == []
    row.start_time -= timedelta(days=1)
    db_session.commit()
    duplicate = programme(db_session, epg)
    assert preview(client)['events'][0]['epg_matches'] == []
    db_session.delete(duplicate)
    epg.epg_source.enabled = False
    db_session.commit()
    assert preview(client)['events'][0]['epg_matches'] == []


def test_date_only_matches_local_calendar_day_without_inventing_kickoff(client, db_session):
    _, epg, _ = channel_inventory(db_session)
    programme(db_session, epg)
    data = schedule()
    data['observations'][0].update(starts_at=None, scheduled_date='2026-10-24')
    event = preview(client, data)['events'][0]
    assert event['starts_at'] is None
    assert len(event['epg_matches']) == 1
