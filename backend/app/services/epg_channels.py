"""Channel queries, matching rules and retention. Shared session and service surface supplied by EPGService."""
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import EPGChannel, EPGProgram, EPGStringMapping, TVChannel
import logging

logger = logging.getLogger(__name__)


class EPGChannelOperations:
    db: Session

    def find_channel_by_xml_id_across_sources(self, channel_xml_id: str) -> Optional[EPGChannel]:
        """Find an EPG channel by channel_xml_id across all sources."""
        return self.db.query(EPGChannel).filter(EPGChannel.channel_xml_id == channel_xml_id).first()

    def get_channels(self, source_id: Optional[int] = None, skip: int = 0, limit: int = 50) -> Tuple[List[EPGChannel], int]:
        """Get paginated EPG channels, optionally filtered by source."""
        skip = max(skip, 0)
        limit = 50 if limit <= 0 else min(limit, 100)

        query = self.db.query(EPGChannel)

        if source_id is not None:
            query = query.filter(EPGChannel.epg_source_id == source_id)

        total = query.count()
        items = query.order_by(EPGChannel.name.asc(), EPGChannel.id.asc()).offset(skip).limit(limit).all()
        return items, total

    def get_channel(self, channel_id: int) -> Optional[EPGChannel]:
        """Get an EPG channel by ID"""
        return self.db.query(EPGChannel).filter(EPGChannel.id == channel_id).first()

    def get_channel_by_source_and_xml_id(self, source_id: int, channel_xml_id: str) -> Optional[EPGChannel]:
        """Resolve an EPG channel by source and XML identifier."""
        return (
            self.db.query(EPGChannel)
            .filter(
                EPGChannel.epg_source_id == source_id,
                EPGChannel.channel_xml_id == channel_xml_id,
            )
            .first()
        )

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

    def purge_expired_programs(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Delete programs that ended more than ``EPG_PROGRAM_RETENTION_HOURS`` ago.

        TV programming is only useful while it is current: the hourly refresh
        keeps adding upcoming programs, so without this the table grows
        forever. A negative retention disables the purge.
        """
        from app.config.settings import get_settings

        retention_hours = float(get_settings().EPG_PROGRAM_RETENTION_HOURS)
        if retention_hours < 0:
            return {"deleted": 0, "retention_hours": retention_hours, "cutoff": None, "disabled": True}

        now = now or datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=retention_hours)
        deleted = (
            self.db.query(EPGProgram)
            .filter(EPGProgram.end_time < cutoff)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        logger.info("Purged %s EPG programs that ended before %s", deleted, cutoff.isoformat())
        return {"deleted": int(deleted), "retention_hours": retention_hours, "cutoff": cutoff.isoformat(), "disabled": False}

    def get_all_string_mappings(self) -> List[EPGStringMapping]:
        """Get all EPG string mappings across all channels"""
        return self.db.query(EPGStringMapping).all()

    def auto_map_channels(self) -> Dict[str, Any]:
        """Auto-map TV channels to EPG channels based on string patterns (supports regex and case sensitivity)"""
        from app.services.epg_link_service import EPGLinkService
        links = EPGLinkService(self.db)
        repaired = links.repair()
        tv_channels = self.db.query(TVChannel).all()
        epg_channels = self.db.query(EPGChannel).all()
        mappings = self.db.query(EPGStringMapping).all()
        auto_mapped = []
        for tv in tv_channels:
            if links.available(tv):
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
            'auto_mapped_count': len(auto_mapped) + repaired,
            'auto_mapped': auto_mapped
        }
