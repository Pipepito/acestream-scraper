"""
Repository for channel data operations
"""
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.models.models import AcestreamChannel, EPGChannel, TVChannel


class ChannelRepository:
    def get_tv_channels_with_total(self, skip: int = 0, limit: int = 100) -> (list, int):
        query = self.db.query(TVChannel)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
    def assign_acestreams_to_tv_channel(self, acestream_ids: list, tv_channel_id: int) -> int:
        """Assign multiple acestream channels to a TV channel by setting their tv_channel_id."""
        if not acestream_ids:
            return 0
        available_count = (
            self.db.query(AcestreamChannel)
            .filter(
                AcestreamChannel.id.in_(acestream_ids),
                AcestreamChannel.tv_channel_id.is_(None),
            )
            .count()
        )
        if available_count != len(acestream_ids):
            raise ValueError("One or more accepted Acestream channels are already associated with another TV channel.")
        updated = (
            self.db.query(AcestreamChannel)
            .filter(
                AcestreamChannel.id.in_(acestream_ids),
                AcestreamChannel.tv_channel_id.is_(None),
            )
            .update({"tv_channel_id": tv_channel_id}, synchronize_session=False)
        )
        if self.db.in_nested_transaction():
            self.db.flush()
        else:
            self.db.commit()
        return updated
    def get_tv_channel_by_epg_id(self, epg_id: str) -> Optional[TVChannel]:
        """Get a TV channel by EPG ID"""
        return self.db.query(TVChannel).filter(TVChannel.epg_id == epg_id).first()

    def get_tv_channels_by_epg_id(self, epg_id: str) -> List[TVChannel]:
        """Get all TV channels for an EPG ID."""
        return self.db.query(TVChannel).filter(TVChannel.epg_id == epg_id).order_by(TVChannel.id.asc()).all()

    def get_epg_channels_by_ids(self, epg_channel_ids: List[int]) -> List[EPGChannel]:
        """Get EPG channels by IDs preserving deterministic order."""
        if not epg_channel_ids:
            return []
        return (
            self.db.query(EPGChannel)
            .filter(EPGChannel.id.in_(epg_channel_ids))
            .order_by(EPGChannel.id.asc())
            .all()
        )
    """Repository for channel operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_channels(self,
                    skip: int = 0,
                    limit: int = 100,
                    active_only: bool = True,
                    search: Optional[str] = None) -> List[AcestreamChannel]:
        """Get channels with optional filtering"""
        query = self.db.query(AcestreamChannel)

        if active_only:
            query = query.filter(AcestreamChannel.is_active == True)

        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))

        return query.offset(skip).limit(limit).all()

    def get_filtered_channels(self,
                             search: Optional[str] = None,
                             group: Optional[str] = None,
                             only_online: bool = False,
                             include_groups: Optional[List[str]] = None,
                             exclude_groups: Optional[List[str]] = None,
                             favorites_only: bool = False) -> List[AcestreamChannel]:
        """
        Get channels with advanced filtering options

        Args:
            search: Optional search term for channel names
            group: Optional specific group to filter by
            only_online: Whether to include only online channels
            include_groups: Optional list of groups to include
            exclude_groups: Optional list of groups to exclude
            favorites_only: Whether to include only channels linked to favorite TV channels

        Returns:
            List of filtered channels
        """
        query = self.db.query(AcestreamChannel)

        if favorites_only:
            query = query.join(TVChannel, AcestreamChannel.tv_channel_id == TVChannel.id).filter(TVChannel.is_favorite == True)

        # Apply filters
        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))

        if group:
            query = query.filter(AcestreamChannel.group == group)

        if only_online:
            query = query.filter(AcestreamChannel.is_online == True)

        if include_groups and len(include_groups) > 0:
            query = query.filter(AcestreamChannel.group.in_(include_groups))

        if exclude_groups and len(exclude_groups) > 0:
            query = query.filter(~AcestreamChannel.group.in_(exclude_groups))

        # Always sort by group and name
        query = query.order_by(AcestreamChannel.group, AcestreamChannel.name)

        return query.all()

    def get_unique_groups(self) -> List[str]:
        """
        Get a list of all unique channel groups

        Returns:
            List of group names
        """
        groups = self.db.query(AcestreamChannel.group).distinct().all()
        # Return only non-None/empty groups
        return [group[0] for group in groups if group[0]]

    def get_channel_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        """Get a channel by ID"""
        return self.db.query(AcestreamChannel).filter(AcestreamChannel.id == channel_id).first()

    def create_or_update_channel(self,
                               channel_id: str,
                               name: str,
                               source_url: Optional[str] = None,
                               group: Optional[str] = None,
                               logo: Optional[str] = None,
                               tvg_id: Optional[str] = None,
                               tvg_name: Optional[str] = None,
                               is_online: Optional[bool] = None,
                               commit: bool = True) -> AcestreamChannel:
        """Create a new channel or update existing one. Always update tvg_id and tvg_name if present (even if empty string)."""
        channel = self.get_channel_by_id(channel_id)

        if not channel:
            channel = AcestreamChannel(
                id=channel_id,
                name=name,
                source_url=source_url,
                group=group or None,
                logo=logo or None,
                tvg_id=tvg_id or None,
                tvg_name=tvg_name or None,
                last_seen=datetime.now(timezone.utc),
                is_active=True,
                is_online=is_online if is_online is not None else True  # Default to True
            )
            self.db.add(channel)
        else:
            # Update existing channel
            channel.name = name
            channel.last_seen = datetime.now(timezone.utc)
            channel.is_active = True
            if source_url is not None:
                channel.source_url = source_url
            if group is not None:
                channel.group = group or None
            if logo is not None:
                channel.logo = logo or None
            # Always update tvg_id and tvg_name, even if empty string (to allow clearing)
            if tvg_id is not None:
                channel.tvg_id = tvg_id or None
            if tvg_name is not None:
                channel.tvg_name = tvg_name or None
            if is_online is not None:
                channel.is_online = is_online

        if commit:
            self.db.commit()
            self.db.refresh(channel)
        else:
            self.db.flush()
        return channel

    def update_channel(self, channel_id: str, updates: Dict[str, Any]) -> AcestreamChannel:
        """Update channel properties"""
        channel = self.get_channel_by_id(channel_id)
        if not channel:
            return None

        # Update fields from the dictionary
        for key, value in updates.items():
            if hasattr(channel, key):
                setattr(channel, key, value)

        self.db.commit()
        self.db.refresh(channel)
        return channel

    def delete_channel(self, channel_id: str) -> bool:
        """Delete a channel"""
        channel = self.get_channel_by_id(channel_id)
        if not channel:
            return False

        self.db.delete(channel)
        self.db.commit()
        return True

    def bulk_delete_channels(self, channel_ids: List[str]) -> bool:
        """
        Delete multiple channels by IDs
        """
        if not channel_ids:
            return False
        deleted = (
            self.db.query(AcestreamChannel)
            .filter(AcestreamChannel.id.in_(channel_ids))
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return deleted > 0

    def bulk_update_channels(self, channel_ids: List[str], fields: Dict[str, Any]) -> List[AcestreamChannel]:
        """
        Update multiple channels by IDs and fields
        """
        if not channel_ids or not fields:
            return []
        valid_fields = {key: value for key, value in fields.items() if hasattr(AcestreamChannel, key)}
        if not valid_fields:
            return []
        updated = (
            self.db.query(AcestreamChannel)
            .filter(AcestreamChannel.id.in_(channel_ids))
            .all()
        )
        for channel in updated:
            for key, value in valid_fields.items():
                setattr(channel, key, value)
        self.db.commit()
        return updated

    def bulk_activate_channels(self, channel_ids: List[str], active: bool) -> List[AcestreamChannel]:
        """
        Activate/deactivate multiple channels by IDs
        """
        if not channel_ids:
            return []
        self.db.query(AcestreamChannel).filter(AcestreamChannel.id.in_(channel_ids)).update(
            {"is_active": active},
            synchronize_session=False,
        )
        self.db.commit()
        return (
            self.db.query(AcestreamChannel)
            .filter(AcestreamChannel.id.in_(channel_ids))
            .all()
        )

    def update_channel_status(self, channel_id: str, is_online: bool, error: str = None) -> AcestreamChannel:
        """Update the online status of a channel"""
        channel = self.get_channel_by_id(channel_id)
        if not channel:
            return None

        channel.is_online = is_online
        channel.last_checked = datetime.now(timezone.utc)
        channel.check_error = error
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def check_all_channels_status(self) -> int:
        """Check status for all active channels"""
        updated_count = (
            self.db.query(AcestreamChannel)
            .filter(AcestreamChannel.is_active == True)
            .update({"last_checked": datetime.now(timezone.utc)}, synchronize_session=False)
        )
        self.db.commit()
        return updated_count

    def get_tv_channels(self, skip: int = 0, limit: int = 100) -> List[TVChannel]:
        """Get TV channels"""
        return self.db.query(TVChannel).offset(skip).limit(limit).all()

    def get_tv_channel_by_id(self, tv_channel_id: int) -> Optional[TVChannel]:
        """Get a TV channel by ID"""
        return self.db.query(TVChannel).filter(TVChannel.id == tv_channel_id).first()

    def get_tv_channel_by_name(self, name: str) -> Optional[TVChannel]:
        """Get a TV channel by name"""
        return self.db.query(TVChannel).filter(TVChannel.name == name).first()

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
        """Create a new TV channel"""
        tv_channel = TVChannel(
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
        self.db.add(tv_channel)
        self.db.commit()
        self.db.refresh(tv_channel)
        return tv_channel

    def update_tv_channel(self, tv_channel_id: int, updates: Dict[str, Any]) -> Optional[TVChannel]:
        """Update TV channel properties"""
        tv_channel = self.get_tv_channel_by_id(tv_channel_id)
        if not tv_channel:
            return None

        # Update fields from the dictionary
        for key, value in updates.items():
            if hasattr(tv_channel, key):
                setattr(tv_channel, key, value)

        tv_channel.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(tv_channel)
        return tv_channel

    def delete_tv_channel(self, tv_channel_id: int) -> bool:
        """Delete a TV channel"""
        tv_channel = self.get_tv_channel_by_id(tv_channel_id)
        if not tv_channel:
            return False

        self.db.delete(tv_channel)
        self.db.commit()
        return True

    def associate_acestream_to_tv_channel(self,
                                        tv_channel_id: int,
                                        acestream_channel_id: str) -> bool:
        """Associate an acestream channel with a TV channel"""
        tv_channel = self.get_tv_channel_by_id(tv_channel_id)
        acestream_channel = self.get_channel_by_id(acestream_channel_id)

        if not tv_channel or not acestream_channel:
            return False

        acestream_channel.tv_channel_id = tv_channel_id
        self.db.commit()
        return True

    def remove_acestream_from_tv_channel(self,
                                       tv_channel_id: int,
                                       acestream_channel_id: str) -> bool:
        """Remove association between acestream and TV channel"""
        acestream_channel = self.get_channel_by_id(acestream_channel_id)

        if not acestream_channel or acestream_channel.tv_channel_id != tv_channel_id:
            return False

        acestream_channel.tv_channel_id = None
        self.db.commit()
        return True

    def get_advanced_filtered_channels(self,
                                      skip: int = 0,
                                      limit: int = 100,
                                      active_only: bool = True,
                                      search: Optional[str] = None,
                                      group: Optional[str] = None,
                                      country: Optional[str] = None,
                                      language: Optional[str] = None,
                                      is_active: Optional[bool] = None,
                                      is_online: Optional[bool] = None) -> List[AcestreamChannel]:
        """
        Get channels with advanced/custom field filtering
        """
        query = self.db.query(AcestreamChannel)
        if active_only:
            query = query.filter(AcestreamChannel.is_active == True)
        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))
        if group:
            query = query.filter(AcestreamChannel.group == group)
        if country:
            query = query.filter(AcestreamChannel.country == country)
        if language:
            query = query.filter(AcestreamChannel.language == language)
        if is_active is not None:
            query = query.filter(AcestreamChannel.is_active == is_active)
        if is_online is not None:
            query = query.filter(AcestreamChannel.is_online == is_online)
        return query.offset(skip).limit(limit).all()

    def get_advanced_filtered_channels_with_total(self,
                                      skip: int = 0,
                                      limit: int = 100,
                                      active_only: bool = True,
                                      search: Optional[str] = None,
                                      group: Optional[str] = None,
                                      country: Optional[str] = None,
                                      language: Optional[str] = None,
                                      is_active: Optional[bool] = None,
                                      is_online: Optional[bool] = None):
        """
        Get paginated channels and total count for current filter
        """
        query = self.db.query(AcestreamChannel)
        if active_only:
            query = query.filter(AcestreamChannel.is_active == True)
        if search:
            query = query.filter(AcestreamChannel.name.ilike(f"%{search}%"))
        if group:
            query = query.filter(AcestreamChannel.group == group)
        if country:
            query = query.filter(AcestreamChannel.country == country)
        if language:
            query = query.filter(AcestreamChannel.language == language)
        if is_active is not None:
            query = query.filter(AcestreamChannel.is_active == is_active)
        if is_online is not None:
            query = query.filter(AcestreamChannel.is_online == is_online)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total
