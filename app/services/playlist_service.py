import os
from typing import List, Dict, Optional
from ..repositories import ChannelRepository
from app.utils.config import Config
from app.repositories.tv_channel_repository import TVChannelRepository
from app.services.tv_channel_service import TVChannelService

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
                extinf += f' {" ".join(metadata)}'
            extinf += f',{display_name}'
            
            playlist_lines.append(extinf)
            playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)
        
    def generate_tv_channels_playlist(self, search_term=None, favorites_only=False):
        """Generate M3U playlist with TV channels using their best acestreams.
        
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
        
        # Process each TV channel
        for local_id, tv_channel in enumerate(sorted_channels, start=0):
            # Get the best acestream for this TV channel
            best_acestream = self.tv_channel_service.get_best_acestream(tv_channel.id)
            
            # Skip channels without acestreams
            if not best_acestream:
                continue
                
            # Use _format_stream_url to get the correct URL format for the best acestream
            stream_url = self._format_stream_url(best_acestream.id, local_id)
            
            # Handle duplicate names
            base_name = tv_channel.name
            if base_name in name_counts:
                name_counts[base_name] += 1
                display_name = f"{base_name} {name_counts[base_name]}"
            else:
                name_counts[base_name] = 1
                display_name = base_name
            
            # Add metadata if available
            metadata = []
            
            # If channel has a channel number, include it as tvg-chno
            if tv_channel.channel_number is not None:
                metadata.append(f'tvg-chno="{tv_channel.channel_number}"')
            
            # Prioritize TV channel metadata, fall back to acestream metadata if needed
            if tv_channel.epg_id:
                metadata.append(f'tvg-id="{tv_channel.epg_id}"')
            elif best_acestream.tvg_id:
                metadata.append(f'tvg-id="{best_acestream.tvg_id}"')
                
            metadata.append(f'tvg-name="{display_name}"')
            
            # Use TV channel logo if available, otherwise use acestream logo
            if tv_channel.logo_url:
                metadata.append(f'tvg-logo="{tv_channel.logo_url}"')
            elif best_acestream.logo:
                metadata.append(f'tvg-logo="{best_acestream.logo}"')
                
            # Use channel category as group
            if tv_channel.category:
                metadata.append(f'group-title="{tv_channel.category}"')
            
            # Create EXTINF line with metadata
            extinf = '#EXTINF:-1'
            if metadata:
                extinf += f' {" ".join(metadata)}'
            extinf += f',{display_name}'
            
            playlist_lines.append(extinf)
            playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)
        
    def generate_epg_xml(self, search_term=None, favorites_only=False):
        """Generate XML EPG guide for channels with EPG data.
        
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
        
        # Filter to channels with EPG data
        channels_with_epg = [c for c in channels if c.epg_id]
        
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