"""Reviewed guide setup, safe automation and player-visible export contracts."""
from datetime import datetime, timedelta, timezone
import re
from unittest.mock import AsyncMock
from xml.etree import ElementTree as ET

import pytest
from app.models.models import AcestreamChannel, EPGSource, EPGChannel, EPGProgram, TVChannel
from app.schemas.config import EPGMatchingConfig
from app.services.epg_matching_automation import EPGMatchingAutomation
from app.services.epg_match_service import EPGMatchService
from app.services.tvchannel_service import TVChannelService, StaleEPGPreview
from app.services.epg_service import EPGService
from app.services.tuner_service import TunerService


@pytest.fixture
def inventory(db_session):
    source = EPGSource(name='Guide', url='https://example.com/guide', enabled=True)
    db_session.add(source); db_session.flush()
    epg = EPGChannel(name='ES: News One', channel_xml_id='news.one', epg_source_id=source.id)
    stream = AcestreamChannel(id='a'*40, name='ES: News One HD', is_active=True, is_online=True)
    db_session.add_all([epg, stream]); db_session.flush()
    now = datetime.now(timezone.utc)
    db_session.add(EPGProgram(epg_channel_id=epg.id, title='Morning news', start_time=now, end_time=now+timedelta(hours=1)))
    db_session.commit()
    return source, epg, stream


def analyze(db):
    return EPGMatchService(db).analyze_matches('strict')['rows']


def apply(db, row, **kwargs):
    return TVChannelService(db).create_tv_channels_from_epg_analysis(
        'strict', [row['epg_channel_id']], expected_previews={row['epg_channel_id']: row['review_token']}, **kwargs)


def test_review_is_read_only_and_default_automation_is_off(client, db_session, inventory):
    assert client.get('/api/v1/config/epg-matching').json() == {'enabled': False}
    assert EPGMatchingAutomation(db_session).run() is None
    preview = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'strict'}).json()
    assert preview['rows'][0]['can_apply']
    assert db_session.query(TVChannel).count() == 0
    assert inventory[2].tv_channel_id is None


@pytest.mark.parametrize('route', [
    '/api/v1/playlists/m3u', '/api/v1/playlists/playlists/m3u',
    '/api/v1/playlists/tv-channels/m3u', '/api/v1/playlists/all-streams/m3u',
    '/api/playlists/m3u', '/api/playlists/tv-channels/m3u', '/api/playlists/all-streams/m3u',
    '/playlists/m3u', '/playlist.m3u',
])
def test_review_to_authenticated_player_guide(client, db_session, inventory, monkeypatch, route):
    row = analyze(db_session)[0]
    result = apply(db_session, row)
    assert result['created_count'] == result['associated_count'] == 1
    monkeypatch.setenv('API_TOKEN', 'test +/&?token')
    response = client.get(route, params={'token': 'test +/&?token'})
    assert response.status_code == 200
    advertised = re.search('url-tvg="([^"]+)"', response.text)[1]
    guide = client.get(advertised)
    assert guide.status_code == 200
    xml = ET.fromstring(guide.text)
    channel_id = re.search('tvg-id="([^"]+)"', response.text)[1]
    assert xml.find('channel').attrib['id'] == channel_id
    assert xml.find('programme').attrib['channel'] == channel_id
    assert xml.find('programme/title').text == 'Morning news'
    assert client.get('/api/v1/epg/xml').status_code == 401


@pytest.mark.parametrize('header', ['Authorization', 'X-Api-Token'])
def test_authenticated_header_carriers(client, monkeypatch, header):
    monkeypatch.setenv('API_TOKEN', 'test-secret')
    token = 'Bearer test-secret' if header == 'Authorization' else 'test-secret'
    response = client.get('/playlist.m3u', headers={header: token})
    url = re.search('url-tvg="([^"]+)"', response.text)[1]
    assert client.get(url).status_code == 200


def test_cross_source_ids_are_consistent_in_filtered_exports(client, db_session, inventory):
    source, epg, _ = inventory
    apply(db_session, analyze(db_session)[0])
    second = EPGSource(name='Other guide', url='https://example.com/other', enabled=True)
    db_session.add(second); db_session.flush()
    epg2 = EPGChannel(name='Other station', channel_xml_id=epg.channel_xml_id, epg_source_id=second.id)
    tv2 = TVChannel(name='Other station', epg_id=epg.channel_xml_id, epg_source_id=second.id, is_active=True)
    db_session.add_all([epg2, tv2]); db_session.flush()
    db_session.add(AcestreamChannel(id='b'*40, name='Other station', tv_channel_id=tv2.id, is_online=True))
    now = datetime.now(timezone.utc)
    db_session.add(EPGProgram(epg_channel_id=epg2.id, title='Other show', start_time=now, end_time=now+timedelta(hours=1)))
    db_session.commit()
    xml = ET.fromstring(client.get('/api/v1/epg/xml').text)
    ids = [c.attrib['id'] for c in xml.findall('channel')]
    assert len(set(ids)) == 2
    playlist = client.get('/api/v1/playlists/m3u').text
    assert set(re.findall('tvg-id="([^"]+)"', playlist)) == set(ids)
    filtered = client.get('/api/v1/playlists/tv-channels/m3u', params={'search': 'Other station'}).text
    filtered_id = re.search('tvg-id="([^"]+)"', filtered)[1]
    assert filtered_id == xml.findall('programme')[1].attrib['channel']
    tuner = TunerService(db_session)
    assert set(re.findall('tvg-id="([^"]+)"', tuner.build_playlist_m3u(tuner.build_lineup(), 'http://testserver'))) == set(ids)


def test_same_identity_exported_once(db_session, inventory):
    source, epg, _ = inventory
    apply(db_session, analyze(db_session)[0])
    db_session.add(TVChannel(name='Another name', epg_id=epg.channel_xml_id, epg_source_id=source.id))
    db_session.commit()
    xml = ET.fromstring(EPGService(db_session).generate_epg_xml())
    assert len(xml.findall('channel')) == len(xml.findall('programme')) == 1


def test_automation_opt_in_repeat_and_preserve_channel(db_session, inventory):
    automation = EPGMatchingAutomation(db_session)
    automation.save(EPGMatchingConfig(enabled=True))
    first = automation.run()
    assert first.created == first.assigned == 1
    tv = db_session.query(TVChannel).one()
    tv.is_favorite, tv.channel_number = True, 23
    db_session.commit()
    second = automation.run()
    assert second.created == second.assigned == 0
    assert (tv.is_favorite, tv.channel_number) == (True, 23)
    assert db_session.query(TVChannel).count() == 1
    assert automation.last_run().status == 'success'


@pytest.mark.parametrize('change', ['country', 'missing_country', 'fuzzy', 'protected', 'inactive', 'conflicting_id', 'assigned', 'disabled_source', 'existing_manual'])
def test_automation_preserves_uncertain_or_manual_inventory(db_session, inventory, change):
    source, epg, stream = inventory
    if change == 'country': stream.name = 'UK: News One'
    if change == 'missing_country': stream.name = 'News One'
    if change == 'fuzzy': stream.name = 'ES: News Ones'
    if change == 'protected': stream.epg_update_protected = True
    if change == 'inactive': stream.is_active = False
    if change == 'conflicting_id': stream.tvg_id = 'different.id'
    if change == 'disabled_source': source.enabled = False
    if change in ('assigned', 'existing_manual'):
        tv = TVChannel(name='ES: News One' if change == 'existing_manual' else 'Manual', epg_id='manual.id')
        db_session.add(tv); db_session.flush()
        if change == 'assigned': stream.tv_channel_id = tv.id
    db_session.commit()
    before = db_session.query(TVChannel).count()
    automation = EPGMatchingAutomation(db_session)
    automation.save(EPGMatchingConfig(enabled=True))
    result = automation.run()
    assert result.created == result.assigned == 0
    assert db_session.query(TVChannel).count() == before


def test_ambiguous_sources_require_explicit_source_review(db_session, inventory):
    _, epg, stream = inventory
    other = EPGSource(name='Other', url='https://example.com/2', enabled=True)
    db_session.add(other); db_session.flush()
    db_session.add(EPGChannel(name=epg.name, channel_xml_id=epg.channel_xml_id, epg_source_id=other.id))
    db_session.commit()
    assert all(row['ambiguous_count'] == 1 and not row['can_apply'] for row in analyze(db_session))
    automation = EPGMatchingAutomation(db_session); automation.save(EPGMatchingConfig(enabled=True))
    assert automation.run().created == 0
    row = EPGMatchService(db_session).analyze_matches('strict', source_id=other.id)['rows'][0]
    apply(db_session, row, source_id=other.id)
    db_session.refresh(stream)
    assert stream.tv_channel.epg_source_id == other.id


def test_stale_preview_rejects_new_candidates_without_writes(client, db_session, inventory):
    row = analyze(db_session)[0]
    db_session.add(AcestreamChannel(id='b'*40, name=inventory[2].name, is_active=True))
    db_session.commit()
    result = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={
        'strictness': 'strict', 'epg_channel_ids': [row['epg_channel_id']],
        'expected_previews': {str(row['epg_channel_id']): row['review_token']}})
    assert result.status_code == 409
    assert db_session.query(TVChannel).count() == 0


def test_automation_budget_failure_preserves_inventory(db_session, inventory, monkeypatch):
    automation = EPGMatchingAutomation(db_session); automation.save(EPGMatchingConfig(enabled=True))
    monkeypatch.setattr('app.services.epg_match_service.MAX_ANALYSIS_COMPARISONS', 0)
    assert automation.run().status == 'error'
    assert db_session.query(AcestreamChannel).count() == 1
    assert db_session.query(TVChannel).count() == 0


def test_refresh_runs_optional_matching_after_success(db_session, inventory, monkeypatch):
    automation = EPGMatchingAutomation(db_session); automation.save(EPGMatchingConfig(enabled=True))
    service = EPGService(db_session)
    monkeypatch.setattr(service, '_fetch_epg_from_source', lambda _: {'success': True, 'channels_found': 1, 'programs_found': 1})
    assert service.refresh_source(inventory[0].id)['success']
    assert db_session.query(TVChannel).count() == 1


@pytest.mark.asyncio
async def test_scrape_then_review_fresh_catalogue(client, db_session, monkeypatch):
    from app.services.scraper_service import ScraperService
    from types import SimpleNamespace
    fake = SimpleNamespace(scrape=AsyncMock(return_value=([('c'*40, 'ES: News One HD', {})], 'OK')))
    monkeypatch.setattr('app.services.scraper_service.create_scraper_for_url', lambda *args: fake)
    channels, status = await ScraperService(db_session).scrape_url('https://example.com/list')
    assert status == 'OK' and len(channels) == 1
    assert db_session.query(TVChannel).count() == 0
    source = EPGSource(name='Guide', url='https://example.com/guide', enabled=True)
    db_session.add(source); db_session.commit()
    now = datetime.now(timezone.utc)
    start = now.strftime('%Y%m%d%H%M%S +0000')
    end = (now+timedelta(hours=1)).strftime('%Y%m%d%H%M%S +0000')
    EPGService(db_session)._process_epg_xml(source.id, f'<tv><channel id="news"><display-name>ES: News One</display-name></channel><programme channel="news" start="{start}" stop="{end}"><title>News</title></programme></tv>'.encode())
    db_session.commit()
    row = analyze(db_session)[0]; apply(db_session, row)
    response = client.get('/api/v1/playlists/all-streams/m3u')
    guide = client.get(re.search('url-tvg="([^"]+)"', response.text)[1])
    xml = ET.fromstring(guide.text)
    assert xml.find('programme/title').text == 'News'
    assert f'tvg-id="{xml.find("channel").attrib["id"]}"' in response.text
    assert client.get('/api/v1/playlists/guide-coverage').json() == {'streams': 1, 'linked_streams': 1, 'guide_channels': 1}


@pytest.mark.asyncio
@pytest.mark.parametrize('status', ['OK', 'Extracted 1 channels from direct M3U file'])
async def test_successful_scrape_runs_opt_in_matching(db_session, inventory, monkeypatch, status):
    from app.services.scraper_service import ScraperService
    from types import SimpleNamespace
    EPGMatchingAutomation(db_session).save(EPGMatchingConfig(enabled=True))
    fake = SimpleNamespace(scrape=AsyncMock(return_value=([('d'*40, 'ES: News One HD', {})], status)))
    monkeypatch.setattr('app.services.scraper_service.create_scraper_for_url', lambda *args: fake)
    channels, returned_status = await ScraperService(db_session).scrape_url('https://example.com/list')
    assert returned_status == status
    assert channels[0].metadata['tv_channel_id'] is not None
    assert db_session.query(TVChannel).count() == 1
    assert EPGMatchingAutomation(db_session).last_run().assigned == 2


def test_disabled_auth_does_not_echo_arbitrary_token(client, monkeypatch):
    monkeypatch.delenv('API_TOKEN', raising=False)
    response = client.get('/playlist.m3u?token=not-a-credential')
    assert 'not-a-credential' not in response.text
    assert response.headers['cache-control'] == 'private, no-store'


def test_disable_automation_preserves_applied_assignments(client, db_session, inventory):
    assert client.put('/api/v1/config/epg-matching', json={'enabled': True}).status_code == 200
    EPGMatchingAutomation(db_session).run()
    assert client.put('/api/v1/config/epg-matching', json={'enabled': False}).status_code == 200
    assert EPGMatchingAutomation(db_session).run() is None
    db_session.refresh(inventory[2])
    assert inventory[2].tv_channel_id is not None
    assert client.get('/api/v1/config/epg-matching/last-run').json()['assigned'] == 1


def test_existing_other_country_does_not_block_a_distinct_station(db_session, inventory):
    db_session.add(TVChannel(name='UK: News One', country='UK', epg_id='uk.news'))
    db_session.commit()
    automation = EPGMatchingAutomation(db_session)
    automation.save(EPGMatchingConfig(enabled=True))
    result = automation.run()
    assert result.created == result.assigned == 1
    assert db_session.query(TVChannel).count() == 2
