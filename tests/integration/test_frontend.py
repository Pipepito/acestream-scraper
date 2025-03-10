import pytest
import json
import re
from datetime import datetime, timezone
from app.models import AcestreamChannel, ScrapedURL
from app.utils.config import Config

def test_dashboard_timezone_handling(client, db_session):
    """Test that dates in the API are properly formatted for client-side timezone handling."""
    # Create test data
    test_date = datetime.now(timezone.utc)
    channel = AcestreamChannel(
        id="test123",
        name="Test Channel",
        last_processed=test_date,
        last_checked=test_date,
        is_online=True
    )
    db_session.add(channel)
    db_session.commit()
    
    # Get channel API response - add trailing slash
    response = client.get('/api/channels/')
    assert response.status_code == 200
    
    # Check that dates are returned as ISO strings
    data = response.json
    assert len(data) == 1
    assert data[0]['id'] == "test123"
    
    # Verify ISO format for dates
    date_fields = ['last_processed', 'last_checked']
    for field in date_fields:
        assert data[0][field] is not None
        # Validate ISO format (simple regex check)
        assert re.match(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', data[0][field])

def test_stats_rescrape_interval(client, db_session, config):
    """Test that rescrape interval shows up in stats."""
    # Configure the endpoint URL correctly (missing trailing slash?)
    response = client.get('/api/stats/')
    assert response.status_code == 200
    data = response.json
    
    # Verify rescrape interval is present
    assert 'rescrape_interval' in data
    assert data['rescrape_interval'] == 24

def test_update_rescrape_interval(client, db_session, mock_task_manager):
    # Test updating the interval without checking GET first
    # since your API likely doesn't have a GET endpoint for this
    response = client.put('/api/config/rescrape_interval', json={'hours': 24})
    assert response.status_code == 200
    assert 'updated successfully' in response.json.get('message', '')
    
    # Get the current value from stats API which does include this info
    response = client.get('/api/stats/')
    assert response.status_code == 200
    assert response.json.get('rescrape_interval') == 24