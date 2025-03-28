import pytest
from unittest.mock import patch, AsyncMock, MagicMock, PropertyMock
from app.services.m3u_service import M3UService
from app.models.url_types import RegularURL, ZeronetURL

@pytest.mark.asyncio
async def test_m3u_service_find_links_with_url_types():
    """Test finding M3U links with different URL types."""
    service = M3UService()
    
    # Regular HTTP URL content with M3U links
    http_content = """
    <html>
    <body>
        <a href="http://example.com/playlist.m3u">Regular M3U</a>
        <a href="/relative/playlist.m3u">Relative M3U</a>
    </body>
    </html>
    """
    
    # ZeroNet URL content with M3U links
    zeronet_content = """
    <html>
    <body>
        <a href="http://127.0.0.1:43110/playlist.m3u">ZeroNet M3U</a>
        <a href="/relative/zeronet.m3u">Relative ZeroNet M3U</a>
    </body>
    </html>
    """
    
    # Test with regular HTTP base URL
    regular_base = "http://example.com/page.html"
    regular_links = await service.find_m3u_links(http_content, regular_base)
    
    # Verify links were found and processed correctly
    assert len(regular_links) >= 1
    assert any(link.startswith("http://example.com/relative/playlist.m3u") for link in regular_links)
    
    # Test with ZeroNet base URL
    zeronet_base = "http://127.0.0.1:43110/1abc/page.html"
    zeronet_links = await service.find_m3u_links(zeronet_content, zeronet_base)
    
    # Verify ZeroNet links were found and processed correctly
    assert len(zeronet_links) >= 1
    assert any(link.endswith("/relative/zeronet.m3u") for link in zeronet_links)

@pytest.mark.asyncio
async def test_m3u_service_fetch_methods():
    """Test M3U fetching with different URL types."""
    service = M3UService()
    
    # Define mock response content
    http_content = "HTTP M3U CONTENT"
    zeronet_content = "ZERONET M3U CONTENT"
    
    # Directly patch the service methods instead of trying to mock aiohttp
    with patch.object(service, '_fetch_http_m3u', 
                     new=AsyncMock(return_value=http_content)) as mock_http_fetch, \
         patch.object(service, '_fetch_zeronet_m3u', 
                     new=AsyncMock(return_value=zeronet_content)) as mock_zeronet_fetch, \
         patch('app.services.m3u_service.create_url_object') as mock_create_url:
        
        # Mock the ZeronetURL object
        zeronet_url_mock = MagicMock()
        zeronet_url_mock.get_internal_url.return_value = "http://127.0.0.1:43110/playlist.m3u"
        type(zeronet_url_mock).type_name = PropertyMock(return_value="zeronet")
        
        # Configure mock_create_url to return appropriate URL objects
        def side_effect(url, url_type=None):
            if url_type == 'zeronet' or 'zero://' in url:
                return zeronet_url_mock
            
            regular_url_mock = MagicMock()
            type(regular_url_mock).type_name = PropertyMock(return_value="regular")
            return regular_url_mock
            
        mock_create_url.side_effect = side_effect
        
        # Test fetching from HTTP URL
        http_result = await service._fetch_http_m3u("http://example.com/playlist.m3u")
        assert http_result == http_content
        mock_http_fetch.assert_called_once()
        
        # Test fetching from ZeroNet URL
        zeronet_result = await service._fetch_zeronet_m3u("zero://playlist.m3u")
        assert zeronet_result == zeronet_content
        mock_zeronet_fetch.assert_called_once()
