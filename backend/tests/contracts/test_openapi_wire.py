"""Actual provider exchange validation and deliberate contract failure probes."""
import copy
import json
from pathlib import Path

import pytest
from openapi_core import OpenAPI
from scripts.validate_api_contracts import consumer_schema, request_adapter, validate_response


@pytest.fixture(scope='module')
def schema():
    return json.loads((Path(__file__).resolve().parents[2] / 'openapi.json').read_text())


@pytest.fixture(scope='module')
def contract(schema):
    return OpenAPI.from_dict(schema)


@pytest.mark.parametrize('url', ['/api/v1/tv-channels/', '/api/v1/tv-channels/now-next', '/api/v1/tv-channels/now-next?channel_ids=1&channel_ids=2', '/api/v1/tv-channels/browse?limit=50&is_favorite=false&skip=0', '/api/v1/tv-channels/inventory', '/api/v1/acestream-channels/'])
def test_real_provider_success_contract(client, contract, url):
    response = client.get(url)
    assert response.status_code == 200
    request = request_adapter({'method': 'GET', 'url': f'http://testserver{url}'})
    contract.validate_request(request)
    validate_response(contract, request, response.status_code, response.headers, response.content)


@pytest.mark.parametrize('change', ['endpoint', 'method', 'type', 'extra', 'missing'])
def test_invalid_consumer_requests_fail(schema, change):
    exchange = {'method': 'PUT', 'url': 'http://testserver/api/v1/acestream-channels/bulk_edit',
                'headers': {'Content-Type': 'application/json'}}
    body = {'acestreamchannel_ids': ['one'], 'fields': {'group': '', 'is_active': False}}
    if change == 'endpoint':
        exchange['url'] += '-missing'
    elif change == 'method':
        exchange['method'] = 'PATCH'
    elif change == 'type':
        body['fields']['is_active'] = 'not-a-boolean'
    elif change == 'extra':
        body['fields']['country'] = 'ES'
    else:
        del body['acestreamchannel_ids']
    exchange['body'] = json.dumps(body)
    with pytest.raises(Exception):
        OpenAPI.from_dict(consumer_schema(schema)).validate_request(request_adapter(exchange))


@pytest.mark.parametrize('status,content_type,body', [(200, 'application/json', b'{"items":[],"total":"wrong"}'),
    (201, 'application/json', b'{"items":[],"total":0}'), (200, 'text/plain', b'not json')])
def test_response_drift_fails(contract, status, content_type, body):
    request = request_adapter({'method': 'GET', 'url': 'http://testserver/api/v1/tv-channels/'})
    with pytest.raises(Exception):
        validate_response(contract, request, status, {'Content-Type': content_type}, body)


def test_closure_preserves_intentional_maps_and_original_compatibility(schema):
    original = copy.deepcopy(schema)
    closed = consumer_schema(schema)
    assert schema == original
    assert closed['components']['schemas']['SetupUpdate']['properties']['runtime']['additionalProperties'] != False


@pytest.mark.parametrize('url', ['/api/v1/channels/', '/api/v1/acestream-channels/'])
def test_real_token_rejection_contract(client, contract, monkeypatch, url):
    monkeypatch.setenv('API_TOKEN', 'fixture-only-secret')
    response = client.get(url)
    assert response.status_code == 401
    assert response.headers['WWW-Authenticate'] == 'Bearer'
    validate_response(contract, request_adapter({'method': 'GET', 'url': f'http://testserver{url}'}),
                      response.status_code, response.headers, response.content)


def test_real_missing_resource_contract(client, contract):
    url = 'http://testserver/api/v1/tv-channels/999999'
    response = client.get(url)
    assert response.status_code == 404
    validate_response(contract, request_adapter({'method': 'GET', 'url': url}),
                      response.status_code, response.headers, response.content)


def test_real_empty_bulk_edit_contract(client, contract):
    url = 'http://testserver/api/v1/acestream-channels/bulk_edit'
    body = {'acestreamchannel_ids': ['one'], 'fields': {}}
    response = client.put(url, json=body)
    assert response.status_code == 400
    request = request_adapter({'method': 'PUT', 'url': url, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(body)})
    contract.validate_request(request)
    validate_response(contract, request, response.status_code, response.headers, response.content)


@pytest.mark.parametrize('collection', ['all', 'library', 'upcoming', 'history'])
def test_real_recording_collection_contract(client, contract, collection):
    url = f'http://testserver/api/v1/recordings?collection={collection}&offset=0&limit=50'
    response = client.get(url)
    assert response.status_code == 200
    request = request_adapter({'method': 'GET', 'url': url})
    contract.validate_request(request)
    validate_response(contract, request, response.status_code, response.headers, response.content)


def test_redacted_event_validation_matches_declared_contract(client, contract):
    from test_sporting_events import schedule
    payload = schedule()
    payload['observations'][0]['timezone'] = 'invalid-private-input'
    url = 'http://testserver/api/v1/events/preview'
    response = client.post(url, json=payload)
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'EVENT_TIMEZONE_INVALID'
    assert 'invalid-private-input' not in response.text
    request = request_adapter({'method': 'POST', 'url': url, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(payload)})
    validate_response(contract, request, response.status_code, response.headers, response.content)


@pytest.mark.parametrize('path,content_type,prefix', [
    ('/api/v1/playlists/m3u', 'text/plain', b'#EXTM3U'),
    ('/api/v1/epg/xml', 'application/xml', b'<?xml'),
    ('/api/v1/acestream-channels/export_csv', 'text/csv', b'id,'),
])
def test_non_json_download_contract(client, contract, path, content_type, prefix):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers['content-type'].split(';')[0] == content_type
    assert response.content.startswith(prefix)
    if path.endswith('/xml'):
        from xml.etree.ElementTree import fromstring
        assert fromstring(response.content).tag == 'tv'
    if path.endswith('/export_csv'):
        import csv
        from io import StringIO
        rows = list(csv.reader(StringIO(response.text)))
        assert rows[0] == ['id', 'name', 'source_url', 'group', 'logo', 'tvg_id', 'tvg_name', 'is_online', 'is_active', 'last_seen']
    assert 'attachment;' in response.headers['content-disposition']
    request = request_adapter({'method': 'GET', 'url': 'http://testserver' + path})
    validate_response(contract, request, response.status_code, response.headers, response.content)
    with pytest.raises(Exception):
        validate_response(contract, request, 200, {'Content-Type': 'application/json'}, b'{}')


def test_diagnostics_binary_download_contract(client, contract, monkeypatch, tmp_path):
    from io import BytesIO
    from zipfile import ZipFile
    monkeypatch.setenv('CAPTURE_LOG_DIR', str(tmp_path))
    response = client.get('/api/v1/system/diagnostics')
    assert response.status_code == 200
    assert response.headers['content-type'] == 'application/zip'
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['content-disposition'].endswith('"acestream-diagnostics.zip"')
    with ZipFile(BytesIO(response.content)) as archive:
        assert archive.testzip() is None
        assert archive.namelist()
    request = request_adapter({'method': 'GET', 'url': 'http://testserver/api/v1/system/diagnostics'})
    validate_response(contract, request, response.status_code, response.headers, response.content)


def test_telegram_requires_its_separate_administration_header(contract):
    exchange = {'method': 'GET', 'url': 'https://testserver/api/v1/telegram/status'}
    with pytest.raises(Exception):
        contract.validate_request(request_adapter(exchange))
    exchange['headers'] = {'X-Api-Token': 'ordinary-api-token'}
    with pytest.raises(Exception):
        contract.validate_request(request_adapter(exchange))
    exchange['headers']['X-Telegram-Admin'] = 'synthetic-telegram-token'
    contract.validate_request(request_adapter(exchange))
