import re
import logging
import json
from abc import ABC, abstractmethod
from typing import List, Tuple, Set
from datetime import datetime
from bs4 import BeautifulSoup

from ..extensions import db
from ..models import ScrapedURL

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base scraper class with common acestream link extraction logic."""

    def __init__(self, timeout: int = 10, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        self.identified_ids: Set[str] = set()

    @abstractmethod
    async def fetch_content(self, url: str) -> str:
        """Fetch content from the source URL."""
        pass

    def extract_from_script(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extract acestream links from script tags."""
        channels = []
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
                            if id and id not in self.identified_ids:
                                channels.append((id, link.get('name', f'Channel {id}')))
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
                channel_name = link_name_div.text.strip() if link_name_div else f"Channel {id}"
                channels.append((id, channel_name))
                self.identified_ids.add(id)

        return channels

    async def scrape(self, url: str) -> Tuple[List[Tuple[str, str]], str]:
        """Main scraping method."""
        channels = []
        status = "OK"
        retries_left = self.retries

        while retries_left >= 0:
            try:
                content = await self.fetch_content(url)
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract from both sources
                channels.extend(self.extract_from_script(soup))
                channels.extend(self.extract_from_content(soup))
                
                break
            except Exception as e:
                logger.error(f"Error scraping {url}: {e}")
                retries_left -= 1
                if retries_left < 0:
                    status = "Error"
                    break
                self.timeout += 5  # Increase timeout for retry

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