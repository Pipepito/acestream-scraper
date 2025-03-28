import pytest
from app.models.url_types import RegularURL, ZeronetURL, create_url_object

class TestRegularURL:
    def test_valid_http_url(self):
        url = "http://example.com"
        url_obj = RegularURL(url)
        assert url_obj.original_url == url
        assert url_obj.type_name == "regular"
        assert url_obj.get_normalized_url() == url
        
    def test_valid_https_url(self):
        url = "https://example.com/path?query=value"
        url_obj = RegularURL(url)
        assert url_obj.original_url == url
        assert url_obj.get_normalized_url() == url
        
    def test_invalid_url(self):
        with pytest.raises(ValueError):
            RegularURL("not-a-url")
            
    def test_is_valid_url_static_method(self):
        assert RegularURL.is_valid_url("http://example.com") is True
        assert RegularURL.is_valid_url("https://example.com") is True
        assert RegularURL.is_valid_url("ftp://example.com") is False
        assert RegularURL.is_valid_url("not-a-url") is False

class TestZeronetURL:
    def test_valid_zero_protocol_url(self):
        url = "zero://1abc2def3ghi"
        url_obj = ZeronetURL(url)
        assert url_obj.original_url == url
        assert url_obj.type_name == "zeronet"
        assert url_obj.get_normalized_url() == url
        assert url_obj.get_internal_url() == "http://127.0.0.1:43110/1abc2def3ghi"
        
    def test_valid_http_zeronet_url(self):
        url = "http://127.0.0.1:43110/1abc2def3ghi"
        url_obj = ZeronetURL(url)
        assert url_obj.original_url == url
        assert url_obj.get_normalized_url() == "zero://1abc2def3ghi"
        assert url_obj.get_internal_url() == url
        
    def test_valid_remote_http_zeronet_url(self):
        url = "http://zeronet.example.com:43110/1abc2def3ghi"
        url_obj = ZeronetURL(url)
        assert url_obj.original_url == url
        assert url_obj.get_normalized_url() == "zero://1abc2def3ghi"
        assert url_obj.get_internal_url("zeronet.example.com") == url
        
    def test_invalid_url(self):
        with pytest.raises(ValueError):
            ZeronetURL("http://example.com")
            
    def test_is_valid_url_static_method(self):
        assert ZeronetURL.is_valid_url("zero://1abc2def3ghi") is True
        assert ZeronetURL.is_valid_url("http://127.0.0.1:43110/1abc2def3ghi") is True
        assert ZeronetURL.is_valid_url("http://zeronet.example.com:43110/path") is True
        assert ZeronetURL.is_valid_url("http://example.com") is False

class TestCreateUrlObject:
    def test_auto_detect_regular_url(self):
        url = "http://example.com"
        url_obj = create_url_object(url)
        assert isinstance(url_obj, RegularURL)
        
    def test_auto_detect_zeronet_url(self):
        url = "zero://1abc2def3ghi"
        url_obj = create_url_object(url)
        assert isinstance(url_obj, ZeronetURL)
        
    def test_auto_detect_http_zeronet_url(self):
        url = "http://127.0.0.1:43110/1abc2def3ghi"
        url_obj = create_url_object(url)
        assert isinstance(url_obj, ZeronetURL)
        
    def test_explicit_regular_url(self):
        url = "http://example.com"
        url_obj = create_url_object(url, url_type='regular')
        assert isinstance(url_obj, RegularURL)
        
    def test_explicit_zeronet_url(self):
        # Use a URL that conforms to ZeroNet format instead of a regular HTTP URL
        url = "http://127.0.0.1:43110/1abc"  # A valid ZeroNet URL
        url_obj = create_url_object(url, url_type='zeronet')
        assert isinstance(url_obj, ZeronetURL)
        
    def test_unsupported_url_type(self):
        with pytest.raises(ValueError):
            create_url_object("http://example.com", "unsupported_type")
