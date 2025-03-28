from typing import Optional
from .base import BaseScraper
from .http import HTTPScraper
from .zeronet import ZeronetScraper
from ..models.url_types import ZeronetURL, RegularURL, create_url_object

def create_scraper_for_url(url: str, url_type: str, timeout: Optional[int] = None, retries: Optional[int] = None) -> BaseScraper:
    """
    Factory function to create the appropriate scraper based on the URL type.
    
    Args:
        url: The URL to scrape
        url_type: The URL type ('auto', 'zeronet', 'regular')
        timeout: Optional custom timeout value
        retries: Optional custom retry count
    
    Returns:
        BaseScraper: The appropriate scraper for the URL type
    """
    url_obj = create_url_object(url, url_type)
    
    # Validate URL type is not 'auto'
    if url_type == 'auto':
        raise ValueError("URL type 'auto' is not allowed. Please specify 'regular' or 'zeronet'")
    
    if isinstance(url_obj, ZeronetURL):
        timeout = timeout or 20
        retries = retries or 5
        return ZeronetScraper(url_obj, timeout=timeout, retries=retries)
    elif isinstance(url_obj, RegularURL):
        timeout = timeout or 10
        retries = retries or 3
        return HTTPScraper(url_obj, timeout=timeout, retries=retries)
    else:
        raise ValueError(f"Unsupported URL type: {url_obj.__class__.__name__}")

# For backward compatibility
def create_scraper(url: str, timeout: Optional[int] = None, retries: Optional[int] = None) -> BaseScraper:
    """Legacy function for backward compatibility"""
    return create_scraper_for_url(url, 'auto', timeout, retries)

__all__ = ['create_scraper', 'create_scraper_for_url', 'BaseScraper', 'HTTPScraper', 'ZeronetScraper']