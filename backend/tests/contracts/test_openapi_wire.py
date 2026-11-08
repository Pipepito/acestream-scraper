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


@pytest.mark.parametrize('url', ['/api/v1/tv-channels/', '/api/v1/tv-channels/now-next', '/api/v1/acestream-channels/'])
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
