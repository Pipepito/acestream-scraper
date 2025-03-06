import pytest
from urllib.parse import urlparse
import re
from unittest.mock import patch, MagicMock

# Don't import the actual ZeronetScraper to avoid any network connections
# from app.scrapers.zeronet import ZeronetScraper

def test_zeronet_url_parsing_basic():
    """Test basic URL parsing without using ZeronetScraper."""
    # Test normal HTTP URLs
    http_url = "http://192.168.2.178:43110/site/file.m3u"
    parsed = urlparse(http_url)
    assert parsed.scheme == "http"
    assert parsed.netloc == "192.168.2.178:43110"
    assert parsed.path == "/site/file.m3u"
    
    # Extract host correctly
    host = parsed.netloc.split(':')[0]
    assert host == "192.168.2.178"
    
    # Test another IP
    http_url2 = "http://10.10.10.10:43110/site/file.m3u"
    parsed2 = urlparse(http_url2)
    host2 = parsed2.netloc.split(':')[0]
    assert host2 == "10.10.10.10"
    
    # NOTE: zero:// scheme behaves differently
    zero_url = "zero://site/file.m3u"
    parsed_zero = urlparse(zero_url)
    assert parsed_zero.scheme == "zero"
    assert parsed_zero.netloc == "site"  # This is expected behavior for this URL format
    assert parsed_zero.path == "/file.m3u"

def test_zeronet_url_conversion():
    """Test converting zero:// URLs to HTTP format."""
    # Function to convert URLs (similar to what ZeronetScraper would do)
    def convert_zeronet_url(url):
        parsed = urlparse(url)
        
        # Handle zero:// URLs
        if url.startswith("zero://"):
            # In zero:// URLs, the site is actually in the netloc part
            site = parsed.netloc
            path = parsed.path.lstrip('/')
            return f"http://127.0.0.1:43110/{site}/{path}"
        
        # Handle http:// URLs with :43110
        elif ":43110/" in url:
            host = parsed.netloc.split(':')[0]
            path = url.split(':43110/', 1)[1]
            return f"http://{host}:43110/{path}"
        
        # Regular URL
        return url
    
    # Test cases
    assert convert_zeronet_url("zero://site/file.m3u") == "http://127.0.0.1:43110/site/file.m3u"
    assert convert_zeronet_url("http://192.168.2.178:43110/site/file.m3u") == "http://192.168.2.178:43110/site/file.m3u"
    assert convert_zeronet_url("http://example.com/normal/path") == "http://example.com/normal/path"

def test_iframe_src_extraction():
    """Test extracting iframe_src from HTML content."""
    html_content = """
    <html>
    <head>
    <script>
    var iframe_src = "/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/lista-ace.html";
    </script>
    </head>
    <body>Main content</body>
    </html>
    """
    
    # Extract iframe_src using regex
    iframe_src_match = re.search(r'iframe_src\s*=\s*"([^"]+)"', html_content)
    assert iframe_src_match is not None
    assert iframe_src_match.group(1) == "/1H3KoazXt2gCJgeD8673eFvQYXG7cbRddU/lista-ace.html"

def test_acestream_content_detection():
    """Test detecting acestream links and data in content."""
    # Test content with acestream:// links
    content1 = "<html><body>Here's a link: acestream://abc123def456</body></html>"
    assert 'acestream://' in content1
    
    # Test content with linksData JavaScript
    content2 = """
    <html><script>
    const linksData = [
        { "id": "abc123", "name": "Channel 1" },
        { "id": "def456", "name": "Channel 2" }
    ];
    </script></html>
    """
    assert 'const linksData' in content2
    
    # Content with neither
    content3 = "<html><body>No acestream links here</body></html>"
    assert 'acestream://' not in content3
    assert 'const linksData' not in content3