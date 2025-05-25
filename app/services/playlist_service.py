import os
from typing import List, Dict, Optional
from ..repositories import ChannelRepository
from app.utils.config import Config
from app.repositories.tv_channel_repository import TVChannelRepository
from app.services.tv_channel_service import TVChannelService
from app.models.acestream_channel import AcestreamChannel

class PlaylistService:
    def __init__(self):
        self.channel_repository = ChannelRepository()
        self.config = Config()
        self.tv_channel_repository = TVChannelRepository()
        self.tv_channel_service = TVChannelService()

    def _format_stream_url(self, channel_id: str, local_id: int) -> str:
        """Format stream URL based on base_url configuration."""
        # Get base_url directly from config instance
        base_url = getattr(self.config, 'base_url', 'acestream://')
        
        # Check if PID parameter should be added
        should_add_pid = getattr(self.config, 'addpid', False)
                
        # Don't add pid if addpid is False
        if should_add_pid:
            return f'{base_url}{channel_id}&pid={local_id}'
        else:            
            return f'{base_url}{channel_id}'

    def _get_channels(self, search_term: str = None):
        """Retrieve channels from the repository with optional search term."""
        if search_term:
            return self.channel_repository.model.query.filter(
                (self.channel_repository.model.status == 'active') &
                (self.channel_repository.model.name.ilike(f'%{search_term}%'))
            ).all()
        return self.channel_repository.get_active()

    def generate_playlist(self, search_term=None):
        """Generate M3U playlist with channels."""
        playlist_lines = ['#EXTM3U']
        
        # Query channels from the database
        channels = self._get_channels(search_term)
        
        # Track used names and their counts
        name_counts = {}
        
        # Add each channel to the playlist
        for local_id, channel in enumerate(channels, start=0):
            # Use _format_stream_url to get the correct URL format
            stream_url = self._format_stream_url(channel.id, local_id)
            
            # Handle duplicate names
            base_name = channel.name
            if base_name in name_counts:
                # Increment the counter for this name
                name_counts[base_name] += 1
                # For duplicates, append the counter value (2, 3, etc.)
                display_name = f"{base_name} {name_counts[base_name]}"
            else:
                # First occurrence - use original name and initialize counter
                name_counts[base_name] = 1
                display_name = base_name
            
            # Add metadata if available
            metadata = []
            if channel.tvg_name:
                metadata.append(f'tvg-name="{channel.tvg_name}"')
            if channel.tvg_id:
                metadata.append(f'tvg-id="{channel.tvg_id}"')
            if channel.logo:
                metadata.append(f'tvg-logo="{channel.logo}"')
            if channel.group:
                metadata.append(f'group-title="{channel.group}"')
            
            # Create EXTINF line with metadata
            extinf = '#EXTINF:-1'
            if metadata:
                extinf += f' {"".join(metadata)}'
            extinf += f',{display_name}'
            
            playlist_lines.append(extinf)
            playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)
    
    def generate_tv_channels_playlist(self, search_term=None, favorites_only=False):
        """Generate M3U playlist with TV channels using all their acestreams.
        
        Args:
            search_term: Optional search term to filter channels by name
            favorites_only: If True, only include favorite channels
            
        Returns:
            String containing the M3U playlist content
        """
        playlist_lines = ['#EXTM3U']
        
        # Query TV channels with filters
        channels, total, _ = self.tv_channel_repository.filter_channels(
            search_term=search_term,
            favorites_only=favorites_only,
            per_page=1000  # Large value to avoid pagination
        )
        
        # Sort channels by channel_number if available
        sorted_channels = sorted(
            channels, 
            key=lambda c: (c.channel_number is None, c.channel_number or 0, c.name.lower())
        )
        
        # Track used names and their counts
        name_counts = {}
        local_id = 0
        
        # Process each TV channel
        for tv_channel in sorted_channels:
            # Get all acestreams for this TV channel, prioritize online and best quality
            acestreams = AcestreamChannel.query.filter_by(tv_channel_id=tv_channel.id).all()
            
            # Skip channels without acestreams
            if not acestreams:
                continue
                
            # Sort acestreams by quality (online first, then by metadata completeness)
            def score_acestream(acestream):
                score = 0
                if acestream.is_online:
                    score += 10
                if acestream.logo:
                    score += 3
                if acestream.tvg_id:
                    score += 2
                if acestream.tvg_name:
                    score += 1
                return score
                
            sorted_acestreams = sorted(acestreams, key=score_acestream, reverse=True)
            
            # Process each acestream for this TV channel
            for stream_index, acestream in enumerate(sorted_acestreams):
                # Use _format_stream_url to get the correct URL format
                stream_url = self._format_stream_url(acestream.id, local_id)
                local_id += 1
                
                # Handle duplicate names and multiple streams per channel
                base_name = tv_channel.name
                if len(sorted_acestreams) > 1:
                    # Multiple streams for same channel: use sub-numbering
                    display_name = f"{base_name} ({stream_index + 1})"
                else:
                    # Single stream: check for global name duplicates
                    if base_name in name_counts:
                        name_counts[base_name] += 1
                        display_name = f"{base_name} {name_counts[base_name]}"
                    else:
                        name_counts[base_name] = 1
                        display_name = base_name
                
                # Add metadata if available
                metadata = []
                
                # Channel numbering: use sub-numbering for multiple streams
                if tv_channel.channel_number is not None:
                    if len(sorted_acestreams) > 1:
                        # Sub-numbering: 101.1, 101.2, etc.
                        channel_number = f"{tv_channel.channel_number}.{stream_index + 1}"
                    else:
                        # Single stream: use original number
                        channel_number = str(tv_channel.channel_number)
                    metadata.append(f'tvg-chno="{channel_number}"')
                
                # Prioritize TV channel metadata, fall back to acestream metadata if needed
                if tv_channel.epg_id:
                    metadata.append(f'tvg-id="{tv_channel.epg_id}"')
                elif acestream.tvg_id:
                    metadata.append(f'tvg-id="{acestream.tvg_id}"')
                    
                metadata.append(f'tvg-name="{display_name}"')
                
                # Use TV channel logo if available, otherwise use acestream logo
                if tv_channel.logo_url:
                    metadata.append(f'tvg-logo="{tv_channel.logo_url}"')
                elif acestream.logo:
                    metadata.append(f'tvg-logo="{acestream.logo}"')
                    
                # Use channel category as group
                if tv_channel.category:
                    metadata.append(f'group-title="{tv_channel.category}"')
                
                # Create EXTINF line with metadata
                extinf = '#EXTINF:-1'
                if metadata:
                    extinf += f' {"".join(metadata)}'
                extinf += f',{display_name}'
                
                playlist_lines.append(extinf)
                playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)
    
    def generate_epg_xml(self, search_term=None, favorites_only=False):
        """Generate XML EPG guide for channels with EPG data and associated acestreams.
        
        Args:
            search_term: Optional search term to filter channels by name
            favorites_only: If True, only include favorite channels
            
        Returns:
            String containing the XML EPG guide content
        """
        # Start with XML header and root element
        xml_lines = [
            '<?xml version="1.0" encoding="utf-8" ?>',
            '<!DOCTYPE tv SYSTEM "xmltv.dtd">',
            '<tv generator-info-name="Acestream Scraper EPG Generator" generator-info-url="https://github.com/pipepito/acestream-scraper">'
        ]
        
        # Get TV channels with filters
        channels, _, _ = self.tv_channel_repository.filter_channels(
            search_term=search_term,
            favorites_only=favorites_only,
            is_active=True,
            per_page=1000  # Large value to avoid pagination
        )
        
        # Filter to channels with EPG data AND associated acestreams
        channels_with_epg = []
        for channel in channels:
            if channel.epg_id and channel.acestream_channels.count() > 0:
                channels_with_epg.append(channel)
          # First, add channel definitions
        for channel in channels_with_epg:
            channel_id = channel.epg_id
            if not channel_id:
                continue
                
            xml_lines.append(f'  <channel id="{channel_id}">')
            xml_lines.append(f'    <display-name>{channel.name}</display-name>')
            
            if channel.logo_url:
                xml_lines.append(f'    <icon src="{channel.logo_url}" />')
                
            if channel.website:
                xml_lines.append(f'    <url>{channel.website}</url>')
                
            xml_lines.append('  </channel>')
        
        # Close the XML document
        # Note: In a real implementation, we would fetch and add program data here
        # But without actual EPG program data source, we're just creating channel definitions
        
        xml_lines.append('</tv>')
        
        return '\n'.join(xml_lines)
    
    def generate_all_streams_playlist(self, search_term=None, include_unassigned=True):
        """Generate M3U playlist with all acestreams, including both TV channels and unassigned streams.
        
        Args:
            search_term: Optional search term to filter channels by name
            include_unassigned: If True, include acestreams not assigned to TV channels
            
        Returns:
            String containing the M3U playlist content
        """
        playlist_lines = ['#EXTM3U']
        local_id = 0
        name_counts = {}
        
        # First, get all TV channels and their acestreams
        channels, _, _ = self.tv_channel_repository.filter_channels(
            search_term=search_term,
            per_page=1000  # Large value to avoid pagination
        )
        
        # Sort channels by channel_number if available
        sorted_channels = sorted(
            channels, 
            key=lambda c: (c.channel_number is None, c.channel_number or 0, c.name.lower())
        )
        
        processed_acestreams = set()
        
        # Process TV channels and their acestreams first
        for tv_channel in sorted_channels:
            acestreams = AcestreamChannel.query.filter_by(tv_channel_id=tv_channel.id).all()
            
            if not acestreams:
                continue
                
            # Sort acestreams by quality
            def score_acestream(acestream):
                score = 0
                if acestream.is_online:
                    score += 10
                if acestream.logo:
                    score += 3
                if acestream.tvg_id:
                    score += 2
                if acestream.tvg_name:
                    score += 1
                return score
                
            sorted_acestreams = sorted(acestreams, key=score_acestream, reverse=True)
            
            # Process each acestream for this TV channel
            for stream_index, acestream in enumerate(sorted_acestreams):
                processed_acestreams.add(acestream.id)
                
                stream_url = self._format_stream_url(acestream.id, local_id)
                local_id += 1
                
                # Channel numbering and naming
                base_name = tv_channel.name
                if len(sorted_acestreams) > 1:
                    display_name = f"{base_name} ({stream_index + 1})"
                else:
                    if base_name in name_counts:
                        name_counts[base_name] += 1
                        display_name = f"{base_name} {name_counts[base_name]}"
                    else:
                        name_counts[base_name] = 1
                        display_name = base_name
                
                metadata = []
                
                # Channel numbering with sub-numbering
                if tv_channel.channel_number is not None:
                    if len(sorted_acestreams) > 1:
                        channel_number = f"{tv_channel.channel_number}.{stream_index + 1}"
                    else:
                        channel_number = str(tv_channel.channel_number)
                    metadata.append(f'tvg-chno="{channel_number}"')
                
                # EPG and metadata
                if tv_channel.epg_id:
                    metadata.append(f'tvg-id="{tv_channel.epg_id}"')
                elif acestream.tvg_id:
                    metadata.append(f'tvg-id="{acestream.tvg_id}"')
                    
                metadata.append(f'tvg-name="{display_name}"')
                
                if tv_channel.logo_url:
                    metadata.append(f'tvg-logo="{tv_channel.logo_url}"')
                elif acestream.logo:
                    metadata.append(f'tvg-logo="{acestream.logo}"')
                    
                if tv_channel.category:
                    metadata.append(f'group-title="{tv_channel.category}"')
                
                extinf = '#EXTINF:-1'
                if metadata:
                    extinf += f' {"".join(metadata)}'
                extinf += f',{display_name}'
                
                playlist_lines.append(extinf)
                playlist_lines.append(stream_url)
        
        # Now process unassigned acestreams if requested
        if include_unassigned:
            unassigned_query = AcestreamChannel.query.filter_by(tv_channel_id=None)
            if search_term:
                unassigned_query = unassigned_query.filter(
                    AcestreamChannel.name.ilike(f'%{search_term}%')
                )
                
            unassigned_acestreams = unassigned_query.all()
            
            # Find the next available channel number
            next_channel_number = 9000  # Start unassigned streams at 9000
            if sorted_channels:
                max_channel_number = max((c.channel_number or 0) for c in sorted_channels)
                next_channel_number = max(next_channel_number, max_channel_number + 1)
            
            for acestream in unassigned_acestreams:
                if acestream.id in processed_acestreams:
                    continue
                    
                stream_url = self._format_stream_url(acestream.id, local_id)
                local_id += 1
                
                # Use acestream name or fallback
                display_name = acestream.name or f"Stream {acestream.id[:8]}"
                
                # Handle duplicate names
                if display_name in name_counts:
                    name_counts[display_name] += 1
                    display_name = f"{display_name} {name_counts[display_name]}"
                else:
                    name_counts[display_name] = 1
                
                metadata = []
                
                # Assign channel number to unassigned streams
                metadata.append(f'tvg-chno="{next_channel_number}"')
                next_channel_number += 1
                
                if acestream.tvg_id:
                    metadata.append(f'tvg-id="{acestream.tvg_id}"')
                    
                metadata.append(f'tvg-name="{display_name}"')
                
                if acestream.logo:
                    metadata.append(f'tvg-logo="{acestream.logo}"')
                    
                # Group unassigned streams
                if acestream.group:
                    metadata.append(f'group-title="{acestream.group}"')
                else:
                    metadata.append(f'group-title="Unassigned Streams"')
                
                extinf = '#EXTINF:-1'
                if metadata:
                    extinf += f' {"".join(metadata)}'
                extinf += f',{display_name}'
                
                playlist_lines.append(extinf)
                playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)