import pytest
from app.models.url_types import RegularURL, ZeronetURL, create_url_object, BaseURL

def test_base_url_type_name():
    """Test the type_name property of URL objects."""
    
    # Create a concrete implementation for testing
    class TestURL(BaseURL):
        def _validate(self):
            pass
            
        def get_normalized_url(self):
            return self.original_url
            
        @staticmethod
        def is_valid_url(url):
            return True
    
    # Test default implementation of type_name
    test_url = TestURL("http://example.com")
    assert test_url.type_name == "test"
    
    # Test with RegularURL
    regular_url = RegularURL("http://example.com", skip_validation=True)
    assert regular_url.type_name == "regular"
    
    # Test with ZeronetURL
    zeronet_url = ZeronetURL("zero://example", skip_validation=True)
    assert zeronet_url.type_name == "zeronet"

def test_zeronet_url_validation_modes():
    """Test ZeronetURL validation with different modes."""
    # Valid ZeroNet URLs
    assert ZeronetURL.is_valid_url("zero://1abc2def3")
    assert ZeronetURL.is_valid_url("http://127.0.0.1:43110/1abc2def3")
    assert ZeronetURL.is_valid_url("http://example.com:43110/1abc2def3")
    
    # Invalid ZeroNet URLs
    assert not ZeronetURL.is_valid_url("http://example.com")
    assert not ZeronetURL.is_valid_url("https://example.com:8080/path")
    
    # Test validation skip
    # This would normally fail validation
    non_zeronet = ZeronetURL("http://example.com", skip_validation=True)
    assert non_zeronet.original_url == "http://example.com"
    # And it would return the original URL unchanged
    assert non_zeronet.get_normalized_url() == "http://example.com"
    
    # But without skip_validation, it should fail
    with pytest.raises(ValueError):
        ZeronetURL("http://example.com")

def test_create_url_object_with_invalid_inputs():
    """Test create_url_object function with various edge cases."""
    # Valid cases already tested elsewhere
    
    # Test with empty URL
    with pytest.raises(ValueError):
        create_url_object("")
    
    # Test with None URL
    with pytest.raises(TypeError):
        create_url_object(None)
    
    # Test with unsupported URL type
    with pytest.raises(ValueError):
        create_url_object("http://example.com", "invalid_type")
    
    # Test with URL that doesn't match any type but explicit type provided
    url_obj = create_url_object("not-a-url", "regular")
    assert isinstance(url_obj, RegularURL)
    assert url_obj.original_url == "not-a-url"
    
    # Test with URL that doesn't match any type and no explicit type
    with pytest.raises(ValueError):
        create_url_object("not-a-url")
