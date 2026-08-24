"""Service for TVChannel operations"""
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.channel_repository import ChannelRepository
from app.models.models import AcestreamChannel, EPGChannel, TVChannel
from app.services.epg_match_service import EPGMatchService

class TVChannelService:
    def get_tv_channels_with_total(self, skip: int = 0, limit: int = 100,
                                   search: Optional[str] = None,
                                   favorites_only: bool = False):
        return self.repository.get_tv_channels_with_total(
            skip=skip, limit=limit, search=search, favorites_only=favorites_only
        )
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
        tv_channel = self.repository.create_tv_channel(name=name, logo_url=logo_url, description=description, category=category, country=country, language=language, website=website, epg_id=epg_id, epg_source_id=epg_source_id, channel_number=channel_number, is_active=is_active, is_favorite=is_favorite)
        self.auto_associate_acestreams(tv_channel)
        return tv_channel

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

    def create_tv_channels_from_epg(self, epg_channel_ids: List[int]) -> Dict[str, Any]:
        created_channels: List[TVChannel] = []
        skipped_count = 0
        associated_count = 0

        epg_channels = (
            self.repository.db.query(EPGChannel)
            .filter(EPGChannel.id.in_(epg_channel_ids))
            .all()
        )

        for epg_channel in epg_channels:
            existing_channel = self.get_tv_channel_by_epg_id(epg_channel.channel_xml_id)
            if existing_channel:
                skipped_count += 1
                continue

            tv_channel = self.repository.create_tv_channel(
                name=epg_channel.name,
                logo_url=getattr(epg_channel, "icon_url", None),
                language=getattr(epg_channel, "language", None),
                epg_id=epg_channel.channel_xml_id,
                epg_source_id=epg_channel.epg_source_id,
                is_active=True,
                is_favorite=False,
            )
            created_channels.append(tv_channel)
            associated_count += self.auto_associate_acestreams(tv_channel)

        return {
            "created_count": len(created_channels),
            "skipped_count": skipped_count,
            "associated_count": associated_count,
            "items": created_channels,
        }

    def create_tv_channels_from_epg_analysis(self, strictness: str, epg_channel_ids: List[int]) -> Dict[str, Any]:
        selected_ids = sorted(set(epg_channel_ids))
        analysis = EPGMatchService(self.repository.db).analyze_matches(
            strictness=strictness,
            epg_channel_ids=selected_ids,
        )
        selected_rows = analysis["rows"]

        if not selected_rows:
            raise ValueError("No accepted matches found for selected EPG rows.")

        accepted_rows = [row for row in selected_rows if row["candidates"]]
        if not accepted_rows:
            raise ValueError("No accepted matches found for selected EPG rows.")

        epg_channels = {
            channel.id: channel
            for channel in self.repository.get_epg_channels_by_ids([row["epg_channel_id"] for row in selected_rows])
        }

        created_count = 0
        skipped_count = 0
        associated_count = 0
        failure_count = 0
        row_outcomes: List[Dict[str, Any]] = []

        for row in selected_rows:
            epg_channel_id = row["epg_channel_id"]
            epg_channel = epg_channels.get(epg_channel_id)
            if epg_channel is None:
                failure_count += 1
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel_id,
                        "status": "failed",
                        "reason": "Selected EPG channel not found.",
                        "associated_count": 0,
                    }
                )
                continue

            existing_channels = self.repository.get_tv_channels_by_epg_id(epg_channel.channel_xml_id)
            if len(existing_channels) > 1:
                skipped_count += 1
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel.id,
                        "status": "duplicate_existing_conflict",
                        "reason": "Multiple TV channels already exist for this epg_id.",
                        "associated_count": 0,
                    }
                )
                continue

            if len(existing_channels) == 1:
                skipped_count += 1
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel.id,
                        "status": "skipped_existing",
                        "reason": "A TV channel already exists for this epg_id.",
                        "tv_channel_id": existing_channels[0].id,
                        "associated_count": 0,
                    }
                )
                continue

            candidate_ids = [candidate["acestream_channel_id"] for candidate in row["candidates"]]
            if not candidate_ids:
                skipped_count += 1
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel.id,
                        "status": "no_accepted_matches",
                        "reason": "No accepted matches found for selected EPG row.",
                        "associated_count": 0,
                    }
                )
                continue

            try:
                with self.repository.db.begin_nested():
                    tv_channel = TVChannel(
                        name=epg_channel.name,
                        logo_url=getattr(epg_channel, "icon_url", None),
                        language=getattr(epg_channel, "language", None),
                        epg_id=epg_channel.channel_xml_id,
                        epg_source_id=epg_channel.epg_source_id,
                        is_active=True,
                        is_favorite=False,
                    )
                    self.repository.db.add(tv_channel)
                    self.repository.db.flush()

                    associated_for_row = self.repository.assign_acestreams_to_tv_channel(candidate_ids, tv_channel.id)
                    self.repository.db.refresh(tv_channel)

                created_count += 1
                associated_count += associated_for_row
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel.id,
                        "status": "created",
                        "tv_channel_id": tv_channel.id,
                        "associated_count": associated_for_row,
                    }
                )
            except Exception as exc:
                failure_count += 1
                row_outcomes.append(
                    {
                        "epg_channel_id": epg_channel.id,
                        "status": "failed",
                        "reason": str(exc),
                        "associated_count": 0,
                    }
                )

        try:
            self.repository.db.commit()
        except SQLAlchemyError:
            self.repository.db.rollback()
            raise

        if not accepted_rows:
            raise ValueError("No accepted matches found for selected EPG rows.")

        return {
            "created_count": created_count,
            "skipped_count": skipped_count,
            "associated_count": associated_count,
            "failure_count": failure_count,
            "row_outcomes": row_outcomes,
        }

    def set_favorite(self, tv_channel_id: int, value: Optional[bool] = None) -> Optional[TVChannel]:
        """Set (or toggle when value is None) a TV channel's favorite flag."""
        tv_channel = self.repository.get_tv_channel_by_id(tv_channel_id)
        if tv_channel is None:
            return None
        new_value = (not tv_channel.is_favorite) if value is None else value
        return self.repository.update_tv_channel(tv_channel_id, {"is_favorite": new_value})

    def find_unassigned_matches(self, tv_channel_id: int) -> Optional[List[AcestreamChannel]]:
        """Suggest unassigned acestreams matching a TV channel by EPG id or
        normalized name. Returns None when the TV channel does not exist."""
        tv_channel = self.repository.get_tv_channel_by_id(tv_channel_id)
        if tv_channel is None:
            return None
        candidates = self._find_matching_acestreams(tv_channel)
        return [candidate for candidate in candidates if candidate.tv_channel_id is None]

    def auto_associate_acestreams(self, tv_channel: TVChannel) -> int:
        candidates = self._find_matching_acestreams(tv_channel)
        candidate_ids = [candidate.id for candidate in candidates if candidate.tv_channel_id != tv_channel.id]
        if not candidate_ids:
            return 0
        return self.repository.assign_acestreams_to_tv_channel(candidate_ids, tv_channel.id)

    def _find_matching_acestreams(self, tv_channel: TVChannel) -> List[AcestreamChannel]:
        matched: Dict[str, AcestreamChannel] = {}

        if tv_channel.epg_id:
            epg_matches = (
                self.repository.db.query(AcestreamChannel)
                .filter(AcestreamChannel.tvg_id == tv_channel.epg_id)
                .all()
            )
            for channel in epg_matches:
                matched[channel.id] = channel

        target_name = self._normalize_channel_name(tv_channel.name)
        if target_name:
            name_candidates = self.repository.db.query(AcestreamChannel).all()
            for channel in name_candidates:
                candidate_names = [channel.name, channel.tvg_name]
                if any(self._normalize_channel_name(candidate_name) == target_name for candidate_name in candidate_names if candidate_name):
                    matched[channel.id] = channel

        return list(matched.values())

    @staticmethod
    def _normalize_channel_name(value: Optional[str]) -> str:
        if not value:
            return ""
        normalized = value.lower()
        normalized = re.sub(r"\b(hd|fhd|uhd|4k)\b", " ", normalized)
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
        return " ".join(normalized.split())
