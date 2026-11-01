"""Exercise both shared async client fixtures with HTTPX's ASGI transport."""
import pytest


@pytest.mark.asyncio
async def test_async_client_reads_catalogue(async_client):
    response = await async_client.get('/api/v1/acestream-channels/')
    assert response.status_code == 200
    assert response.json() == {'items': [], 'total': 0}


@pytest.mark.asyncio
async def test_migrated_async_client_reads_catalogue(alembic_async_client):
    response = await alembic_async_client.get('/api/v1/acestream-channels/')
    assert response.status_code == 200
    assert response.json() == {'items': [], 'total': 0}
