"""Synthetic W3U documents: never depend on mutable public lists."""
import asyncio
import json
import pytest

from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
from app.services.w3u_parser import W3UTraversal, Limits
from app.utils.bounded_source import SourceResponse

A = 'a' * 40
B = 'b' * 40


def station(name='Alpha', url=None, **extra):
    return dict(name=name, url=url or f'acestream://{A}', **extra)


def run(data, **kwargs):
    return asyncio.run(W3UTraversal(**kwargs).run(sample=json.dumps(data)))


def test_normalization_metadata_identity_and_truthful_counts():
    result = run({'name': 'TV', 'url': 'https://example.test/self.w3u', 'stations': [
        station(epgId='alpha.es', number=7, online=True),
        station(url=f'http://127.0.0.1:6878/ace/getstream?id={A}'),
        station(url=f'acestream://{B}'), station(url=f'acestream://{A}junk'),
        station(url='https://media.test/live.m3u8?token=SECRET', userAgent='Agent'),
        station(url='https://media.test/watch.php', embed=True),
        station(url='https://media.test/movie.mp4'), station(url='https://media.test/a.mpd'),
    ]})
    assert result['counts']['accepted'] == 3
    assert result['counts']['duplicates'] == 1
    assert result['counts']['invalid'] == 1
    assert result['counts']['unsupported'] == 3
    entries = result['entries'][1:]
    assert entries[0]['guide_id'] == 'alpha.es'
    assert entries[0]['number'] == 7
    assert entries[1]['channel_id'] == A
    assert entries[4]['_headers'] == {'User-Agent': 'Agent'}
    assert len({e['id'] for e in entries}) == len(entries)


def test_relative_links_false_import_redirect_cycle_and_repeated_document(monkeypatch):
    calls = []
    documents = {
        'https://example.test/root': {'name': 'Root', 'url': '/root', 'groups': [
            {'name': 'One', 'url': '/short', 'import': False},
            {'name': 'Two', 'url': '/child'}]},
        'https://example.test/child': {'groups': [{'name': 'Back', 'url': '/root'}],
                                      'stations': [station()]},
    }
    async def get(url, **kwargs):
        calls.append(url)
        assert kwargs['timeout'] <= 10
        assert kwargs['max_bytes'] <= 4 * 1024 * 1024
        if url.endswith('/short'):
            return SourceResponse(302, b'', {'Location': '/child'})
        return SourceResponse(200, json.dumps(documents[url]).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    result = asyncio.run(W3UTraversal().run(url='https://example.test/root'))
    assert calls == ['https://example.test/root', 'https://example.test/short', 'https://example.test/child']
    assert result['counts']['accepted'] == 1
    assert result['counts']['duplicates'] == 1
    assert len([e for e in result['entries'] if e['reason'] == 'Cycle/update reference skipped']) == 2
    assert not result['partial']


@pytest.mark.parametrize('limits', [Limits(records=3), Limits(depth=0)])
def test_record_and_depth_limits(limits):
    result = run({'groups': [{'name': 'Folder', 'stations': [station(), station(url=f'acestream://{B}')]}]}, limits=limits)
    assert result['partial']
    assert result['warnings']
    assert len(result['entries']) <= limits.records


def test_malformed_fields_are_data_and_no_arbitrary_fetch(monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail('station/image/root URL must not be fetched')
    monkeypatch.setattr('app.services.w3u_parser.source_get', forbidden)
    result = run({'url': 'https://example.test/update', 'stations': [None,
        station(url='http://[broken'), station(url='javascript:alert(1)'),
        station(url='https://example.test/watch', isHost=True),
        station(image='http://169.254.169.254/logo', cookie='secret')]})
    assert result['counts']['accepted'] == 0
    assert all(e['image'] is None for e in result['entries'])


def test_request_budget_and_failed_child(monkeypatch):
    async def get(url, **kwargs):
        if url.endswith('/root'):
            return SourceResponse(200, json.dumps({'groups': [
                {'name': 'bad', 'url': '/bad'}, {'name': 'more', 'url': '/more'}]}).encode(), {})
        raise ValueError('Sensitive upstream URL and token')
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    result = asyncio.run(W3UTraversal(limits=Limits(requests=2)).run(url='https://example.test/root'))
    assert result['partial']
    assert result['counts']['failed_fetches'] == 1
    assert result['counts']['requests'] == 2
    assert 'Sensitive' not in json.dumps(result)


def test_conditional_cache(monkeypatch):
    seen = []
    data = {'stations': [station()]}
    async def get(url, **kwargs):
        seen.append(kwargs['headers'])
        return SourceResponse(304, b'', {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    cached = {'https://example.test/list': dict(url='https://example.test/list', data=data, size=100, etag='"v1"')}
    result = asyncio.run(W3UTraversal(cached=cached).run(url='https://example.test/list'))
    assert seen == [{'If-None-Match': '"v1"'}]
    assert result['counts']['cached_documents'] == 1
    assert result['counts']['accepted'] == 1


def test_reviewed_import_no_tv_rows_and_public_masking(db_session):
    from app.services.catalogue_service import CatalogueService
    from app.models.models import AcestreamChannel, TVChannel, W3UCatalogue
    svc = CatalogueService(db_session)
    preview = svc.preview(CataloguePreviewRequest(sample=json.dumps({'name': 'Catalogue', 'groups': [
        {'name': 'Ace', 'stations': [station()]},
        {'name': 'HTTP', 'stations': [station(url='https://cdn.test/live.m3u8?key=SECRET', referer='https://page.test/?token=PRIVATE')]}
    ]})))
    assert 'SECRET' not in preview.model_dump_json()
    assert 'PRIVATE' not in preview.model_dump_json()
    assert not db_session.query(AcestreamChannel).count()
    assert not db_session.query(W3UCatalogue).count()
    folder = next(e.id for e in preview.entries if e.name == 'Ace')
    saved = svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=preview.preview_token, name='Mine', selected_branches=[folder]))
    assert db_session.query(AcestreamChannel).count() == 1
    assert not db_session.query(TVChannel).count()
    channel = db_session.get(AcestreamChannel, A)
    assert channel.is_online is None
    assert channel.source_url == f'catalogue:{saved.id}'
    assert next(e for e in svc.get(saved.id).entries if e.channel_id == A).imported
    # Local snapshot can be reviewed again without accessing the network.
    second = svc.preview(CataloguePreviewRequest(catalogue_id=saved.id))
    channel.name = 'Manual name'
    channel.is_active = False
    db_session.commit()
    svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=second.preview_token, name='Mine', selected_branches=['root']))
    assert db_session.get(AcestreamChannel, A).name == 'Manual name'
    assert db_session.get(AcestreamChannel, A).is_active is False
    assert db_session.query(AcestreamChannel).count() == 2
    svc.repository.delete(saved.id)
    assert db_session.query(AcestreamChannel).count() == 2


def test_stale_preview_rejected_atomically(db_session):
    from app.services.catalogue_service import CatalogueService
    svc = CatalogueService(db_session)
    preview = svc.preview(CataloguePreviewRequest(sample=json.dumps({'stations': [station()]})))
    saved = svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=preview.preview_token, name='Mine', selected_branches=[]))
    p1 = svc.preview(CataloguePreviewRequest(catalogue_id=saved.id))
    p2 = svc.preview(CataloguePreviewRequest(catalogue_id=saved.id))
    svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=p1.preview_token, name='Changed', selected_branches=[]))
    with pytest.raises(ValueError, match='changed'):
        svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=p2.preview_token, name='Old', selected_branches=['root']))
    assert svc.get(saved.id).name == 'Changed'


def test_partial_refresh_retains_old_inventory(monkeypatch, db_session):
    from app.services.catalogue_service import CatalogueService
    svc = CatalogueService(db_session)
    failing = False
    async def get(url, **kwargs):
        if url.endswith('/root'):
            return SourceResponse(200, json.dumps({'groups': [{'name': 'TV', 'url': '/child'}]}).encode(), {})
        if failing:
            return SourceResponse(500, b'', {})
        return SourceResponse(200, json.dumps({'stations': [station()]}).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    p = svc.preview(CataloguePreviewRequest(url='https://example.test/root'))
    saved = svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=p.preview_token, name='Remote', selected_branches=['root'], refresh_enabled=True))
    failing = True
    refreshed = svc.refresh(saved.id)
    assert refreshed.partial
    assert refreshed.counts.failed_fetches == 1
    assert next(e for e in refreshed.entries if e.channel_id == A).retained


def test_api_preview_save_and_upload_limits(client):
    response = client.post('/api/v1/catalogues/preview', json={'sample': json.dumps({'stations': [station()]})})
    assert response.status_code == 200, response.text
    preview = response.json()
    saved = client.post('/api/v1/catalogues', json={'preview_token': preview['preview_token'], 'name': 'Test', 'selected_branches': ['root']})
    assert saved.status_code == 200, saved.text
    catalogue_id = saved.json()['id']
    assert client.get(f'/api/v1/catalogues/{catalogue_id}').json()['name'] == 'Test'
    assert client.get('/api/v1/catalogues').json()[0]['id'] == catalogue_id
    assert client.post('/api/v1/catalogues/preview', content=b'{}', headers={'Content-Length': str(9 * 1024 * 1024)}).status_code == 413
    assert client.delete(f'/api/v1/catalogues/{catalogue_id}').status_code == 204


def test_migration_upgrade_preserves_channels_and_fresh_schema(tmp_path):
    from sqlalchemy import create_engine, inspect, text
    from migration_test_utils import upgrade_to_revision, upgrade_to_head, downgrade_to_revision, database_url_for
    path = tmp_path / 'catalogues.db'
    upgrade_to_revision(path, '20261021_1200')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO acestream_channels (id, name) VALUES ('existing', 'Manual')"))
        upgrade_to_head(path)
        assert 'w3u_catalogues' in inspect(engine).get_table_names()
        with engine.connect() as conn:
            assert conn.execute(text('SELECT name FROM acestream_channels')).scalar() == 'Manual'
        downgrade_to_revision(path, '20261021_1200')
        assert 'w3u_catalogues' not in inspect(engine).get_table_names()
        upgrade_to_head(path)
    finally:
        engine.dispose()
    fresh = tmp_path / 'fresh.db'
    upgrade_to_head(fresh)
    engine = create_engine(database_url_for(fresh))
    try:
        assert 'w3u_catalogues' in inspect(engine).get_table_names()
    finally:
        engine.dispose()


def test_headers_variants_do_not_overwrite_each_other():
    result = run({'stations': [station(url='https://cdn.test/live.m3u8', userAgent='One'),
                               station(url='https://cdn.test/live.m3u8', userAgent='Two')]})
    assert result['counts']['accepted'] == 2
    assert len({e['channel_id'] for e in result['entries'][1:]}) == 2


def test_byte_budget_counts_failed_overflow(monkeypatch):
    calls = []
    async def get(url, **kwargs):
        calls.append(url)
        if url.endswith('/root'):
            return SourceResponse(200, json.dumps({'groups': [{'url': '/large'}, {'url': '/another'}]}).encode(), {})
        raise ValueError('Source response exceeds byte limit')
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    result = asyncio.run(W3UTraversal(limits=Limits(bytes=1000)).run(url='https://example.test/root'))
    assert len(calls) == 2
    assert result['partial']
    assert result['counts']['bytes_read'] == 1000


def test_preview_api_requires_token_before_reading_body(client, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setenv('API_TOKEN', 'catalogue-test-token')
    get_settings.cache_clear()
    try:
        assert client.post('/api/v1/catalogues/preview', content=b'{invalid').status_code == 401
        assert client.get('/api/v1/catalogues').status_code == 401
    finally:
        get_settings.cache_clear()


def test_invalid_request_does_not_echo_private_input(client):
    response = client.post('/api/v1/catalogues/preview', json={
        'url': 'https://source.test/?token=PRIVATE', 'sample': '{"password": "SECRET"}'})
    assert response.status_code == 422
    assert 'PRIVATE' not in response.text
    assert 'SECRET' not in response.text


def test_metadata_child_is_denied_even_with_private_sources(monkeypatch):
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'true')
    result = run({'groups': [{'name': 'Blocked', 'url': 'http://169.254.169.254/latest'}]})
    assert result['partial']
    assert result['counts']['failed_fetches'] == 1
    assert result['counts']['accepted'] == 0


def test_literal_metadata_media_is_not_importable(monkeypatch):
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'true')
    result = run({'stations': [station(url='http://169.254.169.254/live.m3u8')]})
    assert result['counts']['invalid'] == 1
    assert result['entries'][1]['channel_id'] is None


def test_bad_url_port_never_leaks_input(client):
    response = client.post('/api/v1/catalogues/preview', json={'url': 'https://example.test:PRIVATE/list'})
    assert response.status_code == 422
    assert 'PRIVATE' not in response.text


def test_scheduled_catalogue_results_are_in_totals_and_notification(db_session, monkeypatch):
    from app.tasks import url_scraping_task
    from sqlalchemy.orm import sessionmaker
    monkeypatch.setattr(url_scraping_task, 'SessionLocal', sessionmaker(bind=db_session.get_bind()))
    from app.services import notification_service
    monkeypatch.setattr(url_scraping_task.ScraperService, 'get_enabled_urls', lambda self: [])
    monkeypatch.setattr('app.services.catalogue_service.CatalogueService.refresh_enabled',
                        lambda self: {'catalogues': 3, 'catalogue_failures': 1, 'catalogue_partial': 1})
    sent = []
    monkeypatch.setattr(notification_service, 'notify', lambda *args: sent.append(args))
    result = url_scraping_task.run_url_scraping_task()
    assert result['processed'] == 3 and result['failures'] == 1
    assert '3 W3U catalogue(s), 1 partial' in sent[0][2]


@pytest.mark.parametrize('route', ['/playlist.m3u', '/api/v1/playlists/tv-channels/m3u'])
def test_w3u_export_never_publishes_private_http_inputs(client, db_session, route):
    from app.services.catalogue_service import CatalogueService
    from app.models.models import AcestreamChannel, TVChannel
    svc = CatalogueService(db_session)
    preview = svc.preview(CataloguePreviewRequest(sample=json.dumps({'stations': [
        station(), station(name='HTTP private', url='https://cdn.test/live.m3u8?token=PRIVATE',
                           referer='https://page.test/?key=SECRET')]})))
    saved = svc.save(CatalogueSaveRequest(confirm_live=True, preview_token=preview.preview_token, name='Private', selected_branches=['root']))
    if 'tv-channels' in route:
        tv = TVChannel(name='Assigned', is_active=True)
        db_session.add(tv)
        db_session.flush()
        for entry in saved.entries:
            if entry.channel_id:
                db_session.get(AcestreamChannel, entry.channel_id).tv_channel_id = tv.id
        db_session.commit()
    response = client.get(route, params={'base_url': 'acestream://', 'only_online': 'false', 'include_unassigned': 'true'})
    assert response.status_code == 200
    assert A in response.text
    assert 'PRIVATE' not in response.text and 'SECRET' not in response.text
    assert 'cdn.test' not in response.text and 'page.test' not in response.text


def test_metadata_labels_redact_credentials():
    result = run({'name': 'List token=SECRET', 'stations': [station(info='password=PRIVATE')]})
    assert 'SECRET' not in result['entries'][0]['name']
    assert 'PRIVATE' not in result['entries'][1]['description']


def test_fetch_budget_keeps_already_downloaded_sibling_sections(monkeypatch):
    docs = {
        'https://example.test/root': {'groups': [{'name': 'Archive', 'url': '/archive'}, {'name': 'Live', 'url': '/live'}]},
        'https://example.test/archive': {'groups': [{'name': 'More', 'url': '/more'}]},
        'https://example.test/live': {'stations': [station(url='https://cdn.test/live.m3u8')]},
    }
    async def get(url, **kwargs):
        return SourceResponse(200, json.dumps(docs[url]).encode(), {})
    monkeypatch.setattr('app.services.w3u_parser.source_get', get)
    result = asyncio.run(W3UTraversal(limits=Limits(requests=3)).run(url='https://example.test/root'))
    assert result['partial']
    assert result['counts']['requests'] == 3
    assert result['counts']['accepted'] == 1
    assert any(e['kind'] == 'hls' for e in result['entries'])


def test_unsupported_folder_headers_do_not_silently_import_unusable_children():
    result = run({'headers': {'Authorization': 'secret'}, 'stations': [station()]})
    assert result['partial']
    assert result['counts']['accepted'] == 0
    assert result['warnings']
