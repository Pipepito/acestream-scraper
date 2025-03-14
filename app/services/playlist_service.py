from ..repositories import ChannelRepository
from app.utils.config import Config

class PlaylistService:
    def __init__(self):
        self.channel_repository = ChannelRepository()
        self.config = Config()

    def _format_stream_url(self, channel_id: str, local_id: int) -> str:
        """Format stream URL based on base_url configuration."""
        # Get base_url directly from config instance
        base_url = getattr(self.config, 'base_url', 'acestream://')
        return f'{base_url}{channel_id}&pid={local_id}'

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
        
        # Add each channel to the playlist
        for local_id, channel in enumerate(channels, start=0):
            # Use _format_stream_url to get the correct URL format
            stream_url = self._format_stream_url(channel.id, local_id)
            
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
            extinf += f',{channel.name}'
            
            playlist_lines.append(extinf)
            playlist_lines.append(stream_url)
            
        return '\n'.join(playlist_lines)