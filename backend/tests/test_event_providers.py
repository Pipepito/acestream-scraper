from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.events import EventProviderOptions, EventInterests
from app.services.event_providers import (parse_wosti, parse_openfootball, select_provider_rows,
    provider_location)
from test_sporting_events import schedule, preview, apply

HTML = (Path(__file__).parent / 'fixtures/events/providers/wosti.html').read_text()
NOW = datetime(2026, 10, 26, tzinfo=timezone.utc)


def test_wosti_multisport_snapshots_never_expose_affiliates_or_merge_doubleheaders():
    rows = parse_wosti(HTML)
    assert len(rows) == 4
    assert rows[0].external_id != rows[1].external_id
    assert rows[0].starts_at.isoformat() == '2026-10-26T18:30:00+00:00'
    assert [b.label for b in rows[0].broadcasts] == ['DAZN F1', 'DAZN']
    assert all(b.url is None and b.channel_id is None for o in rows for b in o.broadcasts)
    assert rows[2].sport == 'Motorsport' and rows[2].title == 'G.P. Example · Libres 1'
    assert rows[3].starts_at is None and rows[3].scheduled_date.isoformat() == '2026-10-27'
    # A changed broadcast doesn't change occurrence identity. Changed time must be reviewed.
    updated = parse_wosti(HTML.replace('DAZN F1', 'TV Example'))
    assert rows[0].external_id == updated[0].external_id
    assert rows[0].external_id != parse_wosti(HTML.replace('19:30', '20:00'))[0].external_id
    with pytest.raises(ValueError, match='markup'):
        parse_wosti('<html>Login required</html>')
    with pytest.raises(ValueError, match='Incomplete'):
        parse_wosti(HTML.replace('26/10/2026', 'today'))


def test_provider_filters_are_union_and_window_is_calendar_days():
    rows = parse_wosti(HTML)
    options = EventProviderOptions(provider='wosti_es', window_days=1,
        interests=EventInterests(competitions=['Fórmula 1'], teams=['North United']))
    result = select_provider_rows(rows, options, zone='Europe/Madrid', now=NOW)
    assert len(result.observations) == 2
    options.window_days = 14
    result = select_provider_rows(rows, options, zone='Europe/Madrid', now=NOW)
    assert len(result.observations) == 3
    assert 'NBA' in result.available_interests.competitions  # Discovery isn't narrowed by interests.
    assert len(select_provider_rows(rows * 2, options, zone='Europe/Madrid', now=NOW).observations) == 3
    options.interests = EventInterests(sports=['Basketball'], competitions=['formula 1'])
    assert len(select_provider_rows(rows, options, zone='Europe/Madrid', now=NOW).observations) == 2


def football():
    return {'matches': [dict(round='Matchday 1', team1='North', team2='South', date='2026-10-26', time='19:30'),
                        dict(round='Matchday 2', team1='West', team2='East', date='2026-11-08'),
                        dict(round='Matchday 3', team1='West', team2='East', date='2026-11-09')]}


def test_openfootball_identity_survives_rescheduling_and_does_not_invent_time():
    options = EventProviderOptions(provider='openfootball', league='en.1')
    data = football()
    rows = parse_openfootball(json.dumps(data), options, 'Europe/London')
    assert rows[1].starts_at is None and rows[1].scheduled_date.isoformat() == '2026-11-08'
    assert rows[1].broadcasts == [] and rows[1].ends_at is None
    result = select_provider_rows(rows, options, zone='Europe/London', now=NOW)
    assert len(result.observations) == 2  # Day 14 included, day 15 excluded.
    data['matches'][0]['date'] = '2026-11-01'
    assert parse_openfootball(json.dumps(data), options, 'Europe/London')[0].external_id == rows[0].external_id
    data['matches'].append(data['matches'][0])
    with pytest.raises(ValueError, match='Ambiguous'):
        parse_openfootball(json.dumps(data), options, 'Europe/London')


def test_provider_urls_cannot_be_overridden():
    with pytest.raises(ValidationError):
        EventProviderOptions(provider='openfootball', season='../../private')
    with pytest.raises(ValueError):
        provider_location(EventProviderOptions(provider='wosti_es', feeds=['https://internal.example']))
    with pytest.raises(ValueError):
        provider_location(EventProviderOptions(provider='openfootball', season='2026-30'))


def test_saved_provider_filters_empty_preview_and_refresh_preserve_data(client, db_session, monkeypatch):
    from app.services import event_source_service
    from app.services.event_source_service import EventSourceService
    options = EventProviderOptions(provider='wosti_es', interests=EventInterests(competitions=['Fórmula 1']))
    seen = []
    async def fetch(url, **kwargs):
        seen.append(kwargs['adapter'])
        configured = EventProviderOptions.model_validate(kwargs['adapter']['provider_options'])
        return select_provider_rows(parse_wosti(HTML), configured, zone='Europe/Madrid', now=NOW)
    monkeypatch.setattr(event_source_service, 'fetch_schedule', fetch)
    response = client.post('/api/v1/events/sources/preview', json={'provider_options': options.model_dump()})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data['events']) == 1
    assert client.get('/api/v1/events/sources').json() == []
    saved = client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': [data['events'][0]['id']], 'refresh_source': True})
    assert saved.status_code == 200, saved.text
    source = client.get('/api/v1/events/sources').json()[0]
    duplicate = client.post('/api/v1/events/sources/preview', json={'provider_options': options.model_dump()})
    assert duplicate.status_code == 409 and 'already saved' in duplicate.text
    assert source['provider_options']['window_days'] == 14
    assert source['provider_options']['interests']['competitions'] == ['Fórmula 1']
    result = EventSourceService(db_session).refresh(source['id'])
    assert result.updated == 1 and result.pending == 0
    options.interests = EventInterests(teams=['Unlisted team'])
    data = client.post('/api/v1/events/sources/preview', json={'source_id': source['id'], 'provider_options': options.model_dump()}).json()
    assert data['events'] == []
    result = client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': [], 'refresh_source': True})
    assert result.status_code == 200, result.text
    assert EventSourceService(db_session).refresh(source['id']).status == 'unchanged'
    assert client.get('/api/v1/events').json()['total'] == 1
    assert len(client.get('/api/v1/events/sources').json()) == 1


def test_empty_selection_still_rejected_for_manual_import(client):
    data = preview(client)
    assert client.post('/api/v1/events/apply', json={'token': data['token'], 'selected_ids': []}).status_code == 409


def channel_inventory(db):
    from app.models.models import TVChannel, EPGChannel, EPGSource
    source = EPGSource(name='Spanish guide', url='https://example.org/guide.xml', enabled=True)
    db.add(source)
    db.flush()
    tv = TVChannel(name='Sports One', country='es', is_active=True)
    epg = EPGChannel(name='Sports One [ES]', channel_xml_id='sports.es', epg_source_id=source.id)
    other = EPGChannel(name='Otro canal [ES]', channel_xml_id='otro.es', epg_source_id=source.id)
    db.add_all([tv, epg, other])
    db.commit()
    return tv, epg, other


def plain_schedule():
    data = schedule()
    data['observations'] = data['observations'][:1]
    data['observations'][0]['broadcasts'] = [{'id': 'plain', 'label': 'Sports One', 'country': 'es'}]
    return data


def test_tv_priority_epg_fallback_ambiguous_and_regional_names(client, db_session):
    from app.models.models import EPGChannel
    tv, epg, _ = channel_inventory(db_session)
    event = apply(client, preview(client, plain_schedule()))[0]
    assert event['broadcasts'][0]['target']['kind'] == 'tv'
    assert event['broadcasts'][0]['content_id'] is None
    assert event['broadcasts'][0]['compatibility'] == 'linked'
    tv.is_active = False
    db_session.commit()
    event = client.get('/api/v1/events/' + event['id']).json()
    assert event['broadcasts'][0]['target']['id'] == epg.id
    db_session.add(EPGChannel(name='Sports One [ES]', channel_xml_id='other.es', epg_source_id=epg.epg_source_id))
    db_session.commit()
    assert client.get('/api/v1/events/' + event['id']).json()['broadcasts'][0]['target'] is None
    data = plain_schedule()
    data['observations'][0]['broadcasts'][0]['country'] = 'uk'
    assert preview(client, data)['events'][0]['broadcasts'][0]['target'] is None


def test_manual_cross_region_mapping_survives_refresh_and_missing_target_is_not_replaced(client, db_session):
    from app.models.models import TVChannel
    _, _, other = channel_inventory(db_session)
    event = apply(client, preview(client, plain_schedule()))[0]
    broadcast = event['broadcasts'][0]
    result = client.patch('/api/v1/events/' + event['id'] + '/broadcast', json={'revision': event['revision'],
        'broadcast_id': broadcast['id'], 'target_kind': 'epg', 'target_id': other.id})
    assert result.status_code == 200, result.text
    assert result.json()['broadcasts'][0]['target']['id'] == other.id
    refreshed = apply(client, preview(client, plain_schedule()))[0]
    assert refreshed['broadcasts'][0]['target']['id'] == other.id
    assert refreshed['broadcasts'][0]['manually_mapped']
    other.channel_xml_id = 'replacement.es'
    db_session.commit()
    current = client.get('/api/v1/events/' + event['id']).json()['broadcasts'][0]
    assert current['target'] is None and current['compatibility'] == 'unavailable'
    # Search permits another country/name; automatic matching remains conservative.
    db_session.add(TVChannel(name='Sky Sports [UK]', country='uk', is_active=True))
    db_session.commit()
    assert client.get('/api/v1/events/broadcast-targets', params={'search': 'Sky'}).json()[0]['country'] == 'uk'


def test_date_only_and_mixed_display_filters(client):
    rows = parse_wosti(HTML)
    apply(client, preview(client, {'version': 1, 'observations': [row.model_dump(mode='json') for row in rows]}))
    result = client.get('/api/v1/events', params={'interests': json.dumps({'sports': ['Basketball'], 'competitions': ['Fórmula 1']})})
    assert result.status_code == 200
    assert result.json()['total'] == 2
    result = client.get('/api/v1/events', params={'day': '2026-10-27', 'sport': 'Basketball'})
    assert result.json()['total'] == 1 and result.json()['events'][0]['starts_at'] is None
    assert 'NBA' in client.get('/api/v1/events/interests').json()['competitions']


def test_duplicate_feed_occurrences_retain_all_broadcasters():
    from app.schemas.events import EventBroadcast
    rows = parse_wosti(HTML)
    extra = rows[0].model_copy(update={'broadcasts': [EventBroadcast(id='other', label='Other broadcaster')]})
    result = select_provider_rows([rows[0], extra], EventProviderOptions(provider='wosti_es'), zone='Europe/Madrid', now=NOW)
    assert len(result.observations) == 1
    assert len(result.observations[0].broadcasts) == 3


def test_provider_transport_is_bounded_and_uses_guarded_sessions(monkeypatch):
    import asyncio
    from app.services import event_providers
    calls = []
    payload = HTML.encode()
    class Response:
        def __init__(self):
            self.content = self
        def raise_for_status(self):
            pass
        async def iter_chunked(self, size):
            yield payload
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
    class Session(Response):
        def get(self, url, **kwargs):
            calls.append((url, kwargs))
            return Response()
    monkeypatch.setattr(event_providers, 'source_session', lambda **kw: Session())
    result = asyncio.run(event_providers.fetch_provider({'provider': 'wosti_es', 'feeds': ['all']}, zone='Europe/Madrid', now=NOW))
    assert len(result.observations) == 4
    assert calls == [('https://www.futbolenlatv.es/deporte', {'max_redirects': 5})]
    payload = b'x' * (2 * 1024 * 1024 + 1)
    with pytest.raises(ExceptionGroup):
        asyncio.run(event_providers.fetch_provider({'provider': 'wosti_es', 'feeds': ['all']}, zone='Europe/Madrid', now=NOW))


def test_manual_target_removes_a_different_source_stream_and_reset_restores_it(client, db_session):
    tv, _, _ = channel_inventory(db_session)
    data = plain_schedule()
    data['observations'][0]['broadcasts'][0]['url'] = 'acestream://' + 'a' * 40
    event = apply(client, preview(client, data))[0]
    assert event['broadcasts'][0]['compatibility'] == 'playable'
    response = client.patch('/api/v1/events/' + event['id'] + '/broadcast', json={
        'revision': event['revision'], 'broadcast_id': event['broadcasts'][0]['id'], 'target_kind': 'tv', 'target_id': tv.id})
    assert response.status_code == 200
    assert response.json()['broadcasts'][0]['content_id'] is None
    assert response.json()['broadcasts'][0]['compatibility'] == 'linked'
    response = client.patch('/api/v1/events/' + event['id'] + '/broadcast', json={
        'revision': response.json()['revision'], 'broadcast_id': event['broadcasts'][0]['id'], 'channel_id': None})
    assert response.status_code == 200
    assert response.json()['broadcasts'][0]['content_id'] == 'a' * 40


def test_football_linked_teams_and_competition_headers():
    html = '''<table class="tablaPrincipal">
      <tr class="cabeceraTabla"><td>28/10/2026</td></tr>
      <tr class="cabeceraCompericion"><td><a>Copa del Rey</a></td></tr>
      <tr><td class="hora">19:00</td><td class="detalles"><span class="ajusteDoslineas">1ª Ronda</span></td>
      <td class="local"><a><span>North United</span></a></td><td class="visitante"><a><span>South City</span></a></td>
      <td><ul class="listaCanales"><li>Sports One</li></ul></td></tr></table>'''
    row = parse_wosti(html, feed='football')[0]
    assert row.competition == 'Copa del Rey'
    assert row.participants == ['North United', 'South City']
    assert row.starts_at.isoformat() == '2026-10-28T18:00:00+00:00'
    assert row.broadcasts[0].label == 'Sports One'
