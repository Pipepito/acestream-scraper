"""Assign every imported stream under a W3U folder to one TV channel, one folder or by name match."""
from datetime import datetime, timezone

import pytest

HD_ID = 'a' * 40
SD_ID = 'b' * 40
NEWS_ID = 'c' * 40
VOD_ID = 'd' * 40


def entry(id, parent_id, name, kind='folder', **extra):
    row = {'id': id, 'parent_id': parent_id, 'name': name, 'kind': kind, 'content_type': 'live' if kind != 'folder' else 'unknown',
           'reason': '', 'description': '', 'image': None, 'guide_id': None, 'number': None, 'origin': 'example.test',
           'header_names': [], 'channel_id': None, 'duplicate': False, 'retained': False, 'imported': False}
    row.update(extra)
    return row


@pytest.fixture
def other_tv(db_session):
    from app.models.models import TVChannel
    tv = TVChannel(name='Other', is_active=True)
    db_session.add(tv)
    db_session.commit()
    return tv


@pytest.fixture
def catalogue(db_session, other_tv):
    """root → Sports → DAZN 1 → {HD, SD, dup(HD), vod}; root → News → n1 (on Other); root → Empty."""
    from app.models.models import AcestreamChannel
    from app.repositories.catalogue_repository import CatalogueRepository
    db_session.add_all([
        AcestreamChannel(id=HD_ID, name='DAZN 1 HD', is_active=True),
        AcestreamChannel(id=SD_ID, name='DAZN 1 SD', is_active=True),
        AcestreamChannel(id=NEWS_ID, name='News 24', is_active=True, tv_channel_id=other_tv.id),
        AcestreamChannel(id=VOD_ID, name='Old match', is_active=True),
    ])
    entries = [
        entry('root', None, 'Catalogue'),
        entry('sports', 'root', 'Sports'),
        entry('dazn1', 'sports', 'DAZN 1'),
        entry('hd', 'dazn1', 'HD'),
        entry('sd', 'dazn1', 'SD'),
        entry('hd-stream', 'hd', 'DAZN 1 HD', kind='acestream', channel_id=HD_ID, imported=True),
        entry('sd-stream', 'sd', 'DAZN 1 SD', kind='acestream', channel_id=SD_ID, imported=True),
        entry('dup-stream', 'dazn1', 'DAZN 1 HD (mirror)', kind='acestream', channel_id=HD_ID, imported=True, duplicate=True),
        entry('vod-stream', 'dazn1', 'Old match', kind='acestream', channel_id=VOD_ID, imported=False, content_type='vod'),
        entry('news', 'root', 'News'),
        entry('news-stream', 'news', 'News 24', kind='acestream', channel_id=NEWS_ID, imported=True),
        entry('empty', 'root', 'Empty'),
    ]
    snapshot = {'entries': entries, 'counts': {}, 'partial': False, 'warnings': [], 'documents': []}
    row = CatalogueRepository(db_session).save(None, None, dict(name='Fixture', source_url=None, snapshot=snapshot,
        selected_branches=['root'], mode='compatible', refresh_enabled=False, updated_at=datetime.now(timezone.utc)))
    db_session.commit()
    return row


def assigned_ids(db_session, tv_channel_id):
    from app.models.models import AcestreamChannel
    return {c.id for c in db_session.query(AcestreamChannel).filter(AcestreamChannel.tv_channel_id == tv_channel_id)}


def test_folder_assignment_dedupes_shared_channel_rows(client, db_session, catalogue):
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folders/dazn1/tv-channel', json={'create_name': 'DAZN 1'})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['tv_channel']['name'] == 'DAZN 1'
    assert body['assigned'] == 2 and body['already'] == 0 and body['moved'] == 0
    assert body['skipped_other_channel'] == 0 and body['skipped_not_imported'] == 1
    assert assigned_ids(db_session, body['tv_channel']['id']) == {HD_ID, SD_ID}


def test_folder_assignment_skips_then_moves_streams_on_other_channels(client, db_session, catalogue, other_tv):
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folders/news/tv-channel', json={'tv_channel_id': other_tv.id})
    assert response.status_code == 200, response.text
    assert response.json()['already'] == 1 and response.json()['assigned'] == 0
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folders/sports/tv-channel', json={'create_name': 'All sports'})
    assert response.status_code == 200, response.text
    assert response.json()['assigned'] == 2 and response.json()['skipped_other_channel'] == 0
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folders/root/tv-channel', json={'tv_channel_id': response.json()['tv_channel']['id']})
    assert response.json()['already'] == 2 and response.json()['skipped_other_channel'] == 1
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folders/root/tv-channel',
                           json={'tv_channel_id': response.json()['tv_channel']['id'], 'reassign': True})
    assert response.json()['moved'] == 1 and response.json()['already'] == 2
    assert assigned_ids(db_session, response.json()['tv_channel']['id']) == {HD_ID, SD_ID, NEWS_ID}
    assert assigned_ids(db_session, other_tv.id) == set()


def test_folder_match_preview_lists_parents_and_statuses(client, db_session, catalogue, other_tv):
    from app.models.models import TVChannel
    db_session.add(TVChannel(name='DAZN 1', country=None, is_active=True))
    db_session.commit()
    rows = {row['folder_id']: row for row in client.post(f'/api/v1/catalogues/{catalogue.id}/folder-matches/preview').json()['rows']}
    # Folders with their own streams are listed; a parent is listed when its name matches a TV channel.
    assert set(rows) == {'dazn1', 'hd', 'sd', 'news'}
    assert rows['dazn1']['status'] == 'match' and rows['dazn1']['candidate']['name'] == 'DAZN 1'
    assert rows['dazn1']['stream_count'] == 2 and rows['dazn1']['path'] == 'Sports / DAZN 1'
    assert rows['hd']['status'] == 'none' and rows['hd']['path'] == 'Sports / DAZN 1 / HD' and rows['hd']['stream_count'] == 1
    assert rows['news']['status'] == 'assigned' and rows['news']['current']['id'] == other_tv.id and rows['news']['candidate'] is None
    db_session.add(TVChannel(name='Sports', country='es', is_active=True))
    db_session.commit()
    rows = {row['folder_id']: row for row in client.post(f'/api/v1/catalogues/{catalogue.id}/folder-matches/preview').json()['rows']}
    assert rows['sports']['status'] == 'match' and rows['sports']['stream_count'] == 2 and rows['sports']['path'] == 'Sports'


def test_folder_match_apply_is_deepest_first_and_atomic(client, db_session, catalogue):
    from app.models.models import AcestreamChannel, TVChannel
    tv = TVChannel(name='DAZN 1', is_active=True)
    db_session.add(tv)
    db_session.commit()
    body = {'assignments': [{'folder_id': 'sports', 'create': True}, {'folder_id': 'dazn1', 'tv_channel_id': tv.id}]}
    response = client.post(f'/api/v1/catalogues/{catalogue.id}/folder-matches/apply', json=body)
    assert response.status_code == 200, response.text
    results = {row['folder_id']: row for row in response.json()['results']}
    assert results['dazn1']['assigned'] == 2 and results['dazn1']['tv_channel']['id'] == tv.id
    assert results['sports']['assigned'] == 0 and results['sports']['tv_channel'] is None and results['sports']['note']
    assert db_session.get(AcestreamChannel, HD_ID).tv_channel_id == tv.id
    assert db_session.query(TVChannel).filter(TVChannel.name == 'Sports').first() is None
    bad = {'assignments': [{'folder_id': 'hd', 'tv_channel_id': 999999}, {'folder_id': 'news', 'create': True}]}
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folder-matches/apply', json=bad).status_code == 409
    assert db_session.query(TVChannel).filter(TVChannel.name == 'News').first() is None
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folder-matches/apply', json={'assignments': [{'folder_id': 'hd'}]}).status_code == 422


def test_folder_assignment_rejects_non_folders_and_empty_folders(client, catalogue):
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/hd-stream/tv-channel', json={'create_name': 'x'}).status_code == 404
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/missing/tv-channel', json={'create_name': 'x'}).status_code == 404
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/empty/tv-channel', json={'create_name': 'x'}).status_code == 422
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/dazn1/tv-channel', json={}).status_code == 422
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/dazn1/tv-channel', json={'create_name': 'x', 'tv_channel_id': 1}).status_code == 422
    assert client.post(f'/api/v1/catalogues/{catalogue.id}/folders/dazn1/tv-channel', json={'tv_channel_id': 999999}).status_code == 404
    assert client.post('/api/v1/catalogues/999999/folders/dazn1/tv-channel', json={'create_name': 'x'}).status_code == 404
