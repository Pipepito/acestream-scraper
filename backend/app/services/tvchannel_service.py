"""
Service for TVChannel operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.channel_repository import ChannelRepository
from app.models.models import TVChannel

class TVChannelService:
    def get_tv_channels_with_total(self, skip: int = 0, limit: int = 100):
        return self.repository.get_tv_channels_with_total(skip=skip, limit=limit)
    def get_tv_channel_by_epg_id(self, epg_id: str) -> Optional[TVChannel]:
        return self.repository.get_tv_channel_by_epg_id(epg_id)
    """Service for TVChannel-related operations"""
    def __init__(self, db: Session):
        self.repository = ChannelRepository(db)

    def get_all_tv_channels(self, skip: int = 0, limit: int = 100) -> List[TVChannel]:
        return self.repository.get_tv_channels(skip=skip, limit=limit)

    def get_tv_channel_by_id(self, tv_channel_id: int) -> Optional[TVChannel]:
        return self.repository.get_tv_channel_by_id(tv_channel_id)

    def get_tv_channel_by_name(self, name: str) -> Optional[TVChannel]:
        return self.repository.get_tv_channel_by_name(name)

    def create_tv_channel(self, name: str, logo_url: Optional[str] = None, description: Optional[str] = None, category: Optional[str] = None, country: Optional[str] = None, language: Optional[str] = None, website: Optional[str] = None, epg_id: Optional[str] = None, epg_source_id: Optional[int] = None, channel_number: Optional[int] = None, is_active: bool = True, is_favorite: bool = False) -> TVChannel:
        return self.repository.create_tv_channel(name=name, logo_url=logo_url, description=description, category=category, country=country, language=language, website=website, epg_id=epg_id, epg_source_id=epg_source_id, channel_number=channel_number, is_active=is_active, is_favorite=is_favorite)

    def update_tv_channel(self, tv_channel_id: int, updates: Dict[str, Any]) -> Optional[TVChannel]:
        return self.repository.update_tv_channel(tv_channel_id=tv_channel_id, updates=updates)

    def delete_tv_channel(self, tv_channel_id: int) -> bool:
        return self.repository.delete_tv_channel(tv_channel_id)

    def associate_acestream(self, tv_channel_id: int, acestream_id: str) -> bool:
        return self.repository.associate_acestream_to_tv_channel(tv_channel_id=tv_channel_id, acestream_channel_id=acestream_id)

    def remove_acestream_association(self, tv_channel_id: int, acestream_id: str) -> bool:
        return self.repository.remove_acestream_from_tv_channel(tv_channel_id=tv_channel_id, acestream_channel_id=acestream_id)

    def batch_associate_acestreams(self, assignments: List[Dict]) -> Dict[str, Any]:
        results = {"success_count": 0, "failure_count": 0, "details": {}}
        for assignment in assignments:
            tv_channel_id = assignment.get("tv_channel_id")
            acestream_id = assignment.get("acestream_channel_id")
            if tv_channel_id is None or acestream_id is None:
                results["failure_count"] += 1
                continue
            tv_channel_id_str = str(tv_channel_id)
            if tv_channel_id_str not in results["details"]:
                results["details"][tv_channel_id_str] = {"success": [], "failure": []}
            success = self.associate_acestream(tv_channel_id, acestream_id)
            if success:
                results["success_count"] += 1
                results["details"][tv_channel_id_str]["success"].append(acestream_id)
            else:
                results["failure_count"] += 1
                results["details"][tv_channel_id_str]["failure"].append(acestream_id)
        return results
