"""HDHomeRun-style tuner lineup and settings (spec 7.2)."""
from __future__ import annotations

import hashlib
import html
import secrets
from dataclasses import dataclass, field
from typing import List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import EPGSource, TVChannel
from app.repositories.channel_repository import ChannelRepository
from app.repositories.settings_repository import SettingsRepository
from app.services.epg_service import EPGService
from app.services.stream_ranking import sort_streams_curated
from app.utils.m3u import m3u_attr

# libhdhomerun's device-id checksum table, verbatim.
_LOOKUP = [0xA, 0x5, 0xF, 0x6, 0x7, 0xC, 0x1, 0xB, 0x9, 0x2, 0x8, 0xD, 0x4, 0x3, 0xE, 0x0]

MIN_TUNER_COUNT, MAX_TUNER_COUNT = 1, 16
MIN_MAX_CHANNELS, MAX_MAX_CHANNELS = 1, 1000


def hdhr_device_id_valid(device_id: str) -> bool:
    """libhdhomerun's nibble checksum: odd positions (MSB first) go through the lookup table."""
    if len(device_id) != 8:
        return False
    try:
        value = int(device_id, 16)
    except ValueError:
        return False
    checksum = 0
    for position in range(7, -1, -1):
        nibble = (value >> (position * 4)) & 0xF
        checksum ^= _LOOKUP[nibble] if position % 2 == 1 else nibble
    return checksum == 0


def generate_hdhr_device_id() -> str:
    """A random id Jellyfin and Plex accept: seven random nibbles plus the
    checksum nibble that makes hdhr_device_id_valid() true."""
    while True:
        value = secrets.randbits(28) << 4  # seven random nibbles, last nibble computed
        checksum = 0
        for position in range(7, 0, -1):
            nibble = (value >> (position * 4)) & 0xF
            checksum ^= _LOOKUP[nibble] if position % 2 == 1 else nibble
        device_id = f"{value | checksum:08X}"
        if device_id[0] != "0" and hdhr_device_id_valid(device_id):
            return device_id


@dataclass
class TunerSettings:
    friendly_name: str
    tuner_count: int
    max_channels: int
    only_online: bool


@dataclass
class LineupEntry:
    guide_number: str
    guide_name: str
    content_id: str
    tv_channel_id: int
    epg_id: Optional[str]
    epg_source_id: Optional[int]
    logo_url: Optional[str]
    category: Optional[str]
    requested_number: Optional[int]


@dataclass
class Renumbered:
    tv_channel_id: int
    name: str
    requested_number: int
    assigned_number: int


@dataclass
class Lineup:
    entries: List[LineupEntry] = field(default_factory=list)
    renumbered: List[Renumbered] = field(default_factory=list)
    overflow: int = 0


class TunerService:
    def __init__(self, db: Session):
        self.db = db
        self.settings_repo = SettingsRepository(db)

    # --- settings -----------------------------------------------------------
    def settings(self) -> TunerSettings:
        repo = self.settings_repo
        return TunerSettings(
            friendly_name=repo.get_setting(SettingsRepository.TUNER_FRIENDLY_NAME) or SettingsRepository.DEFAULT_TUNER_FRIENDLY_NAME,
            tuner_count=int(repo.get_setting(SettingsRepository.TUNER_COUNT) or SettingsRepository.DEFAULT_TUNER_COUNT),
            max_channels=int(repo.get_setting(SettingsRepository.TUNER_MAX_CHANNELS) or SettingsRepository.DEFAULT_TUNER_MAX_CHANNELS),
            only_online=str(repo.get_setting(SettingsRepository.TUNER_ONLY_ONLINE) or "false").lower() in ("true", "1"),
        )

    def update_settings(self, *, friendly_name: Optional[str] = None, tuner_count: Optional[int] = None,
                        max_channels: Optional[int] = None, only_online: Optional[bool] = None) -> TunerSettings:
        repo = self.settings_repo
        if friendly_name is not None:
            repo.set_setting(SettingsRepository.TUNER_FRIENDLY_NAME, friendly_name.strip() or SettingsRepository.DEFAULT_TUNER_FRIENDLY_NAME, "Tuner name shown in Jellyfin/Plex")
        if tuner_count is not None:
            repo.set_setting(SettingsRepository.TUNER_COUNT, str(max(MIN_TUNER_COUNT, min(MAX_TUNER_COUNT, int(tuner_count)))), "Concurrent tuner streams advertised")
        if max_channels is not None:
            repo.set_setting(SettingsRepository.TUNER_MAX_CHANNELS, str(max(MIN_MAX_CHANNELS, min(MAX_MAX_CHANNELS, int(max_channels)))), "Maximum channels in the tuner lineup")
        if only_online is not None:
            repo.set_setting(SettingsRepository.TUNER_ONLY_ONLINE, "true" if only_online else "false", "Hide channels whose streams are all offline")
        return self.settings()

    def device_id(self) -> str:
        """The advertised HDHomeRun DeviceID, generated and persisted once: a
        media server identifies the tuner by it, so it must never change."""
        current = (self.settings_repo.get_setting(SettingsRepository.TUNER_DEVICE_ID) or "").strip().upper()
        if hdhr_device_id_valid(current):
            return current
        generated = generate_hdhr_device_id()
        self.settings_repo.set_setting(SettingsRepository.TUNER_DEVICE_ID, generated, "HDHomeRun device id advertised to Jellyfin/Plex")
        return generated

    # --- lineup -------------------------------------------------------------
    def build_lineup(self) -> Lineup:
        """Active TV channels with at least one stream, in curated playlist
        order, each on a GuideNumber no other channel claims."""
        settings = self.settings()
        channels: List[TVChannel] = ChannelRepository(self.db).get_playlist_tv_channels()
        candidates = []
        for tv in channels:
            streams = [s for s in tv.acestream_channels if s.id]
            if not streams:
                continue
            if settings.only_online and not any(s.is_online for s in streams):
                continue
            candidates.append((tv, sort_streams_curated(streams)[0]))

        # Above every manual number in the database — not just the ones in this
        # lineup: an automatic number is the channel's identity in Jellyfin and
        # Plex (GuideNumber, and the XMLTV channel id the guide is keyed on), so
        # it must not move when an unrelated channel drops out of the lineup
        # because its streams went offline, it was deactivated, or the daily
        # cleanup removed its last stream.
        highest_manual = self.db.query(func.max(TVChannel.channel_number)).scalar()
        fallback_base = max(1000, int(highest_manual or 0) + 1)
        taken: Set[int] = set()
        lineup = Lineup()
        for tv, best in candidates:
            requested = tv.channel_number
            if requested is not None and requested not in taken:
                number = requested
            else:
                number = fallback_base + tv.id
                if requested is not None:
                    lineup.renumbered.append(Renumbered(tv_channel_id=tv.id, name=tv.name, requested_number=requested, assigned_number=number))
            taken.add(number)
            lineup.entries.append(LineupEntry(
                guide_number=str(number), guide_name=tv.name, content_id=best.id, tv_channel_id=tv.id,
                epg_id=tv.epg_id, epg_source_id=tv.epg_source_id, logo_url=tv.logo_url or best.logo, category=tv.category,
                requested_number=requested,
            ))
        if len(lineup.entries) > settings.max_channels:
            lineup.overflow = len(lineup.entries) - settings.max_channels
            lineup.entries = lineup.entries[: settings.max_channels]
        return lineup

    @staticmethod
    def lineup_fingerprint(lineup: Lineup) -> str:
        """Changes whenever a media server would have to re-read the lineup."""
        digest = hashlib.sha256()
        for entry in lineup.entries:
            digest.update(f"{entry.guide_number}|{entry.guide_name}|{entry.content_id}\n".encode("utf-8"))
        return digest.hexdigest()

    def guide_fingerprint(self) -> str:
        """Changes on every EPG refresh and on source add/remove/enable. A source
        that failed its last refresh is ignored: its stamp says nothing new."""
        rows = (
            self.db.query(EPGSource.id, EPGSource.last_updated)
            .filter(EPGSource.enabled == True, EPGSource.last_error.is_(None))  # noqa: E712
            .order_by(EPGSource.id)
            .all()
        )
        digest = hashlib.sha256()
        for source_id, last_updated in rows:
            digest.update(f"{source_id}|{last_updated.isoformat() if last_updated else ''}\n".encode("utf-8"))
        return digest.hexdigest()

    # --- exports ------------------------------------------------------------
    def build_guide_xml(self, lineup: Lineup, days_back: int = 1, days_forward: int = 7) -> str:
        """XMLTV whose channel ids are the lineup's GuideNumbers, which is how
        Jellyfin and Plex match an HDHomeRun lineup to its guide."""
        epg = EPGService(self.db)
        tv_channels = (
            self.db.query(TVChannel)
            .filter(TVChannel.id.in_([entry.tv_channel_id for entry in lineup.entries]))
            .all()
            if lineup.entries
            else []
        )
        lookup = epg.epg_channel_lookup(tv_channels)

        lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper Tuner Guide" generator-info-url="https://github.com/pipepito/acestream-scraper">',
        ]
        mapped = []
        for entry in lineup.entries:
            lines.append(f'  <channel id="{entry.guide_number}">')
            # Three display names: media servers match on any of the three forms.
            lines.append(f'    <display-name>{entry.guide_number} {html.escape(entry.guide_name)}</display-name>')
            lines.append(f'    <display-name>{entry.guide_number}</display-name>')
            lines.append(f'    <display-name>{html.escape(entry.guide_name)}</display-name>')
            if entry.logo_url:
                lines.append(f'    <icon src="{html.escape(entry.logo_url)}" />')
            lines.append('  </channel>')
            epg_channel = lookup.get((entry.epg_source_id, entry.epg_id)) if entry.epg_id else None
            if epg_channel is not None:
                mapped.append((entry, epg_channel))
        lines.append('')

        programs = epg.programs_in_window([channel.id for _, channel in mapped], days_back, days_forward)
        for entry, epg_channel in mapped:
            for program in programs.get(epg_channel.id, []):
                lines.extend(epg.programme_xml_lines(program, entry.guide_number))
        lines.append('</tv>')
        return '\n'.join(lines)

    @staticmethod
    def build_playlist_m3u(lineup: Lineup, public_base_url: str) -> str:
        """M3U for Jellyfin's M3U tuner: tvg-id keeps the upstream EPG id, and
        every stream URL points at the relay rather than at the engine."""
        base = public_base_url.rstrip('/')
        lines = ["#EXTM3U"]
        for entry in lineup.entries:
            attrs = []
            if entry.epg_id:
                attrs.append(f'tvg-id="{m3u_attr(entry.epg_id)}"')
            attrs.append(f'tvg-chno="{entry.guide_number}"')
            attrs.append(f'tvg-name="{m3u_attr(entry.guide_name)}"')
            if entry.logo_url:
                attrs.append(f'tvg-logo="{m3u_attr(entry.logo_url)}"')
            if entry.category:
                attrs.append(f'group-title="{m3u_attr(entry.category)}"')
            lines.append(f'#EXTINF:-1 {" ".join(attrs)},{m3u_attr(entry.guide_name)}')
            lines.append(f"{base}/tuner/stream/{entry.content_id}.ts")
        return "\n".join(lines) + "\n"
