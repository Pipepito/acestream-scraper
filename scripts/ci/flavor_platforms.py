#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def load_json(path: str) -> dict:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_platforms(platform_manifest_path: str, acestream_manifest_path: str, flavor_name: str) -> list[str]:
    platform_payload = load_json(platform_manifest_path)
    acestream_payload = load_json(acestream_manifest_path)

    flavors = platform_payload.get("flavors", {})
    flavor = flavors.get(flavor_name)
    if not isinstance(flavor, dict):
        raise ValueError(f"Unknown flavor: {flavor_name}")

    baseline = [item.strip() for item in platform_payload.get("baseline_platforms", []) if str(item).strip()]
    acestream_supported = {
        item.strip()
        for item in acestream_payload.get("platforms", {}).keys()
        if str(item).strip()
    }

    platform_source = flavor.get("platform_source")
    if platform_source == "baseline":
        allowed = [item.strip() for item in flavor.get("platforms", baseline) if str(item).strip()]
    elif platform_source == "acestream_supported":
        allowed = [item for item in baseline if item in acestream_supported]
    else:
        raise ValueError(
            f"Flavor {flavor_name} uses unsupported platform_source: {platform_source}"
        )

    if not allowed:
        raise ValueError(f"Flavor {flavor_name} does not resolve to any supported platforms")

    return allowed


def select_platforms(allowed: list[str], requested_csv: str, flavor_name: str) -> list[str]:
    if requested_csv.strip():
        requested = [item.strip() for item in requested_csv.split(",") if item.strip()]
        invalid = [item for item in requested if item not in allowed]
        if invalid:
            allowed_csv = ",".join(allowed)
            invalid_csv = ",".join(invalid)
            raise ValueError(
                f"Flavor {flavor_name} does not support requested platforms: {invalid_csv}. "
                f"Allowed platforms: {allowed_csv}"
            )
        return requested
    return allowed


def main() -> int:
    if len(sys.argv) not in {4, 5}:
        print(
            "Usage: flavor_platforms.py <platform_manifest> <acestream_manifest> <flavor> [requested_platforms_csv]",
            file=sys.stderr,
        )
        return 2

    platform_manifest, acestream_manifest, flavor_name = sys.argv[1:4]
    requested_csv = sys.argv[4] if len(sys.argv) == 5 else ""

    try:
        allowed = resolve_platforms(platform_manifest, acestream_manifest, flavor_name)
        selected = select_platforms(allowed, requested_csv, flavor_name)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(",".join(selected))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
