import re
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Tuple, Set
from datetime import datetime
from bs4 import BeautifulSoup

from ..extensions import db
from ..models import ScrapedURL
from ..services.m3u_service import M3UService

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base scraper class with common acestream link extraction logic."""

    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        self.m3u_pattern = re.compile(r'https?://[^\s<>"]+?\.m3u[8]?(?=[\s<>"]|$)')
        self.identified_ids: Set[str] = set()
        self.m3u_service = M3UService()
        # Pattern to match multiple whitespace characters (spaces, tabs, newlines)
        self.whitespace_pattern = re.compile(r'\s+')

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

    async def extract_from_m3u_links(self, content: str) -> List[Tuple[str, str, dict]]:
        """Extract channels from M3U files linked in the content."""
        channels = []
        
        # Find M3U links in content
        m3u_urls = await self.m3u_service.find_m3u_links(content, self.current_url)
        
        # Add any direct M3U URLs found via regex
        direct_m3u_urls = set(self.m3u_pattern.findall(content))
        m3u_urls.extend(direct_m3u_urls)
        
        # Process each unique M3U URL
        for m3u_url in set(m3u_urls):
            try:
                m3u_channels = await self.m3u_service.extract_channels_from_m3u(m3u_url)
                for channel_id, name, metadata in m3u_channels:
                    # Only add channels with actual names, not ID-based names
                    if channel_id not in self.identified_ids and name and not name.startswith("Channel "):
                        # Clean the channel name
                        cleaned_name = self.clean_channel_name(name)
                        channels.append((channel_id, cleaned_name, metadata))
                        self.identified_ids.add(channel_id)
            except Exception as e:
                logger.warning(f"Failed to process M3U file {m3u_url}: {e}")
                
        return channels

    def extract_from_iframe_content(self, soup: BeautifulSoup) -> List[Tuple[str, str, dict]]:
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

    async def scrape(self, url: str) -> Tuple[List[Tuple[str, str, dict]], str]:
        """Main scraping method."""
        self.current_url = url  # Store current URL for relative path resolution
        channels = []
        status = "OK"
        retries_left = self.retries

        while retries_left >= 0:
            try:
                content = await self.fetch_content(url)
                soup = BeautifulSoup(content, 'html.parser')
                
                # First check script tags for listaplana.txt content
                script_channels = [(id, name, {}) for id, name in self.extract_from_script(soup)]
                
                # If we found channels from script (possibly from listaplana.txt), use only those
                if script_channels:
                    channels.extend(script_channels)
                else:
                    # Otherwise, try other extraction methods, but still be careful not to create ID-based names
                    iframe_channels = self.extract_from_iframe_content(soup)
                    content_channels = [(id, name, {}) for id, name in self.extract_from_content(soup)]
                    m3u_channels = await self.extract_from_m3u_links(content)
                    
                    channels.extend(iframe_channels)
                    channels.extend(content_channels)
                    channels.extend(m3u_channels)
                
                break
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                retries_left -= 1
                if retries_left < 0:
                    status = "Error"
                    break
                self.timeout += 5

        # Update URL status in database
        self.update_url_status(url, status)
        
        return channels, status

    def update_url_status(self, url: str, status: str, error: str = None):
        """Update URL status in database."""
        url_record = ScrapedURL.query.filter_by(url=url).first()
        
        if not url_record:
            url_record = ScrapedURL(url=url)
        
        url_record.update_status(status, error)
        db.session.add(url_record)
        db.session.commit()