from abc import ABC, abstractmethod
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class BaseURL(ABC):
    """Base class for all URL types"""
    
    def __init__(self, url, skip_validation=False):
        self.original_url = url
        self.parsed_url = urlparse(url)
        self.skip_validation = skip_validation
        if not skip_validation:
            self._validate()
    
    @abstractmethod
    def _validate(self):
        """Validate the URL format"""
        pass
    
    @abstractmethod
    def get_normalized_url(self):
        """Return a normalized version of this URL"""
        pass
    
    @staticmethod
    @abstractmethod
    def is_valid_url(url):
        """Check if a URL string is valid for this URL type"""
        pass
    
    @property
    def type_name(self):
        """Return the name of this URL type"""
        return self.__class__.__name__.lower().replace('url', '')


class ZeronetURL(BaseURL):
    """URL type for ZeroNet URLs"""
    
    def _validate(self):
        """Validate ZeroNet URL format"""
        if self.skip_validation:
            # Skip validation if explicitly requested (user selected zeronet type)
            return
            
        if not self.is_valid_url(self.original_url):
            raise ValueError(f"Invalid ZeroNet URL: {self.original_url}")
    
    def get_normalized_url(self):
        """Return a normalized ZeroNet URL"""
        # If validation was skipped, return original URL as is
        if self.skip_validation:
            return self.original_url
            
        # If it's already a zero:// URL, return as is
        if self.original_url.startswith('zero://'):
            return self.original_url
            
        # If it's an HTTP URL with 43110 port, convert to zero:// format
        if ':43110/' in self.original_url:
            path = self.original_url.split(':43110/', 1)[1]
            return f"zero://{path}"
            
        return self.original_url
    
    def get_internal_url(self, host='127.0.0.1'):
        """Get internal HTTP URL for ZeroNet service"""
        # If validation was skipped, we don't attempt to transform the URL
        if self.skip_validation:
            return self.original_url
            
        if self.original_url.startswith('zero://'):
            return f"http://{host}:43110/{self.original_url[7:]}"
        elif ':43110/' in self.original_url:
            # For URLs that already contain a host and port 43110, 
            # we should preserve the original host
            parsed = urlparse(self.original_url)
            original_host = parsed.netloc.split(':')[0]
            path = self.original_url.split(':43110/', 1)[1]
            
            # Only use provided host if it's not the default,
            # otherwise keep the original host from the URL
            actual_host = original_host if host == '127.0.0.1' else host
            return f"http://{actual_host}:43110/{path}"
        return self.original_url
    
    @staticmethod
    def is_valid_url(url):
        """Check if a URL is a valid ZeroNet URL"""
        return (
            url.startswith('zero://') or 
            url.startswith('http://127.0.0.1:43110/') or
            ':43110/' in url
        )


class RegularURL(BaseURL):
    """URL type for regular HTTP/HTTPS URLs"""
    
    def _validate(self):
        """Validate regular URL format"""
        if self.skip_validation:
            # Skip validation if explicitly requested
            return
            
        if not self.is_valid_url(self.original_url):
            raise ValueError(f"Invalid HTTP/HTTPS URL: {self.original_url}")
    
    def get_normalized_url(self):
        """Return a normalized HTTP/HTTPS URL"""
        # Add any normalization logic if needed
        return self.original_url
    
    @staticmethod
    def is_valid_url(url):
        """Check if a URL is a valid HTTP/HTTPS URL"""
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


def create_url_object(url, url_type='auto'):
    """
    Create a URL object of the appropriate type based on the URL string.
    
    Args:
        url (str): The URL string
        url_type (str): Optional explicit URL type ('regular', 'zeronet', 'auto')
        
    Returns:
        BaseURL: A subclass of BaseURL appropriate for the URL type
        
    Raises:
        ValueError: If the URL type is not supported or cannot be determined
    """
    if url is None:
        raise TypeError("URL cannot be None")
    
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Handle explicit URL types
    if url_type == 'regular':
        # For explicit regular URLs, skip validation to allow non-standard URLs
        return RegularURL(url, skip_validation=True)
    elif url_type == 'zeronet':
        # For explicit ZeroNet URLs, skip validation as user has specified the type
        return ZeronetURL(url, skip_validation=True)
    elif url_type != 'auto':
        raise ValueError(f"Unsupported URL type: {url_type}")
    
    # For auto detection, try to determine the type
    if url.startswith('zero://') or (
            '43110' in url and (':43110/' in url or '.43110/' in url)):
        # ZeroNet URL pattern detected
        return ZeronetURL(url)
    
    # Try as regular URL
    if url.startswith('http://') or url.startswith('https://'):
        return RegularURL(url)
    
    # If we can't determine the type, raise an error
    raise ValueError(f"Could not determine URL type for: {url}")
