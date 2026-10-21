"""
Service for managing and generating M3U playlists
"""
import re
from urllib.parse import quote, urlsplit, urlunsplit
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel
from app.services.stream_ranking import score_acestream, sort_streams_curated
from app.utils.m3u import m3u_attr


LIVE_MIMETYPE_PROP = '#KODIPROP:mimetype=application/vnd.apple.mpegurl'
RELAY_MIMETYPE_PROP = '#KODIPROP:mimetype=video/mp2t'


class PlaylistService:
    """Service for generating M3U playlists"""

    def __init__(self, db: Session, live_base_url: Optional[str] = None):
        """Initialize with database session.

        live_base_url is the server's public address, where players open a
        broadcaster's live channel (/live/...).
        """
        self.db = db
        self.live_base_url = live_base_url
        self.channel_repository = ChannelRepository(db)

    def guide_coverage(self):
        from app.repositories.epg_match_repository import EPGMatchRepository
        return EPGMatchRepository(self.db).coverage()

    @property
    def epg_ids(self):
        from app.services.epg_identity_service import EPGIdentityService
        if not hasattr(self, "_epg_ids"):
            self._epg_ids = EPGIdentityService(self.db)
        return self._epg_ids

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
        format: Optional[str] = None,
        include_unassigned: Optional[bool] = None,
        epg_url: Optional[str] = None,
        per_source: bool = False,
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
        base_url, addpid_enabled = self._resolve_output_settings(base_url, base_url_id)
        # Fetch channels that match criteria
        channels = self.channel_repository.get_filtered_channels(
            search=None if "{tv_channel_id}" in base_url else search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups,
            favorites_only=favorites_only
        )

        if "{tv_channel_id}" in base_url:
            tv_ids = {channel.tv_channel_id for channel in channels if channel.tv_channel_id is not None}
            tv_channels = [tv for tv in self.channel_repository.get_playlist_tv_channels(search=search, favorites_only=favorites_only)
                           if tv.id in tv_ids]
            name_counts = {}
            entries, _, _ = self._tv_channel_entries(
                tv_channels, base_url, False, 1, name_counts, per_source=per_source,
                source_ids={channel.id for channel in channels},
            )
            if include_unassigned:
                unassigned = [c for c in channels if c.tv_channel_id is None
                              and (not search or search.casefold() in (c.name or '').casefold())]
                entries.extend(self._unassigned_entries(unassigned, tv_channels, base_url, False, 1, name_counts))
            return self._m3u_header(epg_url) + "\n" + "\n".join(entries) + "\n"

        if include_unassigned is False:
            channels = [c for c in channels if c.tv_channel_id is not None]
        # Keep unassigned streams after the assigned catalogue.
        channels = sorted(channels, key=lambda c: c.tv_channel_id is None)
        # Generate M3U content
        m3u_content = self._generate_m3u_content(
            channels,
            base_url=base_url,
            format=format,
            addpid=addpid_enabled,
            epg_url=epg_url,
        )
        return m3u_content

    async def generate_tv_channels_playlist(
        self,
        search: Optional[str] = None,
        favorites_only: bool = False,
        base_url: Optional[str] = None,
        base_url_id: Optional[int] = None,
        format: Optional[str] = None,
        epg_url: Optional[str] = None,
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

        lines: List[str] = [self._m3u_header(epg_url)]
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
        format: Optional[str] = None,
        epg_url: Optional[str] = None,
    ) -> str:
        """
        Generate an M3U playlist of numbered TV channels followed by
        acestreams not assigned to any TV channel (numbered from 9000).
        """
        tv_channels = self.channel_repository.get_playlist_tv_channels(search=search)
        base_url, addpid = self._resolve_output_settings(base_url, base_url_id)

        lines: List[str] = [self._m3u_header(epg_url)]
        pid_counter = 1
        name_counts: Dict[str, int] = {}
        entry_lines, pid_counter, processed_ids = self._tv_channel_entries(
            tv_channels, base_url, addpid, pid_counter, name_counts
        )
        lines.extend(entry_lines)

        if include_unassigned:
            unassigned = self.channel_repository.get_unassigned_channels(search=search)
            lines.extend(self._unassigned_entries(unassigned, tv_channels, base_url, addpid, pid_counter, name_counts))

        return "\n".join(lines) + "\n"

    @staticmethod
    def _raw_relay_base(base_url: str) -> str:
        """The relay route for one stream, next to a TV-channel relay format."""
        parts = urlsplit(base_url)
        # Preserve a reverse-proxy prefix for the built-in tuner route.
        prefix = parts.path.split('/tuner/channel/', 1)[0] if '/tuner/channel/' in parts.path else ''
        return urlunsplit((parts.scheme, parts.netloc, prefix + '/tuner/stream/{channel_id}.ts', parts.query, ''))

    def _source_entries(self, tv_channel, streams, base_url, name_counts, epg_id):
        """One entry per source of a relayed TV channel, right after it, to
        switch by hand when the automatic choice fails.

        Named as the source publishes itself plus the start of the acestream
        id, numbered N.1, N.2... so they sort under the channel, and sharing
        its guide. Acestream sources go through the raw relay (no failover:
        the point is to pick this one); the rest open as in any stream list.
        """
        stream_base = self._raw_relay_base(base_url)
        width = len(str(len(streams)))
        # Use the parent entry's resolved guide even when its preferred stream
        # is excluded from the optional source list by a stream-level filter.
        lines = []
        for index, stream in enumerate(streams, start=1):
            label = (stream.name or "").strip() or tv_channel.name
            if not getattr(stream, 'stream_url', None):
                label = f"{label} [{stream.id[:8]}]"
            name = self._dedupe_name(self._attr(label), name_counts)
            attrs = []
            if tv_channel.channel_number is not None:
                attrs.append(f'tvg-chno="{tv_channel.channel_number}.{index:0{width}d}"')
            if epg_id:
                attrs.append(f'tvg-id="{self._attr(epg_id)}"')
            attrs.append(f'tvg-name="{name}"')
            logo = tv_channel.logo_url or stream.logo
            if logo:
                attrs.append(f'tvg-logo="{self._attr(logo)}"')
            if tv_channel.category:
                attrs.append(f'group-title="{self._attr(tv_channel.category)}"')
            lines.append(f'#EXTINF:-1 {" ".join(attrs)},{name}')
            lines.extend(self._link_lines(self._stream_link(stream_base, stream.id, stream_url=getattr(stream, 'stream_url', None), stream_headers=getattr(stream, 'stream_headers', None), live_base_url=self.live_base_url)))
        return lines

    def _unassigned_entries(self, channels, tv_channels, base_url, addpid, pid_counter, name_counts):
        """Append standalone streams after TV numbers, using raw relay IDs when needed."""
        if "{tv_channel_id}" in base_url:
            base_url = self._raw_relay_base(base_url)
            addpid = False
        number = max([8999] + [tv.channel_number for tv in tv_channels if tv.channel_number is not None]) + 1
        lines = []
        for channel in channels:
            if not channel.id:
                continue
            name = self._dedupe_name(self._attr(channel.name or f"Stream {channel.id[:8]}"), name_counts)
            attrs = [f'tvg-chno="{number}"', f'tvg-name="{name}"']
            number += 1
            epg_id = self.epg_ids.resolve(None, channel.tvg_id)
            if epg_id:
                attrs.append(f'tvg-id="{self._attr(epg_id)}"')
            if channel.logo:
                attrs.append(f'tvg-logo="{self._attr(channel.logo)}"')
            attrs.append(f'group-title="{self._attr(channel.group or "Unassigned Streams")}"')
            lines.append(f'#EXTINF:-1 {" ".join(attrs)},{name}')
            lines.extend(self._link_lines(self._stream_link(base_url, channel.id, pid_counter if addpid else None, stream_url=getattr(channel, 'stream_url', None), stream_headers=getattr(channel, 'stream_headers', None), live_base_url=self.live_base_url)))
            if addpid:
                pid_counter += 1
        return lines

    def _tv_channel_entries(
        self,
        tv_channels: List["TVChannel"],
        base_url: str,
        addpid: bool,
        pid_counter: int,
        name_counts: Dict[str, int],
        per_source: bool = False,
        source_ids: Optional[set[str]] = None,
    ):
        """Build EXTINF/link line pairs for TV channels with their assigned
        streams. Returns (lines, next_pid_counter, processed_acestream_ids).

        per_source adds each source under its relayed channel."""
        lines: List[str] = []
        processed_ids = set()

        for tv_channel in tv_channels:
            streams = [s for s in tv_channel.acestream_channels if s.id]
            if not streams:
                continue
            streams = sort_streams_curated(streams)
            stable = "{tv_channel_id}" in base_url
            sources = [stream for stream in streams
                       if source_ids is None or stream.id in source_ids] if stable and per_source else []
            if stable:
                processed_ids.update(stream.id for stream in streams)
                streams = streams[:1]
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
                epg_id = self.epg_ids.resolve(tv_channel.epg_source_id, tv_channel.epg_id) if tv_channel.epg_id else self.epg_ids.resolve(None, stream.tvg_id)
                if epg_id:
                    attrs.append(f'tvg-id="{self._attr(epg_id)}"')
                attrs.append(f'tvg-name="{display_name}"')
                if tv_channel.logo_url:
                    attrs.append(f'tvg-logo="{self._attr(tv_channel.logo_url)}"')
                elif stream.logo:
                    attrs.append(f'tvg-logo="{self._attr(stream.logo)}"')
                if tv_channel.category:
                    attrs.append(f'group-title="{self._attr(tv_channel.category)}"')

                lines.append(f'#EXTINF:-1 {" ".join(attrs)},{display_name}')
                # A stream with its own URL is handed out as that URL even in
                # a relay format: the TV relay only opens acestreams.
                link = self._stream_link(base_url, stream.id, pid_counter if addpid else None, tv_channel_id=tv_channel.id, stream_url=getattr(stream, 'stream_url', None), stream_headers=getattr(stream, 'stream_headers', None), live_base_url=self.live_base_url)
                lines.extend(self._link_lines(link))
                if addpid:
                    pid_counter += 1
            if sources:
                lines.extend(self._source_entries(tv_channel, sources, base_url, name_counts, epg_id))

        return lines, pid_counter, processed_ids

    @staticmethod
    def _score_acestream(stream: AcestreamChannel) -> int:
        """Rank a stream's quality for best-stream-first ordering.

        Thin alias over the shared helper (app.services.stream_ranking) so
        the playlist, tuner lineup and TV-channel API stay on one ranking.
        """
        return score_acestream(stream)

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
    def _m3u_header(epg_url: Optional[str] = None) -> str:
        """The #EXTM3U line, carrying url-tvg when the caller knows the guide.

        Without url-tvg a player has the channel ids but nowhere to fetch the
        guide from, so the EPG never shows up however well the ids match.
        """
        if not epg_url:
            return "#EXTM3U"
        return f'#EXTM3U url-tvg="{PlaylistService._attr(epg_url)}"'

    @staticmethod
    def _attr(value) -> str:
        """Sanitize a value for use inside a double-quoted EXTINF attribute.

        Thin alias over the shared helper (app.utils.m3u) so the curated
        playlists and the tuner playlist quote attributes identically.
        """
        return m3u_attr(value)

    def _link_lines(self, link: str) -> List[str]:
        """The lines that open a stream: its link, preceded by the mimetype
        when it goes through /live/ or the tuner relay.

        Without it IPTV Simple finds out the type by opening the link in
        Kodi's INTERFACE thread, twice. Against a broadcaster that does not
        answer, that left the remote dead for 16 s even with the 8 s budget
        on /live/; with the mimetype, 0 s (measured with a provider that never
        answers). Everything behind /live/ is HLS. Direct links to
        other CDNs may be MPEG-TS or anything else, so they are left alone.
        """
        from app.services import live_providers
        if self.live_base_url and link.startswith(f"{self.live_base_url.rstrip('/')}{live_providers.LIVE_PATH}"):
            return [LIVE_MIMETYPE_PROP, link]
        # The tuner relay always answers MPEG-TS, and opening an acestream
        # through it is when Kodi waits longest: a dead channel left the
        # remote dead for 13 s while it probed the type, 0 s with this line;
        # a live one showed video at 5.5 s instead of 8.5 s. Other link
        # formats are the user's and may be anything.
        # Only real HTTP relay paths (upstream 84ce59a): a user's link that
        # merely contains the words must not get the hint.
        try:
            parts = urlsplit(link)
        except ValueError:
            return [link]
        if (parts.scheme in ('http', 'https') and parts.netloc
                and re.search(r'/tuner/(?:channel|stream)/[^/]+\.ts$', parts.path)):
            return [RELAY_MIMETYPE_PROP, link]
        return [link]

    @staticmethod
    def _stream_link(base_url: str, channel_id: str, pid: Optional[int] = None, *, tv_channel_id: Optional[int] = None, stream_url: Optional[str] = None, stream_headers: Optional[dict] = None, live_base_url: Optional[str] = None) -> str:
        """Build a stream link from a base-URL pattern (#62).

        A pattern containing {channel_id} is rendered by substitution
        (with {pid} filled from the per-entry counter, or stripped when
        pids are disabled); a pattern without placeholders is a plain
        prefix, matching the legacy base_url behavior.

        A stream that carries its own `stream_url` -- an IPTV entry that is
        not an acestream id -- is emitted as that URL, untouched. Every base
        URL pattern assumes an engine that resolves an acestream id; applied
        here it would produce `...getstream?id=url:<sha1>`, which no engine
        can play.
        """
        if stream_url:
            from app.services import live_providers
            from app.services.hls_manifest import needs_manifest
            if live_base_url and needs_manifest(stream_url, stream_headers):
                # Its manifests are served by us, whole: ffmpeg reads them
                # cut short from the CDN. Segments still go straight to it.
                stream_url = f"{live_base_url.rstrip('/')}{live_providers.LIVE_PATH}{quote(str(channel_id), safe='')}"
            elif live_providers.for_stream_url(stream_url) is not None:
                # Its link expires: point the player at the route that signs
                # a new one when the channel is opened.
                if not live_base_url:
                    raise ValueError("A live channel needs the server's public address")
                stream_url = f"{live_base_url.rstrip('/')}{live_providers.LIVE_PATH}{quote(str(channel_id), safe='')}"
            return PlaylistService._with_headers(stream_url, stream_headers)
        if "{tv_channel_id}" in base_url:
            if tv_channel_id is None:
                raise ValueError("This relay format requires a TV channel assignment")
            return base_url.replace("{tv_channel_id}", str(tv_channel_id))
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

    # Kodi reads `url|Name=value&Name=value` and sends those headers itself,
    # to the playlist AND to every segment it fetches from the CDN. The values
    # must be percent-encoded: unescaped, Kodi cuts each one at its first
    # space, and a 120-character User-Agent arrives as `Mozilla/5.0`.
    _HEADER_ORDER = ("User-Agent", "Referer", "Origin")

    @staticmethod
    def _with_headers(url: str, headers: Optional[dict]) -> str:
        if not headers:
            return url
        from urllib.parse import quote
        parts = [f"{name}={quote(str(headers[name]), safe='')}"
                 for name in PlaylistService._HEADER_ORDER if headers.get(name)]
        if not parts:
            return url
        # A list may already carry some headers after its own `|`.
        return url + ("&" if "|" in url else "|") + "&".join(parts)

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

    def _generate_m3u_content(self, channels: List[AcestreamChannel], base_url: Optional[str] = None, format: Optional[str] = None, addpid: bool = False, epg_url: Optional[str] = None) -> str:
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
        header = self._m3u_header(epg_url) + "\n"

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
            tv = channel.tv_channel
            tvg_id = (self.epg_ids.resolve(tv.epg_source_id, tv.epg_id) if tv and tv.epg_id
                      else self.epg_ids.resolve(None, channel.tvg_id))
            if tvg_id:
                attrs.append(f'tvg-id="{self._attr(tvg_id)}"')

            # Generate entry
            entry = f'#EXTINF:-1 {" ".join(attrs)}, {channel.name}\n'

            link = self._stream_link(base_url, channel.id, pid_counter if addpid else None, stream_url=getattr(channel, 'stream_url', None), stream_headers=getattr(channel, 'stream_headers', None), live_base_url=self.live_base_url)
            entry += ''.join(line + '\n' for line in self._link_lines(link))

            entries.append(entry)
            if addpid:
                pid_counter += 1

        # Combine all parts
        return header + '\n'.join(entries)
