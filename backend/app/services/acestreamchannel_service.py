"""
Service for AcestreamChannel operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel

class AcestreamChannelService:
    """Service for AcestreamChannel-related operations"""
    def __init__(self, db: Session):
        self.repository = ChannelRepository(db)

    def get_all_channels(self, skip: int = 0, limit: int = 100, active_only: bool = True, search: Optional[str] = None) -> List[AcestreamChannel]:
        return self.repository.get_channels(skip=skip, limit=limit, active_only=active_only, search=search)

    def get_filtered_channels(self, search: Optional[str] = None, group: Optional[str] = None, only_online: bool = False, include_groups: Optional[List[str]] = None, exclude_groups: Optional[List[str]] = None) -> List[AcestreamChannel]:
        return self.repository.get_filtered_channels(search=search, group=group, only_online=only_online, include_groups=include_groups, exclude_groups=exclude_groups)

    def get_channel_groups(self) -> List[str]:
        return self.repository.get_unique_groups()

    def get_channel_by_id(self, channel_id: str) -> Optional[AcestreamChannel]:
        return self.repository.get_channel_by_id(channel_id)

    def create_channel(self, channel_id: str, name: str, source_url: Optional[str] = None, group: Optional[str] = None, logo: Optional[str] = None, tvg_id: Optional[str] = None, tvg_name: Optional[str] = None, is_online: Optional[bool] = None) -> AcestreamChannel:
        return self.repository.create_or_update_channel(channel_id=channel_id, name=name, source_url=source_url, group=group, logo=logo, tvg_id=tvg_id, tvg_name=tvg_name, is_online=is_online)

    def update_channel(self, channel_id: str, updates: Dict[str, Any]) -> Optional[AcestreamChannel]:
        return self.repository.update_channel(channel_id=channel_id, updates=updates)

    def delete_channel(self, channel_id: str) -> bool:
        return self.repository.delete_channel(channel_id)

    def check_channel_status(self, channel_id: str) -> Optional[AcestreamChannel]:
        return self.repository.update_channel_status(channel_id=channel_id, is_online=True)

    def check_all_channels_status(self) -> int:
        return self.repository.check_all_channels_status()

    def bulk_delete_channels(self, channel_ids: List[str]) -> bool:
        return self.repository.bulk_delete_channels(channel_ids)

    def bulk_update_channels(self, channel_ids: List[str], fields: Dict[str, Any]) -> List[AcestreamChannel]:
        return self.repository.bulk_update_channels(channel_ids, fields)

    def bulk_activate_channels(self, channel_ids: List[str], active: bool) -> List[AcestreamChannel]:
        return self.repository.bulk_activate_channels(channel_ids, active)

    def get_advanced_filtered_channels(self, skip: int = 0, limit: int = 100, active_only: bool = True, search: Optional[str] = None, group: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, is_active: Optional[bool] = None, is_online: Optional[bool] = None) -> List[AcestreamChannel]:
        return self.repository.get_advanced_filtered_channels(skip=skip, limit=limit, active_only=active_only, search=search, group=group, country=country, language=language, is_active=is_active, is_online=is_online)

    def get_advanced_filtered_channels_with_total(self, *args, **kwargs):
        return self.repository.get_advanced_filtered_channels_with_total(*args, **kwargs)
