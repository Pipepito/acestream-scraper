"""
Service for managing EPG operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
import xml.etree.ElementTree as ET
import requests
from datetime import datetime, timedelta
import html
import re

from app.models.models import EPGSource, EPGChannel, EPGProgram, EPGStringMapping, TVChannel
from app.schemas.epg import EPGSourceCreate, EPGSourceUpdate

logger = logging.getLogger(__name__)


class EPGService:
    def find_channel_by_xml_id_across_sources(self, channel_xml_id: str) -> Optional[EPGChannel]:
        """Find an EPG channel by channel_xml_id across all sources."""
        return self.db.query(EPGChannel).filter(EPGChannel.channel_xml_id == channel_xml_id).first()
    """Service for managing EPG operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_sources(self, skip: int = 0, limit: int = 100) -> List[EPGSource]:
        """Get all EPG sources"""
        return self.db.query(EPGSource).offset(skip).limit(limit).all()

    def get_enabled_sources(self) -> List[EPGSource]:
        """Get all enabled EPG sources"""
        return self.db.query(EPGSource).filter(EPGSource.enabled == True).all()

    def get_source(self, source_id: int) -> Optional[EPGSource]:
        """Get an EPG source by ID"""
        return self.db.query(EPGSource).filter(EPGSource.id == source_id).first()

    def create_source(self, source_data: EPGSourceCreate) -> EPGSource:
        """Create a new EPG source"""
        db_source = EPGSource(
            url=source_data.url,
            name=source_data.name,
            enabled=source_data.enabled
        )
        self.db.add(db_source)
        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def update_source(self, source_id: int, source_data: EPGSourceUpdate) -> Optional[EPGSource]:
        """Update an EPG source"""
        db_source = self.get_source(source_id)
        if not db_source:
            return None

        update_data = source_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_source, key, value)

        self.db.commit()
        self.db.refresh(db_source)
        return db_source

    def delete_source(self, source_id: int) -> bool:
        """Delete an EPG source"""
        db_source = self.get_source(source_id)
        if not db_source:
            return False

        self.db.delete(db_source)
        self.db.commit()
        return True

    async def refresh_source_async(self, source_id: int) -> Dict[str, Any]:
        """
        Refresh EPG data for a source (async version)

        Args:
            source_id: ID of the EPG source to refresh

        Returns:
            Dict with refresh results
        """
        # Call the synchronous version
        return self.refresh_source(source_id)

    def _process_epg_xml(self, source_id: int, xml_content: bytes) -> Tuple[int, int]:
        """
        Process EPG XML content and store in database

        Args:
            source_id: ID of the EPG source
            xml_content: XML content to process

        Returns:
            Tuple of (channels_found, programs_found)
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)

            # Track counts
            channels_found = 0
            programs_found = 0

            # First pass: Process channels
            for channel_elem in root.findall(".//channel"):
                channel_id = channel_elem.get("id", "")
                if not channel_id:
                    continue

                # Get channel display name
                display_name_elem = channel_elem.find("display-name")
                name = display_name_elem.text if display_name_elem is not None else channel_id

                # Get language from display-name attribute
                language = display_name_elem.get("lang") if display_name_elem is not None else None

                # Get icon URL
                icon_url = None
                icon_elem = channel_elem.find("icon")
                if icon_elem is not None:
                    icon_url = icon_elem.get("src")

                # Check if channel already exists
                db_channel = self.db.query(EPGChannel).filter(
                    and_(
                        EPGChannel.epg_source_id == source_id,
                        EPGChannel.channel_xml_id == channel_id
                    )
                ).first()

                if not db_channel:
                    # Create new channel
                    db_channel = EPGChannel(
                        epg_source_id=source_id,
                        channel_xml_id=channel_id,
                        name=name,
                        icon_url=icon_url,
                        language=language,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self.db.add(db_channel)
                    channels_found += 1
                else:
                    # Update existing channel
                    db_channel.name = name
                    db_channel.icon_url = icon_url
                    db_channel.language = language
                    db_channel.updated_at = datetime.now()

            # Commit channel changes to get IDs
            self.db.commit()

            # Get channel mapping for programs
            epg_channels = self.db.query(EPGChannel).filter(
                EPGChannel.epg_source_id == source_id
            ).all()
            channel_mapping = {ch.channel_xml_id: ch.id for ch in epg_channels}

            # Second pass: Process programs
            for program_elem in root.findall(".//programme"):
                channel_id = program_elem.get("channel", "")
                start_time_str = program_elem.get("start", "")
                stop_time_str = program_elem.get("stop", "")

                if not (channel_id and start_time_str and stop_time_str):
                    continue

                # Find channel ID
                epg_channel_id = channel_mapping.get(channel_id)
                if not epg_channel_id:
                    continue

                # Parse dates
                try:
                    start_time = self._parse_xmltv_time(start_time_str)
                    end_time = self._parse_xmltv_time(stop_time_str)
                except ValueError:
                    continue

                # Get program details
                title_elem = program_elem.find("title")
                title = title_elem.text if title_elem is not None else "Unknown Program"

                subtitle_elem = program_elem.find("sub-title")
                subtitle = subtitle_elem.text if subtitle_elem is not None else None

                desc_elem = program_elem.find("desc")
                description = desc_elem.text if desc_elem is not None else None

                category_elem = program_elem.find("category")
                category = category_elem.text if category_elem is not None else None

                # Get icon URL
                icon_elem = program_elem.find("icon")
                image_url = icon_elem.get("src") if icon_elem is not None else None

                # Check if program already exists
                db_program = self.db.query(EPGProgram).filter(
                    and_(
                        EPGProgram.epg_channel_id == epg_channel_id,
                        EPGProgram.start_time == start_time,
                        EPGProgram.end_time == end_time,
                        EPGProgram.title == title
                    )
                ).first()

                if not db_program:
                    # Create new program
                    db_program = EPGProgram(
                        epg_channel_id=epg_channel_id,
                        start_time=start_time,
                        end_time=end_time,
                        title=title,
                        subtitle=subtitle,
                        description=description,
                        category=category,
                        image_url=image_url
                    )
                    self.db.add(db_program)
                    programs_found += 1
                else:
                    # Update existing program
                    db_program.title = title
                    db_program.subtitle = subtitle
                    db_program.description = description
                    db_program.category = category
                    db_program.image_url = image_url

            # Commit all changes
            self.db.commit()

            return channels_found, programs_found

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing EPG XML: {str(e)}")
            raise

    def get_channels(self, source_id: Optional[int] = None, skip: int = 0, limit: int = 100) -> List[EPGChannel]:
        """Get EPG channels, optionally filtered by source"""
        query = self.db.query(EPGChannel)

        if source_id:
            query = query.filter(EPGChannel.epg_source_id == source_id)

        return query.offset(skip).limit(limit).all()

    def get_channel(self, channel_id: int) -> Optional[EPGChannel]:
        """Get an EPG channel by ID"""
        return self.db.query(EPGChannel).filter(EPGChannel.id == channel_id).first()

    def map_channel_to_tv(self, epg_channel_id: int, tv_channel_id: int) -> bool:
        """Map an EPG channel to a TV channel"""
        epg_channel = self.get_channel(epg_channel_id)
        tv_channel = self.db.query(TVChannel).filter(TVChannel.id == tv_channel_id).first()

        if not epg_channel or not tv_channel:
            return False

        tv_channel.epg_id = epg_channel.channel_xml_id
        tv_channel.epg_source_id = epg_channel.epg_source_id
        self.db.commit()

        return True

    def unmap_channel_from_tv(self, epg_channel_id: int, tv_channel_id: int) -> bool:
        """Remove mapping between EPG channel and TV channel"""
        epg_channel = self.get_channel(epg_channel_id)
        tv_channel = self.db.query(TVChannel).filter(TVChannel.id == tv_channel_id).first()

        if not epg_channel or not tv_channel:
            return False

        # Check if this TV channel is mapped to this EPG channel
        if tv_channel.epg_source_id != epg_channel.epg_source_id or tv_channel.epg_id != epg_channel.channel_xml_id:
            return False

        tv_channel.epg_id = None
        tv_channel.epg_source_id = None
        self.db.commit()

        return True

    def get_programs(
        self,
        channel_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[EPGProgram]:
        """Get programs for an EPG channel, optionally filtered by date range"""
        query = self.db.query(EPGProgram).filter(EPGProgram.epg_channel_id == channel_id)

        if start_date:
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(EPGProgram.start_time >= start_datetime)

        if end_date:
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(EPGProgram.end_time <= end_datetime)

        return query.order_by(EPGProgram.start_time).offset(skip).limit(limit).all()

    def get_string_mappings(self, channel_id: int) -> List[EPGStringMapping]:
        """Get string mappings for an EPG channel"""
        return (
            self.db.query(EPGStringMapping)
            .filter(EPGStringMapping.epg_channel_id == channel_id)
            .all()
        )

    def add_string_mapping(self, channel_id: int, search_pattern: str, is_exclusion: bool = False) -> EPGStringMapping:
        """Add a string mapping for an EPG channel"""
        db_mapping = EPGStringMapping(
            epg_channel_id=channel_id,
            search_pattern=search_pattern,
            is_exclusion=is_exclusion
        )
        self.db.add(db_mapping)
        self.db.commit()
        self.db.refresh(db_mapping)
        return db_mapping

    def update_string_mapping(self, mapping_id: int, search_pattern: str, is_exclusion: bool = False) -> Optional[EPGStringMapping]:
        """Update an existing EPG string mapping"""
        db_mapping = self.db.query(EPGStringMapping).filter(EPGStringMapping.id == mapping_id).first()
        if not db_mapping:
            return None
        db_mapping.search_pattern = search_pattern
        db_mapping.is_exclusion = is_exclusion
        self.db.commit()
        self.db.refresh(db_mapping)
        return db_mapping

    def delete_string_mapping(self, mapping_id: int) -> bool:
        """Delete a string mapping"""
        db_mapping = self.db.query(EPGStringMapping).filter(EPGStringMapping.id == mapping_id).first()
        if not db_mapping:
            return False

        self.db.delete(db_mapping)
        self.db.commit()
        return True

    def generate_epg_xml(self, search_term: Optional[str] = None, favorites_only: bool = False,
                         days_back: int = 1, days_forward: int = 7) -> str:
        """
        Generate XML EPG guide for channels with EPG data

        Args:
            search_term: Optional search term to filter channels by name
            favorites_only: If True, only include favorite channels
            days_back: Number of days in the past to include programs for
            days_forward: Number of days in the future to include programs for

        Returns:
            String containing the XML EPG content in XMLTV format
        """
        # Start with XML header and root element
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper EPG Generator" generator-info-url="https://github.com/pipepito/acestream-scraper">'
        ]

        # Get TV channels with filters
        tv_channels_query = self.db.query(TVChannel).filter(TVChannel.epg_id.isnot(None))

        if search_term:
            tv_channels_query = tv_channels_query.filter(TVChannel.name.ilike(f"%{search_term}%"))

        if favorites_only:
            tv_channels_query = tv_channels_query.filter(TVChannel.is_favorite == True)

        tv_channels = tv_channels_query.all()

        # Sort channels by channel_number
        sorted_channels = sorted(
            tv_channels,
            key=lambda c: (c.channel_number is None, c.channel_number or 0, c.name.lower())
        )

        # Track channels and their EPG mappings
        channel_epg_mappings = []
        name_counts = {}  # Track duplicate channel names

        # Process each TV channel
        for tv_channel in sorted_channels:
            # Skip channels without EPG ID or acestreams
            if not tv_channel.epg_id:
                continue

            # Get EPG channel for this TV channel
            epg_channel = self.db.query(EPGChannel).filter(
                and_(
                    EPGChannel.epg_source_id == tv_channel.epg_source_id,
                    EPGChannel.channel_xml_id == tv_channel.epg_id
                )
            ).first()

            if not epg_channel:
                continue

            # Create channel definition
            base_name = tv_channel.name

            # Handle duplicate names
            if base_name in name_counts:
                name_counts[base_name] += 1
                display_name = f"{base_name} {name_counts[base_name]}"
                epg_id = f"{tv_channel.epg_id}.{name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                display_name = base_name
                epg_id = tv_channel.epg_id

            # Store mapping for program generation
            channel_epg_mappings.append({
                'epg_id': epg_id,
                'display_name': display_name,
                'tv_channel': tv_channel,
                'epg_channel': epg_channel
            })

        # Generate channel definitions
        for mapping in channel_epg_mappings:
            epg_id = mapping['epg_id']
            display_name = mapping['display_name']
            tv_channel = mapping['tv_channel']

            xml_lines.append(f'  <channel id="{html.escape(epg_id)}">')
            xml_lines.append(f'    <display-name>{html.escape(display_name)}</display-name>')

            if tv_channel.logo_url:
                xml_lines.append(f'    <icon src="{html.escape(tv_channel.logo_url)}" />')

            xml_lines.append('  </channel>')

        # Add an empty line to separate channels from programs
        xml_lines.append('')

        # Calculate date range for programs
        now = datetime.utcnow()
        start_time = now - timedelta(days=days_back)
        end_time = now + timedelta(days=days_forward)

        # Get program data for each channel mapping
        for mapping in channel_epg_mappings:
            epg_id = mapping['epg_id']
            epg_channel = mapping['epg_channel']

            # Get programs for this channel
            programs = self.db.query(EPGProgram).filter(
                and_(
                    EPGProgram.epg_channel_id == epg_channel.id,
                    EPGProgram.start_time >= start_time,
                    EPGProgram.end_time <= end_time
                )
            ).order_by(EPGProgram.start_time).all()

            # Generate program entries
            for program in programs:
                # Format times in XMLTV format (YYYYMMDDHHMMSS +0000)
                start_time_str = program.start_time.strftime("%Y%m%d%H%M%S %z")
                stop_time_str = program.end_time.strftime("%Y%m%d%H%M%S %z")

                # Ensure timezone info is included
                if not '+' in start_time_str and not '-' in start_time_str:
                    start_time_str += ' +0000'
                if not '+' in stop_time_str and not '-' in stop_time_str:
                    stop_time_str += ' +0000'

                xml_lines.append(f'  <programme start="{start_time_str}" stop="{stop_time_str}" channel="{html.escape(epg_id)}">')
                xml_lines.append(f'    <title>{html.escape(program.title)}</title>')

                if program.subtitle:
                    xml_lines.append(f'    <sub-title>{html.escape(program.subtitle)}</sub-title>')

                if program.description:
                    xml_lines.append(f'    <desc>{html.escape(program.description)}</desc>')

                if program.category:
                    xml_lines.append(f'    <category>{html.escape(program.category)}</category>')

                if program.image_url:
                    xml_lines.append(f'    <icon src="{html.escape(program.image_url)}" />')

                xml_lines.append('  </programme>')

        # Close the XML document
        xml_lines.append('</tv>')

        return '\n'.join(xml_lines)

    def refresh_source(self, source_id: int) -> Dict[str, Any]:
        """
        Refresh EPG data for a specific source
        Returns a dictionary with refresh results
        """
        start_time = datetime.now()

        try:
            # Get the source
            source = self.get_source(source_id)
            if not source:
                return {
                    "source_id": source_id,
                    "success": False,
                    "error": "Source not found",
                    "channels_found": 0,
                    "programs_found": 0,
                    "duration_seconds": 0
                }

            if not source.enabled:
                return {
                    "source_id": source_id,
                    "success": False,
                    "error": "Source is disabled",
                    "channels_found": 0,
                    "programs_found": 0,
                    "duration_seconds": 0
                }

            logger.info(f"Refreshing EPG source: {source.name} ({source.url})")

            # Fetch EPG data from the source
            result = self._fetch_epg_from_source(source)

            # Update source status
            source.last_updated = datetime.now()
            if result["success"]:
                source.error_count = 0
                source.last_error = None
            else:
                source.error_count += 1
                source.last_error = result.get("error", "Unknown error")

            self.db.commit()

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            result["duration_seconds"] = duration

            logger.info(f"EPG refresh completed for source {source.name}: {result}")
            return result

        except Exception as e:
            logger.error(f"Error refreshing EPG source {source_id}: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            return {
                "source_id": source_id,
                "success": False,
                "error": str(e),
                "channels_found": 0,
                "programs_found": 0,
                "duration_seconds": duration
            }

    def refresh_all_sources(self) -> List[Dict[str, Any]]:
        """
        Refresh all enabled EPG sources
        Returns a list of refresh results
        """
        sources = self.get_enabled_sources()
        results = []

        for source in sources:
            result = self.refresh_source(source.id)
            results.append(result)

        return results

    def _fetch_epg_from_source(self, source: EPGSource) -> Dict[str, Any]:
        """
        Fetch and parse EPG data from a specific source
        Returns a dictionary with success status and counts
        """
        try:
            logger.info(f"Fetching EPG data from {source.url}")

            # Make HTTP request with timeout
            response = requests.get(source.url, timeout=60)
            response.raise_for_status()

            # Handle gzipped content
            content = response.content
            if source.url.endswith('.gz'):
                import gzip
                content = gzip.decompress(content)

            # Use the improved _process_epg_xml method
            channels_found, programs_found = self._process_epg_xml(source.id, content)

            return {
                "source_id": source.id,
                "success": True,
                "error": None,
                "channels_found": channels_found,
                "programs_found": programs_found
            }

        except requests.RequestException as e:
            return {
                "source_id": source.id,
                "success": False,
                "error": f"HTTP error: {str(e)}",
                "channels_found": 0,
                "programs_found": 0
            }
        except Exception as e:
            return {
                "source_id": source.id,
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "channels_found": 0,
                "programs_found": 0
            }

    def _parse_xmltv_time(self, time_str: str) -> datetime:
        """
        Parse XMLTV time format: YYYYMMDDHHMMSS +ZZZZ
        Examples: 20231201120000 +0000, 20231201120000
        """
        import re

        # Remove any extra whitespace
        time_str = time_str.strip()

        # Handle timezone information
        timezone_offset = 0
        if '+' in time_str:
            time_part, tz_part = time_str.split('+')
            time_part = time_part.strip()
            tz_part = tz_part.strip()

            # Parse timezone offset (format: HHMM or HH:MM)
            if len(tz_part) == 4:
                timezone_offset = int(tz_part[:2]) * 60 + int(tz_part[2:])
            elif len(tz_part) == 2:
                timezone_offset = int(tz_part) * 60
        elif '-' in time_str and not time_str.startswith('-'):
            time_part, tz_part = time_str.split('-')
            time_part = time_part.strip()
            tz_part = tz_part.strip()

            # Parse timezone offset (format: HHMM or HH:MM)
            if len(tz_part) == 4:
                timezone_offset = -(int(tz_part[:2]) * 60 + int(tz_part[2:]))
            elif len(tz_part) == 2:
                timezone_offset = -int(tz_part) * 60
        else:
            time_part = time_str

        # Parse the time part (format: YYYYMMDDHHMMSS)
        if len(time_part) == 14:
            # Full format: YYYYMMDDHHMMSS
            year = int(time_part[:4])
            month = int(time_part[4:6])
            day = int(time_part[6:8])
            hour = int(time_part[8:10])
            minute = int(time_part[10:12])
            second = int(time_part[12:14])
        elif len(time_part) == 12:
            # Format without seconds: YYYYMMDDHHMM
            year = int(time_part[:4])
            month = int(time_part[4:6])
            day = int(time_part[6:8])
            hour = int(time_part[8:10])
            minute = int(time_part[10:12])
            second = 0
        elif len(time_part) == 8:
            # Format without time: YYYYMMDD
            year = int(time_part[:4])
            month = int(time_part[4:6])
            day = int(time_part[6:8])
            hour = 0
            minute = 0
            second = 0
        else:
            raise ValueError(f"Invalid XMLTV time format: {time_str}")

        # Create datetime object
        dt = datetime(year, month, day, hour, minute, second)

        # Apply timezone offset (convert to UTC)
        if timezone_offset != 0:
            dt = dt - timedelta(minutes=timezone_offset)

        return dt

    def get_all_string_mappings(self) -> List[EPGStringMapping]:
        """Get all EPG string mappings across all channels"""
        return self.db.query(EPGStringMapping).all()

    def auto_map_channels(self) -> Dict[str, Any]:
        """Auto-map TV channels to EPG channels based on string patterns (supports regex and case sensitivity)"""
        tv_channels = self.db.query(TVChannel).all()
        epg_channels = self.db.query(EPGChannel).all()
        mappings = self.db.query(EPGStringMapping).all()
        auto_mapped = []
        for tv in tv_channels:
            if tv.epg_id and tv.epg_source_id:
                continue
            for mapping in mappings:
                pattern = mapping.search_pattern
                is_exclusion = mapping.is_exclusion
                epg_channel = next((ec for ec in epg_channels if ec.id == mapping.epg_channel_id), None)
                if not epg_channel:
                    continue
                # Advanced: regex support if pattern starts and ends with '/'
                is_regex = pattern.startswith('/') and pattern.endswith('/') and len(pattern) > 2
                case_sensitive = False  # Default to case-insensitive for now
                match_found = False
                if is_regex:
                    try:
                        regex_flags = 0 if case_sensitive else re.IGNORECASE
                        regex = re.compile(pattern[1:-1], flags=regex_flags)
                        match_found = bool(regex.search(tv.name))
                    except re.error:
                        continue  # Skip invalid regex
                else:
                    if case_sensitive:
                        match_found = pattern in tv.name
                    else:
                        match_found = pattern.lower() in tv.name.lower()
                # Exclusion logic
                if is_exclusion or (pattern.startswith('!')):
                    if match_found:
                        break  # Exclude this mapping
                    continue
                # Inclusion logic
                if match_found:
                    tv.epg_id = epg_channel.channel_xml_id
                    tv.epg_source_id = epg_channel.epg_source_id
                    auto_mapped.append({
                        'tv_channel_id': tv.id,
                        'tv_channel_name': tv.name,
                        'epg_channel_id': epg_channel.id,
                        'epg_channel_name': epg_channel.name,
                        'pattern': pattern,
                        'regex': is_regex,
                        'case_sensitive': case_sensitive
                    })
                    break
        self.db.commit()
        return {
            'auto_mapped_count': len(auto_mapped),
            'auto_mapped': auto_mapped
        }
