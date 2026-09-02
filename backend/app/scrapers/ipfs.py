"""
IPFS scraper implementation
"""
import logging
import aiohttp
import asyncio

from bs4 import BeautifulSoup

from app.models.url_types import IpfsURL
from app.scrapers.base import BaseScraper
from app.config.settings import settings
from app.utils.url_guard import BlockedURLError, validate_outbound_url

logger = logging.getLogger(__name__)


class IpfsScraper(BaseScraper):
    """Scraper for IPFS/IPNS URLs fetched through an IPFS HTTP gateway."""

    def __init__(self, url_obj: IpfsURL, timeout: int = 30, retries: int = 3):
        super().__init__(url_obj, timeout, retries)
        self.gateway_url = settings.IPFS_GATEWAY_URL
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def resolve_fetch_url(self, url: str) -> str:
        """Map native ipfs://ipns:// URLs onto the configured HTTP gateway;
        plain http(s) URLs (including explicit gateway links) pass through."""
        return IpfsURL.to_gateway_url(url, self.gateway_url)

    async def fetch_content(self, url: str) -> str:
        """Fetch content through the IPFS gateway with retries."""
        fetch_url = self.resolve_fetch_url(url)

        # SSRF guard: the configured IPFS_GATEWAY_URL host is exempt inside
        # the guard, but explicit http(s) targets must not become an
        # unguarded escape hatch.
        validate_outbound_url(fetch_url)

        logger.info(f"Fetching IPFS content from: {fetch_url}")

        retry_count = 0
        last_error = None
        while retry_count < self.retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        fetch_url,
                        headers=self.headers,
                        timeout=self.timeout
                    ) as response:
                        response.raise_for_status()
                        return await response.text()
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count < self.retries:
                    # Cold-cache gateway fetches routinely fail while the DHT
                    # lookup is still resolving providers; back off and retry.
                    delay = 2 ** retry_count
                    logger.warning(f"Retry {retry_count}/{self.retries} for {fetch_url}. "
                                   f"Error: {str(e)}. Waiting {delay} seconds...")
                    await asyncio.sleep(delay)

        raise Exception(f"Failed to fetch IPFS content after {self.retries} retries. Last error: {last_error}")

    async def scrape(self, url: str = None):
        """Fetch once, then branch: a bare CID carries no filename hint, so
        M3U playlists are detected by content, not only by extension."""
        url_to_scrape = url if url else self.url_obj.get_normalized_url()
        # Relative links found in the page (e.g. href="list.m3u") must resolve
        # against the HTTP gateway URL actually fetched; urljoin cannot extend
        # a native ipfs:// or ipns:// base and would drop the scheme entirely.
        self.current_url = self.resolve_fetch_url(url_to_scrape)
        channels = []
        status = "OK"

        try:
            content = await self.fetch_content(url_to_scrape)
        except BlockedURLError as e:
            logger.error(f"Blocked URL {url_to_scrape}: {str(e)}")
            status = f"Error: {str(e)}"
            await self.update_url_status(url_to_scrape, status)
            return [], status
        except Exception as e:
            logger.error(f"Error scraping {url_to_scrape}: {str(e)}")
            status = f"Error: {str(e)}"
            await self.update_url_status(url_to_scrape, status)
            return [], status

        is_m3u = (url_to_scrape.lower().endswith(('.m3u', '.m3u8'))
                  or content.lstrip().startswith('#EXTM3U'))
        if is_m3u:
            m3u_channels = self.m3u_service.extract_channels_from_content(
                content,
                db=self.db,
                epg_service=self.epg_service,
                tv_channel_service=self.tv_channel_service
            )
            for channel_id, name, metadata in m3u_channels:
                if channel_id not in self.identified_ids and name:
                    channels.append((channel_id, self.clean_channel_name(name), metadata))
                    self.identified_ids.add(channel_id)
        else:
            soup = BeautifulSoup(content, 'html.parser')
            script_channels = [(id, name, {}) for id, name in self.extract_from_script(soup)]
            if script_channels:
                channels.extend(script_channels)
            else:
                channels.extend(self.extract_from_iframe_content(soup))
                channels.extend((id, name, {}) for id, name in self.extract_from_content(soup))
                channels.extend(await self.extract_from_m3u_links(content))
            if self.scrape_bare_ids:
                channels.extend((id, name, {}) for id, name in self.extract_bare_ids(content))

        if channels:
            logger.info(f"Successfully extracted {len(channels)} channels from {url_to_scrape}")
        else:
            logger.warning(f"No channels extracted from {url_to_scrape}")
        await self.update_url_status(url_to_scrape, status)
        return channels, status
