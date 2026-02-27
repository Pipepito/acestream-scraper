"""
ZeroNet scraper implementation
"""
import logging
import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from app.models.url_types import ZeronetURL
from app.scrapers.base import BaseScraper
from app.config.settings import settings

logger = logging.getLogger(__name__)


class ZeronetScraper(BaseScraper):
    """Scraper for Zeronet URLs using internal ZeroNet service."""

    def __init__(self, url_obj: ZeronetURL, timeout: int = 20, retries: int = 5):
        super().__init__(url_obj, timeout, retries)
        self.zeronet_url = settings.ZERONET_URL
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

    async def parse_m3u_content(self, content: str) -> list:
        """Parse M3U content and extract Acestream channel info as dicts."""
        channels = []
        lines = content.splitlines()
        current_info = {}
        for line in lines:
            line = line.strip()
            if line.startswith('#EXTINF:'):
                # Parse attributes from EXTINF
                info = line[8:]
                attrs = {}
                # Extract key="value" pairs
                for match in re.finditer(r'(\w+?)="([^"]*)"', info):
                    attrs[match.group(1)] = match.group(2)
                # Extract group-title if present
                group = attrs.get('group-title', '')
                logo = attrs.get('tvg-logo', '')
                tvg_id = attrs.get('tvg-id', '')
                # The channel name is after the last comma
                name = info.split(',')[-1].strip()
                current_info = {
                    'name': name,
                    'group': group,
                    'logo': logo,
                    'tvg_id': tvg_id
                }
            elif line.startswith('http'):
                # Extract Acestream ID from URL
                match = re.search(r'id=([a-fA-F0-9]{40})', line)
                if match:
                    acestream_id = match.group(1)
                    channel = {
                        'acestream_id': acestream_id,
                        'url': line,
                        **current_info
                    }
                    channels.append(channel)
        return channels

    async def fetch_content(self, url: str) -> str:
        """Fetch content from Zeronet URLs using internal service with retries."""
        # Use the ZeronetURL object to handle URL conversion
        parsed_url = urlparse(url)
        zeronet_host = parsed_url.netloc.split(':')[0] if parsed_url.netloc else '127.0.0.1'

        # Get the internal HTTP URL for ZeroNet service
        internal_url = self.url_obj.get_internal_url(zeronet_host)

        # Check if URL is directly pointing to an M3U file
        is_m3u_file = internal_url.lower().endswith(('.m3u', '.m3u8'))
        if is_m3u_file:
            logger.info(f"Detected direct M3U file URL: {internal_url}")
        else:
            logger.info(f"Fetching ZeroNet content from: {internal_url}")

        retry_count = 0
        last_error = None

        while retry_count < self.retries:
            try:
                async with aiohttp.ClientSession(cookie_jar=self.cookie_jar) as session:
                    # First request to get the content
                    async with session.get(
                        internal_url,
                        headers=self.headers,
                        timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        content = await response.text()

                        # If it's an M3U file, just return the content without further processing
                        if is_m3u_file:
                            if content.strip().startswith('#EXTM3U') or 'acestream://' in content:
                                logger.info(f"Successfully fetched M3U file content ({len(content)} bytes)")
                                # Parse channels for logging/debugging, but do not return the list
                                channels = await self.parse_m3u_content(content)
                                logger.info(f"Extracted {len(channels)} acestream channels from M3U file")
                                return content  # Always return the raw content as string
                            else:
                                logger.warning(f"Content doesn't appear to be a valid M3U file. First 100 chars: {content[:100]}")

                        # Check for new_era_iframe.html format by looking for specific HTML structure
                        if 'channel-item' in content or 'ACEStream NEW ERA' in content:
                            logger.info("Detected NEW ERA iframe format")
                            return content

                        # Look for the iframe_src in the script
                        iframe_src_match = re.search(r'iframe_src\s*=\s*"([^"]+)"', content)
                        if iframe_src_match:
                            iframe_url = iframe_src_match.group(1)
                            logger.info(f"Found iframe URL in script: {iframe_url}")

                            # Handle relative URLs
                            if iframe_url.startswith('/'):
                                base_url = f"http://{zeronet_host}:43110"
                                iframe_url = base_url + iframe_url

                            try:
                                # Try to fetch iframe content
                                async with session.get(
                                    iframe_url,
                                    headers=self.headers,
                                    timeout=self.timeout
                                ) as iframe_response:
                                    iframe_response.raise_for_status()
                                    iframe_content = await iframe_response.text()

                                    if ('acestream://' in iframe_content or
                                        'const linksData' in iframe_content or
                                        'fileContents' in iframe_content or
                                        'channel-item' in iframe_content):
                                        return iframe_content
                            except aiohttp.ClientError as e:
                                logger.warning(f"Failed to fetch iframe content: {e}")
                                # Don't retry on iframe errors, continue with main content

                        # Check main content as fallback
                        if 'acestream://' in content or 'const linksData' in content or 'fileContents' in content:
                            return content

                        # If we get here, no expected content was found in this attempt
                        retry_count += 1
                        if retry_count < self.retries:
                            delay = 2 ** retry_count
                            content_preview = content[:150] + "..." if len(content) > 150 else content
                            logger.warning(f"No relevant content found, retry {retry_count}/{self.retries}. "
                                          f"Content preview: {content_preview}. Waiting {delay} seconds...")
                            await asyncio.sleep(delay)
                        else:
                            content_type = response.headers.get('Content-Type', 'unknown')
                            content_preview = content[:150] + "..." if len(content) > 150 else content
                            error_msg = (f"No acestream data found after max retries. Content-Type: {content_type}. "
                                        f"Content preview: {content_preview}")
                            raise ValueError(error_msg)

            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < self.retries:
                    delay = 2 ** retry_count
                    logger.warning(f"Retry {retry_count}/{self.retries} for {internal_url}. "
                                  f"Error: {str(e)}. Waiting {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Max retries reached for {internal_url}. Last error: {last_error}")
                    raise

        if last_error:
            raise Exception(f"Failed to fetch content after {self.retries} retries. Last error: {last_error}")

        return ""  # Empty content if all attempts fail

    async def scrape(self, url: str = None):
        """Override: If M3U, delegate parsing to M3UService; else fallback to base."""
        url_to_scrape = url if url else self.url_obj.get_normalized_url()
        is_m3u_file = url_to_scrape.lower().endswith(('.m3u', '.m3u8'))
        if is_m3u_file:
            content = await self.fetch_content(url_to_scrape)
            # Delegate all parsing to M3UService for consistency and logging
            channels = self.m3u_service.extract_channels_from_content(
                content,
                db=getattr(self, 'db', None),
                epg_service=getattr(self, 'epg_service', None),
                tv_channel_service=getattr(self, 'tv_channel_service', None)
            )
            status = f"Extracted {len(channels)} channels from direct M3U file"
            return channels, status
        # Fallback to base scraper for non-M3U
        return await super().scrape(url)
