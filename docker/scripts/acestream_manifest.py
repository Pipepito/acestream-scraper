#!/usr/bin/env python3
"""Resolve docker/manifests/acestream.json entries per container platform.

Shared by the Docker build (inside the ``acestream-installer`` stage, where it
selects the engine for ``$TARGETPLATFORM``) and by the CI helpers
(``scripts/ci/derive_acestream_build_args.py``). It has no third-party
dependencies so it runs on the slim build image's stock python3.

CLI::

    acestream_manifest.py <acestream.json> --platform linux/arm64 [--format env|shell|json]
    acestream_manifest.py <acestream.json> --all --format json

``env`` prints ``KEY=VALUE`` lines (``--build-arg`` shape); ``shell`` prints
``export KEY='VALUE'`` lines for ``eval`` in bash; ``json`` prints the raw
entry (or all entries with ``--all``).
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Any

ACESTREAM_FLAVORS = {"scraper-acestream", "scraper-acestream-acexy"}
INSTALL_KINDS = {"executable", "android-apk"}
SUPPORT_LEVELS = {"stable", "experimental"}

# Keys emitted for every install kind.
_COMMON_KEYS = (
    "ACESTREAM_PLATFORM",
    "ACESTREAM_ENGINE_VERSION",
    "ACESTREAM_PLATFORM_SUPPORT",
    "ACESTREAM_DOWNLOAD_URL",
    "ACESTREAM_DOWNLOAD_SHA256",
    "ACESTREAM_ARCHIVE_TYPE",
    "ACESTREAM_VENDORED_FILE",
    "ACESTREAM_VENDOR_SUBDIR",
    "ACESTREAM_MIRROR_URLS",
    "ACESTREAM_INSTALL_KIND",
)


class ManifestError(ValueError):
    """Raised for structural problems in acestream.json."""


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload.get("platforms"), dict) or not payload["platforms"]:
        raise ManifestError("acestream.json declares no platforms")
    return payload


def platform_entry(payload: dict[str, Any], platform: str) -> dict[str, Any]:
    platforms = payload["platforms"]
    if platform not in platforms:
        known = ", ".join(platforms)
        raise ManifestError(f"platform {platform} not in acestream manifest (known: {known})")
    entry = platforms[platform]
    if not isinstance(entry, dict):
        raise ManifestError(f"platform {platform} entry must be an object")
    return entry


def build_args_for(payload: dict[str, Any], platform: str) -> dict[str, str]:
    """Return the ACESTREAM_* variables describing ``platform``'s engine."""
    entry = platform_entry(payload, platform)
    install = entry.get("install") or {}
    kind = install.get("kind", "executable")
    if kind not in INSTALL_KINDS:
        raise ManifestError(
            f"platform {platform}: unsupported install kind {kind!r} "
            f"(expected one of {sorted(INSTALL_KINDS)})"
        )

    pairs: dict[str, str] = {
        "ACESTREAM_PLATFORM": platform,
        "ACESTREAM_ENGINE_VERSION": str(entry.get("engine_version") or payload.get("version", "")),
        "ACESTREAM_PLATFORM_SUPPORT": str(entry.get("support", "stable")),
        "ACESTREAM_DOWNLOAD_URL": str(entry.get("url", "")),
        "ACESTREAM_DOWNLOAD_SHA256": str(entry.get("sha256", "")),
        "ACESTREAM_ARCHIVE_TYPE": str(entry.get("archive_type", "tar.gz")),
        "ACESTREAM_VENDORED_FILE": str(entry.get("vendored_file", "")),
        "ACESTREAM_VENDOR_SUBDIR": Path(str(payload.get("vendor_dir", "docker/vendor/acestream"))).name,
        "ACESTREAM_MIRROR_URLS": " ".join(str(u) for u in entry.get("mirror_urls", []) or []),
        "ACESTREAM_INSTALL_KIND": kind,
    }

    if kind == "executable":
        pairs["ACESTREAM_STRIP_COMPONENTS"] = str(install.get("strip_components", 1))
        pairs["ACESTREAM_BINARY_PATH"] = str(install.get("binary_path", "acestreamengine"))
    else:  # android-apk
        bionic = install.get("bionic") or {}
        pairs["ACESTREAM_ANDROID_ABI"] = str(install.get("abi", ""))
        pairs["ACESTREAM_BIONIC_URL"] = str(bionic.get("url", ""))
        pairs["ACESTREAM_BIONIC_SHA256"] = str(bionic.get("sha256", ""))
        pairs["ACESTREAM_BIONIC_VENDORED_FILE"] = str(bionic.get("vendored_file", ""))
        pairs["ACESTREAM_BIONIC_VENDOR_SUBDIR"] = Path(str(bionic.get("vendor_dir", "docker/vendor/bionic"))).name
        pairs["ACESTREAM_BIONIC_MIRROR_URLS"] = " ".join(
            str(u) for u in bionic.get("mirror_urls", []) or []
        )
        pairs["ACESTREAM_BIONIC_LIBDIR"] = str(bionic.get("libdir", "lib64"))
        pairs["ACESTREAM_BIONIC_LINKER"] = str(bionic.get("linker", "linker64"))
    return pairs


def format_env(pairs: dict[str, str]) -> str:
    return "".join(f"{key}={value}\n" for key, value in pairs.items())


def format_shell(pairs: dict[str, str]) -> str:
    return "".join(f"export {key}={shlex.quote(value)}\n" for key, value in pairs.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", help="path to docker/manifests/acestream.json")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--platform", help="container platform, e.g. linux/arm64")
    selector.add_argument("--all", action="store_true", help="emit every platform (json only)")
    parser.add_argument("--format", choices=("env", "shell", "json"), default="env")
    parser.add_argument(
        "--respect-env",
        action="store_true",
        help="do not emit keys whose environment value is already non-empty (explicit build-args win)",
    )
    args = parser.parse_args(argv)

    try:
        payload = load_manifest(args.manifest)
        if args.all:
            if args.format != "json":
                parser.error("--all requires --format json")
            result = {platform: build_args_for(payload, platform) for platform in payload["platforms"]}
            print(json.dumps(result, indent=2))
            return 0
        pairs = build_args_for(payload, args.platform)
        if args.respect_env:
            pairs = {key: value for key, value in pairs.items() if not os.environ.get(key)}
    except (ManifestError, OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"acestream_manifest: {exc}\n")
        return 1

    if args.format == "json":
        print(json.dumps(pairs, indent=2))
    elif args.format == "shell":
        sys.stdout.write(format_shell(pairs))
    else:
        sys.stdout.write(format_env(pairs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
