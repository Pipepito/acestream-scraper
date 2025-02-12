import logging
import aiohttp
from .base import BaseScraper

logger = logging.getLogger(__name__)

class ZeronetScraper(BaseScraper):
    """Scraper for Zeronet URLs using internal ZeroNet service."""

    def __init__(self, timeout: int = 20, retries: int = 5):
        super().__init__(timeout, retries)
        self.zeronet_url = "http://127.0.0.1:43110"
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        }
        self.cookie_jar = aiohttp.CookieJar()

    async def fetch_content(self, url: str) -> str:
        """Fetch content from Zeronet URLs using internal service."""
        # Convert external Zeronet URL to internal format
        if url.startswith('zero://'):
            internal_url = f"{self.zeronet_url}/{url[7:]}"
        elif ':43110/' in url:
            path = url.split(':43110/', 1)[1]
            internal_url = f"{self.zeronet_url}/{path}"
        else:
            internal_url = url

        logger.info(f"Fetching Zeronet content from: {internal_url}")
        
        async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
            # First request to get wrapper
            async with session.get(
                internal_url,
                headers=self.headers,
                timeout=self.timeout
            ) as response:
                if response.status == 403:
                    # If we get a 403, try with modified Accept header
                    self.headers['Accept'] = 'text/html'
                    async with session.get(
                        internal_url,
                        headers=self.headers,
                        timeout=self.timeout
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.text()
                else:
                    response.raise_for_status()
                    return await response.text()