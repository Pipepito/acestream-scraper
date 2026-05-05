#!/usr/bin/env python3
"""Print ACESTREAM_* build args for the given flavor + platform.

Usage:
    derive_acestream_build_args.py <acestream.json> <flavor> [<platform>]

Emits one `KEY=VALUE` per line, matching --build-arg expectations. If the
flavor does not use acestream, prints nothing and exits 0. If multiple
platforms exist for the flavor and no platform is specified, picks the
first declared platform (deterministic per JSON order).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ACESTREAM_FLAVORS = {"scraper-acestream", "scraper-acestream-acexy"}


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write("usage: derive_acestream_build_args.py <acestream.json> <flavor> [<platform>]\n")
        return 2

    manifest_path = Path(sys.argv[1])
    flavor = sys.argv[2]
    requested_platform = sys.argv[3] if len(sys.argv) >= 4 else ""

    if flavor not in ACESTREAM_FLAVORS:
        return 0  # nothing to emit

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    platforms = payload.get("platforms", {})
    if not platforms:
        sys.stderr.write(f"acestream.json declares no platforms\n")
        return 1

    if requested_platform:
        if requested_platform not in platforms:
            sys.stderr.write(
                f"flavor {flavor}: platform {requested_platform} not in acestream manifest\n"
            )
            return 1
        chosen = requested_platform
    else:
        chosen = next(iter(platforms))

    entry = platforms[chosen]
    install = entry.get("install", {})

    pairs = {
        "ACESTREAM_DOWNLOAD_URL": entry.get("url", ""),
        "ACESTREAM_DOWNLOAD_SHA256": entry.get("sha256", ""),
        "ACESTREAM_ARCHIVE_TYPE": entry.get("archive_type", "tar.gz"),
        "ACESTREAM_STRIP_COMPONENTS": str(install.get("strip_components", 1)),
        "ACESTREAM_INSTALL_KIND": install.get("kind", "executable"),
    }
    if pairs["ACESTREAM_INSTALL_KIND"] == "executable":
        pairs["ACESTREAM_BINARY_PATH"] = install.get("binary_path", "acestreamengine")
    else:
        sys.stderr.write(
            f"unsupported install kind: {pairs['ACESTREAM_INSTALL_KIND']!r} "
            "(only 'executable' is implemented)\n"
        )
        return 1

    for key, value in pairs.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
