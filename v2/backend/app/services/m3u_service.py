"""
M3U service for handling M3U files and extracting channel information.
"""
import re
import logging
import aiohttp
from typing import List, Tuple, Dict, Any, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class M3UService:
    """Service for handling M3U files and extracting channel information."""
    
    def __init__(self):
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        self.m3u_pattern = re.compile(r'https?://[^\s<>"]+?\.m3u[8]?(?=[\s<>"]|$)')
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def find_m3u_links(self, content: str, base_url: str) -> List[str]:
        """Find M3U links in HTML content."""
        m3u_urls = []
        
        # Find direct links
        for url in self.m3u_pattern.findall(content):
            # Handle relative URLs
            if not urlparse(url).netloc:
                url = urljoin(base_url, url)
            m3u_urls.append(url)
        
        # Look for hrefs that point to m3u files
        href_pattern = re.compile(r'href=["\']([^"\']+\.m3u[8]?)["\']')
        for match in href_pattern.finditer(content):
            url = match.group(1)
            # Handle relative URLs
            if not urlparse(url).netloc:
                url = urljoin(base_url, url)
            m3u_urls.append(url)
        
        return m3u_urls
    
    async def extract_channels_from_m3u(self, url: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fetch M3U content from URL and extract channel information."""
        try:
            logger.info(f"Fetching M3U content from {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    response.raise_for_status()
                    content = await response.text()
                    return self.extract_channels_from_content(content)
        except Exception as e:
            logger.error(f"Error fetching M3U from {url}: {str(e)}")
            return []
    
    def extract_channels_from_content(self, content: str) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract channel information from M3U content."""
        channels = []
        
        if not content or not content.strip():
            return channels
        
        lines = content.splitlines()
        current_metadata = {}
        current_name = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Extract metadata from EXTINF line
            if line.startswith('#EXTINF:'):
                # Get duration and name
                match = re.search(r'#EXTINF:([-\d\.]*)\s*,\s*(.*)', line)
                if match:
                    duration, name = match.groups()
                    current_name = name.strip()
                    current_metadata = {'duration': duration}
                    
                    # Extract additional metadata like group-title, tvg-id, etc.
                    tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
                    if tvg_id_match:
                        current_metadata['tvg_id'] = tvg_id_match.group(1)
                        
                    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
                    if tvg_name_match:
                        current_metadata['tvg_name'] = tvg_name_match.group(1)
                        
                    tvg_logo_match = re.search(r'tvg-logo="([^"]*)"', line)
                    if tvg_logo_match:
                        current_metadata['tvg_logo'] = tvg_logo_match.group(1)
                        
                    group_title_match = re.search(r'group-title="([^"]*)"', line)
                    if group_title_match:
                        current_metadata['group_title'] = group_title_match.group(1)
            
            # Extract channel ID from stream URL
            elif line.startswith('acestream://'):
                channel_id = line[11:].strip()
                if channel_id and current_name:
                    channels.append((channel_id, current_name, current_metadata))
                    current_name = ""
                    current_metadata = {}
            
            # Extract acestream IDs from any URL format
            elif 'acestream://' in line:
                acestream_match = self.acestream_pattern.search(line)
                if acestream_match:
                    channel_id = acestream_match.group(1)
                    if channel_id:
                        if not current_name:
                            current_name = f"Channel {len(channels) + 1}"
                        channels.append((channel_id, current_name, current_metadata))
                        current_name = ""
                        current_metadata = {}
        
        logger.info(f"Extracted {len(channels)} channels from M3U content")
        return channels
