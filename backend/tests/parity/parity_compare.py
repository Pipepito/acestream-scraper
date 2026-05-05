"""
Field-level parity comparators for scraper and output regression checks.
"""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any, Dict, List


def normalize_text(value: Any) -> str:
    """Normalize text for fuzzy metadata comparisons."""
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def fuzzy_equal(left: Any, right: Any, threshold: float = 0.82) -> bool:
    """Compare values with a configurable fuzzy threshold."""
    left_norm = normalize_text(left)
    right_norm = normalize_text(right)
    if left_norm == right_norm:
        return True
    similarity = SequenceMatcher(None, left_norm, right_norm).ratio()
    return similarity >= threshold


def compare_channel_fields(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
    required_fields: List[str],
    fuzzy_fields: List[str],
    fuzzy_threshold: float = 0.82,
) -> Dict[str, Any]:
    """Compare one channel record and return structured mismatch details."""
    missing_fields = [field for field in required_fields if field not in actual]
    strict_mismatches: Dict[str, Dict[str, Any]] = {}
    fuzzy_mismatches: Dict[str, Dict[str, Any]] = {}

    for field in required_fields:
        if field not in expected or field not in actual:
            continue

        expected_value = expected[field]
        actual_value = actual[field]

        if field in fuzzy_fields:
            if not fuzzy_equal(expected_value, actual_value, threshold=fuzzy_threshold):
                fuzzy_mismatches[field] = {
                    "expected": expected_value,
                    "actual": actual_value,
                }
        else:
            if expected_value != actual_value:
                strict_mismatches[field] = {
                    "expected": expected_value,
                    "actual": actual_value,
                }

    return {
        "passed": not missing_fields and not strict_mismatches and not fuzzy_mismatches,
        "missing_fields": missing_fields,
        "strict_mismatches": strict_mismatches,
        "fuzzy_mismatches": fuzzy_mismatches,
    }


def compare_channel_collections(
    expected_channels: List[Dict[str, Any]],
    actual_channels: List[Dict[str, Any]],
    required_fields: List[str],
    fuzzy_fields: List[str],
    id_key: str = "id",
) -> Dict[str, Any]:
    """Compare two channel collections and return parity status."""
    expected_by_id = {channel[id_key]: channel for channel in expected_channels}
    actual_by_id = {channel[id_key]: channel for channel in actual_channels}

    expected_ids = set(expected_by_id.keys())
    actual_ids = set(actual_by_id.keys())

    missing_ids = sorted(expected_ids - actual_ids)
    unexpected_ids = sorted(actual_ids - expected_ids)

    per_channel: Dict[str, Dict[str, Any]] = {}
    for channel_id in sorted(expected_ids & actual_ids):
        per_channel[channel_id] = compare_channel_fields(
            expected=expected_by_id[channel_id],
            actual=actual_by_id[channel_id],
            required_fields=required_fields,
            fuzzy_fields=fuzzy_fields,
        )

    channel_failures = [
        channel_id
        for channel_id, result in per_channel.items()
        if not result["passed"]
    ]

    return {
        "passed": not missing_ids and not unexpected_ids and not channel_failures,
        "missing_ids": missing_ids,
        "unexpected_ids": unexpected_ids,
        "channel_failures": channel_failures,
        "per_channel": per_channel,
    }


def compute_gate_score(
    source_results: Dict[str, Dict[str, Any]],
    source_definitions: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Evaluate blocking/non-blocking parity outcomes by source class policy.
    """
    blocking_failures: List[str] = []
    non_blocking_failures: List[str] = []
    by_class: Dict[str, Dict[str, int]] = {}

    for source_id, result in source_results.items():
        source_meta = source_definitions[source_id]
        source_class = source_meta["source_class"]
        class_row = by_class.setdefault(source_class, {"passed": 0, "failed": 0})
        passed = bool(result.get("passed", False))

        if passed:
            class_row["passed"] += 1
            continue

        class_row["failed"] += 1
        if source_meta.get("gate_critical", False):
            blocking_failures.append(source_id)
        else:
            non_blocking_failures.append(source_id)

    return {
        "passed": len(blocking_failures) == 0,
        "blocking_failures": sorted(blocking_failures),
        "non_blocking_failures": sorted(non_blocking_failures),
        "by_class": by_class,
    }
