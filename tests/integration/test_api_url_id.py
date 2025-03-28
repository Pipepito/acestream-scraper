import pytest
import json
import uuid
from unittest.mock import patch, MagicMock
from app.models import ScrapedURL, AcestreamChannel

def test_channels_api_url_id_filter(client, db_session):
    """Test filtering channels by URL ID through the API."""
    # Create test URLs
    url1_id = str(uuid.uuid4())
    url2_id = str(uuid.uuid4())
    
    url1 = ScrapedURL(
        id=url1_id,
        url="http://example.com/test1",
        url_type="regular",
        status="ok"
    )
    url2 = ScrapedURL(
        id=url2_id,
        url="http://example.com/test2",
        url_type="regular",
        status="ok"
    )
    db_session.add_all([url1, url2])
    db_session.commit()
    
    # Create channels for each URL
    channel1 = AcestreamChannel(id="test1_ch1", name="Test Channel 1", source_url=url1.url)
    channel2 = AcestreamChannel(id="test1_ch2", name="Test Channel 2", source_url=url1.url)
    channel3 = AcestreamChannel(id="test2_ch1", name="Test Channel 3", source_url=url2.url)
    
    db_session.add_all([channel1, channel2, channel3])
    db_session.commit()
    
    # Test getting channels with URL ID filter
    response = client.get(f'/api/channels/?url_id={url1_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert len(data) == 2
    
    # Check that we only got channels from URL 1
    channel_ids = [ch['id'] for ch in data]
    assert 'test1_ch1' in channel_ids
    assert 'test1_ch2' in channel_ids
    assert 'test2_ch1' not in channel_ids
    
    # Test with URL 2
    response = client.get(f'/api/channels/?url_id={url2_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert len(data) == 1
    assert data[0]['id'] == 'test2_ch1'

def test_add_url_with_type(client, db_session):
    """Test adding a URL with explicit type through the API."""
    # Test adding regular URL
    response = client.post('/api/urls/', 
                         json={'url': 'http://example.com/api_test', 'url_type': 'regular'})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['url'] == 'http://example.com/api_test'
    assert data['url_type'] == 'regular'
    
    # Verify it was added to the database
    url_obj = ScrapedURL.query.filter_by(url='http://example.com/api_test').first()
    assert url_obj is not None
    assert url_obj.url_type == 'regular'
    
    # Test adding zeronet URL
    response = client.post('/api/urls/', 
                         json={'url': 'zero://zeronet_test', 'url_type': 'zeronet'})
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['url'] == 'zero://zeronet_test'
    assert data['url_type'] == 'zeronet'
    
    # Test adding URL with auto type (should be rejected)
    response = client.post('/api/urls/', 
                         json={'url': 'http://example.com/auto', 'url_type': 'auto'})
    
    assert response.status_code == 400
    
    # Test adding URL without type (should be rejected)
    response = client.post('/api/urls/', 
                         json={'url': 'http://example.com/no_type'})
    
    assert response.status_code == 400

def test_channel_by_url_id_endpoint(client, db_session):
    """Test the endpoint for getting channels by URL ID."""
    # Create a URL
    url_id = str(uuid.uuid4())
    url = ScrapedURL(
        id=url_id,
        url="http://example.com/channels_endpoint",
        url_type="regular",
        status="ok"
    )
    db_session.add(url)
    
    # Create channels for the URL
    channels = [
        AcestreamChannel(id=f"ep_ch{i}", name=f"Endpoint Channel {i}", source_url=url.url)
        for i in range(3)
    ]
    db_session.add_all(channels)
    db_session.commit()
    
    # Test the endpoint
    response = client.get(f'/api/channels/?url_id={url_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert len(data) == 3
    
    channel_names = [ch['name'] for ch in data]
    for i in range(3):
        assert f"Endpoint Channel {i}" in channel_names
