import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError
from app.schemas.extraction import ExtractionRecipe, MAX_SAMPLE_BYTES
from app.services.extraction_service import preview_recipe
from app.utils.outbound_http import PinnedResolver

CATALOGUE = json.loads((Path(__file__).resolve().parents[2] / 'frontend/src/recipes/catalogue.json').read_text())


@pytest.mark.parametrize('entry', CATALOGUE, ids=lambda entry: entry['id'])
def test_catalogue_runs_in_production_worker(entry):
    result = preview_recipe(ExtractionRecipe.model_validate(entry['recipe']), entry['sample'])
    assert result.record_count == 2
    assert result.invalid_count == 0
    assert [row.name for row in result.channels] == [row['name'] for row in entry['expected']]
    assert [row.channel_id for row in result.channels] == [row['channel_id'] for row in entry['expected']]


def test_missing_fields_do_not_pair_names_from_other_records():
    recipe = ExtractionRecipe.model_validate(CATALOGUE[0]['recipe'])
    sample = '<section class="channel"><h3>Orphan</h3></section><section class="channel"><a href="acestream://' + 'a' * 40 + '">Watch</a></section>'
    result = preview_recipe(recipe, sample)
    assert not result.channels and result.invalid_count == 2


def test_unmatched_optional_capture_is_missing_not_whole_match():
    recipe = ExtractionRecipe.model_validate(CATALOGUE[1]['recipe'])
    recipe.fields['name'].pattern = r'(Missing)?Other'
    sample = json.dumps({'data': {'channels': [{'title': 'Other', 'stream': {'id': 'a' * 40}}]}})
    result = preview_recipe(recipe, sample)
    assert not result.channels and result.invalid_count == 1


@pytest.mark.parametrize('mode', ['html', 'json'])
def test_multi_megabyte_pages_keep_the_same_channel_pairs(mode):
    entry = CATALOGUE[0 if mode == 'html' else 1]
    padding = 'x' * (8 * 1024 * 1024)
    if mode == 'html':
        sample = '<script type="application/json">' + json.dumps({'pageState': padding}) + '</script>' + entry['sample']
    else:
        payload = json.loads(entry['sample'])
        payload['pageState'] = padding
        sample = json.dumps(payload)
    result = preview_recipe(ExtractionRecipe.model_validate(entry['recipe']), sample)
    assert result.invalid_count == 0
    assert [row.channel_id for row in result.channels] == [row['channel_id'] for row in entry['expected']]


def test_json_arrays_duplicates_and_invalid_records():
    recipe = ExtractionRecipe.model_validate(CATALOGUE[1]['recipe'])
    sample = json.dumps({'data': {'channels': [
        {'title': 'One', 'stream': {'id': ['a' * 40, 'b' * 40]}},
        {'title': 'Duplicate', 'stream': {'id': 'a' * 40}},
        {'title': 'Invalid', 'stream': {'id': 'garbage'}},
    ]}})
    result = preview_recipe(recipe, sample)
    assert len(result.channels) == 2 and result.duplicate_count == 1 and result.invalid_count == 1
    assert all(channel.name == 'One' for channel in result.channels)


def test_limits_and_expensive_patterns_are_stopped():
    recipe = ExtractionRecipe.model_validate(CATALOGUE[2]['recipe'])
    with pytest.raises(ValueError, match='32 MiB'):
        preview_recipe(recipe, 'x' * (MAX_SAMPLE_BYTES + 1))
    recipe.records = '(a+)+$'
    with pytest.raises(ValueError, match='time limit|Extraction failed'):
        preview_recipe(recipe, 'a' * 100 + '!')
    # A killed worker must release its slot.
    assert preview_recipe(ExtractionRecipe.model_validate(CATALOGUE[2]['recipe']), CATALOGUE[2]['sample']).channels


@pytest.mark.parametrize('change', [
    {'schema_version': 2}, {'credentials': 'secret'}, {'fields': {}}, {'mode': 'code'},
    {'records': '(?P<name>.*)'},
])
def test_rejects_unknown_or_nonportable_recipe(change):
    value = {**CATALOGUE[2]['recipe'], **change}
    with pytest.raises(ValidationError):
        ExtractionRecipe.model_validate(value)


def test_source_recipe_crud_and_preview_do_not_import_channels(client, db_session):
    from app.models.models import AcestreamChannel, ScrapedURL
    recipe = CATALOGUE[1]['recipe']
    response = client.post('/api/v1/scrapers/urls', json={'url': 'https://example.com/api', 'extraction_recipe': recipe})
    assert response.status_code == 201, response.text
    source_id = response.json()['id']
    assert response.json()['extraction_recipe']['mode'] == 'json'
    preview = client.post('/api/v1/scrapers/recipes/preview', json={'recipe': recipe, 'sample': CATALOGUE[1]['sample']})
    assert preview.status_code == 200 and len(preview.json()['channels']) == 2
    assert db_session.query(AcestreamChannel).count() == 0
    assert db_session.query(ScrapedURL).count() == 1
    assert client.patch(f'/api/v1/scrapers/urls/{source_id}', json={'enabled': False}).json()['extraction_recipe'] is not None
    assert client.patch(f'/api/v1/scrapers/urls/{source_id}', json={'extraction_recipe': None}).json()['extraction_recipe'] is None


@pytest.mark.asyncio
async def test_custom_scrapes_keep_existing_channels_on_success_and_failure(db_session, monkeypatch):
    from app.models.models import AcestreamChannel, ScrapedURL, TVChannel
    from app.services.scraper_service import ScraperService
    source = ScrapedURL(url='https://example.com/channels', extraction_recipe=CATALOGUE[1]['recipe'])
    tv = TVChannel(name='Curated', channel_number=1)
    db_session.add_all([source, tv]); db_session.flush()
    db_session.add(AcestreamChannel(id='c' * 40, name='Existing', source_url=source.url, tv_channel_id=tv.id))
    db_session.commit()
    fetch = AsyncMock(return_value=CATALOGUE[1]['sample'])
    monkeypatch.setattr('app.services.extraction_service.fetch_recipe_sample', fetch)
    result, status = await ScraperService(db_session).scrape_url(source.url)
    assert status == 'OK' and len(result) == 2
    assert db_session.query(AcestreamChannel).count() == 3
    fetch.return_value = '{"data":{"channels":[{"title":"Broken"}]}}'
    result, status = await ScraperService(db_session).scrape_url(source.url)
    assert not result and status.startswith('Error:')
    assert db_session.query(AcestreamChannel).count() == 3
    db_session.refresh(source)
    assert source.status.startswith('Error:')


@pytest.mark.asyncio
async def test_resolver_pins_validated_addresses_and_rejects_rebinding(monkeypatch):
    import ipaddress
    monkeypatch.setenv('ALLOW_PRIVATE_SCRAPE_TARGETS', 'false')
    monkeypatch.setattr('app.utils.url_guard._resolve_addresses', lambda host: [ipaddress.ip_address('8.8.8.8')])
    result = await PinnedResolver().resolve('example.com', 443)
    assert result[0]['host'] == '8.8.8.8' and result[0]['hostname'] == 'example.com'
    monkeypatch.setattr('app.utils.url_guard._resolve_addresses', lambda host: [ipaddress.ip_address('127.0.0.1')])
    with pytest.raises(ValueError):
        await PinnedResolver().resolve('example.com', 443)


def test_migration_preserves_sources_and_default_mode(tmp_path):
    from sqlalchemy import create_engine, text
    from migration_test_utils import upgrade_to_revision, upgrade_to_head, database_url_for
    path = tmp_path / 'recipes.db'
    upgrade_to_revision(path, '20260907_1500')
    engine = create_engine(database_url_for(path))
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO scraped_urls (url, enabled) VALUES ('https://example.com', 1)"))
    upgrade_to_head(path)
    with engine.connect() as conn:
        assert conn.execute(text('SELECT url, enabled, extraction_recipe FROM scraped_urls')).one() == ('https://example.com', 1, None)
    engine.dispose()


def test_recipe_endpoints_require_optional_api_token(client, monkeypatch):
    monkeypatch.setenv('API_TOKEN', 'recipe-test-token')
    response = client.post('/api/v1/scrapers/recipes/preview', json={'recipe': CATALOGUE[1]['recipe'], 'sample': CATALOGUE[1]['sample']})
    assert response.status_code == 401
    assert client.post('/api/v1/scrapers/recipes/sample', json={'url': 'https://example.com'}).status_code == 401


@pytest.mark.asyncio
async def test_fetch_caps_content_and_checks_each_redirect(monkeypatch):
    from app.services import extraction_service as service
    class Body:
        length = 8 * 1024 * 1024
        async def iter_chunked(self, size):
            for offset in range(0, self.length, size):
                yield b'x' * min(size, self.length - offset)
    class Response:
        status = 200
        headers = {}
        charset = 'utf-8'
        content = Body()
        def raise_for_status(self):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass
    class Session:
        def __init__(self, **kwargs):
            self.connector = kwargs['connector']
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            await self.connector.close()
        def get(self, *args, **kwargs):
            assert kwargs['allow_redirects'] is False
            return Response()
    monkeypatch.setattr(service.aiohttp, 'ClientSession', Session)
    guard = []
    monkeypatch.setattr(service, 'validate_outbound_url', lambda url: guard.append(url))
    assert len(await service.fetch_recipe_sample('https://example.com')) == Body.length
    guard.clear()
    Body.length = MAX_SAMPLE_BYTES + 1
    with pytest.raises(ValueError, match='32 MiB'):
        await service.fetch_recipe_sample('https://example.com')
    assert guard == ['https://example.com']
    Response.status = 302
    Response.headers = {'Location': 'http://169.254.169.254/latest'}
    def reject_metadata(url):
        guard.append(url)
        if '169.254.169.254' in url:
            raise service.BlockedURLError('blocked')
    monkeypatch.setattr(service, 'validate_outbound_url', reject_metadata)
    with pytest.raises(ValueError, match='Could not fetch'):
        await service.fetch_recipe_sample('https://example.com')
    assert guard[-1] == 'http://169.254.169.254/latest'
