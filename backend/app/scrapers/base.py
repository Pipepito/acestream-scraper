"""
Base scraper class with common acestream link extraction logic.
"""
import re
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Tuple, Set, Dict, Union, Any
from datetime import datetime
from bs4 import BeautifulSoup

from app.models.url_types import BaseURL
from app.services.m3u_service import M3UService
from app.config.database import get_db
from app.utils.url_guard import BlockedURLError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base scraper class with common acestream link extraction logic."""

    def __init__(self, url_obj: BaseURL, timeout: int = 10, retries: int = 3, db=None, epg_service=None, tv_channel_service=None):
        self.url_obj = url_obj
        self.timeout = timeout
        self.retries = retries
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        # Bare acestream content IDs are 40 lowercase hex chars. Only used
        # when the source URL opts in via scrape_bare_ids (#81).
        self.bare_id_pattern = re.compile(r'\b([0-9a-f]{40})\b')
        self.scrape_bare_ids = False
        self.m3u_pattern = re.compile(r'https?://[^\s<>"]+?\.m3u[8]?(?=[\s<>"]|$)')
        self.identified_ids: Set[str] = set()
        self.m3u_service = M3UService()
        self.whitespace_pattern = re.compile(r'\s+')
        self.current_url = url_obj.original_url
        self.db = db
        self.epg_service = epg_service
        self.tv_channel_service = tv_channel_service

    def clean_channel_name(self, name: str) -> str:
        """Clean channel name by replacing multiple whitespace with single space and trimming."""
        if not name:
            return ""
        # Replace all whitespace sequences (including newlines) with a single space
        cleaned_name = self.whitespace_pattern.sub(' ', name)
        # Trim leading/trailing whitespace
        return cleaned_name.strip()

    @abstractmethod
    async def fetch_content(self, url: str) -> str:
        """Fetch content from the source URL."""
        pass

    def extract_from_script(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extract acestream links from script tags."""
        channels = []

        # First try to find fileContents with listaplana.txt
        for script in soup.find_all('script'):
            if script.string and 'fileContents' in script.string and 'listaplana.txt' in script.string:
                logger.info("Found fileContents with listaplana.txt - prioritizing this source")

                # Extract the listaplana.txt content using regex
                lista_plana_match = re.search(r'fileContents\s*=\s*\{[^}]*?listaplana\.txt[^}]*?:\s*`(.*?)`',
                                             script.string, re.DOTALL)
                if lista_plana_match:
                    content = lista_plana_match.group(1)
                    for line in content.splitlines():
                        # Only look for lines with acestream:// format
                        acestream_match = self.acestream_pattern.search(line)
                        if acestream_match:
                            channel_id = acestream_match.group(1)

                            # Only extract name if it exists before the acestream://
                            name_part = line.split('acestream://')[0].strip()
                            if name_part:
                                name = name_part.rstrip(':- ')
                                # Clean the channel name
                                name = self.clean_channel_name(name)

                                if channel_id and channel_id not in self.identified_ids:
                                    channels.append((channel_id, name))
                                    self.identified_ids.add(channel_id)

                    # If we found channels from listaplana.txt, return immediately
                    if channels:
                        logger.info(f"Found {len(channels)} channels from listaplana.txt")
                        return channels

        # Fallback to regular linksData extraction only if listaplana.txt didn't yield results
        script_tag = soup.find('script', text=re.compile(r'const linksData'))
        if script_tag:
            script_content = script_tag.string
            json_str = re.search(r'const linksData = (\{.*?\});', script_content, re.DOTALL)
            if json_str:
                try:
                    links_data = json.loads(json_str.group(1))
                    for link in links_data.get('links', []):
                        if 'acestream://' in link.get('url', ''):
                            id = link['url'].split('acestream://')[1]
                            name = link.get('name', '')
                            # Clean the channel name
                            name = self.clean_channel_name(name)
                            if id and id not in self.identified_ids:
                                channels.append((id, name))
                                self.identified_ids.add(id)
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from script tag: {e}")

        return channels

    def extract_from_content(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extract acestream links from general content."""
        channels = []
        ids = self.acestream_pattern.findall(str(soup))

        for id in ids:
            if id not in self.identified_ids:
                link_name_div = soup.find('div', class_='link-name')
                if link_name_div and link_name_div.text.strip():
                    # Only add channels where a proper name is found
                    channel_name = link_name_div.text.strip()
                    # Clean the channel name
                    channel_name = self.clean_channel_name(channel_name)
                    channels.append((id, channel_name))
                    self.identified_ids.add(id)
                # Do NOT add channels with generated names based on IDs

        return channels

    def extract_bare_ids(self, content: str) -> List[Tuple[str, str]]:
        """Extract bare 40-hex content IDs from text (opt-in per URL, #81).

        Sites covered by this mode list raw hashes, optionally prefixed by a
        channel name on the same line ("Channel Name: <40-hex>"). IDs already
        harvested through acestream:// links are skipped. When no name
        precedes the hash, the hash itself becomes the (editable) name.
        """
        channels = []
        # Build logical lines at block-element boundaries only: inline markup
        # (<b>, <code>, table cells within a row) must not split a channel
        # name from its hash, while rows/paragraphs/list items must.
        soup = BeautifulSoup(content, 'html.parser')
        for br in soup.find_all('br'):
            br.replace_with('\n')
        for tag in soup.find_all(['p', 'li', 'tr', 'div', 'section', 'article',
                                  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre']):
            tag.append('\n')
        text = soup.get_text(' ')

        for raw_line in text.splitlines():
            line = ' '.join(raw_line.split())
            # acestream:// lines belong to the dedicated extractor; never
            # re-capture their hashes here.
            lowered = line.lower()
            if not line or 'acestream://' in lowered:
                continue
            # 40-hex strings inside URLs (git SHAs, gateway paths) or torrent
            # infohashes are not acestream IDs.
            if '://' in lowered or 'btih' in lowered:
                continue
            for match in self.bare_id_pattern.finditer(line):
                channel_id = match.group(1)
                if channel_id in self.identified_ids:
                    continue
                name_part = line[:match.start()].strip().rstrip(':-–— ').strip()
                if name_part and len(name_part) <= 100:
                    name = self.clean_channel_name(name_part)
                else:
                    # No label (or the "label" is a wall of page text): the
                    # hash doubles as the editable name.
                    name = channel_id
                channels.append((channel_id, name))
                self.identified_ids.add(channel_id)

        if channels:
            logger.info(f"Extracted {len(channels)} bare content IDs")
        return channels

    async def extract_from_m3u_links(self, content: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract channels from M3U files linked in the content."""
        channels = []
        m3u_urls = await self.m3u_service.find_m3u_links(content, self.current_url)
        direct_m3u_urls = set(self.m3u_pattern.findall(content))
        m3u_urls.extend(direct_m3u_urls)
        for m3u_url in set(m3u_urls):
            try:
                m3u_content = await self.fetch_content(m3u_url)
                m3u_channels = self.m3u_service.extract_channels_from_content(
                    m3u_content,
                    db=self.db,
                    epg_service=self.epg_service,
                    tv_channel_service=self.tv_channel_service,
                )
                for channel_id, name, metadata in m3u_channels:
                    if channel_id not in self.identified_ids and name and not name.startswith("Channel "):
                        cleaned_name = self.clean_channel_name(name)
                        channels.append((channel_id, cleaned_name, metadata))
                        self.identified_ids.add(channel_id)
            except Exception as e:
                logger.warning(f"Failed to process M3U file {m3u_url}: {e}")
        return channels

    def extract_from_iframe_content(self, soup: BeautifulSoup) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract acestream links from iframe content in ZeroNet sites."""
        channels = []

        # Try to extract from list view (channel-item)
        channel_items = soup.select('.channel-item')
        for item in channel_items:
            name_elem = item.select_one('.item-name')
            url_elem = item.select_one('.item-url')

            if url_elem:  # We only require the ID to be present
                channel_id = url_elem.get_text().strip()

                # Only add the name if it exists and is not empty
                if name_elem and name_elem.get_text().strip():
                    name = name_elem.get_text().strip()
                    # Clean the channel name
                    name = self.clean_channel_name(name)
                    if channel_id and channel_id not in self.identified_ids:
                        channels.append((channel_id, name, {}))
                        self.identified_ids.add(channel_id)

        # Try to extract from script content with fileContents variable
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'fileContents' in script.string:
                # Look for listaplana.txt content in fileContents
                match = re.search(r'fileContents\s*=\s*\{[^}]*listaplana\.txt[^}]*:\s*`(.*?)`', script.string, re.DOTALL)
                if match:
                    content = match.group(1)
                    for line in content.splitlines():
                        if ':' in line and 'acestream://' in line:
                            # Extract name and ID from format "NAME: acestream://ID"
                            parts = line.split('acestream://', 1)
                            if len(parts) == 2:
                                name = parts[0].strip().rstrip(':- ')
                                channel_id = parts[1].strip()

                                # Clean the channel name
                                name = self.clean_channel_name(name)

                                if name and channel_id and channel_id not in self.identified_ids:
                                    channels.append((channel_id, name, {}))
                                    self.identified_ids.add(channel_id)

        return channels

    async def scrape(self, url: str = None) -> Tuple[List[Tuple[str, str, Dict[str, Any]]], str]:
        """Main scraping method."""
        url_to_scrape = url if url else self.url_obj.get_normalized_url()
        self.current_url = url_to_scrape
        channels = []
        status = "OK"
        retries_left = self.retries
        is_m3u_file = url_to_scrape.lower().endswith((".m3u", ".m3u8"))
        while retries_left >= 0:
            try:
                content = await self.fetch_content(url_to_scrape)
                if is_m3u_file:
                    logger.info(f"Processing direct M3U file: {url_to_scrape}")
                    direct_channels = self.m3u_service.extract_channels_from_content(
                        content,
                        db=self.db,
                        epg_service=self.epg_service,
                        tv_channel_service=self.tv_channel_service
                    )
                    for channel_id, name, metadata in direct_channels:
                        if channel_id not in self.identified_ids and name:
                            cleaned_name = self.clean_channel_name(name)
                            channels.append((channel_id, cleaned_name, metadata))
                            self.identified_ids.add(channel_id)
                    if channels:
                        logger.info(f"Extracted {len(channels)} channels from direct M3U file")
                    else:
                        logger.warning(f"No channels found in M3U file content")
                    break
                soup = BeautifulSoup(content, 'html.parser')
                script_channels = [(id, name, {}) for id, name in self.extract_from_script(soup)]
                if script_channels:
                    channels.extend(script_channels)
                else:
                    iframe_channels = self.extract_from_iframe_content(soup)
                    content_channels = [(id, name, {}) for id, name in self.extract_from_content(soup)]
                    m3u_channels = await self.extract_from_m3u_links(content)
                    channels.extend(iframe_channels)
                    channels.extend(content_channels)
                    channels.extend(m3u_channels)
                if self.scrape_bare_ids:
                    channels.extend((id, name, {}) for id, name in self.extract_bare_ids(content))
                break
            except BlockedURLError as e:
                # The block is deterministic — retrying only repeats DNS
                # lookups. Record the status and stop immediately.
                logger.error(f"Blocked URL {url_to_scrape}: {str(e)}")
                status = f"Error: {str(e)}"
                break
            except Exception as e:
                logger.error(f"Error scraping {url_to_scrape}: {str(e)}")
                retries_left -= 1
                if retries_left < 0:
                    status = f"Error: {str(e)}"
                    break
                self.timeout += 5
        if channels:
            logger.info(f"Successfully extracted {len(channels)} channels from {url_to_scrape}")
        else:
            logger.warning(f"No channels extracted from {url_to_scrape}")
        await self.update_url_status(url_to_scrape, status)
        return channels, status

    async def update_url_status(self, url: str, status: str, error: str = None):
        """Update URL status in database."""
        db = self.db
        owns_session = db is None
        if db is None:
            try:
                from main import app

                override_get_db = app.dependency_overrides.get(get_db)
            except Exception:
                override_get_db = None

            if override_get_db is not None:
                db = next(override_get_db())
                owns_session = False
            else:
                db = next(get_db())

        from app.models.models import ScrapedURL

        candidate_urls = {url}
        if self.url_obj is not None:
            candidate_urls.add(self.url_obj.original_url)
            candidate_urls.add(self.url_obj.get_normalized_url())

        url_record = db.query(ScrapedURL).filter(ScrapedURL.url.in_(candidate_urls)).order_by(ScrapedURL.id.asc()).first()

        if not url_record:
            url_record = ScrapedURL(url=url)

        url_record.update_status(status, error)
        db.add(url_record)
        db.commit()
        if owns_session:
            db.close()
