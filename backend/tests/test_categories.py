"""Category ownership, lossless metadata and cross-page live discovery contracts."""

from datetime import datetime, timedelta, timezone
import xml.etree.ElementTree as ET
import pytest

from app.models.models import TVChannel, AcestreamChannel, EPGSource, EPGChannel, EPGProgram, EPGProgramCategory
from app.services.epg_service import EPGService
from app.services.category_taxonomy import classify_genres, channel_category


@pytest.fixture
def category_data(db_session):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    source = EPGSource(name='Category guide', url='https://example.test/guide', enabled=True)
    db_session.add(source)
    db_session.flush()
    guide = EPGChannel(name='La 1', channel_xml_id='one', epg_source_id=source.id, icon_url='https://example.test/epg-logo.png')
    db_session.add(guide)
    db_session.flush()
    channels = []
    for i in range(3):
        channel = TVChannel(name=['La 1', 'Sports channel', 'Unknown channel'][i], category=['general', 'sports', None][i], epg_id=guide.channel_xml_id if i == 0 else None, epg_source_id=source.id if i == 0 else None, is_active=True, is_favorite=i == 0, logo_url='https://example.test/manual.png' if i == 0 else None)
        db_session.add(channel)
        db_session.flush()
        db_session.add(AcestreamChannel(id=f'{i + 1:040x}', name=channel.name, tv_channel_id=channel.id, is_active=True, is_online=True))
        channels.append(channel)
    program = EPGProgram(epg_channel_id=guide.id, title='Football live', start_time=now - timedelta(minutes=10), end_time=now + timedelta(minutes=10), category='0', category_observations=[EPGProgramCategory(position=0, label='0'), EPGProgramCategory(position=1, label='Football / Soccer', language='en')])
    db_session.add(program)
    db_session.commit()
    return now, source, guide, channels, program


def test_stable_and_now_categories_are_distinct_and_filters_agree(client, category_data):
    now, _, _, channels, _ = category_data
    query = {'watchable': True, 'online_only': True, 'as_of': now.isoformat()}
    stable = client.get('/api/v1/tv-channels/categories', params=query)
    assert stable.status_code == 200, stable.text
    assert {row['id']: row['count'] for row in stable.json()['items']} == {'general': 1, 'sports': 1, 'uncategorized': 1}
    current = client.get('/api/v1/tv-channels/categories', params={**query, 'category_basis': 'now'}).json()
    assert {row['id']: row['count'] for row in current['items']} == {'football': 1, 'sports': 1, 'no-guide': 2}
    selected = client.get('/api/v1/tv-channels/browse', params={**query, 'category_basis': 'now', 'category_id': 'sports', 'limit': 1}).json()
    assert selected['total'] == 1
    assert selected['items'][0]['id'] == channels[0].id
    assert selected['items'][0]['category'] == 'general'
    assert selected['items'][0]['logo_url'].endswith('manual.png')
    assert selected['items'][0]['epg_logo_url'].endswith('epg-logo.png')
    guide = client.get('/api/v1/tv-channels/now-next', params={'channel_ids': channels[0].id, 'as_of': now.isoformat()}).json()
    assert guide[0]['now']['genre_ids'] == ['football', 'sports']


def test_current_programme_boundary_and_disabled_source(client, db_session, category_data):
    now, source, _, channels, program = category_data
    program.end_time = now
    db_session.commit()
    params = {'category_basis': 'now', 'as_of': now.isoformat(), 'is_favorite': True}
    result = client.get('/api/v1/tv-channels/categories', params=params).json()
    assert result['items'][0]['id'] == 'no-guide'
    program.end_time = now + timedelta(minutes=5)
    source.enabled = False
    db_session.commit()
    assert client.get('/api/v1/tv-channels/now-next', params={'channel_ids': channels[0].id}).json() == []


def test_review_is_read_only_atomic_and_rejects_stale_evidence(client, db_session, category_data):
    _, _, _, channels, _ = category_data
    row = channels[0]
    row.category = None
    db_session.commit()
    request = {'channel_ids': [row.id]}
    preview = client.post('/api/v1/tv-channels/category-suggestions/preview', json=request).json()[0]
    assert preview['suggested_category'] == 'general'
    db_session.refresh(row)
    assert row.category is None
    apply = {'items': [{'channel_id': row.id, 'category_id': 'general', 'fingerprint': preview['fingerprint']}]}
    row.name = 'Different identity'
    db_session.commit()
    assert client.post('/api/v1/tv-channels/category-suggestions/apply', json=apply).status_code == 409
    db_session.refresh(row)
    assert row.category is None
    row.name = 'La 1'
    db_session.commit()
    assert client.post('/api/v1/tv-channels/category-suggestions/apply', json=apply).json() == {'updated': 1}
    db_session.refresh(row)
    assert row.category_origin == 'reviewed'
    assert client.post('/api/v1/tv-channels/category-suggestions/apply', json=apply).status_code == 409


def test_manual_clear_and_automatic_reset_have_different_ownership(client, db_session, category_data):
    _, _, _, channels, _ = category_data
    row = channels[0]
    url = f'/api/v1/tv-channels/{row.id}/category'
    response = client.put(url, json={'category': None, 'mode': 'manual', 'expected_revision': 0})
    assert response.status_code == 200, response.text
    preview = client.post('/api/v1/tv-channels/category-suggestions/preview', json={'channel_ids': [row.id]}).json()[0]
    assert preview['suggested_category'] is None
    assert client.put(url, json={'category': 'sports', 'expected_revision': 0}).status_code == 409
    assert client.put(url, json={'mode': 'automatic', 'expected_revision': 1}).status_code == 200
    preview = client.post('/api/v1/tv-channels/category-suggestions/preview', json={'channel_ids': [row.id]}).json()[0]
    assert preview['suggested_category'] == 'general'


def test_multicategory_refresh_export_and_cleanup(db_session, category_data):
    now, source, guide, _, _ = category_data
    start = (now + timedelta(hours=1)).strftime('%Y%m%d%H%M%S +0000')
    end = (now + timedelta(hours=2)).strftime('%Y%m%d%H%M%S +0000')
    template = '<tv><channel id="one"><display-name>La 1</display-name></channel><programme channel="one" start="' + start + '" stop="' + end + '"><title>Next</title>{}</programme></tv>'
    service = EPGService(db_session)
    xml = template.format('<category>0</category><category lang="es">Cine, Acción</category><category lang="en">Action</category><category lang="">Unmapped label</category>')
    service._process_epg_xml(source.id, xml.encode())
    program = db_session.query(EPGProgram).filter_by(title='Next').one()
    identity = program.id
    assert program.category == '0'
    assert program.genre_ids == ['action', 'movies']
    lines = service.programme_xml_lines(program, 'one')
    parsed = ET.fromstring('\n'.join(lines))
    assert [(c.text, c.get('lang')) for c in parsed.findall('category')] == [('0', None), ('Cine, Acción', 'es'), ('Action', 'en'), ('Unmapped label', '')]
    service._process_epg_xml(source.id, xml.encode())
    db_session.expire_all()
    assert db_session.query(EPGProgram).filter_by(title='Next').one().id == identity
    service._process_epg_xml(source.id, template.format('<category>Weather</category>').encode())
    db_session.expire_all()
    program = db_session.query(EPGProgram).filter_by(title='Next').one()
    assert program.categories == [{'label': 'Weather', 'language': None}]
    assert db_session.query(EPGProgramCategory).filter_by(program_id=identity).count() == 1
    service.purge_expired_programs(now=now + timedelta(days=100))
    assert db_session.query(EPGProgramCategory).count() == 0


def test_oversized_metadata_rolls_back_import(db_session, category_data):
    _, source, _, _, _ = category_data
    xml = '<tv><channel id="new"><display-name>New</display-name></channel><programme channel="new" start="20261110000000 +0000" stop="20261110010000 +0000"><title>Long</title><category>' + ('x' * 1025) + '</category></programme></tv>'
    with pytest.raises(ValueError, match='bounds'):
        EPGService(db_session)._process_epg_xml(source.id, xml.encode())
    assert db_session.query(EPGChannel).filter_by(channel_xml_id='new').count() == 0


def test_source_qualified_logo_lookup(client, db_session, category_data):
    _, _, guide, channels, _ = category_data
    other = EPGSource(name='Other', url='https://example.test/other')
    db_session.add(other)
    db_session.flush()
    db_session.add(EPGChannel(name='Wrong', channel_xml_id=guide.channel_xml_id, epg_source_id=other.id, icon_url='https://example.test/wrong.png'))
    db_session.commit()
    result = client.get(f'/api/v1/tv-channels/{channels[0].id}').json()
    assert result['epg_logo_url'].endswith('/epg-logo.png')


def test_category_aliases_keep_unknown_and_custom_text():
    assert classify_genres(['0', 'Deportes, Baloncesto']) == ['basketball', 'sports']
    assert classify_genres(['American Football']) == ['american-football', 'sports']
    assert classify_genres(['Cine, unreviewed random token']) == []
    assert channel_category('My own collection').label == 'My own collection'
    assert channel_category('My own collection').id.startswith('custom-')


def test_atomic_review_rejects_entire_batch_and_conflicting_groups(client, db_session, category_data):
    _, _, _, channels, _ = category_data
    first, second = channels[:2]
    first.category = second.category = None
    second.acestream_channels[0].group = 'Sports'
    db_session.commit()
    previews = client.post('/api/v1/tv-channels/category-suggestions/preview', json={'channel_ids': [first.id, second.id]}).json()
    payload = {'items': [{'channel_id': row['channel_id'], 'category_id': row['suggested_category'], 'fingerprint': row['fingerprint']} for row in previews]}
    second.acestream_channels[0].group = 'News'
    db_session.commit()
    assert client.post('/api/v1/tv-channels/category-suggestions/apply', json=payload).status_code == 409
    db_session.refresh(first)
    assert first.category is None and first.category_revision == 0
    first.acestream_channels[0].group = 'Sports'
    db_session.commit()
    preview = client.post('/api/v1/tv-channels/category-suggestions/preview', json={'channel_ids': [first.id]}).json()[0]
    assert preview['suggested_category'] is None
    assert preview['reason'] == 'Conflicting channel evidence'


def test_category_totals_are_before_pagination_and_manual_edit_rejects_stale(client, db_session, category_data):
    _, _, _, channels, _ = category_data
    for i in range(105):
        db_session.add(TVChannel(name=f'News {i}', category='news'))
    db_session.commit()
    counts = client.get('/api/v1/tv-channels/categories', params={'limit': 1}).json()
    assert counts['total'] == 108
    assert next(item['count'] for item in counts['items'] if item['id'] == 'news') == 105
    page = client.get('/api/v1/tv-channels/browse', params={'category_id': 'news', 'skip': 100, 'limit': 10}).json()
    assert page['total'] == 105 and len(page['items']) == 5
    url = f'/api/v1/tv-channels/{channels[0].id}'
    assert client.put(url, json={'category': 'music', 'expected_category_revision': 0}).status_code == 200
    assert client.put(url, json={'category': 'sports', 'expected_category_revision': 0}).status_code == 409
    assert client.get(url).json()['category'] == 'music'
