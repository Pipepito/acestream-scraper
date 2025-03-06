import pytest
import json
import re
from datetime import datetime
from app.models import AcestreamChannel, ScrapedURL
from app.utils.config import Config

def test_dashboard_timezone_handling(client, db_session):
    """Test that dates in the API are properly formatted for client-side timezone handling."""
    # Create test data
    test_date = datetime.utcnow()
    channel = AcestreamChannel(
        id="test123",
        name="Test Channel",
        last_processed=test_date,
        last_checked=test_date,
        is_online=True
    )
    db_session.add(channel)
    db_session.commit()
    
    # Get channel API response
    response = client.get('/api/channels')
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
    """Test rescrape interval is properly returned in the stats API."""
    # Set test rescrape interval in config
    test_interval = 12  # hours
    Config._instance._config = {"rescrape_interval": test_interval}
    
    # Get stats API response
    response = client.get('/api/stats')
    assert response.status_code == 200
    
    # Check rescrape interval is included
    data = response.json
    assert 'rescrape_interval' in data
    assert data['rescrape_interval'] == test_interval

def test_update_rescrape_interval(client, db_session, config):
    """Test updating the rescrape interval."""
    # Update interval through API
    new_interval = 24  # hours
    response = client.put('/api/config/rescrape_interval', 
                          json={"hours": new_interval})
    assert response.status_code == 200
    
    # Verify update in response
    data = response.json
    assert data['rescrape_interval_hours'] == new_interval
    
    # Verify config was updated
    assert Config._instance._config['rescrape_interval'] == new_interval
    
    # Check stats API also returns updated value
    stats_response = client.get('/api/stats')
    stats_data = stats_response.json
    assert stats_data['rescrape_interval'] == new_interval