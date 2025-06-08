"""
Scraper factory module
"""
from typing import Optional

from app.models.url_types import create_url_object, ZeronetURL, RegularURL, BaseURL
from app.scrapers.base import BaseScraper
from app.scrapers.http import HTTPScraper
from app.scrapers.zeronet import ZeronetScraper


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


__all__ = ['create_scraper_for_url', 'BaseScraper', 'HTTPScraper', 'ZeronetScraper']
