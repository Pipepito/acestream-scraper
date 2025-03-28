import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from app.models.url_types import RegularURL, ZeronetURL
from app.scrapers import create_scraper_for_url, HTTPScraper, ZeronetScraper

def test_create_scraper_for_url_with_explicit_types():
    """Test creating scrapers with explicit URL types."""
    
    # Avoid actual scraper instantiation which would involve URLs
    with patch('app.scrapers.HTTPScraper') as mock_http, \
         patch('app.scrapers.ZeronetScraper') as mock_zeronet:
        
        # Configure mocks to return themselves
        mock_http.return_value = "http_scraper_instance"
        mock_zeronet.return_value = "zeronet_scraper_instance"
        
        # Test with regular URL type
        scraper1 = create_scraper_for_url("http://example.com", "regular")
        assert scraper1 == "http_scraper_instance"
        mock_http.assert_called_once()
        
        # Reset mocks
        mock_http.reset_mock()
        mock_zeronet.reset_mock()
        
        # Test with zeronet URL type
        scraper2 = create_scraper_for_url("http://example.org", "zeronet")
        assert scraper2 == "zeronet_scraper_instance"
        mock_zeronet.assert_called_once()
        
        # Reset mocks
        mock_http.reset_mock()
        mock_zeronet.reset_mock()
        
        # Test with auto - should raise an error now
        with pytest.raises(ValueError):
            create_scraper_for_url("http://example.net", "auto")

def test_scraper_url_object_handling():
    """Test that scrapers correctly receive the URL object."""
    url = "http://example.com"
    
    # Create a proper mock URL object
    url_obj_mock = MagicMock(spec=RegularURL)  # Add spec to pass isinstance check
    url_obj_mock.get_normalized_url.return_value = url
    url_obj_mock.original_url = url
    
    # Configure type_name property correctly
    type(url_obj_mock).type_name = PropertyMock(return_value="regular")
    
    # We need to patch both the create_url_object and scraper initialization
    with patch('app.scrapers.create_url_object', return_value=url_obj_mock), \
         patch('app.scrapers.HTTPScraper') as mock_http:
        
        # Configure the scraper mock
        scraper_mock = MagicMock()
        mock_http.return_value = scraper_mock
        
        # Create the scraper
        create_scraper_for_url(url, "regular")
        
        # Verify scraper was instantiated with the URL object
        mock_http.assert_called_once()
        args, kwargs = mock_http.call_args
        assert args[0] == url_obj_mock  # First argument should be the URL object
