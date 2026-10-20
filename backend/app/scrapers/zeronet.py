"""
ZeroNet scraper implementation
"""
import logging
import aiohttp
from app.utils.outbound_http import source_session
import asyncio
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from app.models.url_types import ZeronetURL
from app.scrapers.base import BaseScraper
from app.config.settings import settings
from app.utils.url_guard import BlockedURLError, validate_outbound_url

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
            'Upgrade-Insecure-Requests': '1',
            # Fixes CORS
            'Sec-Fetch-Mode': 'navigate'
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

    # The node answers a file of a site it does not hold yet with this page
    # (a form with add_nonce) instead of the file, and never adds the site by
    # itself. The node keeps no sites across container recreations unless
    # /data/zeronet is a volume, so after every redeploy each source hit it.
    ADD_SITE_MARKER = 'name="add_nonce"'

    def site_root(self, internal_url: str) -> str:
        """http://host:43110/<site>/... -> http://host:43110/<site>/"""
        parsed = urlparse(internal_url)
        gateway = urlparse(self.zeronet_url or 'http://127.0.0.1:43110')
        prefix = gateway.path.rstrip('/') if (parsed.scheme, parsed.netloc) == (gateway.scheme, gateway.netloc) else ''
        path = parsed.path
        if prefix and path.startswith(prefix + '/'):
            path = path[len(prefix):]
        else:
            prefix = ''
        site = path.lstrip('/').split('/', 1)[0]
        return f"{parsed.scheme}://{parsed.netloc}{prefix}/{site}/"

    async def add_site(self, session, internal_url: str) -> None:
        """Ask the node to add the site: requesting its root page adds it and
        starts the download. The caller's retries then wait for the file."""
        root = self.site_root(internal_url)
        validate_outbound_url(root)
        logger.info(f"ZeroNet node does not hold this site yet; adding it via {root}")
        try:
            async with session.get(root, headers=self.headers, timeout=self.timeout) as response:
                response.raise_for_status()
                await response.read()
        except aiohttp.ClientError as e:
            logger.warning(f"Could not add ZeroNet site {root}: {e}")

    @staticmethod
    def channels_from_json(content: str) -> list:
        """(id, name, {}) from a JSON list of links, such as a site's links.json
        ({"links": [{"name": ..., "url": "acestream://<id>"}]}). Any object with
        an acestream:// value counts, its name taken from name/title/label."""
        try:
            data = json.loads(content)
        except ValueError:
            return []
        found, seen = [], set()

        def walk(node):
            if isinstance(node, dict):
                name = next((str(node[k]).strip() for k in ('name', 'title', 'label')
                             if isinstance(node.get(k), str) and node[k].strip()), None)
                for value in node.values():
                    if isinstance(value, str):
                        for cid in re.findall(r'acestream://([0-9a-fA-F]{40})', value):
                            cid = cid.lower()
                            if cid not in seen:
                                seen.add(cid)
                                found.append((cid, name or cid, {}))
                    else:
                        walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        return found

    async def fetch_content(self, url: str) -> str:
        """Fetch content from Zeronet URLs using internal service with retries."""
        # Use the ZeronetURL object to handle URL conversion
        parsed_url = urlparse(url)
        if url.startswith('zero://'):
            # The netloc of zero://<site>/... is the site, not the node.
            zeronet_host = urlparse(self.zeronet_url or 'http://127.0.0.1:43110').hostname or '127.0.0.1'
        else:
            zeronet_host = parsed_url.netloc.split(':')[0] if parsed_url.netloc else '127.0.0.1'

        # Get the internal HTTP URL for ZeroNet service
        internal_url = self.url_obj.get_internal_url(
            zeronet_host, gateway_url=self.zeronet_url or 'http://127.0.0.1:43110')

        # SSRF guard: zeronet-type URLs pass through get_internal_url
        # verbatim when they aren't real zero.net addresses, so they must not
        # become an unguarded escape hatch. The configured ZERONET_URL host
        # is exempt inside the guard.
        validate_outbound_url(internal_url)

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
                async with source_session(cookie_jar=self.cookie_jar) as session:
                    # First request to get the content
                    async with session.get(
                        internal_url,
                        headers=self.headers,
                        timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        content = await response.text()

                        if self.ADD_SITE_MARKER in content:
                            await self.add_site(session, internal_url)
                            retry_count += 1
                            if retry_count < self.retries:
                                await asyncio.sleep(2 ** retry_count)
                                continue
                            raise ValueError("ZeroNet site is not ready and did not "
                                             "download in time; it will be read on the next scrape")

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
                                iframe_url = urljoin(internal_url, iframe_url)

                            try:
                                validate_outbound_url(iframe_url)
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
                            except (aiohttp.ClientError, BlockedURLError) as e:
                                logger.warning(f"Failed to fetch iframe content: {e}")
                                # Don't retry on iframe errors, continue with main content

                        # Check main content as fallback. With bare-ID
                        # harvesting enabled (#81), a page of raw 40-hex
                        # hashes is also acceptable content.
                        if ('acestream://' in content or 'const linksData' in content
                                or 'fileContents' in content
                                or (self.scrape_bare_ids and self.bare_id_pattern.search(content))):
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
        """Override: M3U files go to M3UService and bare JSON files to
        channels_from_json; everything else falls back to the base scraper.
        Both early paths record the source's status like the base does (they
        used to leave it at "active" with no processing time)."""
        url_to_scrape = url if url else self.url_obj.get_normalized_url()
        path = urlparse(url_to_scrape).path.lower()
        if path.endswith(('.m3u', '.m3u8')):
            try:
                content = await self.fetch_content(url_to_scrape)
                # Delegate all parsing to M3UService for consistency and logging
                channels = self.m3u_service.extract_channels_from_content(
                    content,
                    db=getattr(self, 'db', None),
                    epg_service=getattr(self, 'epg_service', None),
                    tv_channel_service=getattr(self, 'tv_channel_service', None)
                )
                status = "OK"
            except Exception as e:
                channels, status = [], f"Error: {str(e)}"
            await self.update_url_status(url_to_scrape, status)
            return channels, status if status != "OK" else f"Extracted {len(channels)} channels from direct M3U file"
        # A bare JSON file (a site's links.json): the HTML extractors only read
        # `const linksData` inside a <script>, so it used to give 0 channels
        # with status OK.
        if path.endswith('.json'):
            try:
                content = await self.fetch_content(url_to_scrape)
            except Exception as e:
                status = f"Error: {str(e)}"
                await self.update_url_status(url_to_scrape, status)
                return [], status
            channels = self.channels_from_json(content)
            if channels:
                await self.update_url_status(url_to_scrape, "OK")
                return channels, f"Extracted {len(channels)} channels from JSON file"
        # Fallback to base scraper for non-M3U
        return await super().scrape(url)
