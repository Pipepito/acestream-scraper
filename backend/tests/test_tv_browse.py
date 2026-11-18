"""Catalogue-wide filters, stable bounded pages and bounded relationship reads."""
import pytest
from sqlalchemy import event
from app.models.models import TVChannel, AcestreamChannel
from app.repositories.channel_repository import ChannelRepository
from app.schemas.channel import TVChannelResponse
from app.schemas.tv_browse import TVBrowseFilters


@pytest.fixture
def inventory(db_session):
    rows = []
    for i in range(125):
        row = TVChannel(name=f'Channel {i:03}', channel_number=i + 1, category='Sport' if i % 2 else 'News',
                        country='Spain', language='Spanish', is_active=i != 124, is_favorite=i > 100,
                        description='100%_literal' if i == 123 else None)
        db_session.add(row)
        db_session.flush()
        if i != 0:
            db_session.add(AcestreamChannel(id=f'{i:040x}', name=f'Stream {i}', tv_channel_id=row.id,
                                           is_active=i != 123, is_online=None if i % 3 == 0 else i % 3 == 1))
        rows.append(row.id)
    db_session.commit()
    db_session.expire_all()
    return rows


def test_filters_cover_whole_catalogue_before_pagination(client, inventory):
    params = dict(category='Sport', is_favorite='true', sort='channel_number', direction='desc', limit=3)
    response = client.get('/api/v1/tv-channels/browse', params=params)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['total'] == 12
    assert [row['channel_number'] for row in result['items']] == [124, 122, 120]
    second = client.get('/api/v1/tv-channels/browse', params={**params, 'skip': 3}).json()
    assert [row['channel_number'] for row in second['items']] == [118, 116, 114]
    literal = client.get('/api/v1/tv-channels/browse', params={'search': '%_'}).json()
    assert [row['id'] for row in literal['items']] == [inventory[123]]
    stream = client.get('/api/v1/tv-channels/browse', params={'search': 'Stream 120'}).json()
    assert [row['id'] for row in stream['items']] == [inventory[120]]
    metadata = client.get('/api/v1/tv-channels/inventory').json()
    assert metadata == dict(total=125, favorites=24, with_streams=124, categories=['News', 'Sport'], countries=['Spain'], languages=['Spanish'], epg_sources=[])


def test_watchable_inventory_keeps_disabled_and_unknown_distinct(client, inventory):
    params = {'watchable': True, 'online_only': True, 'limit': 100}
    online = client.get('/api/v1/tv-channels/browse', params=params).json()
    assert online['total'] == 41
    assert all(row['is_active'] and any(s['is_active'] and s['is_online'] is True for s in row['acestream_channels']) for row in online['items'])
    all_rows = client.get('/api/v1/tv-channels/browse', params={**params, 'online_only': False}).json()
    assert all_rows['total'] == 122
    assert len(all_rows['items']) == 100
    assert all_rows['items'][0]['id'] == inventory[1]
    unknown = client.get('/api/v1/tv-channels/browse', params={'signal': 'unknown', 'limit': 100}).json()
    assert unknown['total'] == 41
    assert all(row['acestream_channels'] and all(s['is_online'] is None for s in row['acestream_channels']) for row in unknown['items'])


@pytest.mark.parametrize('params', [{'limit': 101}, {'limit': 0}, {'skip': -1}, {'sort': 'not_a_column'}, {'is_favorite': 'maybe'}, {'surprise': 'ignored?'}])
def test_browse_rejects_invalid_bounds_and_fields(client, params):
    assert client.get('/api/v1/tv-channels/browse', params=params).status_code == 422


def test_browse_serialization_uses_three_reads_for_a_hundred_rows(db_session, inventory):
    statements = []
    engine = db_session.get_bind()
    def capture(_connection, _cursor, statement, _parameters, _context, _many):
        if statement.lstrip().upper().startswith('SELECT'):
            statements.append(statement)
    event.listen(engine, 'before_cursor_execute', capture)
    try:
        rows, total = ChannelRepository(db_session).browse_tv_channels(TVBrowseFilters(limit=100))
        serialized = [TVChannelResponse.model_validate(row) for row in rows]
    finally:
        event.remove(engine, 'before_cursor_execute', capture)
    assert total == 125 and len(serialized) == 100
    assert len(statements) == 3
