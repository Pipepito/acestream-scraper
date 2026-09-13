import json
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

from app.models.models import AcestreamChannel
from app.services.scraper_service import ScraperService

from .parity_compare import (
    compare_channel_collections,
    compute_gate_score,
)
from .parity_manifest import (
    load_baseline_manifest,
    source_index,
    split_sources_by_criticality,
    validate_baseline_manifest,
)


PARITY_DIR = Path(__file__).parent
BASELINE_PATH = PARITY_DIR / "baseline_sources.yaml"
SNAPSHOT_PATH = PARITY_DIR / "snapshots" / "scraper_channels_snapshot.json"


def _load_scraper_snapshots() -> Dict[str, Any]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _channels_to_raw_snapshot_rows(channels: List[Dict[str, Any]]) -> List[Any]:
    rows = []
    for channel in channels:
        rows.append(
            (
                channel["id"],
                channel["name"],
                {
                    "group_title": channel["group"],
                    "tvg_logo": channel["logo"],
                    "tvg_id": channel["tvg_id"],
                    "tvg_name": channel["tvg_name"],
                },
            )
        )
    return rows


class _FakeScraper:
    def __init__(self, channels: List[Dict[str, Any]]):
        self._channels = channels
        self.db = None
        self.epg_service = None
        self.tv_channel_service = None

    async def scrape(self):
        return _channels_to_raw_snapshot_rows(self._channels), "OK"


def _as_comparable_channel_rows(channel_results: List[Any]) -> List[Dict[str, Any]]:
    rows = []
    for result in channel_results:
        rows.append(
            {
                "id": result.channel_id,
                "name": result.name,
                "group": result.metadata.get("group"),
                "logo": result.metadata.get("logo"),
                "tvg_id": result.metadata.get("tvg_id"),
                "tvg_name": result.metadata.get("tvg_name"),
                "source_url": result.metadata.get("source_url"),
            }
        )
    return rows


def test_baseline_manifest_schema():
    manifest = load_baseline_manifest(BASELINE_PATH)
    errors = validate_baseline_manifest(manifest)
    assert errors == []

    blocking, non_blocking = split_sources_by_criticality(manifest)
    assert len(blocking) >= 2
    assert len(non_blocking) >= 1
    assert any(source["url_type"] == "zeronet" for source in manifest["sources"])


def test_parity_comparator_rules():
    required = ["id", "name", "group", "logo", "tvg_id", "tvg_name", "source_url"]
    fuzzy = ["name", "group", "logo", "tvg_name"]
    expected = [
        {
            "id": "alpha",
            "name": "Parity Alpha HD",
            "group": "Sports",
            "logo": "https://cdn.example.com/a.png",
            "tvg_id": "alpha.id",
            "tvg_name": "Parity Alpha",
            "source_url": "https://example.com/a.m3u",
        }
    ]
    actual = [
        {
            "id": "alpha",
            "name": "parity   alpha hd",
            "group": "sports",
            "logo": "https://cdn.example.com/a.png",
            "tvg_id": "alpha.id",
            "tvg_name": "PARITY alpha",
            "source_url": "https://example.com/a.m3u",
        }
    ]

    result = compare_channel_collections(expected, actual, required, fuzzy)
    assert result["passed"]

    actual[0]["tvg_id"] = "alpha.changed"
    failed = compare_channel_collections(expected, actual, required, fuzzy)
    assert not failed["passed"]
    assert failed["channel_failures"] == ["alpha"]
    assert "tvg_id" in failed["per_channel"]["alpha"]["strict_mismatches"]


def test_gate_scoring_separates_non_blocking_sources():
    manifest = load_baseline_manifest(BASELINE_PATH)
    indexed = source_index(manifest)
    source_results = {
        "http_m3u_primary": {"passed": True},
        "zeronet_primary": {"passed": True},
        "regional_auth_sample": {"passed": False},
        "legacy_disabled_sample": {"passed": False},
    }
    score = compute_gate_score(source_results, indexed)
    assert score["passed"]
    assert score["blocking_failures"] == []
    assert sorted(score["non_blocking_failures"]) == [
        "legacy_disabled_sample",
        "regional_auth_sample",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("source_id", ["http_m3u_primary", "zeronet_primary"])
async def test_scraper_parity_against_snapshots(db_session, source_id):
    manifest = load_baseline_manifest(BASELINE_PATH)
    snapshots = _load_scraper_snapshots()
    indexed_sources = source_index(manifest)
    source = indexed_sources[source_id]
    expected_channels = snapshots["sources"][source_id]["channels"]

    with patch(
        "app.services.scraper_service.create_scraper_for_url",
        return_value=_FakeScraper(expected_channels),
    ):
        service = ScraperService(db_session)
        channel_results, status = await service.scrape_url(
            source["url"], source["url_type"]
        )

    assert status == "OK"
    actual_channels = _as_comparable_channel_rows(channel_results)
    comparison = compare_channel_collections(
        expected_channels,
        actual_channels,
        required_fields=manifest["required_fields"],
        fuzzy_fields=manifest["fuzzy_fields"],
    )
    assert comparison["passed"], comparison

    persisted = (
        db_session.query(AcestreamChannel)
        .filter(AcestreamChannel.source_url == source["url"])
        .all()
    )
    assert len(persisted) == len(expected_channels)
