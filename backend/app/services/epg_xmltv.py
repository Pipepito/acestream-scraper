"""XMLTV parsing and incremental program reconciliation. Shared session and service surface supplied by EPGService."""
from bisect import bisect_left
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Tuple
from sqlalchemy.orm import Session
from app.models.models import EPGChannel, EPGProgram
import logging

logger = logging.getLogger(__name__)


class XMLTVProcessing:
    db: Session

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
            root = ET.fromstring(xml_content)
            channels_found = 0
            programs_found = 0

            existing_channels = (
                self.db.query(EPGChannel)
                .filter(EPGChannel.epg_source_id == source_id)
                .all()
            )
            channel_mapping = {channel.channel_xml_id: channel for channel in existing_channels}

            for channel_elem in root.findall(".//channel"):
                channel_id = channel_elem.get("id", "")
                if not channel_id:
                    continue

                display_name_elem = channel_elem.find("display-name")
                name = display_name_elem.text if display_name_elem is not None else channel_id
                language = display_name_elem.get("lang") if display_name_elem is not None else None

                icon_url = None
                icon_elem = channel_elem.find("icon")
                if icon_elem is not None:
                    icon_url = icon_elem.get("src")

                db_channel = channel_mapping.get(channel_id)
                if not db_channel:
                    db_channel = EPGChannel(
                        epg_source_id=source_id,
                        channel_xml_id=channel_id,
                        name=name,
                        icon_url=icon_url,
                        language=language,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    self.db.add(db_channel)
                    channel_mapping[channel_id] = db_channel
                    channels_found += 1
                else:
                    db_channel.name = name
                    db_channel.icon_url = icon_url
                    db_channel.language = language
                    db_channel.updated_at = datetime.now(timezone.utc)

            # Existing channel IDs are already available. Avoid taking SQLite's
            # writer lock while parsing/diffing a large replacement guide.
            if channels_found:
                self.db.flush()
            channel_id_map = {xml_id: channel.id for xml_id, channel in channel_mapping.items()}

            existing_programs = (
                self.db.query(EPGProgram)
                .filter(EPGProgram.epg_channel_id.in_(channel_id_map.values()))
                .all()
                if channel_id_map
                else []
            )
            existing_program_map = {
                (program.epg_channel_id, program.start_time, program.end_time, program.title): program
                for program in existing_programs
            }

            incoming_keys = set()
            incoming_intervals = {}
            for program_elem in root.findall(".//programme"):
                channel_id = program_elem.get("channel", "")
                start_time_str = program_elem.get("start", "")
                stop_time_str = program_elem.get("stop", "")

                if not (channel_id and start_time_str and stop_time_str):
                    continue

                epg_channel_id = channel_id_map.get(channel_id)
                if not epg_channel_id:
                    continue

                try:
                    start_time = self._parse_xmltv_time(start_time_str)
                    end_time = self._parse_xmltv_time(stop_time_str)
                except ValueError:
                    continue

                if end_time <= start_time:
                    continue

                title_elem = program_elem.find("title")
                title = title_elem.text if title_elem is not None else "Unknown Program"

                subtitle_elem = program_elem.find("sub-title")
                subtitle = subtitle_elem.text if subtitle_elem is not None else None

                desc_elem = program_elem.find("desc")
                description = desc_elem.text if desc_elem is not None else None

                category_elem = program_elem.find("category")
                category = category_elem.text if category_elem is not None else None

                icon_elem = program_elem.find("icon")
                image_url = icon_elem.get("src") if icon_elem is not None else None

                program_key = (epg_channel_id, start_time, end_time, title)
                incoming_keys.add(program_key)
                incoming_intervals.setdefault(epg_channel_id, []).append((start_time, end_time))
                db_program = existing_program_map.get(program_key)

                if not db_program:
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
                    existing_program_map[program_key] = db_program
                    programs_found += 1
                else:
                    db_program.title = title
                    db_program.subtitle = subtitle
                    db_program.description = description
                    db_program.category = category
                    db_program.image_url = image_url

            # Replace superseded listings only where this feed supplies valid coverage.
            # Preserve gaps, absent channels and other sources; an empty feed deletes nothing.
            coverage = {}
            for channel_id, intervals in incoming_intervals.items():
                merged = []
                for start, end in sorted(intervals):
                    if merged and start <= merged[-1][1]:
                        merged[-1] = (merged[-1][0], max(merged[-1][1], end))
                    else:
                        merged.append((start, end))
                coverage[channel_id] = ([start for start, _ in merged], [end for _, end in merged])
            for program in existing_programs:
                key = (program.epg_channel_id, program.start_time, program.end_time, program.title)
                if key in incoming_keys:
                    if existing_program_map[key] is not program:
                        self.db.delete(program)
                    continue
                intervals = coverage.get(program.epg_channel_id)
                if intervals:
                    starts, ends = intervals
                    index = bisect_left(starts, program.end_time) - 1
                    if index >= 0 and ends[index] > program.start_time:
                        self.db.delete(program)

            from app.services.epg_link_service import EPGLinkService
            EPGLinkService(self.db).repair()
            self.db.commit()
            return channels_found, programs_found

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing EPG XML: {str(e)}")
            raise

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

        # Create the datetime as UTC. ``timezone_offset`` is the offset of the
        # source clock relative to UTC; subtracting it converts the local time
        # back to the UTC instant. Returned datetimes are timezone-aware so
        # they round-trip equality against values reloaded from the DB
        # through ``UtcDateTime`` in ``app/models/models.py``.
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)

        if timezone_offset != 0:
            dt = dt - timedelta(minutes=timezone_offset)

        return dt
