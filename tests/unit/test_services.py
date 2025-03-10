import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from app.services import ScraperService, PlaylistService
from app.models import ScrapedURL, AcestreamChannel

@pytest.mark.asyncio
async def test_scraper_service_scrape_url(db_session):
    service = ScraperService()
    url = "http://test.com"
    
    # Create URL object first
    url_obj = ScrapedURL(url=url)
    db_session.add(url_obj)
    db_session.commit()
    
    # Mock the scraper
    mock_scraper = AsyncMock()
    mock_scraper.scrape.return_value = ([("123", "Test Channel", {})], "OK")
    
    with patch('app.scrapers.create_scraper', return_value=mock_scraper):
        links, status = await service.scrape_url(url)
        
        assert status == "OK"
        assert len(links) == 1
        assert links[0][0] == "123"
        assert links[0][1] == "Test Channel"
        
        # Check that channel was created
        channel = service.channel_repository.get_by_id("123")
        assert channel is not None
        assert channel.name == "Test Channel"

def test_playlist_service_generate(db_session, config):
    """Test playlist generation with base URL configuration."""
    service = PlaylistService()
    
    # Create test channels
    channel_repo = service.channel_repository
    channel_repo.update_or_create("123", "Test Channel 1", "http://test.com")
    channel_repo.update_or_create("456", "Test Channel 2", "http://test.com")
    channel_repo.commit()
    
    # Test with acestream:// format
    config.base_url = "acestream://"
    playlist = service.generate_playlist()
    
    # Verify acestream:// format
    assert "#EXTM3U" in playlist
    assert "Test Channel 1" in playlist
    assert "acestream://123" in playlist
    assert "acestream://456" in playlist
    
    # Test with HTTP format
    config.base_url = "http://localhost:6878/ace/getstream?id="
    playlist = service.generate_playlist()
    
    # Verify HTTP format
    assert "#EXTM3U" in playlist
    assert "Test Channel 1" in playlist
    assert "http://localhost:6878/ace/getstream?id=123" in playlist
    assert "http://localhost:6878/ace/getstream?id=456" in playlist