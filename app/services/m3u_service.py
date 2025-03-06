import re
import logging
import aiohttp
from typing import List, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
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
    def __init__(self):
        self.stream_service = StreamService()
        self.extinf_pattern = re.compile(r'#EXTINF:(-?\d+)\s*(?:\s*(.+?)\s*)?,\s*(.+)')
        self.tvg_pattern = re.compile(r'tvg-(?:id|name|logo|group-title)="([^"]*)"')
        self.m3u_pattern = re.compile(r'href=["\'](.*?\.m3u[8]?)[\'"]\s*(?:rel="[^"]*"\s*)?(?:target="[^"]*")?>(.*?)<')

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

    async def find_m3u_links(self, content: str, source_url: str) -> List[str]:
        """Find M3U links in content and convert relative to absolute URLs."""
        base_url = self._get_base_url(source_url)
        m3u_urls = []
        
        # Find all M3U links
        for match in self.m3u_pattern.finditer(content):
            m3u_path = match.group(1)
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, m3u_path)
            m3u_urls.append(absolute_url)
            
        return m3u_urls

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
                            tvg_name = tag.group(1)
                        elif 'tvg-logo=' in tag_text:
                            logo = tag.group(1)
                        elif 'group-title=' in tag_text:
                            group = tag.group(1)
                    
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

    async def extract_channels_from_m3u(self, url: str) -> List[Tuple[str, str, dict]]:
        """Download and parse M3U file, returning channel information."""
        try:
            content = await self.download_m3u(url)
            channels = self.parse_m3u_content(content)
            
            # Convert to format expected by scrapers
            return [
                (ch.id, ch.name, {
                    'group': ch.group,
                    'logo': ch.logo,
                    'tvg_id': ch.tvg_id,
                    'tvg_name': ch.tvg_name,
                    'm3u_source': url,
                    'original_url': ch.original_url
                }) for ch in channels if ch.id
            ]
            
        except Exception as e:
            logger.error(f"Error processing M3U file from {url}: {e}")
            return []