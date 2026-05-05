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
        exclude_groups: Optional[List[str]] = None,
        favorites_only: bool = False,
        base_url: Optional[str] = None,
        format: Optional[str] = None
    ) -> str:
        """
        Generate an M3U playlist with the specified filters

        Args:
            search: Optional search term for channel names
            group: Optional group filter
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude
            favorites_only: Whether to include only channels linked to favorite TV channels
            base_url: Optional base URL for stream links
            format: Optional format for the playlist output

        Returns:
            The M3U playlist content as a string
        """
        # Fetch channels that match criteria
        channels = self.channel_repository.get_filtered_channels(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups,
            favorites_only=favorites_only
        )

        # Load runtime settings for base URL fallback and addpid toggle.
        from app.repositories.settings_repository import SettingsRepository
        settings_repo = SettingsRepository(self.db)

        # Always get base_url from settings if not provided.
        if not base_url:
            base_url = settings_repo.get_setting(
                SettingsRepository.BASE_URL,
                SettingsRepository.DEFAULT_BASE_URL
            )

        # Get addpid config only.
        addpid = settings_repo.get_setting(SettingsRepository.ADDPID, SettingsRepository.DEFAULT_ADDPID)
        addpid_enabled = str(addpid).lower() in ("true", "1")

        # Generate M3U content
        m3u_content = self._generate_m3u_content(
            channels,
            base_url=base_url,
            format=format,
            addpid=addpid_enabled
        )
        return m3u_content

    async def get_channel_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups

        Returns:
            List of group names
        """
        return self.channel_repository.get_unique_groups()

    def _generate_m3u_content(self, channels: List[AcestreamChannel], base_url: Optional[str] = None, format: Optional[str] = None, addpid: bool = False) -> str:
        """
        Convert channels to M3U format, supporting custom base_url and format

        Args:
            channels: List of channels to include
            base_url: Optional base URL for stream links
            format: Optional format for the playlist output

        Returns:
            M3U formatted string
        """
        # M3U header
        header = "#EXTM3U\n"

        # Generate each channel entry
        entries = []
        pid_counter = 1

        for channel in channels:
            # Skip invalid channels
            if not channel.id or not channel.name:
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

            # Use base_url as-is, concatenate channel.id
            link = f'{base_url}{channel.id}'
            if addpid:
                link += f'&pid={pid_counter}'
            entry += link + '\n'

            entries.append(entry)
            if addpid:
                pid_counter += 1

        # Combine all parts
        return header + '\n'.join(entries)
