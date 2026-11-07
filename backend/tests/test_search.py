"""
Integration tests for Search endpoints
"""

import pytest
import uuid
from fastapi import status


class TestSearchEndpoints:
    """Test search operations."""

    def test_search_channels_empty_query(self, client, mock_search_service):
        """Test searching with empty query."""
        response = client.get("/api/v1/search")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "success" in data
        assert data["success"] == True
        assert data["pagination"]["total_results"] == 2  # Based on mock data
        assert len(data["results"]) == 2

    def test_search_channels_with_query(self, client, mock_search_service):
        """Test searching with a query."""
        response = client.get("/api/v1/search?q=test")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "success" in data
        assert data["pagination"]["total_results"] >= 0
        assert isinstance(data["results"], list)

    def test_search_channels_with_pagination(self, client, mock_search_service):
        """Test searching with pagination parameters."""
        response = client.get("/api/v1/search?q=test&page=2&page_size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["page_size"] == 10

    def test_search_channels_with_category(self, client, mock_search_service):
        """Test searching with category filter."""
        response = client.get("/api/v1/search?q=test&category=entertainment")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "results" in data
        assert "pagination" in data
        assert "total_results" in data["pagination"]

    def test_search_channels_with_invalid_page(self, client, mock_search_service):
        """Test searching with invalid page parameter."""
        response = client.get("/api/v1/search?q=test&page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_search_channels_with_invalid_per_page(self, client, mock_search_service):
        """Test searching with invalid per_page parameter."""
        response = client.get("/api/v1/search?q=test&per_page=0")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_search_channels_with_large_per_page(self, client, mock_search_service):
        """Test searching with large per_page parameter."""
        response = client.get("/api/v1/search?q=test&per_page=1000")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should be capped at maximum allowed
        assert data["pagination"]["page_size"] <= 100


@pytest.mark.parametrize('route', ['/add', '/add_multiple', '/import'])
def test_search_import_routes_resolve_and_preserve_existing(client, db_session, monkeypatch, route):
    from app.models.models import AcestreamChannel
    from app.repositories.settings_repository import SettingsRepository
    from app.services.search_catalogue_client import SearchCatalogueClient
    SettingsRepository(db_session).set_setting('ace_engine_url', 'http://engine')
    ih, cid = 'a' * 40, 'b' * 40
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', lambda self, value: cid)
    item = {'id': ih, 'name': 'Publisher', 'url': 'acestream://' + ih}
    payload = {'items': [{'infohash': ih, 'name': 'Publisher'}]} if route == '/import' else {'channels': [item]} if route == '/add_multiple' else item
    first = client.post('/api/v1/search' + route, json=payload)
    assert first.status_code == 200
    assert first.json()['items'][0]['content_id'] == cid
    row = db_session.get(AcestreamChannel, cid)
    row.name, row.is_active, row.is_online = 'Operator', False, True
    db_session.commit()
    second = client.post('/api/v1/search' + route, json=payload)
    assert second.json()['items'][0]['outcome'] == 'existing'
    db_session.refresh(row)
    assert (row.name, row.is_active, row.is_online) == ('Operator', False, True)
    assert db_session.get(AcestreamChannel, ih) is None


@pytest.mark.parametrize('route,payload', [
    ('/add', {'name': 'Missing ID', 'url': 'acestream://invalid'}),
    ('/add', {'id': 'uuid-not-an-infohash', 'name': 'Invalid ID', 'url': 'acestream://invalid'}),
    ('/add_multiple', {'channels': []}),
    ('/import', {'items': []}),
])
def test_search_import_rejects_missing_or_invalid_infohash(client, route, payload):
    assert client.post('/api/v1/search' + route, json=payload).status_code == 422


@pytest.mark.parametrize('route', ['/add', '/add_multiple'])
def test_legacy_imports_enforce_policy(client, db_session, monkeypatch, route):
    from app.repositories.settings_repository import SettingsRepository
    from app.services.search_catalogue_client import SearchCatalogueClient
    SettingsRepository(db_session).set_setting('ace_engine_url', 'http://engine')
    monkeypatch.setattr(SearchCatalogueClient, 'resolve', lambda *args: 'b' * 40)
    client.post('/api/v1/import-exclusions', json={'kind': 'stream_id_equals', 'value': 'b' * 40})
    item = {'id': 'a' * 40, 'name': 'Blocked', 'url': 'acestream://' + 'a' * 40}
    result = client.post('/api/v1/search' + route, json=item if route == '/add' else {'channels': [item]})
    assert result.status_code == 200
    assert result.json()['excluded'] == 1


def test_empty_search_uses_paginated_catalogue_request(monkeypatch):
    import asyncio
    from types import SimpleNamespace
    from app.services.search_service import SearchService
    from app.services.search_catalogue_client import SearchCatalogueClient
    requests = []
    def get(self, path, params):
        requests.append((path, params))
        return {'result': {'results': [{'infohash': 'a' * 40, 'name': 'All channel'}], 'total': 201}}
    monkeypatch.setattr(SearchCatalogueClient, 'get', get)
    config = SimpleNamespace(get_ace_engine_url=lambda: 'http://engine.example')
    result = asyncio.run(SearchService(config).search('  ', 3, 25, 'sports'))
    assert requests == [('/search', {'query': '', 'category': 'sports', 'page': 2, 'page_size': 25})]
    assert result['pagination'] == dict(page=3, page_size=25, total_results=201, total_pages=9)
