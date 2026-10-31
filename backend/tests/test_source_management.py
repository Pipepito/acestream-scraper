"""Named source definitions and catalogue-aware filtering without live fetches."""
import json

from sqlalchemy import create_engine, inspect, text

from migration_test_utils import database_url_for, upgrade_to_revision, downgrade_to_revision


def test_source_names_upgrade_preserves_old_rows(tmp_path):
    path = tmp_path / 'sources.sqlite'
    upgrade_to_revision(path, '20261028_1200')
    engine = create_engine(database_url_for(path))
    try:
        with engine.begin() as db:
            db.execute(text("INSERT INTO scraped_urls (url,url_type,enabled) VALUES ('https://example.test/list','auto',1)"))
        upgrade_to_revision(path, '20261030_1200')
        with engine.begin() as db:
            assert tuple(db.execute(text('SELECT url,url_type,enabled,name FROM scraped_urls')).one()) == ('https://example.test/list', 'auto', 1, None)
            db.execute(text("UPDATE scraped_urls SET name='My source'"))
        downgrade_to_revision(path, '20261028_1200')
        assert 'name' not in {c['name'] for c in inspect(engine).get_columns('scraped_urls')}
        upgrade_to_revision(path, '20261030_1200')
        with engine.connect() as db:
            assert db.execute(text('SELECT COUNT(*) FROM scraped_urls')).scalar() == 1
    finally:
        engine.dispose()


def test_provider_definitions_and_optional_name_lifecycle(client, db_session):
    from app.models.models import AcestreamChannel
    providers = client.get('/api/v1/scrapers/providers').json()
    assert {p['id'] for p in providers} == {'atresplayer', 'mediaset', '7riojaplay', 'telemadrid'}
    source = providers[0]
    response = client.post('/api/v1/scrapers/urls', json={'url': source['url'], 'name': '  Living room  '})
    assert response.status_code == 201
    row = response.json()
    assert row['name'] == 'Living room'
    assert row['url_type'] == 'broadcaster'
    assert db_session.query(AcestreamChannel).count() == 0
    assert client.patch(f"/api/v1/scrapers/urls/{row['id']}", json={'enabled': False}).json()['name'] == 'Living room'
    assert client.post('/api/v1/scrapers/urls', json={'url': source['url']}).json()['name'] == 'Living room'
    assert client.patch(f"/api/v1/scrapers/urls/{row['id']}", json={'name': ' '}).json()['name'] is None
    assert client.post('/api/v1/scrapers/urls', json={'url': 'https://example.test', 'url_type': 'broadcaster'}).status_code == 422
    assert client.patch(f"/api/v1/scrapers/urls/{row['id']}", json={'name': 'x' * 256}).status_code == 422


def test_source_filter_before_pagination_includes_shared_catalogue_entries(client, db_session):
    from app.models.models import AcestreamChannel, ScrapedURL
    from app.services.catalogue_service import CatalogueService
    from app.schemas.catalogue import CataloguePreviewRequest, CatalogueSaveRequest
    a, b, c = 'a' * 40, 'b' * 40, 'c' * 40
    source = 'https://example.test/feed?part=one%two'
    db_session.add(ScrapedURL(url=source, name='My list'))
    db_session.add_all([AcestreamChannel(id=a, name='Shared', source_url=source, group='News'),
                        AcestreamChannel(id=c, name='Unrelated', source_url=source + 'other')])
    db_session.commit()
    svc = CatalogueService(db_session)
    preview = svc.preview(CataloguePreviewRequest(sample=json.dumps({'stations': [
        {'name': 'Shared', 'url': 'acestream://' + a}, {'name': 'New', 'url': 'acestream://' + b}]})))
    saved = svc.save(CatalogueSaveRequest(preview_token=preview.preview_token, name='Uploaded list', selected_branches=['root'], mode='acestream', confirm_live=True))
    key = f'catalogue:{saved.id}'
    options = client.get('/api/v1/acestream-channels/sources').json()
    assert {'value': source, 'label': 'My list', 'kind': 'scrape'} in options
    assert {'value': key, 'label': 'Uploaded list', 'kind': 'catalogue'} in options
    for route in ('channels', 'acestream-channels'):
        page = client.get(f'/api/v1/{route}/', params={'source_url': key, 'page': 1, 'page_size': 1}).json()
        assert page['total'] == 2
        assert len(page['items']) == 1
        filtered = client.get(f'/api/v1/{route}/', params={'source_url': key, 'group': 'News'}).json()
        assert [x['id'] for x in filtered['items']] == [a]
        exact = client.get(f'/api/v1/{route}/', params={'source_url': source}).json()
        assert [x['id'] for x in exact['items']] == [a]
    db_session.refresh(db_session.get(AcestreamChannel, a))
    assert db_session.get(AcestreamChannel, a).source_url == source
