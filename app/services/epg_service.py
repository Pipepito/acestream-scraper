import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from app.models.acestream_channel import AcestreamChannel
from app.models.epg_source import EPGSource
from app.models.epg_string_mapping import EPGStringMapping
from app.repositories.epg_source_repository import EPGSourceRepository
from app.repositories.epg_string_mapping_repository import EPGStringMappingRepository
from app.repositories.channel_repository import ChannelRepository
from app.extensions import db

logger = logging.getLogger(__name__)

class EPGService:
    def __init__(self):
        self.epg_source_repo = EPGSourceRepository()
        self.epg_string_mapping_repo = EPGStringMappingRepository()
        self.channel_repo = ChannelRepository()
        self.epg_data = {}  # Cache of EPG data {tvg_id: {tvg_name, logo}}
        self.auto_mapping_threshold = 0.75  # Similarity threshold for auto-mapping
    
    def fetch_epg_data(self) -> Dict:
        """Fetch EPG data from all enabled sources."""
        self.epg_data = {}
        sources = self.epg_source_repo.get_enabled()
        
        for source in sources:
            try:
                logger.info(f"Fetching EPG data from {source.url}")
                response = requests.get(source.url, timeout=60)
                if response.status_code == 200:
                    self._parse_epg_xml(response.text)
                    # Update timestamp
                    source.last_updated = datetime.utcnow()
                    source.error_count = 0
                    source.last_error = None
                else:
                    error_msg = f"HTTP error {response.status_code}"
                    logger.warning(f"Error fetching EPG from {source.url}: {error_msg}")
                    source.error_count = source.error_count + 1 if source.error_count else 1
                    source.last_error = error_msg
            except Exception as e:
                logger.error(f"Error processing EPG from {source.url}: {str(e)}")
                source.error_count = source.error_count + 1 if source.error_count else 1
                source.last_error = str(e)
            
            # Save changes to the source
            self.epg_source_repo.update(source)
        
        logger.info(f"Loaded {len(self.epg_data)} channels from EPG sources")
        return self.epg_data
    
    def _parse_epg_xml(self, xml_content: str) -> None:
        """Parse EPG XML and extract channel information."""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract channel information
            for channel in root.findall(".//channel"):
                channel_id = channel.get("id")
                if not channel_id:
                    continue
                
                display_name_elem = channel.find("display-name")
                channel_name = display_name_elem.text if display_name_elem is not None else ""
                
                icon_elem = channel.find("icon")
                icon_url = icon_elem.get("src") if icon_elem is not None else ""
                
                self.epg_data[channel_id] = {
                    "tvg_id": channel_id,
                    "tvg_name": channel_name,
                    "logo": icon_url
                }
                
        except Exception as e:
            logger.error(f"Error parsing EPG XML: {str(e)}")
            raise
    
    def get_channel_epg_data(self, channel: AcestreamChannel) -> Dict:
        """
        Get EPG data for a specific channel with the following priority:
        1. Direct manual mapping in the channel table
        2. String pattern mapping in EPGStringMapping
        3. Automatic mapping by name similarity
        """
        # Ensure we have EPG data
        if not self.epg_data:
            self.fetch_epg_data()
        
        # 1. Check if it already has manual mapping in the table
        if channel.tvg_id and channel.tvg_id in self.epg_data:
            return self.epg_data[channel.tvg_id]
        
        # 2. Look for string pattern matches
        string_mappings = self.epg_string_mapping_repo.get_all()
        for mapping in string_mappings:
            if mapping.search_pattern.lower() in channel.name.lower() and mapping.epg_channel_id in self.epg_data:
                # Found a pattern match
                return self.epg_data[mapping.epg_channel_id]
        
        # 3. Try automatic mapping by similarity
        best_match = None
        best_score = 0
        
        for epg_id, epg_data in self.epg_data.items():
            score = SequenceMatcher(None, channel.name.lower(), epg_data["tvg_name"].lower()).ratio()
            if score > best_score and score >= self.auto_mapping_threshold:
                best_score = score
                best_match = epg_id
        
        if best_match:
            logger.info(f"Auto-mapped '{channel.name}' to '{self.epg_data[best_match]['tvg_name']}' (score: {best_score:.2f})")
            return self.epg_data[best_match]
        
        # If no match, return basic information
        return {
            "tvg_id": "",
            "tvg_name": channel.name,
            "logo": ""
        }
    
    def update_all_channels(self) -> Dict:
        """
        Update EPG metadata for all channels.
        Returns update statistics.
        """
        # First load EPG data if not loaded
        if not self.epg_data:
            self.fetch_epg_data()
        
        if not self.epg_data:
            return {"error": "No EPG data available", "updated": 0, "total": 0}
        
        # Get all active channels
        channels = self.channel_repo.get_active()
        updated_channels = 0
        tvg_id_updates = 0
        tvg_name_updates = 0
        logo_updates = 0
        
        # For each channel, try to find and apply EPG data
        for channel in channels:
            updates = self._update_channel_epg(channel)
            if updates[0]:  # If there was any update
                updated_channels += 1
                tvg_id_updates += 1 if updates[1] else 0
                tvg_name_updates += 1 if updates[2] else 0
                logo_updates += 1 if updates[3] else 0
        
        # Save changes to the database
        db.session.commit()
        
        return {
            "updated_channels": updated_channels,
            "total_channels": len(channels),
            "tvg_id_updates": tvg_id_updates,
            "tvg_name_updates": tvg_name_updates,
            "logo_updates": logo_updates
        }
    
    def _update_channel_epg(self, channel: AcestreamChannel) -> Tuple[bool, bool, bool, bool]:
        """
        Update EPG data for a channel.
        Returns a tuple of (updated, tvg_id_updated, tvg_name_updated, logo_updated)
        """
        updated = False
        tvg_id_updated = False
        tvg_name_updated = False
        logo_updated = False
        
        # 1. Look for pattern mappings
        string_mappings = self.epg_string_mapping_repo.get_all()
        for mapping in string_mappings:
            if mapping.search_pattern.lower() in channel.name.lower() and mapping.epg_channel_id in self.epg_data:
                epg_data = self.epg_data[mapping.epg_channel_id]
                updates = self._apply_epg_data(channel, epg_data)
                
                logger.info(f"Updated EPG for '{channel.name}' using pattern '{mapping.search_pattern}'")
                return (True, *updates)
        
        # 2. Try automatic mapping by similarity
        best_match = None
        best_score = 0
        
        for epg_id, epg_data in self.epg_data.items():
            score = SequenceMatcher(None, channel.name.lower(), epg_data["tvg_name"].lower()).ratio()
            if score > best_score and score >= self.auto_mapping_threshold:
                best_score = score
                best_match = epg_id
        
        if best_match:
            epg_data = self.epg_data[best_match]
            updates = self._apply_epg_data(channel, epg_data)
            
            logger.info(f"Updated EPG for '{channel.name}' using similarity match '{epg_data['tvg_name']}' (score: {best_score:.2f})")
            return (True, *updates)
            
        return (False, False, False, False)
    
    def _apply_epg_data(self, channel: AcestreamChannel, epg_data: Dict) -> Tuple[bool, bool, bool]:
        """
        Apply EPG data to the channel, respecting existing data.
        Returns a tuple of (tvg_id_updated, tvg_name_updated, logo_updated).
        """
        tvg_id_updated = False
        tvg_name_updated = False
        logo_updated = False
        
        # Update tvg_id if it doesn't exist
        if not channel.tvg_id and epg_data["tvg_id"]:
            channel.tvg_id = epg_data["tvg_id"]
            tvg_id_updated = True
        
        # Update tvg_name if it doesn't exist
        if not channel.tvg_name and epg_data["tvg_name"]:
            channel.tvg_name = epg_data["tvg_name"]
            tvg_name_updated = True
        
        # Update logo if it doesn't exist
        if not channel.logo and epg_data["logo"]:
            channel.logo = epg_data["logo"]
            logo_updated = True
            
        return (tvg_id_updated, tvg_name_updated, logo_updated)