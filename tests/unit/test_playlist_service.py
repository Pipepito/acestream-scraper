import os
import pytest
from unittest.mock import patch
from app.utils.config import Config
from app.services.playlist_service import PlaylistService
from app.models import AcestreamChannel
from app.repositories import ChannelRepository

@pytest.fixture
def config_with_base_url(monkeypatch):
    """Configure a base URL for testing."""
    config = Config()
    
    # Mock the base_url property to return a consistent value for tests
    monkeypatch.setattr(config, 'base_url', 'http://localhost:6878/ace/getstream?id=')
    
    return config

@pytest.fixture
def setup_test_channels(db_session):
    """Set up test channels for playlist tests."""
    # Create test channels with correct attribute name (id instead of channel_id)
    ch1 = AcestreamChannel(id='123', name='Sports Channel', group='Sports', logo='sports.png', is_online=True)
    ch2 = AcestreamChannel(id='456', name='News Channel', group='News', logo='news.png', is_online=True)
    db_session.add(ch1)
    db_session.add(ch2)
    db_session.commit()
    return [ch1, ch2]

@pytest.fixture(autouse=True)
def patch_playlist_service_config(monkeypatch, config_with_base_url):
    """Ensure PlaylistService uses our test config."""
    monkeypatch.setattr('app.services.playlist_service.Config', lambda: config_with_base_url)
    return config_with_base_url

def test_generate_playlist_with_search(db_session, setup_test_channels):
    """Test playlist generation with search filter."""
    # Create the service
    service = PlaylistService()
    
    # Generate playlist with search term
    playlist = service.generate_playlist(search_term='Sports')
    
    # Debug output
    print(f"Generated playlist: {playlist}")
    print(f"Expected URL fragment: http://localhost:6878/ace/getstream?id=123")
    
    # Verify correct URLs are in the playlist
    assert '123' in playlist
    assert '456' not in playlist

def test_generate_playlist_all_channels(db_session, setup_test_channels):
    """Test playlist generation with all channels."""
    service = PlaylistService()
    
    # Generate playlist with all channels
    playlist = service.generate_playlist()
    
    # Debug output
    print(f"Generated playlist: {playlist}")
    
    # Verify correct URLs are in the playlist
    assert '123' in playlist
    assert '456' in playlist

# Removed tests that depended on Acexy detection logic:
# - test_format_stream_url_with_acexy
# - test_format_stream_url_without_acexy
# - test_format_stream_url_acexy_environment_overrides_port
# - test_format_stream_url_acexy_overrides_addpid

def test_format_stream_url_with_addpid(db_session, monkeypatch):
    """Test URL formatting when addpid is True."""
    # Create service
    service = PlaylistService()
    
    # Mock the config to set addpid to True
    monkeypatch.setattr(service.config, 'base_url', 'http://localhost:6878/ace/getstream?id=')
    monkeypatch.setattr(service.config, 'addpid', True)
    
    # Format URL
    url = service._format_stream_url('abc123', 42)
    
    # Verify that pid parameter is added
    assert url == 'http://localhost:6878/ace/getstream?id=abc123&pid=42'
    assert '&pid=42' in url

def test_format_stream_url_without_addpid(db_session, monkeypatch):
    """Test URL formatting when addpid is False."""
    # Create service
    service = PlaylistService()
    
    # Mock the config to set addpid to False
    monkeypatch.setattr(service.config, 'base_url', 'http://localhost:6878/ace/getstream?id=')
    monkeypatch.setattr(service.config, 'addpid', False)
    
    # Format URL
    url = service._format_stream_url('abc123', 42)
    
    # Verify that pid parameter is not added
    assert url == 'http://localhost:6878/ace/getstream?id=abc123'
    assert '&pid=' not in url

def test_format_stream_url_with_different_base_urls(db_session, monkeypatch):
    """Test URL formatting with different base URL types."""
    # Create service
    service = PlaylistService()
    
    # Test with acestream:// protocol
    monkeypatch.setattr(service.config, 'base_url', 'acestream://')
    monkeypatch.setattr(service.config, 'addpid', True)
    url = service._format_stream_url('abc123', 42)
    assert url == 'acestream://abc123&pid=42'
    
    # Test with HTTP URL
    monkeypatch.setattr(service.config, 'base_url', 'http://example.com/ace/getstream?id=')
    url = service._format_stream_url('abc123', 42)
    assert url == 'http://example.com/ace/getstream?id=abc123&pid=42'
    
    # Test with HTTPS URL and addpid=False
    monkeypatch.setattr(service.config, 'base_url', 'https://example.com/ace/getstream?id=')
    monkeypatch.setattr(service.config, 'addpid', False)
    url = service._format_stream_url('abc123', 42)
    assert url == 'https://example.com/ace/getstream?id=abc123'
    assert '&pid=' not in url

def test_generate_playlist_with_duplicate_names(db_session):
    """Test playlist generation with duplicate channel names."""
    # Create test channels with duplicate names
    ch1 = AcestreamChannel(id='123', name='Sports Channel', group='Sports', status='active')
    ch2 = AcestreamChannel(id='456', name='Sports Channel', group='Sports', status='active')
    ch3 = AcestreamChannel(id='789', name='Sports Channel', group='Sports', status='active')
    ch4 = AcestreamChannel(id='abc', name='News Channel', group='News', status='active')
    ch5 = AcestreamChannel(id='def', name='News Channel', group='News', status='active')
    
    db_session.add_all([ch1, ch2, ch3, ch4, ch5])
    db_session.commit()
    
    # Create the service
    service = PlaylistService()
    
    # Generate playlist
    playlist = service.generate_playlist()
    
    # Debug output
    print(f"Generated playlist: {playlist}")
    
    # Verify original names are present
    assert ',Sports Channel' in playlist
    assert ',News Channel' in playlist
    
    # Verify numbered duplicates are present
    assert ',Sports Channel 2' in playlist
    assert ',Sports Channel 3' in playlist
    assert ',News Channel 2' in playlist
    
    # Make sure the original name doesn't have a number
    assert ',Sports Channel 1' not in playlist
    assert ',News Channel 1' not in playlist