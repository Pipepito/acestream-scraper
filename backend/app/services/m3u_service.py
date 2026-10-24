"""
M3U service for handling M3U files and extracting channel information.
"""
import hashlib
import re

import logging
import aiohttp
from app.utils.outbound_http import source_session
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
        async with source_session(headers=self.headers) as session:
            async with session.get(m3u_url) as response:
                response.raise_for_status()
                content = await response.text()
        return self.extract_channels_from_content(
            content,
            db=db,
            epg_service=epg_service,
            tv_channel_service=tv_channel_service,
        )

    _VLCOPT = re.compile(r'^#EXTVLCOPT:\s*http-(referrer|user-agent|origin)\s*=\s*(.+)$', re.I)
    _HEADER_NAMES = {'referrer': 'Referer', 'user-agent': 'User-Agent', 'origin': 'Origin'}

    @staticmethod
    def _looks_like_stream(line: str) -> bool:
        """A playable URL that is not an acestream id.

        Only http(s): other schemes in these playlists are either acestream
        -- already handled above -- or things no player can open, and letting
        them through would turn junk lines into channels.
        """
        low = line.strip().lower()
        if low.startswith('http://') or low.startswith('https://'):
            return True
        # A broadcaster's channel (`mediaset://T5`): resolved when opened,
        # see app.services.live_providers.
        from app.services.live_providers import for_stream_url
        return for_stream_url(line.strip()) is not None

    @staticmethod
    def _stream_id(url: str) -> str:
        """A stable id for a stream addressed by URL.

        `url:` prefixed so it can never be mistaken for a content id or an
        infohash, which are bare 40 hex digits.
        """
        return 'url:' + hashlib.sha1(url.strip().encode('utf-8')).hexdigest()

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
            # Headers the playlist publishes for THIS entry, between #EXTINF
            # and its URL. Measured on a public TDT list: 30 of 576 entries
            # carry http-referrer, and their domains were exactly the ones
            # answering 403 -- the "blocked" channels were only missing the
            # header the list itself was publishing.
            vlcopt = self._VLCOPT.match(line)
            if vlcopt:
                channel_info.setdefault('stream_headers', {})[
                    self._HEADER_NAMES[vlcopt.group(1).lower()]] = vlcopt.group(2).strip()
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
            stream_url = None
            if not channel_id and self._looks_like_stream(line):
                # NOT AN ACESTREAM ID, AND IT IS STILL A CHANNEL.
                #
                # Until now any line without an acestream id was dropped in
                # silence, so importing an ordinary IPTV playlist produced
                # zero channels and said nothing about it. Measured on a real
                # box: 592 of 1.599 sources (37%) are plain HTTP, reaching 458
                # of 802 channels -- more than half the grid.
                #
                # The id is derived from the URL so a re-scrape updates the
                # same row instead of duplicating it, and it is deliberately
                # NOT 40 hex: every engine path keyed on that shape keeps
                # ignoring these, which is what we want until the status
                # check learns about them.
                stream_url = line
                channel_id = self._stream_id(line)
            if channel_id:
                name = channel_info.get('name', f"Channel {channel_id}")
                metadata = {k: v for k, v in channel_info.items() if k != 'name'}
                if stream_url:
                    metadata['stream_url'] = stream_url
                else:
                    # Headers only mean something to an HTTP request; an
                    # acestream id goes through the engine.
                    metadata.pop('stream_headers', None)
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
        excluded = tv_channel_service.repository.get_import_assignment_exclusions(
            channel_id for channel_id, _name, _meta in parsed_channels
        )
        tvg_id_map = {}
        for idx, (_ace_id, _name, meta) in enumerate(parsed_channels):
            if _ace_id in excluded:
                continue
            tvg_id = meta.get('tvg_id')
            if tvg_id:
                tvg_id_map.setdefault(tvg_id, []).append(idx)

        # For each tvg_id, check if TV channel exists, else try EPG.
        # Ownership conflicts are expected and filtered below. Unexpected errors
        # must reach the scrape transaction so existing source data is preserved.
        for tvg_id, indices in tvg_id_map.items():
            tv_channel = tv_channel_service.get_tv_channel_by_epg_id(tvg_id)
            if tv_channel:
                self._assign_parsed_streams(
                    tv_channel_service, parsed_channels, indices, tv_channel.id
                )
                continue
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
                self._assign_parsed_streams(
                    tv_channel_service, parsed_channels, indices, new_tv_channel.id
                )
        return parsed_channels

    def _assign_parsed_streams(self, tv_channel_service, parsed_channels, indices, tv_channel_id):
        """Assign playlist hashes to a TV channel, skipping ones owned elsewhere."""
        ace_ids = [parsed_channels[idx][0] for idx in indices]
        repo = tv_channel_service.repository
        conflicting = set(repo.acestreams_owned_by_other_tv_channel(ace_ids, tv_channel_id))
        if conflicting:
            logger.warning(
                "Skipping %s Acestream hash(es) already associated with another TV channel: %s",
                len(conflicting),
                ", ".join(sorted(conflicting)),
            )
        assignable = [ace_id for ace_id in ace_ids if ace_id not in conflicting]
        if assignable:
            repo.assign_acestreams_to_tv_channel(assignable, tv_channel_id)
        for idx in indices:
            if parsed_channels[idx][0] not in conflicting:
                parsed_channels[idx][2]['tv_channel_id'] = tv_channel_id
