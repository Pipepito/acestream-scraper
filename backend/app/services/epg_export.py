"""Playlist-aware XMLTV export and program windows. Shared session and service surface supplied by EPGService."""
import html
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import EPGChannel, EPGProgram, TVChannel


class EPGExportOperations:
    db: Session

    def generate_epg_xml(self, search_term: Optional[str] = None, favorites_only: bool = False,
                         days_back: int = 1, days_forward: int = 7,
                         tv_channel_ids: Optional[List[int]] = None) -> str:
        """Generate the XMLTV guide for TV channels that have EPG data.

        Args:
            search_term: Optional search term to filter channels by name
            favorites_only: If True, only include favorite channels
            days_back: Number of days in the past to include programs for
            days_forward: Number of days in the future to include programs for
            tv_channel_ids: Restrict the export to these TV channels (the tuner
                lineup uses it); None keeps the historical output unchanged.

        Returns:
            String containing the XML EPG content in XMLTV format
        """
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper EPG Generator" generator-info-url="https://github.com/pipepito/acestream-scraper">'
        ]

        tv_channels_query = self.db.query(TVChannel).filter(TVChannel.epg_id.isnot(None))

        if search_term:
            tv_channels_query = tv_channels_query.filter(TVChannel.name.ilike(f"%{search_term}%"))

        if favorites_only:
            tv_channels_query = tv_channels_query.filter(TVChannel.is_favorite == True)

        if tv_channel_ids is not None:
            tv_channels_query = tv_channels_query.filter(TVChannel.id.in_(list(tv_channel_ids)))

        sorted_channels = sorted(
            tv_channels_query.all(),
            key=lambda c: (c.channel_number is None, c.channel_number or 0, c.name.lower())
        )
        epg_lookup = self.epg_channel_lookup(sorted_channels)

        from app.services.epg_identity_service import EPGIdentityService
        identities = EPGIdentityService(self.db)
        channel_epg_mappings = []
        emitted = set()

        for tv_channel in sorted_channels:
            if not tv_channel.epg_id:
                continue
            epg_channel = epg_lookup.get((tv_channel.epg_source_id, tv_channel.epg_id))
            if epg_channel is None:
                continue

            epg_id = identities.resolve(tv_channel.epg_source_id, tv_channel.epg_id)
            if epg_id in emitted:
                continue
            emitted.add(epg_id)
            display_name = tv_channel.name

            channel_epg_mappings.append({
                'epg_id': epg_id,
                'display_name': display_name,
                'tv_channel': tv_channel,
                'epg_channel': epg_channel
            })

        # Generate channel definitions
        for mapping in channel_epg_mappings:
            tv_channel = mapping['tv_channel']

            xml_lines.append(f'  <channel id="{html.escape(mapping["epg_id"])}">')
            xml_lines.append(f'    <display-name>{html.escape(mapping["display_name"])}</display-name>')

            if tv_channel.logo_url:
                xml_lines.append(f'    <icon src="{html.escape(tv_channel.logo_url)}" />')

            xml_lines.append('  </channel>')

        xml_lines.append('')

        programs_by_channel = self.programs_in_window(
            [mapping['epg_channel'].id for mapping in channel_epg_mappings],
            days_back,
            days_forward,
        )
        for mapping in channel_epg_mappings:
            for program in programs_by_channel.get(mapping['epg_channel'].id, []):
                xml_lines.extend(self.programme_xml_lines(program, mapping['epg_id']))

        xml_lines.append('</tv>')

        return '\n'.join(xml_lines)

    def epg_channel_lookup(self, tv_channels: List[TVChannel]) -> Dict[Tuple[Optional[int], str], EPGChannel]:
        """Map (epg_source_id, channel_xml_id) to the EPG channel each TV channel points at."""
        source_ids = {channel.epg_source_id for channel in tv_channels if channel.epg_source_id is not None}
        xml_ids = {channel.epg_id for channel in tv_channels if channel.epg_id}
        if not source_ids or not xml_ids:
            return {}
        epg_channels = (
            self.db.query(EPGChannel)
            .filter(
                EPGChannel.epg_source_id.in_(source_ids),
                EPGChannel.channel_xml_id.in_(xml_ids),
            )
            .all()
        )
        return {
            (epg_channel.epg_source_id, epg_channel.channel_xml_id): epg_channel
            for epg_channel in epg_channels
        }

    def programs_in_window(self, epg_channel_ids: List[int], days_back: int = 1,
                           days_forward: int = 7) -> Dict[int, List[EPGProgram]]:
        """Programs inside the export window, grouped by EPG channel id and ordered by start time."""
        if not epg_channel_ids:
            return {}
        now = datetime.now(timezone.utc)
        programs = (
            self.db.query(EPGProgram)
            .filter(
                EPGProgram.epg_channel_id.in_(epg_channel_ids),
                EPGProgram.start_time >= now - timedelta(days=days_back),
                EPGProgram.end_time <= now + timedelta(days=days_forward),
            )
            .order_by(EPGProgram.epg_channel_id, EPGProgram.start_time)
            .all()
        )
        programs_by_channel: Dict[int, List[EPGProgram]] = {}
        for program in programs:
            programs_by_channel.setdefault(program.epg_channel_id, []).append(program)
        return programs_by_channel

    @staticmethod
    def programme_xml_lines(program: EPGProgram, channel_id: str) -> List[str]:
        """The XMLTV <programme> block for one program, filed under channel_id."""
        start_time_str = program.start_time.strftime("%Y%m%d%H%M%S %z")
        stop_time_str = program.end_time.strftime("%Y%m%d%H%M%S %z")

        if '+' not in start_time_str and '-' not in start_time_str:
            start_time_str += ' +0000'
        if '+' not in stop_time_str and '-' not in stop_time_str:
            stop_time_str += ' +0000'

        lines = [
            f'  <programme start="{start_time_str}" stop="{stop_time_str}" channel="{html.escape(channel_id)}">',
            f'    <title>{html.escape(program.title)}</title>',
        ]

        if program.subtitle:
            lines.append(f'    <sub-title>{html.escape(program.subtitle)}</sub-title>')

        if program.description:
            lines.append(f'    <desc>{html.escape(program.description)}</desc>')

        if program.category:
            lines.append(f'    <category>{html.escape(program.category)}</category>')

        if program.image_url:
            lines.append(f'    <icon src="{html.escape(program.image_url)}" />')

        lines.append('  </programme>')
        return lines
