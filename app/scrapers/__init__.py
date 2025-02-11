from typing import Optional
from .base import BaseScraper
from .http import HTTPScraper
from .zeronet import ZeronetScraper

def create_scraper(url: str, timeout: Optional[int] = None, retries: Optional[int] = None) -> BaseScraper:
    """
    Factory function to create the appropriate scraper based on the URL.
    
    Args:
        url: The URL to scrape
        timeout: Optional custom timeout value
        retries: Optional custom retry count
    
    Returns:
        BaseScraper: Either a ZeronetScraper for Zeronet URLs or HTTPScraper for regular URLs
        
    Note:
        Zeronet URLs are identified by either:
        - Starting with 'zero://'
        - Starting with 'http://127.0.0.1:43110/'
        - Containing ':43110/' anywhere in the URL
    """
    is_zeronet = (
        url.startswith('zero://') or 
        url.startswith('http://127.0.0.1:43110/') or
        ':43110/' in url
    )
    
    if is_zeronet:
        timeout = timeout or 20
        retries = retries or 5
        return ZeronetScraper(timeout=timeout, retries=retries)
    else:
        timeout = timeout or 10
        retries = retries or 3
        return HTTPScraper(timeout=timeout, retries=retries)

__all__ = ['create_scraper', 'BaseScraper', 'HTTPScraper', 'ZeronetScraper']