import re
import logging
import aiohttp
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from ..models.url_types import create_url_object, ZeronetURL, RegularURL
from .stream_service import StreamService

logger = logging.getLogger(__name__)

@dataclass
class M3UChannel:
    id: str
    name: str
    group: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    original_url: Optional[str] = None

class M3UService:
    """Service for handling M3U playlists."""
    
    def __init__(self):
        self.stream_service = StreamService()
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        self.extinf_pattern = re.compile(r'#EXTINF:(-?\d+)\s*(?:\s*(.+?)\s*)?,\s*(.+)')
        self.tvg_pattern = re.compile(r'tvg-(?:id|name|logo|group-title)="([^"]*)"')
        self.m3u_pattern = re.compile(r'https?://[^\s<>"]+?\.m3u[8]?(?=[\s<>"]|$)')
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Pattern to match multiple whitespace characters (spaces, tabs, newlines)
        self.whitespace_pattern = re.compile(r'\s+')

    def clean_text(self, text: str) -> str:
        """Clean text by replacing multiple whitespace with single space and trimming."""
        if not text:
            return ""
        # Replace all whitespace sequences (including newlines) with a single space
        cleaned_text = self.whitespace_pattern.sub(' ', text)
        # Trim leading/trailing whitespace
        return cleaned_text.strip()

    def _get_base_url(self, url: str) -> str:
        """Extract base URL from the source URL."""
        parsed = urlparse(url)
        # Handle ZeroNet URLs specially
        if ':43110/' in url:
            # Keep original host for ZeroNet URLs
            host_with_port = parsed.netloc
            path_base = parsed.path.rsplit('/', 1)[0]
            return f"{parsed.scheme}://{host_with_port}{path_base}/"
        # For regular URLs
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}/"

    async def find_m3u_links(self, content: str, base_url: str) -> List[str]:
        """Find M3U links in content with support for relative URLs."""
        # Direct M3U URLs in the content
        m3u_urls = set(self.m3u_pattern.findall(content))
        
        # Process relative URLs based on base_url
        relative_matches = re.findall(r'(["\'](/[^"\']*?\.m3u[8]?)["\'|\?])', content)
        for match, rel_url in relative_matches:
            try:
                # Determine how to handle the URL based on base_url type
                if ZeronetURL.is_valid_url(base_url):
                    # For ZeroNet URLs
                    url_obj = create_url_object(base_url, 'zeronet')
                    if base_url.startswith('zero://'):
                        abs_url = f"zero://{rel_url.lstrip('/')}"
                    else:
                        # For HTTP ZeroNet URLs
                        host = '127.0.0.1'  # Default
                        parsed = re.match(r'http://([\w\.]+):43110', base_url)
                        if parsed:
                            host = parsed.group(1)
                        abs_url = f"http://{host}:43110{rel_url}"
                else:
                    # For regular HTTP URLs
                    abs_url = urljoin(base_url, rel_url)
                
                m3u_urls.add(abs_url)
            except Exception as e:
                logger.error(f"Error processing relative M3U URL {rel_url}: {e}")
        
        return list(m3u_urls)

    async def download_m3u(self, url: str) -> str:
        """Download M3U file content."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.text()

    def parse_m3u_content(self, content: str) -> List[M3UChannel]:
        """Parse M3U content and extract channel information."""
        channels = []
        current_extinf = None
        
        for line in content.splitlines():
            line = line.strip()
            
            if line.startswith('#EXTINF:'):
                # Parse EXTINF line
                extinf_match = self.extinf_pattern.match(line)
                if extinf_match:
                    # Extract metadata
                    metadata = extinf_match.group(2) or ""
                    name = extinf_match.group(3)
                    
                    # Clean the channel name
                    name = self.clean_text(name)
                    
                    # Parse TVG tags if present
                    tvg_id = None
                    tvg_name = None
                    logo = None
                    group = None
                    
                    for tag in self.tvg_pattern.finditer(metadata):
                        tag_text = tag.group(0)
                        if 'tvg-id=' in tag_text:
                            tvg_id = tag.group(1)
                        elif 'tvg-name=' in tag_text:
                            tvg_name = self.clean_text(tag.group(1))
                        elif 'tvg-logo=' in tag_text:
                            logo = tag.group(1)
                        elif 'group-title=' in tag_text:
                            group = self.clean_text(tag.group(1))
                    
                    current_extinf = M3UChannel(
                        id="",  # Will be set when we find the acestream URL
                        name=name or "Unknown Channel",  # Default name if none provided
                        group=group,
                        logo=logo,
                        tvg_id=tvg_id,
                        tvg_name=tvg_name or name
                    )
            
            elif not line.startswith('#') and current_extinf:
                # Extract acestream ID from URL
                acestream_id = self.stream_service.extract_acestream_id(line)
                if acestream_id:
                    # If no name was provided in EXTINF, use the ID as name
                    if not current_extinf.name or current_extinf.name == "Unknown Channel":
                        current_extinf.name = f"Channel {acestream_id}"
                        
                    current_extinf.id = acestream_id
                    current_extinf.original_url = line  # Store original URL
                    channels.append(current_extinf)
                current_extinf = None

        # Filter out entries with missing IDs
        return [ch for ch in channels if ch.id]

    async def extract_channels_from_m3u(self, m3u_url: str) -> List[Tuple[str, str, Dict]]:
        """Extract channel information from M3U file."""
        channels = []
        
        try:
            # Create the appropriate URL object based on URL type
            url_obj = create_url_object(m3u_url)
            
            # Handle different URL types
            if isinstance(url_obj, ZeronetURL):
                m3u_content = await self._fetch_zeronet_m3u(m3u_url)
            else:
                m3u_content = await self._fetch_http_m3u(m3u_url)
            
            if not m3u_content:
                return []
            
            # Parse the M3U content
            channel_info = {}
            channel_id = None
            
            for line in m3u_content.splitlines():
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    # Extract metadata from EXTINF line
                    if line.startswith('#EXTINF:'):
                        # Parse channel name and optional attributes
                        name_match = re.search(r'#EXTINF:.*,(.+)', line)
                        if name_match:
                            channel_info['name'] = name_match.group(1).strip()
                        
                        # Extract any other metadata
                        # ... (implementation details)
                    continue
                
                # Check if the line contains an acestream link
                acestream_match = self.acestream_pattern.search(line)
                if acestream_match:
                    channel_id = acestream_match.group(1)
                    name = channel_info.get('name', f"Channel {channel_id}")
                    metadata = {k: v for k, v in channel_info.items() if k != 'name'}
                    channels.append((channel_id, name, metadata))
                    channel_info = {}
            
            return channels
        
        except Exception as e:
            logger.error(f"Error extracting channels from M3U at {m3u_url}: {e}")
            return []

    async def _fetch_http_m3u(self, url: str) -> Optional[str]:
        """Fetch M3U content from regular HTTP URL."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching M3U from HTTP URL {url}: {e}")
            return None
    
    async def _fetch_zeronet_m3u(self, url: str) -> Optional[str]:
        """Fetch M3U content from ZeroNet URL."""
        try:
            url_obj = create_url_object(url, 'zeronet')
            internal_url = url_obj.get_internal_url()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(internal_url, headers=self.headers, timeout=20) as response:
                    response.raise_for_status()
                    return await response.text()
        except Exception as e:
            logger.error(f"Error fetching M3U from ZeroNet URL {url}: {e}")
            return None

    def extract_channels_from_content(self, content: str) -> List[Tuple[str, str, Dict]]:
        """Extract channel information directly from M3U content."""
        channels = []
        channel_info = {}
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Handle EXTINF lines
            if line.startswith('#EXTINF:'):
                # Parse channel name and optional attributes
                name_match = re.search(r'#EXTINF:.*,(.+)', line)
                if name_match:
                    channel_info['name'] = name_match.group(1).strip()
                
                # Extract tvg-id, tvg-name, group-title, etc.
                for tag_match in re.finditer(r'(tvg-[^=]+|group-title)="([^"]+)"', line):
                    tag_name = tag_match.group(1)
                    tag_value = tag_match.group(2)
                    
                    # Normalize field names to match database column names
                    if tag_name == 'tvg-id':
                        channel_info['tvg_id'] = tag_value
                    elif tag_name == 'tvg-name':
                        channel_info['tvg_name'] = tag_value
                    elif tag_name == 'tvg-logo':
                        channel_info['logo'] = tag_value
                    elif tag_name == 'group-title':
                        channel_info['group'] = tag_value
                    else:
                        # Store any other metadata with original name
                        channel_info[tag_name] = tag_value
                
                continue
            
            # Skip other comment lines
            if line.startswith('#'):
                continue
            
            # Check if the line contains an acestream link or ace/getstream URL
            acestream_match = self.acestream_pattern.search(line)
            getstream_match = re.search(r'ace/getstream\?id=([\w\d]+)', line) if not acestream_match else None
            
            if acestream_match:
                channel_id = acestream_match.group(1)
                name = channel_info.get('name', f"Channel {channel_id}")
                
                # Extract any other metadata
                metadata = {k: v for k, v in channel_info.items() if k != 'name'}
                
                channels.append((channel_id, name, metadata))
                
                # Reset channel_info for the next channel
                channel_info = {}
            elif getstream_match:
                channel_id = getstream_match.group(1)
                name = channel_info.get('name', f"Channel {channel_id}")
                
                # Extract any other metadata
                metadata = {k: v for k, v in channel_info.items() if k != 'name'}
                
                channels.append((channel_id, name, metadata))
                
                # Reset channel_info for the next channel
                channel_info = {}
        
        logger.info(f"Extracted {len(channels)} channels with metadata from M3U content")
        return channels