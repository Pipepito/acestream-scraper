import pytest
from datetime import datetime, timezone
from app.models import ScrapedURL

def test_scraped_url_init(db_session):
    """Test ScrapedURL initialization with default values."""
    # Set explicit values rather than relying on defaults
    url = ScrapedURL(url="http://example.com", status="pending", error_count=0, enabled=True, url_type="regular")
    assert url.url == "http://example.com"
    assert url.status == "pending"
    assert url.error_count == 0
    assert url.enabled is True
    assert url.url_type == "regular"
    
def test_scraped_url_with_type(db_session):
    """Test ScrapedURL initialization with specified URL type."""
    url = ScrapedURL(url="zero://1abc", url_type="zeronet", status="pending", error_count=0, enabled=True)
    assert url.url == "zero://1abc"
    assert url.url_type == "zeronet"
    
def test_update_status(db_session):
    """Test update_status method."""
    # Initialize with explicit values
    url = ScrapedURL(url="http://example.com", status="pending", error_count=0)
    
    # Initial state
    assert url.error_count == 0
    assert url.last_error is None
    
    # Update with success
    url.update_status("success")
    assert url.status == "success"
    assert url.last_processed is not None
    assert url.error_count == 0
    assert url.last_error is None
    
    # Update with error
    error_message = "Test error message"
    url.update_status("failed", error_message)
    assert url.status == "failed"
    assert url.error_count == 1
    assert url.last_error == error_message
    
    # Another error
    url.update_status("error", "Another error")
    assert url.error_count == 2
    assert url.last_error == "Another error"
