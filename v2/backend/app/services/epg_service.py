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

from app.models.models import EPGSource, EPGChannel, EPGProgram, EPGStringMapping, TVChannel
from app.schemas.epg import EPGSourceCreate, EPGSourceUpdate

logger = logging.getLogger(__name__)


class EPGService:
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
    
    async def refresh_source(self, source_id: int) -> Dict[str, Any]:
        """
        Refresh EPG data for a source
        
        Args:
            source_id: ID of the EPG source to refresh
            
        Returns:
            Dict with refresh results
        """
        start_time = datetime.now()
        
        source = self.get_source(source_id)
        if not source:
            return {
                "source_id": source_id,
                "success": False,
                "error": "EPG source not found"
            }
        
        if not source.enabled:
            return {
                "source_id": source_id,
                "success": False,
                "error": "EPG source is disabled"
            }
        
        try:
            # Download the EPG XML
            response = requests.get(source.url, timeout=60)
            response.raise_for_status()
            xml_content = response.content
            
            # Parse XML and process EPG data
            channels_found, programs_found = self._process_epg_xml(source.id, xml_content)
            
            # Update source last_updated timestamp
            source.last_updated = datetime.now()
            source.error_count = 0
            source.last_error = None
            self.db.commit()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "source_id": source_id,
                "success": True,
                "channels_found": channels_found,
                "programs_found": programs_found,
                "duration_seconds": duration
            }
            
        except Exception as e:
            logger.error(f"Error refreshing EPG source {source_id}: {str(e)}")
            
            # Update source error information
            source.error_count += 1
            source.last_error = str(e)
            self.db.commit()
            
            return {
                "source_id": source_id,
                "success": False,
                "error": str(e)
            }
    
    def _process_epg_xml(self, source_id: int, xml_content: bytes) -> Tuple[int, int]:
        """
        Process EPG XML content
        
        Args:
            source_id: ID of the EPG source
            xml_content: XML content to process
            
        Returns:
            Tuple of (channels_found, programs_found)
        """
        # This is a placeholder implementation
        # A full implementation would parse the XML and update the database
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Track counts
            channels_found = 0
            programs_found = 0
            
            # Process channels (simplified example)
            for channel_elem in root.findall(".//channel"):
                channel_id = channel_elem.get("id", "")
                if not channel_id:
                    continue
                
                # Get channel display name
                display_name_elem = channel_elem.find("display-name")
                name = display_name_elem.text if display_name_elem is not None else channel_id
                
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
                        icon_url=icon_url
                    )
                    self.db.add(db_channel)
                    self.db.flush()  # To get the channel ID
                else:
                    # Update existing channel
                    db_channel.name = name
                    db_channel.icon_url = icon_url
                    db_channel.updated_at = datetime.now()
                
                channels_found += 1
            
            # Process programs (simplified example)
            for program_elem in root.findall(".//programme"):
                channel_id = program_elem.get("channel", "")
                start_time_str = program_elem.get("start", "")
                stop_time_str = program_elem.get("stop", "")
                
                if not (channel_id and start_time_str and stop_time_str):
                    continue
                
                # Find channel
                db_channel = self.db.query(EPGChannel).filter(
                    and_(
                        EPGChannel.epg_source_id == source_id,
                        EPGChannel.channel_xml_id == channel_id
                    )
                ).first()
                
                if not db_channel:
                    continue
                
                # Parse dates (simplified)
                # In a real implementation, handle the XMLTV date format properly
                start_time = datetime.now()  # Placeholder
                end_time = datetime.now() + timedelta(hours=1)  # Placeholder
                
                # Get program details
                title_elem = program_elem.find("title")
                title = title_elem.text if title_elem is not None else "Unknown Program"
                
                desc_elem = program_elem.find("desc")
                description = desc_elem.text if desc_elem is not None else None
                
                # Check if program already exists
                db_program = self.db.query(EPGProgram).filter(
                    and_(
                        EPGProgram.epg_channel_id == db_channel.id,
                        EPGProgram.start_time == start_time,
                        EPGProgram.end_time == end_time
                    )
                ).first()
                
                if not db_program:
                    # Create new program
                    db_program = EPGProgram(
                        epg_channel_id=db_channel.id,
                        start_time=start_time,
                        end_time=end_time,
                        title=title,
                        description=description
                    )
                    self.db.add(db_program)
                else:
                    # Update existing program
                    db_program.title = title
                    db_program.description = description
                
                programs_found += 1
            
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
    
    def delete_string_mapping(self, mapping_id: int) -> bool:
        """Delete a string mapping"""
        db_mapping = self.db.query(EPGStringMapping).filter(EPGStringMapping.id == mapping_id).first()
        if not db_mapping:
            return False
        
        self.db.delete(db_mapping)
        self.db.commit()
        return True
