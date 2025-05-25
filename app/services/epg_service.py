import requests
import xml.etree.ElementTree as ET
import logging
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
import re
import os
import time

from app.models.acestream_channel import AcestreamChannel
from app.models.epg_source import EPGSource
from app.models.epg_string_mapping import EPGStringMapping
from app.models.epg_program import EPGProgram
from app.repositories.epg_source_repository import EPGSourceRepository
from app.repositories.epg_string_mapping_repository import EPGStringMappingRepository
from app.repositories.channel_repository import ChannelRepository
from app.repositories.epg_channel_repository import EPGChannelRepository
from app.repositories.epg_program_repository import EPGProgramRepository
from app.extensions import db

logger = logging.getLogger(__name__)

class EPGService:    
    def __init__(self):
        self.epg_source_repo = EPGSourceRepository()
        self.epg_string_mapping_repo = EPGStringMappingRepository()
        self.channel_repo = ChannelRepository()
        self.epg_channel_repo = EPGChannelRepository()
        self.epg_program_repo = EPGProgramRepository()
        self.epg_data = {}  # Cache of EPG data {tvg_id: {tvg_name, logo}}
        self.auto_mapping_threshold = 0.75  # Similarity threshold for auto-mapping
        self.data_dir = "data"  # Directory to store data files (e.g., timestamps)
    
    def fetch_epg_data(self) -> Dict:
        """Fetch EPG data from all enabled sources."""
        self.epg_data = {}  # Reset cache
        
        # Get ENABLED sources only
        sources = self.epg_source_repo.get_enabled()
        
        logger.info(f"Found {len(sources)} enabled EPG sources")
        
        total_channels = 0
        
        for source in sources:
            try:
                logger.info(f"Fetching EPG data from {source.url}")
                response = requests.get(source.url, timeout=60)
                if response.status_code == 200:
                    # Parse the XML content
                    xml_content = response.text
                    source.cached_data = xml_content
                    
                    # Prepare for bulk insertion
                    channels_to_insert = []
                    
                    # Use original method to parse EPG XML and populate cache
                    self._parse_epg_xml(xml_content, source.id)
                    
                    # Prepare channel data for database storage
                    for channel_id, channel_data in self.epg_data.items():
                        if channel_data.get('source_id') == source.id:
                            # Create dictionary for database insertion
                            # Fix field names to match EPGChannel model
                            channel_db_data = {
                                'epg_source_id': source.id,
                                'channel_xml_id': channel_id,
                                'name': channel_data.get('tvg_name', ''), 
                                'icon_url': channel_data.get('logo', ''),
                                'language': channel_data.get('language')
                            }
                            channels_to_insert.append(channel_db_data)
                    
                    # Bulk insert channels to database
                    if channels_to_insert:
                        # First delete existing channels for this source
                        self.epg_channel_repo.delete_by_source_id(source.id)
                        # Then insert new ones
                        inserted_count = self.epg_channel_repo.bulk_insert(channels_to_insert)
                        logger.info(f"Bulk inserted {inserted_count} channels from source {source.id}")
                    
                    # Update last_updated timestamp for this source
                    source.last_updated = datetime.now()
                    self.epg_source_repo.update(source)
                    logger.info(f"Updated last_updated timestamp for source {source.id} to {source.last_updated.isoformat()}")
            
            except Exception as e:
                logger.error(f"Error fetching EPG data from {source.url}: {e}")
    
        return self.epg_data    
    
    def _parse_epg_xml(self, xml_content: str, source_id: int) -> None:
        try:
            root = ET.fromstring(xml_content)
            
            # Extract channel information
            for channel in root.findall(".//channel"):
                channel_id = channel.get("id")
                if not channel_id:
                    continue
                
                # Get the display name
                display_name_elem = channel.find("display-name")
                channel_name = display_name_elem.text if display_name_elem is not None else ""
                
                # Get language from the display-name attribute
                language = display_name_elem.get("lang") if display_name_elem is not None else None
                
                # Get icon URL
                icon_elem = channel.find("icon")
                icon_url = icon_elem.get("src") if icon_elem is not None else ""
                
                self.epg_data[channel_id] = {
                    "tvg_id": channel_id,
                    "tvg_name": channel_name,
                    "logo": icon_url,
                    "source_id": source_id,  # Store the source ID
                    "language": language     # Store the language
                }
              # Parse program data and store in database
            self._parse_and_store_programs(root, source_id)
                
        except Exception as e:
            logger.error(f"Error parsing EPG XML: {str(e)}")
            raise

    def _parse_and_store_programs(self, xml_root, source_id: int) -> None:
        """Parse program data from EPG XML and store in database."""
        try:
            from datetime import datetime
            import re
            
            # First, get all EPG channels for this source to create a mapping
            epg_channels = self.epg_channel_repo.get_by_source_id(source_id)
            channel_mapping = {ch.channel_xml_id: ch.id for ch in epg_channels}
            
            # Clear existing programs for this source
            self.epg_program_repo.delete_by_source_id(source_id)
            
            programs_to_insert = []
            
            # Extract program information
            for programme in xml_root.findall(".//programme"):
                channel_xml_id = programme.get("channel")
                start_str = programme.get("start")
                stop_str = programme.get("stop")
                
                if not all([channel_xml_id, start_str, stop_str]):
                    continue
                
                # Check if we have this channel in our database
                epg_channel_id = channel_mapping.get(channel_xml_id)
                if not epg_channel_id:
                    continue
                
                try:
                    # Parse time strings - XMLTV format: 20230101120000 +0000
                    start_time = self._parse_xmltv_time(start_str)
                    end_time = self._parse_xmltv_time(stop_str)
                    
                    if not start_time or not end_time:
                        continue
                    
                    # Get program details
                    title_elem = programme.find("title")
                    title = title_elem.text if title_elem is not None else "Unknown Program"
                    
                    subtitle_elem = programme.find("sub-title")
                    subtitle = subtitle_elem.text if subtitle_elem is not None else None
                    
                    desc_elem = programme.find("desc")
                    description = desc_elem.text if desc_elem is not None else None
                    
                    category_elem = programme.find("category")
                    category = category_elem.text if category_elem is not None else None
                    
                    # Get episode info if available
                    episode_elem = programme.find("episode-num")
                    episode_number = episode_elem.text if episode_elem is not None else None
                    
                    # Get rating if available
                    rating_elem = programme.find("rating/value")
                    rating = rating_elem.text if rating_elem is not None else None
                    
                    # Get icon if available
                    icon_elem = programme.find("icon")
                    icon_url = icon_elem.get("src") if icon_elem is not None else None
                    
                    # Create program data
                    program_data = {
                        'epg_channel_id': epg_channel_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'title': title[:500],  # Limit title length
                        'subtitle': subtitle[:500] if subtitle else None,
                        'description': description,
                        'category': category[:100] if category else None,
                        'episode_number': episode_number[:100] if episode_number else None,
                        'rating': rating[:20] if rating else None,
                        'icon_url': icon_url
                    }
                    
                    programs_to_insert.append(program_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing program data for channel {channel_xml_id}: {e}")
                    continue
            
            # Bulk insert programs
            if programs_to_insert:
                inserted_count = self.epg_program_repo.bulk_insert(programs_to_insert)
                logger.info(f"Inserted {inserted_count} programs for source {source_id}")
            else:
                logger.warning(f"No programs found for source {source_id}")
                
        except Exception as e:
            logger.error(f"Error parsing and storing programs: {str(e)}")
            raise

    def _parse_xmltv_time(self, time_str: str) -> datetime:
        """Parse XMLTV time format to datetime object."""
        try:
            import re
            from datetime import datetime, timezone
            
            # XMLTV format: 20230101120000 +0000 or 20230101120000
            # Remove timezone info for now and parse as UTC
            time_clean = re.sub(r'\s+[+-]\d{4}$', '', time_str.strip())
            
            # Parse the datetime
            if len(time_clean) >= 14:
                dt = datetime.strptime(time_clean[:14], '%Y%m%d%H%M%S')
                return dt.replace(tzinfo=timezone.utc)
            
            return None
        except Exception as e:
            logger.warning(f"Error parsing XMLTV time '{time_str}': {e}")
            return None

    def parse_epg_channels(self, xml_content):
        """
        Parse EPG channels from XML content.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            List of channel dictionaries
        """
        try:
            # Try to parse XML content
            logger.info("Parsing EPG channels from XML content")
            
            # Handle potential encoding issues
            if isinstance(xml_content, bytes):
                xml_content = xml_content.decode('utf-8', errors='replace')
            
            # Parse the XML
            root = ET.fromstring(xml_content)
            
            # Find all channel elements
            channels = []
            for channel_elem in root.findall(".//channel"):
                channel_id = channel_elem.get('id')
                if not channel_id:
                    continue
                
                # Get display names with language attributes
                display_names = {}
                default_name = None
                
                for display_name in channel_elem.findall('display-name'):
                    name_text = display_name.text
                    if name_text:
                        lang = display_name.get('lang')
                        if lang:
                            display_names[lang] = name_text
                        if not default_name:
                            default_name = name_text
                
                # Use first display name or ID as fallback
                name = default_name or channel_id
                
                # Get icon URL if available
                icon_url = None
                icon_elem = channel_elem.find('icon')
                if icon_elem is not None:
                    icon_url = icon_elem.get('src')
                
                # Extract primary language if available
                primary_language = None
                if display_names:
                    primary_language = next(iter(display_names.keys()), None)
                
                # Create channel dictionary
                channel = {
                    'id': channel_id,
                    'name': name,
                    'logo': icon_url,
                    'language': primary_language,
                    'display_names': display_names
                }
                
                channels.append(channel)
            
            logger.info(f"Parsed {len(channels)} channels from XML content")
            return channels
        except Exception as e:
            logger.error(f"Failed to parse EPG channels: {str(e)}", exc_info=True)
            return []
    
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
    
    def auto_scan_channels(self, threshold=0.75, clean_unmatched=False, respect_existing=True, epg_channels=None):
        """
        Automatically match channels with EPG data based on name similarity.
        
        Args:
            threshold: Minimum similarity threshold (0-1)
            clean_unmatched: Whether to remove EPG data from unmatched channels
            respect_existing: Whether to skip channels that already have EPG data
            epg_channels: Optional pre-loaded EPG channel data
            
        Returns:
            Dict with statistics about the operation
        """
        try:
            # Use provided EPG channels if available, otherwise fetch them
            all_epg_channels = epg_channels or []
            
            # If no channels were provided, fetch them from sources
            if not all_epg_channels:
                for source in self.epg_source_repo.get_all():
                    channels = self.get_channels_from_source(source.id)
                    all_epg_channels.extend(channels)
            
            logger.info(f"Found {len(all_epg_channels)} EPG channels")
            
            # Get all acestream channels
            from app.repositories.channel_repository import ChannelRepository
            channel_repo = ChannelRepository()
            acestream_channels = channel_repo.get_all()
            
            logger.info(f"Found {len(acestream_channels)} acestream channels")
            
            # Use the extracted find_matching_channels function
            stats = self.find_matching_channels(
                all_epg_channels, 
                acestream_channels, 
                threshold, 
                clean_unmatched, 
                respect_existing,
                apply_changes=True
            )
                
            return stats
        except Exception as e:
            logger.error(f"Error in auto_scan_channels: {e}")
            raise

    def find_matching_channels(
        self, epg_channels, acestream_channels, 
        threshold=0.75, clean_unmatched=False, 
        respect_existing=True, apply_changes=False
    ):
        """
        Find potential matches between EPG channels and Acestream channels.
        
        Args:
            epg_channels: List of EPG channel dictionaries
            acestream_channels: List of AcestreamChannel objects
            threshold: Minimum similarity threshold (0-1)
            clean_unmatched: Whether to remove EPG data from unmatched channels
            respect_existing: Whether to skip channels that already have EPG data
            apply_changes: Whether to actually save changes or just return matches
            
        Returns:
            Dict with statistics and matches if apply_changes=False
        """
        from difflib import SequenceMatcher
        
        stats = {
            'matched': 0,
            'cleaned': 0,
            'matches': []  # Will store match details if apply_changes=False
        }
        
        # Create a mapping of clean names to EPG channels
        epg_lookup = {}
        for channel in epg_channels:
            # Clean the channel name
            clean_name = self._clean_channel_name(channel['name'])
            epg_lookup[clean_name] = channel
            
            # Add additional lookups for common abbreviations/aliases
            # If the channel name contains "HD", also add a non-HD version for matching
            if 'HD' in clean_name:
                epg_lookup[clean_name.replace('HD', '').strip()] = channel
        
        # Create a direct mapping of EPG IDs to channels for faster lookup
        epg_id_lookup = {channel['id']: channel for channel in epg_channels}
        
        # Process each acestream channel
        for acestream in acestream_channels:
            try:
                # Skip if it has EPG data and we're respecting existing mappings
                if respect_existing and acestream.tvg_id and acestream.epg_update_protected:
                    continue
                    
                if not acestream.name:
                    continue
                
                best_epg = None
                best_similarity = 0
                best_epg_id = None
                match_method = None  # Track how the match was made
                
                # First, try to match by TVG ID if available
                if acestream.tvg_id and acestream.tvg_id in epg_id_lookup:
                    best_epg = epg_id_lookup[acestream.tvg_id]
                    best_similarity = 1.0  # Perfect match
                    best_epg_id = acestream.tvg_id
                    match_method = "id_match"
                    
                # If no ID match or we want to check for potentially better name matches
                # Clean the acestream name
                clean_name = self._clean_channel_name(acestream.name)
                
                # Check if name exactly matches any EPG channel
                if clean_name in epg_lookup:
                    # If we already have an ID match, only replace it if this is also a perfect match
                    if not best_epg or best_similarity < 1.0:
                        best_epg = epg_lookup[clean_name]
                        best_similarity = 1.0
                        best_epg_id = best_epg['id']
                        match_method = "exact_name_match"
                # If no direct match, try fuzzy matching
                else:
                    # Find the best match using similarity
                    for epg_name, epg_channel in epg_lookup.items():
                        similarity = SequenceMatcher(None, clean_name, epg_name).ratio()
                        # Only consider this match if it's better than what we have AND above threshold
                        if similarity > best_similarity and similarity >= threshold:
                            best_similarity = similarity
                            best_epg = epg_channel
                            best_epg_id = epg_channel['id']
                            match_method = "fuzzy_name_match"
                
                # If we found a match
                if best_epg_id:
                    # If just returning matches
                    if not apply_changes:
                        # Use a consistent dictionary format for matches
                        stats['matches'].append({
                            'channel': acestream,
                            'similarity': best_similarity,
                            'match_method': match_method,
                            'epg_id': best_epg_id,
                            'epg_name': best_epg['name']
                        })
                        continue
                        
                    # If applying changes, update the acestream channel
                    acestream.tvg_id = best_epg_id
                    acestream.tvg_name = best_epg['name']
                    
                    # If the EPG channel has a logo and the acestream doesn't, use it
                    if not acestream.logo and 'logo' in best_epg and best_epg['logo']:
                        acestream.logo = best_epg['logo']
                        
                    stats['matched'] += 1
                    
                # If no match and cleaning unmatched
                elif clean_unmatched and not respect_existing:
                    if not apply_changes:
                        continue
                        
                    # Clean EPG data
                    acestream.tvg_id = None
                    acestream.tvg_name = None
                    stats['cleaned'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing channel {acestream.id}: {e}")
        
        # Commit changes if applying them
        if apply_changes:
            from app.extensions import db
            db.session.commit()
        
        return stats

    def _clean_channel_name(self, name):
        """
        Clean a channel name for better matching.
        
        Args:
            name: The channel name to clean
            
        Returns:
            Cleaned channel name
        """
        if not name:
            return ""
            
        import re
        
        # Convert to lowercase
        clean = name.lower()
        
        # Remove HD, UHD, FHD, 4K, +1, etc. indicators
        clean = re.sub(r'\b(?:hd|uhd|fhd|sd|4k|\+\d)\b', '', clean)
        
        # Remove brackets and their contents
        clean = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', clean)
        
        # Remove common words
        for word in ['channel', 'tv', 'television', 'official']:
            clean = re.sub(r'\b' + word + r'\b', '', clean)
        
        # Remove special characters and normalize spaces
        clean = re.sub(r'[^\w\s]', ' ', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean

    def _apply_epg_data(self, channel: AcestreamChannel, epg_data: Dict) -> Tuple[bool, bool, bool]:
        """
        Apply EPG data to the channel, always updating if the data exists in the EPG.
        This overrides the previous behavior of only updating if the channel data was empty.
        Returns a tuple of (tvg_id_updated, tvg_name_updated, logo_updated).
        """
        tvg_id_updated = False
        tvg_name_updated = False
        logo_updated = False
        
        # Update tvg_id if provided in EPG data (always update, not just when empty)
        if epg_data["tvg_id"]:
            # Only mark as updated if value actually changes
            tvg_id_updated = channel.tvg_id != epg_data["tvg_id"]
            channel.tvg_id = epg_data["tvg_id"]
        
        # Update tvg_name if provided in EPG data
        if epg_data["tvg_name"]:
            tvg_name_updated = channel.tvg_name != epg_data["tvg_name"]
            channel.tvg_name = epg_data["tvg_name"]
        
        # Update logo if provided in EPG data
        if epg_data["logo"]:
            logo_updated = channel.logo != epg_data["logo"]
            channel.logo = epg_data["logo"]
            
        return (tvg_id_updated, tvg_name_updated, logo_updated)
    
    def _update_channel_epg(self, channel: AcestreamChannel) -> Tuple[bool, bool, bool, bool]:
        """
        Update EPG data for a channel.
        
        Returns a tuple of (tvg_id_updated, tvg_name_updated, logo_updated, any_update)
        """
        string_mappings = self.epg_string_mapping_repo.get_all()
        
        # Detect if channel should be excluded
        channel_name_lower = channel.name.lower()
        for mapping in string_mappings:
            if mapping.search_pattern.startswith('!'):
                exclusion_pattern = mapping.search_pattern[1:].lower()
                if exclusion_pattern in channel_name_lower:
                    logger.info(f"Channel '{channel.name}' excluded by pattern '!{exclusion_pattern}'")
                    
                    # Clean EPG data if channel has any data
                    changes_made = False
                    
                    if channel.tvg_id:
                        channel.tvg_id = None
                        changes_made = True
                    
                    if channel.tvg_name:
                        channel.tvg_name = None
                        changes_made = True
                    
                    if channel.logo:
                        channel.logo = None
                        changes_made = True
                    
                    if changes_made:
                        logger.info(f"Cleared EPG data from channel '{channel.name}' due to exclusion pattern")
                        return (True, True, True, True)
                    
                    return (False, False, False, False)
        
        # Improved mapping logic
        potential_mappings = []
        
        # Pre-process channel name to split into words for more exact comparison
        channel_words = channel_name_lower.split()
        
        for mapping in string_mappings:
            if not mapping.search_pattern.startswith('!'):  # Only process regular patterns
                pattern_lower = mapping.search_pattern.lower()
                pattern_words = pattern_lower.split()
                
                # Only consider patterns that are within the channel name
                if pattern_lower in channel_name_lower:
                    # Base score - pattern length multiplied by 10 to give it more weight
                    pattern_score = len(pattern_lower) * 10
                    
                    # HIGHEST PRIORITY: Exact match with full name
                    if pattern_lower == channel_name_lower:
                        pattern_score += 10000  # Extremely high priority
                    
                    # VERY HIGH PRIORITY: Pattern exactly matches the start of the name
                    if channel_name_lower.startswith(pattern_lower):
                        pattern_score += 3000  # Higher priority than having numbers
                    
                    # HIGH PRIORITY: Match at the beginning of the name (more important than having numbers)
                    elif channel_name_lower.startswith(pattern_lower + ' '):
                        pattern_score += 2500  # Higher priority than having numbers
                    
                    # Bonus for matching complete words
                    matching_words = 0
                    for word in pattern_words:
                        if word in channel_words:
                            matching_words += 1
                    
                    if matching_words == len(pattern_words):
                        pattern_score += 1000 * matching_words
                        
                        # Bonus if words are in the same order
                        if ' '.join(pattern_words) in ' '.join(channel_words):
                            pattern_score += 500
                    
                    # Bonus for patterns with numbers
                    if any(char.isdigit() for char in pattern_lower):
                        pattern_score += 1500
                    
                    # Bonus if first word of pattern matches first word of channel
                    # This helps prioritize patterns like "dazn laliga" for channels starting with "DAZN"
                    if channel_words and pattern_words and channel_words[0] == pattern_words[0]:
                        pattern_score += 1800
                    
                    potential_mappings.append((mapping, pattern_score))
        
        # Sort by score, highest to lowest
        potential_mappings.sort(key=lambda x: x[1], reverse=True)
        
        # Use the mapping with the highest score if it exists
        if potential_mappings:
            best_mapping, score = potential_mappings[0]
            
            if best_mapping.epg_channel_id in self.epg_data:
                epg_data = self.epg_data[best_mapping.epg_channel_id]
                updates = self._apply_epg_data(channel, epg_data)
                if any(updates):
                    logger.info(f"Channel '{channel.name}' matched pattern '{best_mapping.search_pattern}', applied EPG data from channel '{best_mapping.epg_channel_id}'")
                return updates
            else:
                logger.warning(f"EPG channel ID '{best_mapping.epg_channel_id}' not found for pattern '{best_mapping.search_pattern}'")
        
        # If no suitable mapping was found
        return (False, False, False, False)

    def update_all_channels_epg(self, respect_existing: bool = False, clean_unmatched: bool = False) -> dict:
        """
        Updates EPG information for all channels that don't have EPG locked.
        
        Args:
            respect_existing: If True, don't modify channels that already have some EPG data
            clean_unmatched: If True, clear EPG data from channels with no match
        
        Returns:
            Stats about the update process.
        """
        stats = {
            "total": 0,
            "updated": 0,
            "locked": 0,
            "excluded": 0,
            "cleaned": 0,
            "skipped": 0,
            "errors": 0
        }
        
        # Check if there are mapping rules defined
        string_mappings = self.epg_string_mapping_repo.get_all()
        normal_rules = [m for m in string_mappings if not m.search_pattern.startswith('!')]
        has_mapping_rules = len(normal_rules) > 0
        
        logger.info(f"Updating EPG mappings. Has mapping rules: {has_mapping_rules}, Normal rules count: {len(normal_rules)}")
        
        channels = self.channel_repo.get_all()
        channels_with_epg = [c for c in channels if c.tvg_id or c.tvg_name or c.logo]
        
        logger.info(f"Processing {len(channels)} channels, {len(channels_with_epg)} have some EPG data")
        stats["total"] = len(channels)
        
        # First make sure to load EPG data
        if not self.epg_data:
            self.fetch_epg_data()
        
        # Use an explicit transaction to ensure changes are applied
        from sqlalchemy.orm import Session
        session = db.session
        
        try:
            for channel in channels:
                try:
                    # Check if channel is protected from EPG updates
                    if channel.epg_update_protected:
                        stats["locked"] += 1
                        continue
                    
                    # If respect_existing option is active and channel already has data, skip it
                    if respect_existing and (channel.tvg_id or channel.tvg_name or channel.logo):
                        stats["skipped"] += 1
                        continue
                    
                    if not has_mapping_rules:
                        # If there are no mapping rules and the channel has data, clean it ONLY if clean_unmatched is true
                        if clean_unmatched and (channel.tvg_id or channel.tvg_name or channel.logo):
                            old_data = f"tvg_id={channel.tvg_id}, tvg_name={channel.tvg_name}, logo={'Yes' if channel.logo else 'No'}"
                            
                            # Perform cleaning directly
                            channel.tvg_id = None
                            channel.tvg_name = None
                            channel.logo = None
                            
                            # Update the channel in the database
                            try:
                                self.channel_repo.update(channel)
                                session.flush()
                                
                                stats["cleaned"] += 1
                                logger.info(f"CLEANED: Channel '{channel.name}' (previous: {old_data}) - no mapping rules exist")
                            except Exception as e:
                                logger.error(f"Failed to update channel {channel.name}: {str(e)}")
                                stats["errors"] += 1
                        continue
                    
                    # If there are rules, proceed with applying mappings
                    was_updated, tvg_id_updated, tvg_name_updated, logo_updated = self._update_channel_epg(channel)
                    
                    if was_updated:
                        try:
                            self.channel_repo.update(channel)
                            session.flush()  # Ensure changes are applied
                            
                            if not channel.tvg_id and not channel.tvg_name and not channel.logo:
                                stats["cleaned"] += 1
                                stats["excluded"] += 1
                                logger.info(f"EXCLUDED: Channel '{channel.name}' matched exclusion rule")
                            else:
                                stats["updated"] += 1
                                logger.info(f"UPDATED: Channel '{channel.name}' with new EPG data")
                        except Exception as e:
                            logger.error(f"Failed to save updates for channel {channel.name}: {str(e)}")
                            stats["errors"] += 1
                        continue
                    
                    # If channel was not updated and not excluded, clean its data
                    is_excluded = self._is_excluded_by_rule(channel)
                    
                    if not is_excluded and (channel.tvg_id or channel.tvg_name or channel.logo):
                        # Clean only if clean_unmatched is true
                        if clean_unmatched:
                            old_data = f"tvg_id={channel.tvg_id}, tvg_name={channel.tvg_name}, logo={'Yes' if channel.logo else 'No'}"
                            
                            # Clean data
                            channel.tvg_id = None
                            channel.tvg_name = None
                            channel.logo = None
                            
                            try:
                                self.channel_repo.update(channel)
                                session.flush()
                                
                                stats["cleaned"] += 1
                                logger.info(f"CLEANED: Channel '{channel.name}' (previous: {old_data}) - no matching rule")
                            except Exception as e:
                                logger.error(f"Failed to clean channel {channel.name}: {str(e)}")
                                stats["errors"] += 1
                    elif is_excluded:
                        stats["excluded"] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing channel {channel.name}: {str(e)}")
                    stats["errors"] += 1
            
            # Confirm all changes
            session.commit()
            logger.info(f"EPG update completed. Summary: Updated={stats['updated']}, Cleaned={stats['cleaned']}, Locked={stats['locked']}, Excluded={stats['excluded']}, Errors={stats['errors']}")
        
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed, rolling back: {str(e)}")
            stats["errors"] += 1
            raise
                
        return stats
    
    def _is_excluded_by_rule(self, channel: AcestreamChannel) -> bool:
        """Determine if a channel is excluded by a pattern rule."""
        channel_name_lower = channel.name.lower()
        string_mappings = self.epg_string_mapping_repo.get_all()
        
        for mapping in string_mappings:
            if mapping.search_pattern.startswith('!'):
                exclusion_pattern = mapping.search_pattern[1:].lower()
                if exclusion_pattern in channel_name_lower:
                    return True
        
        return False

    def get_channels_from_source(self, source_id):
        """
        Get all EPG channels from a specific source.
        
        Args:
            source_id: The EPG source ID
            
        Returns:
            List of channel dictionaries
        """
        try:
            # Get the source from the database
            epg_source_repo = EPGSourceRepository()
            source = epg_source_repo.get_by_id(source_id)
            
            if not source:
                logger.warning(f"EPG source {source_id} not found")
                return []
            
            # Get XML content directly from URL
            xml_content = None
            
            if source.url:
                logger.info(f"Fetching data from URL for EPG source {source_id}: {source.url}")
                try:
                    response = requests.get(source.url, timeout=30)
                    if response.status_code == 200:
                        xml_content = response.text
                    else:
                        logger.error(f"Error fetching EPG source {source_id}: HTTP {response.status_code}")
                except Exception as e:
                    logger.error(f"Error fetching EPG source {source_id} URL: {str(e)}")
            
            if not xml_content:
                logger.warning(f"No XML content available for EPG source {source_id}")
                return []
            
            # Parse the XML content to get channels
            channels = self.parse_epg_channels(xml_content)
            
            logger.info(f"Found {len(channels)} channels from EPG source {source_id}")
            return channels
            
        except Exception as e:
            logger.error(f"Error getting channels from EPG source {source_id}: {str(e)}")
            return []

    def get_epg_channels(self, page=1, per_page=50, source_id=None):
        """
        Get EPG channels with pagination from XML data.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            source_id: Optional EPG source ID to filter by
            
        Returns:
            Dictionary with channels, pagination info
        """
        # Get EPG sources based on filter
        from app.repositories.epg_source_repository import EPGSourceRepository
        repo = EPGSourceRepository()
        
        if source_id:
            # Get specific source
            source = repo.get_by_id(source_id)
            sources = [source] if source else []
        else:
            # Get all sources - removed active_only parameter which was causing the error
            sources = repo.get_all()
        
        if not sources:
            return {'channels': [], 'page': page, 'total_pages': 0, 'total': 0}

        # Collect channels from all specified sources
        all_channels = []
        for source in sources:
            if not source or not source.url:
                continue
                
            try:
                # Parse and get channels from this source
                channels = self._extract_channels_from_epg_source(source)
                for channel in channels:
                    # Add source information to each channel
                    channel['source_id'] = source.id
                    channel['source_name'] = source.name
                    all_channels.append(channel)
            except Exception as e:
                logger.error(f"Error getting channels from EPG source {source.id}: {e}")
        
        # Sort channels by name
        all_channels.sort(key=lambda x: x.get('name', '').lower())
        
        # Calculate pagination
        total = len(all_channels)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_channels = all_channels[start_idx:end_idx]
        
        return {
            'channels': paginated_channels,
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages
        }
    
    def _extract_channels_from_epg_source(self, source):
        """
        Extract channels from an EPG source.
        
        Args:
            source: EPGSource object
            
        Returns:
            List of channel dictionaries with id, name, icon
        """
        if not source or not source.url:
            return []
            
        try:
            # Fetch and parse XML
            import requests
            import xml.etree.ElementTree as ET
            from io import StringIO
            
            # Try to fetch the XML data
            response = requests.get(source.url, timeout=30)
            response.raise_for_status()
            
            # Parse the XML
            xml_data = response.text
            tree = ET.parse(StringIO(xml_data))
            root = tree.getroot()
            
            # Find all channel elements
            channels = []
            for channel_elem in root.findall('.//channel'):
                channel_id = channel_elem.get('id', '')
                
                # Get channel name
                display_name_elem = channel_elem.find('./display-name')
                name = display_name_elem.text if display_name_elem is not None else channel_id
                
                # Get channel icon if available
                icon_url = None
                icon_elem = channel_elem.find('./icon')
                if icon_elem is not None:
                    icon_url = icon_elem.get('src')
                
                # Create channel entry
                channel = {
                    'id': channel_id,
                    'name': name,
                    'icon': icon_url
                }
                
                channels.append(channel)
                
            return channels
        except Exception as e:
            logger.error(f"Error extracting channels from EPG source: {e}")
            return []
    
    def should_refresh_epg(self):
        """
        Check if EPG data should be refreshed based on last refresh time
        
        Returns:
            bool: True if EPG should be refreshed, False otherwise
        """
        # Get the most recently updated enabled EPG source
        sources = self.epg_source_repo.get_enabled()
        
        # If no enabled sources, refresh is needed
        if not sources:
            logger.info("Initial EPG refresh needed (no enabled EPG sources)")
            return True
        
        # Find the most recently updated source
        latest_source = None
        for source in sources:
            if source.last_updated and (not latest_source or source.last_updated > latest_source.last_updated):
                latest_source = source
        
        # If no previous refresh or no enabled sources with last_updated, refresh is needed
        if not latest_source or not latest_source.last_updated:
            logger.info("Initial EPG refresh needed (no previous refresh recorded)")
            return True
        
        # Define refresh interval (24 hours by default)
        refresh_interval = timedelta(hours=24)
        
        current_time = datetime.now()
        next_refresh_time = latest_source.last_updated + refresh_interval
        
        if current_time >= next_refresh_time:
            logger.info(f"EPG refresh needed (last refresh: {latest_source.last_updated.isoformat()})")
            return True
        else:
            logger.info(f"EPG data up to date (last refresh: {latest_source.last_updated.isoformat()}, next: {next_refresh_time.isoformat()})")
            return False

    def _update_last_refresh_time(self):
        """Update the timestamp of the last EPG refresh"""
        # Get current time
        current_time = datetime.now()
        
        # Update last_updated timestamp for all enabled sources that we refreshed
        sources = self.epg_source_repo.get_enabled()
        for source in sources:
            source.last_updated = current_time
        
        # Commit changes to the database
        self.epg_source_repo.session.commit()
        logger.info(f"Updated EPG refresh timestamp to {current_time.isoformat()}")
