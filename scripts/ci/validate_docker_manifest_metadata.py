#!/usr/bin/env python3
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = REPO_ROOT / "docker" / "manifests"
FULL_FLAVOR = "scraper-acestream-acexy"
EXPECTED_FLAVORS = {
    "scraper",
    "scraper-acestream",
    "scraper-acexy",
    "scraper-acestream-acexy",
}


def load_json(relative_path: str) -> dict:
    path = REPO_ROOT / relative_path
    if not path.is_file():
        raise AssertionError(f"Missing manifest file: {relative_path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def require_keys(payload: dict, keys: list[str], label: str) -> None:
    for key in keys:
        if key not in payload:
            raise AssertionError(f"{label} missing required key: {key}")


def require_platform_entry(entry: dict, platform: str) -> None:
    require_keys(
        entry,
        ["url", "sha256", "archive_type", "install"],
        f"acestream.json platform {platform}",
    )
    if not isinstance(entry["install"], dict):
        raise AssertionError(
            f"acestream.json platform {platform} install must be an object"
        )
    require_keys(
        entry["install"],
        ["strip_components", "binary_path", "engine_http_port"],
        f"acestream.json platform {platform} install",
    )
    if not isinstance(entry["sha256"], str):
        raise AssertionError(
            f"acestream.json platform {platform} sha256 must be a string"
        )


def main() -> int:
    platforms = load_json("docker/manifests/platforms.json")
    acestream = load_json("docker/manifests/acestream.json")
    acexy = load_json("docker/manifests/acexy.json")

    require_keys(platforms, ["baseline_platforms", "flavors", "tag_aliases"], "platforms.json")
    if not isinstance(platforms["baseline_platforms"], list) or not platforms["baseline_platforms"]:
        raise AssertionError("platforms.json baseline_platforms must be a non-empty list")
    if not isinstance(platforms["flavors"], dict) or not platforms["flavors"]:
        raise AssertionError("platforms.json flavors must be a non-empty object")

    missing_flavors = sorted(EXPECTED_FLAVORS - set(platforms["flavors"].keys()))
    if missing_flavors:
        raise AssertionError(
            "platforms.json missing flavor rules: " + ", ".join(missing_flavors)
        )

    for flavor, entry in platforms["flavors"].items():
        if not isinstance(entry, dict):
            raise AssertionError(f"platforms.json flavor {flavor} must be an object")
        require_keys(entry, ["platform_source", "includes"], f"platforms.json flavor {flavor}")

    tag_aliases = platforms["tag_aliases"]
    if not isinstance(tag_aliases, dict):
        raise AssertionError("platforms.json tag_aliases must be an object")
    if tag_aliases.get("latest") != FULL_FLAVOR:
        raise AssertionError(f"platforms.json latest must map to {FULL_FLAVOR}")
    if tag_aliases.get("version") != FULL_FLAVOR:
        raise AssertionError(f"platforms.json version must map to {FULL_FLAVOR}")

    require_keys(acestream, ["version", "platforms"], "acestream.json")
    if not isinstance(acestream["platforms"], dict) or not acestream["platforms"]:
        raise AssertionError("acestream.json platforms must be a non-empty object")
    for platform, entry in acestream["platforms"].items():
        if not isinstance(entry, dict):
            raise AssertionError(f"acestream.json platform {platform} must be an object")
        require_platform_entry(entry, platform)

    require_keys(acexy, ["repo", "ref", "version"], "acexy.json")
    if "expected_binary_name" in acexy and (
        not isinstance(acexy["expected_binary_name"], str)
        or not acexy["expected_binary_name"].strip()
    ):
        raise AssertionError(
            "acexy.json expected_binary_name must be a non-empty string when present"
        )

    ace_stream_platforms = set(acestream["platforms"].keys())
    for flavor in ("scraper-acestream", "scraper-acestream-acexy"):
        flavor_entry = platforms["flavors"][flavor]
        if flavor_entry.get("platform_source") != "acestream_supported":
            raise AssertionError(
                f"platforms.json flavor {flavor} must use platform_source=acestream_supported"
            )
        includes = set(flavor_entry.get("includes", []))
        if "acestream" not in includes:
            raise AssertionError(f"platforms.json flavor {flavor} must include acestream")

    baseline_platforms = set(platforms["baseline_platforms"])
    for flavor in ("scraper", "scraper-acexy"):
        flavor_entry = platforms["flavors"][flavor]
        if flavor_entry.get("platform_source") != "baseline":
            raise AssertionError(
                f"platforms.json flavor {flavor} must use platform_source=baseline"
            )
        declared = set(flavor_entry.get("platforms", baseline_platforms))
        if declared != baseline_platforms:
            raise AssertionError(
                f"platforms.json flavor {flavor} baseline platforms must match baseline_platforms"
            )

    if not ace_stream_platforms.issubset(baseline_platforms):
        raise AssertionError(
            "acestream.json platforms must be a subset of platforms.json baseline_platforms"
        )

    print("Docker manifest metadata validation passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
