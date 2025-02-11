import aiohttp
import logging
from typing import Optional
from .base import BaseScraper

logger = logging.getLogger(__name__)

class HTTPScraper(BaseScraper):
    """Scraper for regular HTTP/HTTPS URLs."""

    def __init__(self, timeout: int = 10, retries: int = 3):
        super().__init__(timeout, retries)
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def fetch_content(self, url: str) -> str:
        """Fetch content from regular HTTP/HTTPS URLs."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, 
                                 headers=self.headers,
                                 timeout=self.timeout) as response:
                response.raise_for_status()
                return await response.text()