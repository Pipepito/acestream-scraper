"""Bulk EPG-to-Acestream match analysis service."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import AcestreamChannel, EPGChannel, TVChannel


MAX_ANALYSIS_COMPARISONS = 50_000_000

STRICTNESS_THRESHOLDS = {
    "loose": 0.70,
    "balanced": 0.82,
    "strict": 0.92,
}

STAGE_PRIORITY = {
    "xml_id_exact": 0,
    "name_exact": 1,
    "name_similarity": 2,
}

QUALITY_PATTERN = re.compile(r"\b(?:hd|fhd|uhd|sd|4k)\b", re.IGNORECASE)
BRACKET_PATTERN = re.compile(r"\([^)]*\)|\[[^\]]*\]|\{[^}]*\}")
SEPARATOR_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass
class CandidateMatch:
    acestream_channel: AcestreamChannel
    score: float
    match_stage: str


class EPGMatchService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_matches(
        self,
        strictness: str,
        source_id: Optional[int] = None,
        epg_channel_ids: Optional[List[int]] = None,
    ) -> Dict[str, object]:
        threshold = STRICTNESS_THRESHOLDS[strictness]
        epg_query = self.db.query(EPGChannel)
        if source_id is not None:
            epg_query = epg_query.filter(EPGChannel.epg_source_id == source_id)
        if epg_channel_ids is not None:
            if not epg_channel_ids:
                epg_channels = []
            else:
                epg_query = epg_query.filter(EPGChannel.id.in_(epg_channel_ids))
        if epg_channel_ids is None or epg_channel_ids:
            epg_channels = epg_query.order_by(EPGChannel.name.asc(), EPGChannel.id.asc()).all()
        acestream_channels = self.db.query(AcestreamChannel).order_by(AcestreamChannel.name.asc(), AcestreamChannel.id.asc()).all()

        self._ensure_budget(len(epg_channels), len(acestream_channels))

        existing_channels = self._load_existing_tv_channels(epg_channels)
        row_state = []
        candidate_claims: Dict[str, List[Dict[str, object]]] = {}

        for epg_channel in epg_channels:
            matches = self._match_candidates(epg_channel, acestream_channels, threshold)
            row = {
                "epg_channel": epg_channel,
                "existing_tv_channel_ids": existing_channels.get(epg_channel.channel_xml_id, []),
                "candidates": matches,
            }
            row_state.append(row)
            for match in matches:
                candidate_claims.setdefault(match.acestream_channel.id, []).append(
                    {
                        "epg_channel": epg_channel,
                        "candidate": match,
                    }
                )

        winning_candidate_ids = self._resolve_candidate_uniqueness(candidate_claims)
        rows = []
        matched_epg_channels = 0
        matched_acestream_channels = 0
        creatable_rows = 0
        skipped_existing_tv_channels = 0

        for row in row_state:
            epg_channel = row["epg_channel"]
            accepted_candidates = [
                candidate
                for candidate in row["candidates"]
                if winning_candidate_ids.get(candidate.acestream_channel.id) == epg_channel.id
            ]
            accepted_candidates.sort(key=self._candidate_sort_key)

            best_candidate = accepted_candidates[0] if accepted_candidates else None
            existing_tv_channel_ids = row["existing_tv_channel_ids"]
            existing_tv_channel_id = existing_tv_channel_ids[0] if len(existing_tv_channel_ids) == 1 else None
            has_duplicate_existing_conflict = len(existing_tv_channel_ids) > 1
            is_creatable = bool(accepted_candidates) and not existing_tv_channel_ids
            if accepted_candidates:
                matched_epg_channels += 1
                matched_acestream_channels += len(accepted_candidates)
            if is_creatable:
                creatable_rows += 1
            if existing_tv_channel_ids:
                skipped_existing_tv_channels += 1

            rows.append(
                {
                    "epg_channel_id": epg_channel.id,
                    "epg_channel_xml_id": epg_channel.channel_xml_id,
                    "epg_channel_name": epg_channel.name,
                    "epg_source_id": epg_channel.epg_source_id,
                    "epg_source_name": epg_channel.epg_source.name if epg_channel.epg_source else None,
                    "existing_tv_channel_id": existing_tv_channel_id,
                    "existing_tv_channel_count": len(existing_tv_channel_ids),
                    "has_duplicate_existing_conflict": has_duplicate_existing_conflict,
                    "candidate_count": len(accepted_candidates),
                    "candidates": [self._serialize_candidate(candidate) for candidate in accepted_candidates],
                    "best_match_type": best_candidate.match_stage if best_candidate else None,
                    "best_match_confidence": self._confidence_for_candidate(best_candidate),
                    "is_creatable": is_creatable,
                }
            )

        return {
            "summary": {
                "epg_channels_analyzed": len(epg_channels),
                "matched_epg_channels": matched_epg_channels,
                "matched_acestream_channels": matched_acestream_channels,
                "creatable_rows": creatable_rows,
                "skipped_existing_tv_channels": skipped_existing_tv_channels,
            },
            "rows": rows,
        }

    def _ensure_budget(self, epg_count: int, acestream_count: int) -> None:
        if epg_count * acestream_count > MAX_ANALYSIS_COMPARISONS:
            raise ValueError(
                f"Estimated analysis workload exceeds budget ({epg_count} x {acestream_count} comparisons)."
            )

    def _load_existing_tv_channels(self, epg_channels: List[EPGChannel]) -> Dict[str, List[int]]:
        xml_ids = [channel.channel_xml_id for channel in epg_channels]
        if not xml_ids:
            return {}
        existing = self.db.query(TVChannel).filter(TVChannel.epg_id.in_(xml_ids)).all()
        existing_by_epg_id: Dict[str, List[int]] = {}
        for channel in existing:
            if not channel.epg_id:
                continue
            existing_by_epg_id.setdefault(channel.epg_id, []).append(channel.id)
        for channel_ids in existing_by_epg_id.values():
            channel_ids.sort()
        return existing_by_epg_id

    def _match_candidates(
        self,
        epg_channel: EPGChannel,
        acestream_channels: List[AcestreamChannel],
        threshold: float,
    ) -> List[CandidateMatch]:
        matches: List[CandidateMatch] = []
        normalized_epg_name = self.normalize_name(epg_channel.name)

        for acestream_channel in acestream_channels:
            match = self._score_candidate(epg_channel, normalized_epg_name, acestream_channel, threshold)
            if match is not None:
                matches.append(match)

        return matches

    def _score_candidate(
        self,
        epg_channel: EPGChannel,
        normalized_epg_name: str,
        acestream_channel: AcestreamChannel,
        threshold: float,
    ) -> Optional[CandidateMatch]:
        if epg_channel.channel_xml_id and acestream_channel.tvg_id == epg_channel.channel_xml_id:
            return CandidateMatch(acestream_channel=acestream_channel, score=1.0, match_stage="xml_id_exact")

        candidate_names = [name for name in [acestream_channel.name, acestream_channel.tvg_name] if name]
        normalized_names = [self.normalize_name(name) for name in candidate_names]

        if normalized_epg_name and any(name == normalized_epg_name for name in normalized_names if name):
            return CandidateMatch(acestream_channel=acestream_channel, score=1.0, match_stage="name_exact")

        if not normalized_epg_name:
            return None

        best_score = 0.0
        for normalized_name in normalized_names:
            if not normalized_name:
                continue
            best_score = max(best_score, SequenceMatcher(None, normalized_epg_name, normalized_name).ratio())

        if best_score >= threshold:
            return CandidateMatch(acestream_channel=acestream_channel, score=best_score, match_stage="name_similarity")
        return None

    def _resolve_candidate_uniqueness(self, candidate_claims: Dict[str, List[Dict[str, object]]]) -> Dict[str, int]:
        winners: Dict[str, int] = {}
        for candidate_id, claims in candidate_claims.items():
            winning_claim = sorted(claims, key=self._candidate_claim_sort_key)[0]
            winners[candidate_id] = winning_claim["epg_channel"].id
        return winners

    @staticmethod
    def _candidate_claim_sort_key(claim: Dict[str, object]) -> tuple:
        epg_channel = claim["epg_channel"]
        candidate = claim["candidate"]
        return (
            STAGE_PRIORITY[candidate.match_stage],
            -candidate.score,
            epg_channel.name.casefold(),
            epg_channel.id,
        )

    @staticmethod
    def _candidate_sort_key(candidate: CandidateMatch) -> tuple:
        return (
            STAGE_PRIORITY[candidate.match_stage],
            -candidate.score,
            candidate.acestream_channel.name.casefold(),
            candidate.acestream_channel.id,
        )

    @staticmethod
    def _serialize_candidate(candidate: CandidateMatch) -> Dict[str, object]:
        return {
            "acestream_channel_id": candidate.acestream_channel.id,
            "name": candidate.acestream_channel.name,
            "tvg_id": candidate.acestream_channel.tvg_id,
            "tvg_name": candidate.acestream_channel.tvg_name,
            "score": round(candidate.score, 6),
            "match_stage": candidate.match_stage,
        }

    @staticmethod
    def _confidence_for_candidate(candidate: Optional[CandidateMatch]) -> Optional[str]:
        if candidate is None:
            return None
        if candidate.match_stage in {"xml_id_exact", "name_exact"} or candidate.score >= STRICTNESS_THRESHOLDS["strict"]:
            return "high"
        if candidate.score >= STRICTNESS_THRESHOLDS["balanced"]:
            return "medium"
        return "low"

    @staticmethod
    def normalize_name(value: Optional[str]) -> str:
        if not value:
            return ""
        normalized = value.lower()
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(char for char in normalized if not unicodedata.combining(char))
        normalized = QUALITY_PATTERN.sub(" ", normalized)
        normalized = BRACKET_PATTERN.sub(" ", normalized)
        normalized = SEPARATOR_PATTERN.sub(" ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()
