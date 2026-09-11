"""
HTTP scraper implementation
"""
import aiohttp
import certifi
import logging
import ssl
from typing import Optional
from urllib.parse import urljoin

from app.models.url_types import RegularURL
from app.scrapers.base import BaseScraper
from app.utils.url_guard import BlockedURLError, validate_outbound_url

MAX_REDIRECTS = 5

logger = logging.getLogger(__name__)


class HTTPScraper(BaseScraper):
    """Scraper for regular HTTP/HTTPS URLs."""

    def __init__(self, url_obj: RegularURL, timeout: int = 10, retries: int = 3):
        super().__init__(url_obj, timeout, retries)
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def fetch_content(self, url: str) -> str:
        """Fetch content from regular HTTP/HTTPS URLs."""
        validate_outbound_url(url)

        # Check if URL is directly pointing to an M3U file
        is_m3u_file = url.lower().endswith(('.m3u', '.m3u8'))
        if is_m3u_file:
            logger.info(f"Detected direct M3U file URL: {url}")
        else:
            logger.info(f"Fetching HTTP content from: {url}")

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Redirects are followed manually so every hop goes through
                # the outbound URL guard — a public host 302ing to a private
                # or metadata address must not slip past the initial check.
                current_url = url
                for _ in range(MAX_REDIRECTS + 1):
                    async with session.get(current_url,
                                         headers=self.headers,
                                         timeout=self.timeout,
                                         allow_redirects=False) as response:
                        if response.status in (301, 302, 303, 307, 308):
                            location = response.headers.get('Location')
                            if not location:
                                response.raise_for_status()
                            current_url = urljoin(current_url, location)
                            validate_outbound_url(current_url)
                            continue
                        response.raise_for_status()
                        content = await response.text()

                        # If it's an M3U file, validate and log appropriately
                        if is_m3u_file:
                            if content.strip().startswith('#EXTM3U') or 'acestream://' in content:
                                logger.info(f"Successfully fetched M3U file content ({len(content)} bytes)")
                            else:
                                logger.warning(f"Content doesn't appear to be a valid M3U file. First 100 chars: {content[:100]}")

                        return content
                raise BlockedURLError(f"Too many redirects fetching '{url}'")
        except Exception as e:
            # The caller decides whether this is fatal (it retries); keep it at warning here.
            logger.warning(f"Error fetching content from {url}: {str(e)}")
            raise
