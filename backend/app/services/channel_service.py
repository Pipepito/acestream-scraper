"""
Service for channel operations
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy.orm import Session
from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel, TVChannel
from app.services.acestreamchannel_service import AcestreamChannelService
from app.services.tvchannel_service import TVChannelService


class ChannelService:
    """Service for channel-related operations"""

    def __init__(self, db: Session):
        self.acestream_service = AcestreamChannelService(db)
        self.tv_service = TVChannelService(db)
        self.repository = ChannelRepository(db)

    # Delegate AcestreamChannel methods
    def get_all_channels(self,
                        skip: int = 0,
                        limit: int = 100,
                        active_only: bool = True,
                        search: Optional[str] = None) -> List[AcestreamChannel]:
        """
        Get all channels with optional filtering

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            active_only: Whether to include only active channels
            search: Optional search term

        Returns:
            List of channels
        """
        return self.acestream_service.get_all_channels(
            skip=skip,
            limit=limit,
            active_only=active_only,
            search=search
        )

    def get_filtered_channels(self,
                             search: Optional[str] = None,
                             group: Optional[str] = None,
                             only_online: bool = False,
                             include_groups: Optional[List[str]] = None,
                             exclude_groups: Optional[List[str]] = None) -> List[AcestreamChannel]:
        """
        Get channels with advanced filtering options

        Args:
            search: Optional search term for channel names
            group: Optional specific group to filter by
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude

        Returns:
            List of filtered channels
        """
        return self.acestream_service.get_filtered_channels(
            search=search,
            group=group,
            only_online=only_online,
            include_groups=include_groups,
            exclude_groups=exclude_groups
        )

    def get_channel_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups

        Returns:
            List of group names
        """
        return self.acestream_service.get_channel_groups()

    def get_channel_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        """
        Get a channel by ID

        Args:
            channel_id: The acestream ID

        Returns:
            Channel object or None
        """
        return self.acestream_service.get_channel_by_id(channel_id)

    def create_channel(self,
                      channel_id: str,
                      name: str,
                      source_url: Optional[str] = None,
                      group: Optional[str] = None,
                      logo: Optional[str] = None,
                      tvg_id: Optional[str] = None,
                      tvg_name: Optional[str] = None,
                      is_online: Optional[bool] = None) -> AcestreamChannel:
        """
        Create a new channel

        Args:
            channel_id: The acestream ID
            name: The channel name
            source_url: Optional URL where the channel was found
            group: Optional channel group
            logo: Optional URL to channel logo
            tvg_id: Optional TV guide ID
            tvg_name: Optional TV guide name
            is_online: Optional online status

        Returns:
            The created channel
        """
        return self.acestream_service.create_channel(
            channel_id=channel_id,
            name=name,
            source_url=source_url,
            group=group,
            logo=logo,
            tvg_id=tvg_id,
            tvg_name=tvg_name,
            is_online=is_online
        )

    def update_channel(self, channel_id: str, updates: Dict[str, Any]) -> Optional[AcestreamChannel]:
        """
        Update a channel

        Args:
            channel_id: The acestream ID
            updates: Dictionary of fields to update

        Returns:
            Updated channel or None if not found
        """
        return self.acestream_service.update_channel(channel_id=channel_id, updates=updates)

    def delete_channel(self, channel_id: str) -> bool:
        """
        Delete a channel

        Args:
            channel_id: The acestream ID

        Returns:
            True if deleted, False if not found
        """
        return self.acestream_service.delete_channel(channel_id)

    def check_channel_status(self, channel_id: str) -> Optional[AcestreamChannel]:
        """
        Check if a channel is online

        Args:
            channel_id: The acestream ID

        Returns:
            Updated channel or None if not found
        """
        # In a real implementation, this would check the acestream status
        # For now, we'll just mark it as online
        return self.acestream_service.check_channel_status(channel_id=channel_id, is_online=True)

    def check_all_channels_status(self) -> int:
        """
        Check status for all channels

        Returns:
            Number of channels checked
        """
        return self.acestream_service.check_all_channels_status()

    # TV Channel methods

    def get_all_tv_channels(self, skip: int = 0, limit: int = 100) -> List[TVChannel]:
        """
        Get all TV channels

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of TV channels
        """
        return self.tv_service.get_all_tv_channels(skip=skip, limit=limit)

    def get_tv_channel_by_id(self, tv_channel_id: int) -> Optional[TVChannel]:
        """
        Get a TV channel by ID

        Args:
            tv_channel_id: The TV channel ID

        Returns:
            TV channel or None
        """
        return self.tv_service.get_tv_channel_by_id(tv_channel_id)

    def get_tv_channel_by_name(self, name: str) -> Optional[TVChannel]:
        """
        Get a TV channel by name

        Args:
            name: The TV channel name

        Returns:
            TV channel or None
        """
        return self.tv_service.get_tv_channel_by_name(name)

    def create_tv_channel(self,
                         name: str,
                         logo_url: Optional[str] = None,
                         description: Optional[str] = None,
                         category: Optional[str] = None,
                         country: Optional[str] = None,
                         language: Optional[str] = None,
                         website: Optional[str] = None,
                         epg_id: Optional[str] = None,
                         epg_source_id: Optional[int] = None,
                         channel_number: Optional[int] = None,
                         is_active: bool = True,
                         is_favorite: bool = False) -> TVChannel:
        """
        Create a new TV channel

        Args:
            name: The channel name
            logo_url: Optional URL to channel logo
            description: Optional channel description
            category: Optional channel category
            country: Optional channel country
            language: Optional channel language
            website: Optional channel website
            epg_id: Optional EPG ID
            epg_source_id: Optional EPG source ID
            channel_number: Optional channel number
            is_active: Whether the channel is active
            is_favorite: Whether the channel is a favorite

        Returns:
            The created TV channel
        """
        return self.tv_service.create_tv_channel(
            name=name,
            logo_url=logo_url,
            description=description,
            category=category,
            country=country,
            language=language,
            website=website,
            epg_id=epg_id,
            epg_source_id=epg_source_id,
            channel_number=channel_number,
            is_active=is_active,
            is_favorite=is_favorite
        )

    def update_tv_channel(self, tv_channel_id: int, updates: Dict[str, Any]) -> Optional[TVChannel]:
        """
        Update a TV channel

        Args:
            tv_channel_id: The TV channel ID
            updates: Dictionary of fields to update

        Returns:
            Updated TV channel or None if not found
        """
        return self.tv_service.update_tv_channel(tv_channel_id=tv_channel_id, updates=updates)

    def delete_tv_channel(self, tv_channel_id: int) -> bool:
        """
        Delete a TV channel

        Args:
            tv_channel_id: The TV channel ID

        Returns:
            True if deleted, False if not found
        """
        return self.tv_service.delete_tv_channel(tv_channel_id)

    def associate_acestream(self, tv_channel_id: int, acestream_id: str) -> bool:
        """
        Associate an acestream with a TV channel

        Args:
            tv_channel_id: The TV channel ID
            acestream_id: The acestream ID

        Returns:
            True if associated, False if either not found
        """
        return self.tv_service.associate_acestream(tv_channel_id=tv_channel_id, acestream_id=acestream_id)

    def remove_acestream_association(self, tv_channel_id: int, acestream_id: str) -> bool:
        """
        Remove an acestream association from a TV channel

        Args:
            tv_channel_id: The TV channel ID
            acestream_id: The acestream ID

        Returns:
            True if removed, False if not found
        """
        return self.tv_service.remove_acestream_association(tv_channel_id=tv_channel_id, acestream_id=acestream_id)

    def batch_associate_acestreams(self, assignments: List[Dict]) -> Dict[str, Any]:
        """
        Associate multiple acestreams with TV channels

        Args:
            assignments: List of dictionaries with tv_channel_id and acestream_channel_id

        Returns:
            Dictionary with results
        """
        return self.tv_service.batch_associate_acestreams(assignments=assignments)

    def get_advanced_filtered_channels_with_total(self, *args, **kwargs):
        """
        Get channels with advanced/custom field filtering and total count
        """
        return self.acestream_service.get_advanced_filtered_channels_with_total(*args, **kwargs)
