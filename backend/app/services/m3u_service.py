"""
M3U service for handling M3U files and extracting channel information.
"""
import re

import logging
import aiohttp
from typing import List, Tuple, Dict, Any, Set
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)
# Forced logger activation diagnostic
logger.warning(f"[M3UService] MODULE IMPORTED, logger name: {logger.name}")


class M3UService:
    """Service for handling M3U files and extracting channel information."""

    def __init__(self):
        self.acestream_pattern = re.compile(r'acestream://([\w\d]+)')
        self.m3u_pattern = re.compile(r"https?://[^\s<>\"']+?\.m3u[8]?(?=[\s<>\"']|$)")
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

    def extract_channels_from_content(self, content: str, db=None, epg_service=None, tv_channel_service=None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract channel information from M3U content."""
        logger.warning(f"[M3UService] ENTERED extract_channels_from_content, logger name: {logger.name}")
        print(f"[M3UService][PRINT] ENTERED extract_channels_from_content, logger name: {logger.name}")
        channels = []

        if not content or not content.strip():
            return channels

        lines = content.splitlines()
        channel_info = {}
        for idx, line in enumerate(lines):
            raw_line = line
            line = line.strip()
            if not line:
                continue
            if line.startswith('#EXTINF:'):
                # Parse channel name and optional attributes
                name_match = re.search(r'#EXTINF:.*,(.+)', line)
                if name_match:
                    channel_info['name'] = name_match.group(1).strip()
                logger.debug(f"[M3UService] #EXTINF line: {line}")
                # Extract tvg-id, tvg-name, group-title, etc. (quoted only, as in v1)
                for tag_match in re.finditer(r'(tvg-[^=]+|group-title)="([^"]+)"', line):
                    tag_name = tag_match.group(1)
                    tag_value = tag_match.group(2)
                    # Normalize field names to match v1/v2 conventions
                    if tag_name == 'tvg-id':
                        channel_info['tvg_id'] = tag_value
                    elif tag_name == 'tvg-name':
                        channel_info['tvg_name'] = tag_value
                    elif tag_name == 'tvg-logo':
                        channel_info['tvg_logo'] = tag_value
                    elif tag_name == 'group-title':
                        channel_info['group_title'] = tag_value
                    else:
                        channel_info[tag_name] = tag_value
                logger.debug(f"[M3UService] Parsed metadata after #EXTINF: {channel_info}")
                continue
            # Skip other comment lines
            if line.startswith('#'):
                continue
            # Check for acestream:// or getstream?id=... links
            acestream_match = self.acestream_pattern.search(line)
            getstream_match = re.search(r'getstream\?id=([a-fA-F0-9]{40})', line)
            channel_id = None
            if acestream_match:
                channel_id = acestream_match.group(1)
            elif getstream_match:
                channel_id = getstream_match.group(1)
            if channel_id:
                name = channel_info.get('name', f"Channel {channel_id}")
                metadata = {k: v for k, v in channel_info.items() if k != 'name'}
                logger.debug(f"[M3UService] Adding channel: id={channel_id}, name={name}, metadata={metadata}")
                channels.append((channel_id, name, metadata))
                channel_info = {}
        print(f"[M3UService][PRINT] Extracted {len(channels)} channels from M3U content")
        logger.info(f"Extracted {len(channels)} channels from M3U content")
        for ch in channels:
            logger.debug(f"[M3UService] Extracted channel: id={ch[0]}, name={ch[1]}, metadata={ch[2]}")
        # Auto-create TV channels from EPG if services are provided
        if db and epg_service and tv_channel_service:
            channels = self.auto_create_tv_channels_from_epg(db, channels, epg_service, tv_channel_service)
        return channels

    def auto_create_tv_channels_from_epg(self, db, parsed_channels, epg_service, tv_channel_service):
        """
        For each unique tvg_id in parsed_channels, if no TV channel exists but EPG has a channel,
        create a new TV channel from EPG and assign all matching streams to it.
        Args:
            db: SQLAlchemy session
            parsed_channels: List of (acestream_id, name, metadata) tuples
            epg_service: EPGService instance
            tv_channel_service: TVChannelService instance
        Returns:
            List of (acestream_id, name, metadata) with tv_channel_id assigned where applicable
        """
        # Build tvg_id -> [channel indices] mapping
        tvg_id_map = {}
        for idx, (_ace_id, _name, meta) in enumerate(parsed_channels):
            tvg_id = meta.get('tvg_id')
            if tvg_id:
                tvg_id_map.setdefault(tvg_id, []).append(idx)

        # For each tvg_id, check if TV channel exists, else try EPG
        for tvg_id, indices in tvg_id_map.items():
            # Check if TV channel exists
            tv_channel = tv_channel_service.get_tv_channel_by_epg_id(tvg_id)
            if tv_channel:
                # Assign tv_channel_id to all matching streams
                ace_ids = [parsed_channels[idx][0] for idx in indices]
                tv_channel_service.repository.assign_acestreams_to_tv_channel(ace_ids, tv_channel.id)
                for idx in indices:
                    parsed_channels[idx][2]['tv_channel_id'] = tv_channel.id
                continue
            # Check EPG for channel across all sources
            epg_channel = epg_service.find_channel_by_xml_id_across_sources(tvg_id)
            if epg_channel:
                tv_channel_data = {
                    'name': epg_channel.name,
                    'logo_url': getattr(epg_channel, 'icon_url', None),
                    'category': getattr(epg_channel, 'group', None),
                    'language': getattr(epg_channel, 'language', None),
                    'epg_id': epg_channel.channel_xml_id,
                    'epg_source_id': epg_channel.epg_source_id,
                    'is_active': True
                }
                new_tv_channel = tv_channel_service.create_tv_channel(**tv_channel_data)
                ace_ids = [parsed_channels[idx][0] for idx in indices]
                tv_channel_service.repository.assign_acestreams_to_tv_channel(ace_ids, new_tv_channel.id)
                for idx in indices:
                    parsed_channels[idx][2]['tv_channel_id'] = new_tv_channel.id
        return parsed_channels
