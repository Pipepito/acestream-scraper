import pytest
from app.middleware import recipe_limits
from test_extraction_recipes import CATALOGUE


def test_rejects_large_declared_body_before_parser(client, monkeypatch):
    monkeypatch.setattr(recipe_limits, 'MAX_PREVIEW_BODY_BYTES', 100)
    response = client.post('/api/v1/scrapers/recipes/preview', content=b'invalid json', headers={'content-length': '101'})
    assert response.status_code == 413


def test_streamed_body_cannot_bypass_limit_and_slot_is_released(client, monkeypatch):
    monkeypatch.setattr(recipe_limits, 'MAX_PREVIEW_BODY_BYTES', 100)
    response = client.post('/api/v1/scrapers/recipes/preview', content=iter([b'a' * 60, b'b' * 60]))
    assert response.status_code == 413
    monkeypatch.setattr(recipe_limits, 'MAX_PREVIEW_BODY_BYTES', 10000)
    response = client.post('/api/v1/scrapers/recipes/preview', json={'recipe': CATALOGUE[1]['recipe'], 'sample': CATALOGUE[1]['sample']})
    assert response.status_code == 200


def test_admission_auth_and_compression(client, monkeypatch):
    monkeypatch.setenv('API_TOKEN', 'configured')
    url = '/api/v1/scrapers/recipes/preview'
    assert client.post(url, content=b'invalid').status_code == 401
    headers = {'X-Api-Token': 'configured'}
    assert client.post(url, content=b'invalid', headers={**headers, 'content-encoding': 'gzip'}).status_code == 415
    assert recipe_limits._PREVIEWS.acquire(False)
    assert recipe_limits._PREVIEWS.acquire(False)
    try:
        assert client.post(url, content=b'invalid', headers=headers).status_code == 503
    finally:
        recipe_limits._PREVIEWS.release()
        recipe_limits._PREVIEWS.release()
