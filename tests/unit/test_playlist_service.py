import pytest
from app.services.playlist_service import PlaylistService
from app.repositories import ChannelRepository

def test_generate_playlist_with_search(db_session):
    """Test generating playlist with search filter."""
    service = PlaylistService()
    # Configure test base URL
    service.config._config = {"base_url": "acestream://"}
    
    # Add test channels
    repo = ChannelRepository()
    repo.update_or_create("123", "Sports Channel", "test", 
                        {"group": "Sports", "logo": "sports.png"})
    repo.update_or_create("456", "News Channel", "test", 
                        {"group": "News", "logo": "news.png"})
    repo.update_or_create("789", "Another Sports", "test", 
                        {"group": "Sports"})
    repo.commit()
    
    # Test with filter
    sports_playlist = service.generate_playlist("sports")
    
    # Check that only sports channels are included
    assert "Sports Channel" in sports_playlist
    assert "Another Sports" in sports_playlist
    assert "News Channel" not in sports_playlist
    
    # Check proper formatting
    assert "#EXTM3U" in sports_playlist
    assert "group-title=\"Sports\"" in sports_playlist
    assert "tvg-logo=\"sports.png\"" in sports_playlist
    assert "acestream://123" in sports_playlist

def test_generate_playlist_all_channels(db_session):
    """Test generating playlist with all channels."""
    service = PlaylistService()
    # Use custom base URL format
    service.config._config = {"base_url": "http://localhost:6878/ace/getstream?id="}
    
    # Add test channels
    repo = ChannelRepository()
    repo.update_or_create("123", "Channel 1", "test")
    repo.update_or_create("456", "Channel 2", "test")
    repo.commit()
    
    # Test without filter
    all_playlist = service.generate_playlist()
    
    # Check that all channels are included
    assert "Channel 1" in all_playlist
    assert "Channel 2" in all_playlist
    
    # Check base URL formatting is correct
    assert "http://localhost:6878/ace/getstream?id=123" in all_playlist
    assert "http://localhost:6878/ace/getstream?id=456" in all_playlist