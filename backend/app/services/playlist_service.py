"""
Service for managing and generating M3U playlists
"""
import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel


class PlaylistService:
    """Service for generating M3U playlists"""

    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.channel_repository = ChannelRepository(db)

    async def generate_playlist(
        self,
        search: Optional[str] = None,
        group: Optional[str] = None,
        only_online: bool = False,
        include_groups: Optional[List[str]] = None,
        exclude_groups: Optional[List[str]] = None,
        favorites_only: bool = False,
        base_url: Optional[str] = None,
        base_url_id: Optional[int] = None,
        format: Optional[str] = None
    ) -> str:
        """
        Generate an M3U playlist with the specified filters

        Args:
            search: Optional search term for channel names
            group: Optional group filter
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude
            favorites_only: Whether to include only channels linked to favorite TV channels
            base_url: Optional base URL for stream links
            format: Optional format for the playlist output

        Returns:
            The M3U playlist content as a string
        """
        # Fetch channels that match criteria
        channels = self.channel_repository.get_filtered_channels(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups,
            favorites_only=favorites_only
        )

        # Load runtime settings for base URL fallback and addpid toggle.
        base_url, addpid_enabled = self._resolve_output_settings(base_url, base_url_id)

        # Generate M3U content
        m3u_content = self._generate_m3u_content(
            channels,
            base_url=base_url,
            format=format,
            addpid=addpid_enabled
        )
        return m3u_content

    async def generate_tv_channels_playlist(
        self,
        search: Optional[str] = None,
        favorites_only: bool = False,
        base_url: Optional[str] = None,
        base_url_id: Optional[int] = None,
        format: Optional[str] = None
    ) -> str:
        """
        Generate a curated M3U playlist of TV channels with their assigned
        acestreams, ordered by channel number then name. Channels without
        assigned streams are skipped.
        """
        tv_channels = self.channel_repository.get_playlist_tv_channels(
            search=search,
            favorites_only=favorites_only,
        )
        base_url, addpid = self._resolve_output_settings(base_url, base_url_id)

        lines: List[str] = ["#EXTM3U"]
        pid_counter = 1
        name_counts: Dict[str, int] = {}
        entry_lines, pid_counter, _ = self._tv_channel_entries(
            tv_channels, base_url, addpid, pid_counter, name_counts
        )
        lines.extend(entry_lines)
        return "\n".join(lines) + "\n"

    async def generate_all_streams_playlist(
        self,
        search: Optional[str] = None,
        include_unassigned: bool = True,
        base_url: Optional[str] = None,
        base_url_id: Optional[int] = None,
        format: Optional[str] = None
    ) -> str:
        """
        Generate an M3U playlist of numbered TV channels followed by
        acestreams not assigned to any TV channel (numbered from 9000).
        """
        tv_channels = self.channel_repository.get_playlist_tv_channels(search=search)
        base_url, addpid = self._resolve_output_settings(base_url, base_url_id)

        lines: List[str] = ["#EXTM3U"]
        pid_counter = 1
        name_counts: Dict[str, int] = {}
        entry_lines, pid_counter, processed_ids = self._tv_channel_entries(
            tv_channels, base_url, addpid, pid_counter, name_counts
        )
        lines.extend(entry_lines)

        if include_unassigned:
            unassigned = self.channel_repository.get_unassigned_channels(search=search)

            # Number unassigned streams after the TV-channel range, starting
            # at 9000 (matching v1 behavior).
            next_channel_number = 9000
            numbers = [c.channel_number for c in tv_channels if c.channel_number is not None]
            if numbers:
                next_channel_number = max(next_channel_number, max(numbers) + 1)

            for channel in unassigned:
                if channel.id in processed_ids or not channel.id:
                    continue
                display_name = self._attr(channel.name) if channel.name else f"Stream {channel.id[:8]}"
                display_name = self._dedupe_name(display_name, name_counts)

                attrs = [f'tvg-chno="{next_channel_number}"']
                next_channel_number += 1
                if channel.tvg_id:
                    attrs.append(f'tvg-id="{self._attr(channel.tvg_id)}"')
                attrs.append(f'tvg-name="{display_name}"')
                if channel.logo:
                    attrs.append(f'tvg-logo="{self._attr(channel.logo)}"')
                attrs.append(f'group-title="{self._attr(channel.group) if channel.group else "Unassigned Streams"}"')

                lines.append(f'#EXTINF:-1 {" ".join(attrs)},{display_name}')
                lines.append(self._stream_link(base_url, channel.id, pid_counter if addpid else None))
                if addpid:
                    pid_counter += 1

        return "\n".join(lines) + "\n"

    def _tv_channel_entries(
        self,
        tv_channels: List["TVChannel"],
        base_url: str,
        addpid: bool,
        pid_counter: int,
        name_counts: Dict[str, int],
    ):
        """Build EXTINF/link line pairs for TV channels with their assigned
        streams. Returns (lines, next_pid_counter, processed_acestream_ids)."""
        lines: List[str] = []
        processed_ids = set()

        for tv_channel in tv_channels:
            streams = [s for s in tv_channel.acestream_channels if s.id]
            if not streams:
                continue
            streams = sorted(streams, key=lambda s: (-self._score_acestream(s), s.id))
            multi = len(streams) > 1

            for index, stream in enumerate(streams, start=1):
                processed_ids.add(stream.id)

                # Disambiguate multi-stream channels with a parenthesized
                # suffix so "DAZN 1 (2)" can't be confused with a channel
                # actually named "DAZN 1 2" (#125). Route the generated name
                # through the shared registry so later duplicates can't
                # collide with it.
                base_name = self._attr(tv_channel.name)
                if multi:
                    display_name = self._dedupe_name(f"{base_name} ({index})", name_counts)
                else:
                    display_name = self._dedupe_name(base_name, name_counts)

                attrs = []
                if tv_channel.channel_number is not None:
                    if multi:
                        # Zero-pad the sub-number so 10+ streams stay distinct
                        # when players parse tvg-chno as a decimal (5.1 vs 5.10).
                        width = len(str(len(streams)))
                        attrs.append(f'tvg-chno="{tv_channel.channel_number}.{index:0{width}d}"')
                    else:
                        attrs.append(f'tvg-chno="{tv_channel.channel_number}"')
                # All streams of a channel share the channel's EPG listing, so
                # tvg-id stays un-suffixed and keeps matching the EPG XML ids.
                if tv_channel.epg_id:
                    attrs.append(f'tvg-id="{self._attr(tv_channel.epg_id)}"')
                elif stream.tvg_id:
                    attrs.append(f'tvg-id="{self._attr(stream.tvg_id)}"')
                attrs.append(f'tvg-name="{display_name}"')
                if tv_channel.logo_url:
                    attrs.append(f'tvg-logo="{self._attr(tv_channel.logo_url)}"')
                elif stream.logo:
                    attrs.append(f'tvg-logo="{self._attr(stream.logo)}"')
                if tv_channel.category:
                    attrs.append(f'group-title="{self._attr(tv_channel.category)}"')

                lines.append(f'#EXTINF:-1 {" ".join(attrs)},{display_name}')
                lines.append(self._stream_link(base_url, stream.id, pid_counter if addpid else None))
                if addpid:
                    pid_counter += 1

        return lines, pid_counter, processed_ids

    @staticmethod
    def _score_acestream(stream: AcestreamChannel) -> int:
        """Rank a stream's quality for best-stream-first ordering."""
        score = 0
        if stream.is_online:
            score += 10
        if stream.logo:
            score += 3
        if stream.tvg_id:
            score += 2
        if stream.tvg_name:
            score += 1
        return score

    @staticmethod
    def _dedupe_name(name: str, name_counts: Dict[str, int]) -> str:
        """Claim a unique display name: second 'X' becomes 'X (2)'.

        Every returned name is registered in name_counts, and generated
        suffixed candidates are probed against the registry, so the multi-
        stream '(n)' suffixes and duplicate-name suffixes can never collide
        with each other or with literal 'X (n)' channel names.
        """
        count = name_counts.get(name, 0) + 1
        name_counts[name] = count
        if count == 1:
            return name
        candidate = f"{name} ({count})"
        while candidate in name_counts:
            count += 1
            name_counts[name] = count
            candidate = f"{name} ({count})"
        name_counts[candidate] = 1
        return candidate

    @staticmethod
    def _attr(value) -> str:
        """Sanitize a value for use inside a double-quoted EXTINF attribute."""
        return str(value).replace('"', "'").replace("\r", " ").replace("\n", " ")

    @staticmethod
    def _stream_link(base_url: str, channel_id: str, pid: Optional[int] = None) -> str:
        """Build a stream link from a base-URL pattern (#62).

        A pattern containing {channel_id} is rendered by substitution
        (with {pid} filled from the per-entry counter, or stripped when
        pids are disabled); a pattern without placeholders is a plain
        prefix, matching the legacy base_url behavior.
        """
        if "{channel_id}" in base_url:
            link = base_url.replace("{channel_id}", str(channel_id))
            if "{pid}" in link:
                if pid is not None:
                    link = link.replace("{pid}", str(pid))
                else:
                    link = PlaylistService._strip_pid_placeholder(link)
            return link
        # Legacy prefix behavior. A stray {pid} without {channel_id} can't be
        # persisted (schema validation) but can arrive via an explicit
        # ?base_url= string — never leak the literal placeholder to players.
        if "{pid}" in base_url:
            if pid is not None:
                base_url = base_url.replace("{pid}", str(pid))
                link = f"{base_url}{channel_id}"
                return link
            base_url = PlaylistService._strip_pid_placeholder(base_url)
        link = f"{base_url}{channel_id}"
        if pid is not None:
            link += f"&pid={pid}"
        return link

    @staticmethod
    def _strip_pid_placeholder(link: str) -> str:
        """Remove an unfilled pid={pid} query parameter, keeping the query
        string valid whether the parameter was first, middle, or last."""
        # pid param followed by another parameter: keep the leading separator
        link = re.sub(r"([?&])pid=\{pid\}&", r"\1", link)
        # pid param at the end of the query string
        link = re.sub(r"[?&]pid=\{pid\}$", "", link)
        # any remaining bare occurrence
        return link.replace("{pid}", "")

    def _resolve_output_settings(self, base_url: Optional[str],
                                 base_url_id: Optional[int] = None):
        """Resolve the effective base URL and addpid toggle.

        Precedence: explicit base_url string > base_url_id lookup > the
        default named base URL > the legacy base_url setting.
        """
        from app.repositories.base_url_repository import BaseUrlRepository
        from app.repositories.settings_repository import SettingsRepository
        settings_repo = SettingsRepository(self.db)
        if not base_url and base_url_id is not None:
            entry = BaseUrlRepository(self.db).get(base_url_id)
            if entry is None:
                raise LookupError(f"Base URL id {base_url_id} not found")
            base_url = entry.pattern
        if not base_url:
            default_entry = BaseUrlRepository(self.db).get_default()
            if default_entry is not None:
                base_url = default_entry.pattern
        if not base_url:
            base_url = settings_repo.get_setting(
                SettingsRepository.BASE_URL,
                SettingsRepository.DEFAULT_BASE_URL
            )
        addpid = settings_repo.get_setting(SettingsRepository.ADDPID, SettingsRepository.DEFAULT_ADDPID)
        addpid_enabled = str(addpid).lower() in ("true", "1")
        return base_url, addpid_enabled

    async def get_channel_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups

        Returns:
            List of group names
        """
        return self.channel_repository.get_unique_groups()

    def _generate_m3u_content(self, channels: List[AcestreamChannel], base_url: Optional[str] = None, format: Optional[str] = None, addpid: bool = False) -> str:
        """
        Convert channels to M3U format, supporting custom base_url and format

        Args:
            channels: List of channels to include
            base_url: Optional base URL for stream links
            format: Optional format for the playlist output

        Returns:
            M3U formatted string
        """
        # M3U header
        header = "#EXTM3U\n"

        # Generate each channel entry
        entries = []
        pid_counter = 1

        for channel in channels:
            # Skip invalid channels
            if not channel.id or not channel.name:
                continue

            # Build channel attributes
            attrs = []
            if channel.group:
                attrs.append(f'group-title="{channel.group}"')

            # Use TV channel logo if available
            logo = None
            if hasattr(channel, 'tv_channel') and channel.tv_channel and channel.tv_channel.logo_url:
                logo = channel.tv_channel.logo_url

            if logo:
                attrs.append(f'tvg-logo="{logo}"')

            # Add channel name and ID if available
            tvg_id = getattr(channel, 'tvg_id', '')
            if tvg_id:
                attrs.append(f'tvg-id="{tvg_id}"')

            # Generate entry
            entry = f'#EXTINF:-1 {" ".join(attrs)}, {channel.name}\n'

            link = self._stream_link(base_url, channel.id, pid_counter if addpid else None)
            entry += link + '\n'

            entries.append(entry)
            if addpid:
                pid_counter += 1

        # Combine all parts
        return header + '\n'.join(entries)
