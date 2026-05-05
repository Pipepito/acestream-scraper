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
        self.m3u_pattern = re.compile(r"https?://[^\s<>\"']+?\.m3u[8]?(?=[\s<>\"']|$)")
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def _extract_quoted_attributes(self, line: str) -> Dict[str, str]:
        """Extract quoted M3U attributes from a metadata line."""
        return {match.group(1): match.group(2) for match in re.finditer(r'([\w-]+)="([^"]+)"', line)}

    def _resolve_m3u_url(self, base_url: str, candidate_url: str) -> str:
        """Resolve relative M3U URLs for both HTTP(S) and zero:// bases."""
        if urlparse(candidate_url).scheme or urlparse(candidate_url).netloc:
            return candidate_url
        if base_url.startswith("zero://"):
            zero_path = base_url[len("zero://"):]
            base_parts = [part for part in zero_path.split("/") if part]
            if not base_parts:
                return f"zero://{candidate_url.lstrip('/')}"
            if not base_url.endswith("/") and len(base_parts) > 1:
                base_parts = base_parts[:-1]
            candidate_parts = [part for part in candidate_url.split("/") if part and part != "."]
            resolved_parts = list(base_parts)
            for part in candidate_parts:
                if part == "..":
                    if resolved_parts:
                        resolved_parts.pop()
                    continue
                resolved_parts.append(part)
            return f"zero://{'/'.join(resolved_parts)}"
        return urljoin(base_url, candidate_url)

    async def extract_channels_from_m3u(
        self,
        m3u_url: str,
        db=None,
        epg_service=None,
        tv_channel_service=None,
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Fetch and parse channels from a remote M3U URL."""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(m3u_url) as response:
                response.raise_for_status()
                content = await response.text()
        return self.extract_channels_from_content(
            content,
            db=db,
            epg_service=epg_service,
            tv_channel_service=tv_channel_service,
        )

    async def find_m3u_links(self, content: str, base_url: str) -> List[str]:
        """Find M3U links in HTML content."""
        m3u_urls = []

        # Find direct links
        for url in self.m3u_pattern.findall(content):
            # Handle relative URLs
            if not urlparse(url).netloc:
                url = self._resolve_m3u_url(base_url, url)
            m3u_urls.append(url)

        # Look for hrefs that point to m3u files
        href_pattern = re.compile(r'href=["\']([^"\']+\.m3u[8]?)["\']')
        for match in href_pattern.finditer(content):
            url = match.group(1)
            # Handle relative URLs
            if not urlparse(url).netloc:
                url = self._resolve_m3u_url(base_url, url)
            m3u_urls.append(url)

        return m3u_urls

    def extract_channels_from_content(self, content: str, db=None, epg_service=None, tv_channel_service=None) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract channel information from M3U content."""
        channels = []

        if not content or not content.strip():
            return channels

        lines = content.splitlines()
        channel_info = {}
        current_group_metadata = {}
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('#EXTGRP:'):
                extgrp_attrs = self._extract_quoted_attributes(line)
                current_group_metadata = {}
                if 'group-title' in extgrp_attrs or 'group-logo' in extgrp_attrs:
                    if extgrp_attrs.get('group-title'):
                        current_group_metadata['group_title'] = extgrp_attrs['group-title']
                    if extgrp_attrs.get('group-logo'):
                        current_group_metadata['group_logo'] = extgrp_attrs['group-logo']
                continue
            if line.startswith('#EXTINF:'):
                # Parse channel name and optional attributes
                channel_info = {}
                name_match = re.search(r'#EXTINF:.*,(.+)', line)
                if name_match:
                    channel_info['name'] = name_match.group(1).strip()
                attrs = self._extract_quoted_attributes(line)
                if attrs.get('tvg-id'):
                    channel_info['tvg_id'] = attrs['tvg-id']
                if attrs.get('tvg-name'):
                    channel_info['tvg_name'] = attrs['tvg-name']
                if attrs.get('tvg-logo'):
                    channel_info['tvg_logo'] = attrs['tvg-logo']
                if attrs.get('group-title'):
                    channel_info['group_title'] = attrs['group-title']
                elif current_group_metadata.get('group_title'):
                    channel_info['group_title'] = current_group_metadata['group_title']
                if (
                    'tvg_logo' not in channel_info
                    and current_group_metadata.get('group_logo')
                    and channel_info.get('group_title') == current_group_metadata.get('group_title')
                ):
                    channel_info['tvg_logo'] = current_group_metadata['group_logo']
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
                channels.append((channel_id, name, metadata))
                channel_info = {}
        logger.info(f"Extracted {len(channels)} channels from M3U content")
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
