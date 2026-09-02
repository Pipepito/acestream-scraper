#!/usr/bin/env python3
"""Validate docker/manifests/{platforms,acestream,acexy}.json and the vendored payloads.

Run from anywhere: ``python3 scripts/ci/validate_docker_manifest_metadata.py``.
Exit 1 with ``VALIDATION FAILED: ...`` on the first problem.
"""
import json
import re
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
INSTALL_KINDS = {"executable", "android-apk"}
SUPPORT_LEVELS = {"stable", "experimental"}
ARCHIVE_TYPES_BY_KIND = {"executable": {"tar.gz"}, "android-apk": {"apk"}}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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


def load_sha256sums(vendor_dir: Path, label: str) -> dict[str, str]:
    sums_path = vendor_dir / "SHA256SUMS"
    if not sums_path.is_file():
        raise AssertionError(f"{label}: missing {sums_path.relative_to(REPO_ROOT)}")
    sums: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, name = line.partition("  ")
        sums[name.strip()] = digest.strip()
    return sums


def require_vendored(label: str, vendor_dir_rel: str, vendored_file: str, sha256: str, mirror_urls: list, mirror_base: str) -> None:
    vendor_dir = REPO_ROOT / vendor_dir_rel
    if not vendor_dir.is_dir():
        raise AssertionError(f"{label}: vendor_dir {vendor_dir_rel} does not exist")
    if not isinstance(vendored_file, str) or not vendored_file or "/" in vendored_file:
        raise AssertionError(f"{label}: vendored_file must be a bare file name")
    vendored_path = vendor_dir / vendored_file
    if not vendored_path.is_file():
        raise AssertionError(f"{label}: vendored file missing: {vendor_dir_rel}/{vendored_file}")
    sums = load_sha256sums(vendor_dir, label)
    if sums.get(vendored_file) != sha256:
        raise AssertionError(
            f"{label}: {vendor_dir_rel}/SHA256SUMS entry for {vendored_file} does not match the manifest sha256"
        )
    if not isinstance(mirror_urls, list) or not mirror_urls:
        raise AssertionError(f"{label}: mirror_urls must be a non-empty list")
    for url in mirror_urls:
        if not isinstance(url, str) or not url.startswith("https://"):
            raise AssertionError(f"{label}: mirror url must be https: {url!r}")
        if not url.endswith("/" + vendored_file):
            raise AssertionError(f"{label}: mirror url must end with /{vendored_file}: {url}")
    if mirror_base and not any(url.startswith(mirror_base.rstrip("/") + "/") for url in mirror_urls):
        raise AssertionError(f"{label}: no mirror url under mirror_base_url {mirror_base}")


def require_platform_entry(entry: dict, platform: str, acestream: dict) -> None:
    label = f"acestream.json platform {platform}"
    require_keys(entry, ["url", "sha256", "archive_type", "install", "vendored_file", "mirror_urls", "support", "engine_version"], label)
    if not isinstance(entry["sha256"], str) or not SHA256_RE.match(entry["sha256"]):
        raise AssertionError(f"{label} sha256 must be a 64-hex string")
    if not isinstance(entry["url"], str) or not entry["url"].startswith("https://"):
        raise AssertionError(f"{label} url must be https")
    if entry["support"] not in SUPPORT_LEVELS:
        raise AssertionError(f"{label} support must be one of {sorted(SUPPORT_LEVELS)}, got {entry['support']!r}")
    if not isinstance(entry["engine_version"], str) or not entry["engine_version"]:
        raise AssertionError(f"{label} engine_version must be a non-empty string")

    install = entry["install"]
    if not isinstance(install, dict):
        raise AssertionError(f"{label} install must be an object")
    require_keys(install, ["engine_http_port", "kind"], f"{label} install")
    kind = install["kind"]
    if kind not in INSTALL_KINDS:
        raise AssertionError(f"{label} install.kind must be one of {sorted(INSTALL_KINDS)}, got {kind!r}")
    if entry["archive_type"] not in ARCHIVE_TYPES_BY_KIND[kind]:
        raise AssertionError(
            f"{label} archive_type {entry['archive_type']!r} is not valid for kind {kind} "
            f"(expected {sorted(ARCHIVE_TYPES_BY_KIND[kind])})"
        )

    require_vendored(
        label,
        acestream.get("vendor_dir", "docker/vendor/acestream"),
        entry["vendored_file"],
        entry["sha256"],
        entry["mirror_urls"],
        acestream.get("mirror_base_url", ""),
    )

    if kind == "executable":
        require_keys(install, ["binary_path", "strip_components", "python_version"], f"{label} install (kind=executable)")
        if not isinstance(install["binary_path"], str) or not install["binary_path"]:
            raise AssertionError(f"{label} install.binary_path must be a non-empty string")
        if not re.fullmatch(r"3\.\d+", str(install["python_version"])):
            raise AssertionError(f"{label} install.python_version must look like 3.N, got {install['python_version']!r}")
    else:  # android-apk
        require_keys(install, ["abi", "bionic"], f"{label} install (kind=android-apk)")
        if install["abi"] not in {"arm64-v8a", "armeabi-v7a"}:
            raise AssertionError(f"{label} install.abi must be arm64-v8a or armeabi-v7a, got {install['abi']!r}")
        bionic = install["bionic"]
        if not isinstance(bionic, dict):
            raise AssertionError(f"{label} install.bionic must be an object")
        require_keys(bionic, ["url", "sha256", "vendor_dir", "vendored_file", "mirror_urls", "libdir", "linker"], f"{label} install.bionic")
        if not SHA256_RE.match(str(bionic["sha256"])):
            raise AssertionError(f"{label} install.bionic.sha256 must be a 64-hex string")
        if (bionic["libdir"], bionic["linker"]) not in {("lib64", "linker64"), ("lib", "linker")}:
            raise AssertionError(f"{label} install.bionic libdir/linker must be lib64/linker64 or lib/linker")
        require_vendored(
            f"{label} install.bionic",
            bionic["vendor_dir"],
            bionic["vendored_file"],
            bionic["sha256"],
            bionic["mirror_urls"],
            acestream.get("mirror_base_url", ""),
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

    require_keys(acestream, ["version", "platforms", "vendor_dir", "mirror_base_url"], "acestream.json")
    if not isinstance(acestream["platforms"], dict) or not acestream["platforms"]:
        raise AssertionError("acestream.json platforms must be a non-empty object")
    if "linux/amd64" not in acestream["platforms"]:
        raise AssertionError("acestream.json must keep a linux/amd64 entry")
    for platform, entry in acestream["platforms"].items():
        if not isinstance(entry, dict):
            raise AssertionError(f"acestream.json platform {platform} must be an object")
        require_platform_entry(entry, platform, acestream)

    require_keys(acexy, ["repo", "ref", "version"], "acexy.json")
    if "expected_binary_name" in acexy and (
        not isinstance(acexy["expected_binary_name"], str)
        or not acexy["expected_binary_name"].strip()
    ):
        raise AssertionError(
            "acexy.json expected_binary_name must be a non-empty string when present"
        )

    if "vendored_file" in acexy:
        require_keys(acexy, ["vendor_dir", "vendored_file", "sha256"], "acexy.json (vendored)")
        if not isinstance(acexy["sha256"], str) or not SHA256_RE.match(acexy["sha256"]):
            raise AssertionError("acexy.json sha256 must be a 64-hex string")
        vendor_dir = REPO_ROOT / acexy["vendor_dir"]
        vendored_file = acexy["vendored_file"]
        if not isinstance(vendored_file, str) or not vendored_file or "/" in vendored_file:
            raise AssertionError("acexy.json vendored_file must be a bare file name")
        if not (vendor_dir / vendored_file).is_file():
            raise AssertionError(f"acexy.json vendored file missing: {acexy['vendor_dir']}/{vendored_file}")
        sums = load_sha256sums(vendor_dir, "acexy.json")
        if sums.get(vendored_file) != acexy["sha256"]:
            raise AssertionError(f"{acexy['vendor_dir']}/SHA256SUMS entry for {vendored_file} does not match acexy.json sha256")
        if acexy["vendor_dir"] != "docker/vendor/acexy":
            raise AssertionError("acexy.json vendor_dir must be docker/vendor/acexy (the Dockerfile mounts docker/vendor)")

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
