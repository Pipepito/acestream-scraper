import logging
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from .base import BaseScraper
from urllib.parse import urlparse

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
        """Fetch content from Zeronet URLs using internal service with retries."""
        # Extract host from the URL if available
        parsed_url = urlparse(url)
        zeronet_host = parsed_url.netloc.split(':')[0] if parsed_url.netloc else '127.0.0.1'
        
        # Convert external Zeronet URL to internal format, keeping the host if provided
        if url.startswith('zero://'):
            internal_url = f"http://{zeronet_host}:43110/{url[7:]}"
        elif ':43110/' in url:
            path = url.split(':43110/', 1)[1]
            internal_url = f"http://{zeronet_host}:43110/{path}"
        else:
            internal_url = url

        logger.info(f"Fetching Zeronet content from: {internal_url}")
        
        retry_count = 0
        last_error = None
        
        while retry_count < self.retries:
            try:
                async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
                    # First request to get the main page
                    async with session.get(
                        internal_url,
                        headers=self.headers,
                        timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        content = await response.text()
                        
                        # Look for the iframe_src in the script
                        iframe_src_match = re.search(r'iframe_src\s*=\s*"([^"]+)"', content)
                        if iframe_src_match:
                            iframe_url = iframe_src_match.group(1)
                            logger.info(f"Found iframe URL in script: {iframe_url}")
                            
                            try:
                                # Try to fetch iframe content
                                async with session.get(
                                    iframe_url,
                                    headers=self.headers,
                                    timeout=self.timeout
                                ) as iframe_response:
                                    iframe_response.raise_for_status()
                                    iframe_content = await iframe_response.text()
                                    
                                    if 'acestream://' in iframe_content or 'const linksData' in iframe_content:
                                        return iframe_content
                            except aiohttp.ClientError as e:
                                logger.warning(f"Failed to fetch iframe content: {e}")
                                # Don't retry on iframe errors, continue with main content
                        
                        # Check main content as fallback
                        if 'acestream://' in content or 'const linksData' in content:
                            return content
                        
                        # If we get here, no content was found in this attempt
                        retry_count += 1
                        if retry_count < self.retries:
                            delay = 2 ** retry_count
                            logger.warning(f"No content found, retry {retry_count}/{self.retries}. Waiting {delay} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            raise ValueError("No acestream data found after max retries")
                            
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < self.retries:
                    delay = 2 ** retry_count
                    logger.warning(f"Retry {retry_count}/{self.retries} for {internal_url}. Waiting {delay} seconds... Error: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries reached for {internal_url}. Last error: {last_error}")
                    raise Exception(f"Failed to fetch content after {self.retries} retries. Last error: {last_error}")