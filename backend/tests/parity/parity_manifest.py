"""
Utilities for loading and validating Phase 1 parity baseline manifests.

The baseline file is stored as JSON-compatible YAML to avoid adding new
dependencies in the test harness.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


VALID_SOURCE_CLASSES = {"active", "flaky", "legacy", "disabled"}
VALID_URL_TYPES = {"regular", "zeronet", "auto"}
REQUIRED_SOURCE_FIELDS = {
    "id",
    "url",
    "url_type",
    "source_class",
    "gate_critical",
    "enabled",
    "env_tags",
}


def load_baseline_manifest(path: str | Path) -> Dict[str, Any]:
    """Load a parity baseline manifest from disk."""
    manifest_path = Path(path)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_baseline_manifest(manifest: Dict[str, Any]) -> List[str]:
    """Return validation errors for a loaded baseline manifest."""
    errors: List[str] = []

    if "baseline_version" not in manifest:
        errors.append("Missing root field: baseline_version")
    if "sources" not in manifest or not isinstance(manifest["sources"], list):
        errors.append("Missing or invalid root field: sources")
        return errors

    source_ids = set()
    for source in manifest["sources"]:
        source_id = source.get("id", "<missing-id>")

        missing_fields = REQUIRED_SOURCE_FIELDS - set(source.keys())
        if missing_fields:
            errors.append(
                f"{source_id}: missing fields: {', '.join(sorted(missing_fields))}"
            )
            continue

        if source["id"] in source_ids:
            errors.append(f"Duplicate source id: {source['id']}")
        source_ids.add(source["id"])

        if source["source_class"] not in VALID_SOURCE_CLASSES:
            errors.append(
                f"{source['id']}: invalid source_class '{source['source_class']}'"
            )

        if source["url_type"] not in VALID_URL_TYPES:
            errors.append(f"{source['id']}: invalid url_type '{source['url_type']}'")

        if not isinstance(source["gate_critical"], bool):
            errors.append(f"{source['id']}: gate_critical must be boolean")

        if not isinstance(source["enabled"], bool):
            errors.append(f"{source['id']}: enabled must be boolean")

        if not isinstance(source["env_tags"], list):
            errors.append(f"{source['id']}: env_tags must be a list")

    return errors


def source_index(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Index sources by source id."""
    return {item["id"]: item for item in manifest.get("sources", [])}


def split_sources_by_criticality(
    manifest: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split source definitions into blocking and non-blocking groups."""
    blocking: List[Dict[str, Any]] = []
    non_blocking: List[Dict[str, Any]] = []

    for source in manifest.get("sources", []):
        if source.get("gate_critical", False):
            blocking.append(source)
        else:
            non_blocking.append(source)

    return blocking, non_blocking
