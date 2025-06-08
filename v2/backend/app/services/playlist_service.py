"""
Service for managing and generating M3U playlists
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import time

from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel


class PlaylistService:
    """Service for generating M3U playlists"""
    
    def __init__(self, db: Session):
        """Initialize with database session"""
        self.db = db
        self.channel_repository = ChannelRepository(db)
    
    async def generate_playlist(
        self,
        search: Optional[str] = None,
        group: Optional[str] = None,
        only_online: bool = False,
        include_groups: Optional[List[str]] = None,
        exclude_groups: Optional[List[str]] = None
    ) -> str:
        """
        Generate an M3U playlist with the specified filters
        
        Args:
            search: Optional search term for channel names
            group: Optional group filter
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude
            
        Returns:
            The M3U playlist content as a string
        """
        # Fetch channels that match criteria
        channels = self.channel_repository.get_filtered_channels(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups
        )
        
        # Generate M3U content
        m3u_content = self._generate_m3u_content(channels)
        return m3u_content
    
    async def get_channel_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups
        
        Returns:
            List of group names
        """
        return self.channel_repository.get_unique_groups()
        
    def _generate_m3u_content(self, channels: List[AcestreamChannel]) -> str:
        """
        Convert channels to M3U format
        
        Args:
            channels: List of channels to include
            
        Returns:
            M3U formatted string
        """
        # M3U header
        header = "#EXTM3U\n"
        
        # Current timestamp for cache busting
        timestamp = str(int(time.time()))
        
        # Generate each channel entry
        entries = []
        for channel in channels:
            # Skip invalid channels
            if not channel.channel_id or not channel.name:
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
            tvg_id = getattr(channel, 'tvg_id', '')
            if tvg_id:
                attrs.append(f'tvg-id="{tvg_id}"')
                
            # Generate entry
            entry = f'#EXTINF:-1 {" ".join(attrs)}, {channel.name}\n'
            entry += f'acestream://{channel.channel_id}?{timestamp}\n'
            
            entries.append(entry)
        
        # Combine all parts
        return header + '\n'.join(entries)
