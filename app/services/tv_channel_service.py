from typing import List, Dict, Optional, Tuple
import logging
import re
from difflib import SequenceMatcher
from app.repositories.tv_channel_repository import TVChannelRepository
from app.repositories.channel_repository import ChannelRepository
from app.models.tv_channel import TVChannel
from app.models.acestream_channel import AcestreamChannel
from app.services.epg_service import EPGService

logger = logging.getLogger(__name__)

class TVChannelService:
    """Service for TV Channel business logic."""
    
    def __init__(self):
        self.tv_channel_repo = TVChannelRepository()
        self.acestream_repo = ChannelRepository()
        self.epg_service = EPGService()
        
    def get_best_acestream(self, tv_channel_id: int) -> Optional[AcestreamChannel]:
        """
        Get the best available acestream channel for a TV channel.
        Priority: online status, then EPG data completeness.
        
        Args:
            tv_channel_id: The TV channel ID
            
        Returns:
            Best AcestreamChannel object or None if no channels available
        """
        tv_channel = self.tv_channel_repo.get_by_id(tv_channel_id)
        if not tv_channel:
            return None
            
        # First try to get online channels
        acestreams = AcestreamChannel.query.filter_by(tv_channel_id=tv_channel_id, is_online=True).all()
        
        if not acestreams:
            # If no online channels, get all channels
            acestreams = AcestreamChannel.query.filter_by(tv_channel_id=tv_channel_id).all()
            
        if not acestreams:
            return None
            
        # Score channels based on metadata completeness
        def score_channel(channel):
            score = 0
            if channel.is_online:
                score += 10
            if channel.logo:
                score += 3
            if channel.tvg_id:
                score += 2
            if channel.tvg_name:
                score += 1
            return score
            
        # Return the channel with the highest score
        return sorted(acestreams, key=score_channel, reverse=True)[0]
        
    def sync_epg_data(self, tv_channel_id: int) -> bool:
        """
        Synchronize EPG data between a TV channel and its acestream channels.
        If the TV channel has EPG data, apply it to its acestream channels.
        If not, try to derive EPG data from the acestream channels.
        
        Args:
            tv_channel_id: The TV channel ID
            
        Returns:
            True if changes were made, False otherwise
        """
        tv_channel = self.tv_channel_repo.get_by_id(tv_channel_id)
        if not tv_channel:
            return False
            
        acestreams = AcestreamChannel.query.filter_by(tv_channel_id=tv_channel_id).all()
        if not acestreams:
            return False
            
        changes_made = False
            
        # If TV channel has EPG ID, use it for acestream channels
        if tv_channel.epg_id:
            for acestream in acestreams:
                if not acestream.epg_update_protected and acestream.tvg_id != tv_channel.epg_id:
                    acestream.tvg_id = tv_channel.epg_id
                    acestream.tvg_name = tv_channel.name
                    changes_made = True
        # Otherwise, try to derive from best acestream channel
        else:
            best_acestream = self.get_best_acestream(tv_channel_id)
            if best_acestream and best_acestream.tvg_id:
                tv_channel.epg_id = best_acestream.tvg_id
                tv_channel.name = best_acestream.tvg_name or tv_channel.name
                changes_made = True
                
                # Update logo if not set
                if not tv_channel.logo_url and best_acestream.logo:
                    tv_channel.logo_url = best_acestream.logo
                    
        if changes_made:
            from app.extensions import db
            db.session.commit()
            
        return changes_made
        
    def batch_assign_streams(self, name_patterns: Dict[str, int]) -> Dict[str, int]:
        """
        Batch assign acestream channels to TV channels based on name patterns.
        
        Args:
            name_patterns: Dictionary mapping string patterns to TV channel IDs
            
        Returns:
            Dictionary with counts of assigned channels per TV channel ID
        """
        result = {tv_id: 0 for tv_id in name_patterns.values()}
        
        # Get unassigned acestream channels
        unassigned_channels = AcestreamChannel.query.filter_by(tv_channel_id=None).all()
        
        for channel in unassigned_channels:
            if not channel.name:
                continue
                
            channel_name_lower = channel.name.lower()
            
            # Check each pattern
            for pattern, tv_id in name_patterns.items():
                if pattern.lower() in channel_name_lower:
                    channel.tv_channel_id = tv_id
                    result[tv_id] += 1
                    break
                    
        from app.extensions import db
        db.session.commit()
        return result
        
    def bulk_update_epg(self) -> Dict[str, int]:
        """
        Update EPG data for all TV channels and their associated acestream channels.
        
        Returns:
            Statistics about the update process
        """
        stats = {
            'total': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        tv_channels = self.tv_channel_repo.get_all(is_active=True)
        stats['total'] = len(tv_channels)
        
        for channel in tv_channels:
            try:
                updated = self.sync_epg_data(channel.id)
                if updated:
                    stats['updated'] += 1
                else:
                    stats['skipped'] += 1
            except Exception as e:
                logger.error(f"Error updating EPG for TV channel {channel.id}: {str(e)}")
                stats['errors'] += 1
                
        return stats
        
    def associate_by_epg_id(self) -> Dict[str, int]:
        """
        Associate acestream channels with TV channels based on matching EPG IDs.
        
        Returns:
            Statistics about the association process
        """
        stats = {
            'matched': 0,
            'unmatched': 0
        }
        
        # Get all TV channels with EPG IDs
        tv_channels_with_epg = TVChannel.query.filter(TVChannel.epg_id.isnot(None)).all()
        epg_map = {c.epg_id: c.id for c in tv_channels_with_epg}
        
        if not epg_map:
            return stats
            
        # Get unassigned acestream channels with EPG IDs
        unassigned = AcestreamChannel.query.filter_by(tv_channel_id=None).filter(
            AcestreamChannel.tvg_id.isnot(None)
        ).all()
        
        for channel in unassigned:
            if channel.tvg_id in epg_map:
                channel.tv_channel_id = epg_map[channel.tvg_id]
                stats['matched'] += 1
            else:
                stats['unmatched'] += 1
                
        from app.extensions import db
        db.session.commit()
        return stats

    def generate_tv_channels_from_acestreams(self) -> Dict[str, int]:
        """
        Generate TV channels from existing acestreams based on their metadata.
        This function looks for patterns in names and EPG data to group similar acestreams.
        
        Returns:
            Dictionary with statistics about the creation process
        """
        stats = {
            'created': 0,
            'matched': 0,
            'skipped': 0,
            'errors': 0
        }
        
        # Get all acestreams without TV channel association
        unassigned_acestreams = AcestreamChannel.query.filter_by(tv_channel_id=None).all()
        logger.info(f"Found {len(unassigned_acestreams)} unassigned acestreams")
        
        # Group by EPG ID first (most reliable)
        epg_groups = {}
        for acestream in unassigned_acestreams:
            if acestream.tvg_id:
                if acestream.tvg_id not in epg_groups:
                    epg_groups[acestream.tvg_id] = []
                epg_groups[acestream.tvg_id].append(acestream)
        
        # Create TV channels from EPG groups
        for epg_id, acestreams in epg_groups.items():
            if not acestreams:
                continue
                
            # Use the first acestream as a reference
            reference = acestreams[0]
            
            # Check if a TV channel with this EPG ID already exists
            existing_channel = TVChannel.query.filter_by(epg_id=epg_id).first()
            if existing_channel:
                # Associate all acestreams with this channel
                for acestream in acestreams:
                    acestream.tv_channel_id = existing_channel.id
                stats['matched'] += len(acestreams)
                continue
            
            try:
                # Create a new TV channel
                channel_data = {
                    'name': reference.tvg_name or reference.name or f"Channel {epg_id}",
                    'epg_id': epg_id,
                    'logo_url': reference.logo,
                    'is_active': True
                }
                
                # Try to extract additional metadata
                if reference.name and ':' in reference.name:
                    parts = reference.name.split(':', 1)
                    if len(parts) == 2:
                        category = parts[0].strip()
                        if category:
                            channel_data['category'] = category
                
                # Extract country and language from TVG name if possible
                if reference.tvg_name:
                    # Look for country/language codes in brackets
                    country_match = re.search(r'\(([A-Z]{2})\)', reference.tvg_name)
                    if country_match:
                        channel_data['country'] = country_match.group(1)
                    
                    # Try to guess language based on common patterns
                    if " EN" in reference.tvg_name or "(EN)" in reference.tvg_name:
                        channel_data['language'] = "English"
                    elif " ES" in reference.tvg_name or "(ES)" in reference.tvg_name:
                        channel_data['language'] = "Spanish"
                    elif " FR" in reference.tvg_name or "(FR)" in reference.tvg_name:
                        channel_data['language'] = "French"
                
                # Create the channel
                new_channel = self.tv_channel_repo.create(channel_data)
                
                # Associate acestreams with this new channel
                for acestream in acestreams:
                    acestream.tv_channel_id = new_channel.id
                
                stats['created'] += 1
                stats['matched'] += len(acestreams)
            except Exception as e:
                logger.error(f"Error creating TV channel from EPG ID {epg_id}: {str(e)}")
                stats['errors'] += 1
        
        # Now try to group by name patterns (less reliable)
        remaining = AcestreamChannel.query.filter_by(tv_channel_id=None).all()
        if remaining:
            name_groups = self._group_by_name_patterns(remaining)
            
            for group_name, acestreams in name_groups.items():
                if not acestreams or len(acestreams) < 2:  # Only create channels for groups with multiple acestreams
                    stats['skipped'] += len(acestreams) if acestreams else 0
                    continue
                    
                try:
                    # Create a TV channel for this group
                    channel_data = {
                        'name': group_name,
                        'is_active': True
                    }
                    
                    # Check for logo in any of the acestreams
                    for acestream in acestreams:
                        if acestream.logo:
                            channel_data['logo_url'] = acestream.logo
                            break
                            
                    # Check for EPG data in any of the acestreams
                    for acestream in acestreams:
                        if acestream.tvg_id:
                            channel_data['epg_id'] = acestream.tvg_id
                            break
                    
                    # Create the channel
                    new_channel = self.tv_channel_repo.create(channel_data)
                    
                    # Associate acestreams with this new channel
                    for acestream in acestreams:
                        acestream.tv_channel_id = new_channel.id
                    
                    stats['created'] += 1
                    stats['matched'] += len(acestreams)
                except Exception as e:
                    logger.error(f"Error creating TV channel from name group {group_name}: {str(e)}")
                    stats['errors'] += 1
        
        # Commit all changes
        from app.extensions import db
        db.session.commit()
        
        return stats

    def _group_by_name_patterns(self, acestreams: List[AcestreamChannel]) -> Dict[str, List[AcestreamChannel]]:
        """
        Group acestreams by common patterns in their names.
        
        Args:
            acestreams: List of acestream channels to group
            
        Returns:
            Dictionary mapping group names to lists of acestreams
        """
        groups = {}
        processed = set()
        
        # Sort by name length (shorter first) to prioritize simple names
        sorted_acestreams = sorted(acestreams, key=lambda x: len(x.name) if x.name else float('inf'))
        
        for acestream in sorted_acestreams:
            if not acestream.name or acestream.id in processed:
                continue
                
            # Extract base channel name (without resolution, language markers, etc.)
            base_name = self._extract_base_name(acestream.name)
            if not base_name:
                continue
                
            # Find similar channels
            similar = [a for a in sorted_acestreams 
                      if a.id not in processed 
                      and a.name 
                      and self._names_are_similar(base_name, a.name)]
            
            if similar:
                groups[base_name] = similar
                processed.update(a.id for a in similar)
        
        return groups

    def _extract_base_name(self, name: str) -> str:
        """Extract base channel name by removing common suffixes and prefixes."""
        # Remove resolution indicators, e.g., "HD", "UHD", "FHD", "1080p", etc.
        clean_name = re.sub(r'\b(?:HD|UHD|FHD|SD|4K|1080[pi]|720[pi]|576[pi]|480[pi])\b', '', name, flags=re.IGNORECASE)
        
        # Remove language indicators, e.g., "(EN)", "[ES]", etc.
        clean_name = re.sub(r'[\(\[](?:EN|ES|FR|DE|IT|PT|RU|NL)[\)\]]', '', clean_name, flags=re.IGNORECASE)
        
        # Remove trailing special characters and whitespace
        clean_name = re.sub(r'[:\-_\|]+\s*$', '', clean_name.strip())
        
        # Remove leading special characters and whitespace
        clean_name = re.sub(r'^\s*[:\-_\|]+', '', clean_name.strip())
        
        return clean_name.strip()

    def _names_are_similar(self, name1: str, name2: str) -> bool:
        """Check if two channel names are similar enough to be grouped."""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Exact match
        if name1_lower == name2_lower:
            return True
        
        # One name contains the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return True
        
        # Compare using Levenshtein distance for more subtle similarities
        similarity_ratio = SequenceMatcher(None, name1_lower, name2_lower).ratio()
        return similarity_ratio > 0.8  # 80% similarity threshold
