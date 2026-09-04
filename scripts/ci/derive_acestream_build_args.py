#!/usr/bin/env python3
"""Print the ACESTREAM_* variables for one flavor + platform (``KEY=VALUE`` lines).

Usage:
    derive_acestream_build_args.py <acestream.json> <flavor> [<platform>]

Thin CI wrapper around docker/scripts/acestream_manifest.py (the resolver the
Docker build itself uses). Non-acestream flavors print nothing and exit 0.
Without a platform the first declared one is used. Note that the Docker
build resolves the manifest per $TARGETPLATFORM on its own; this helper is
for inspection, dry-runs and single-platform overrides.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "docker" / "scripts"))

from acestream_manifest import (  # noqa: E402  (path set above)
    ACESTREAM_FLAVORS,
    ManifestError,
    build_args_for,
    format_env,
    load_manifest,
)


def main() -> int:
    if len(sys.argv) < 3:
        sys.stderr.write("usage: derive_acestream_build_args.py <acestream.json> <flavor> [<platform>]\n")
        return 2

    manifest_path = Path(sys.argv[1])
    flavor = sys.argv[2]
    requested_platform = sys.argv[3] if len(sys.argv) >= 4 else ""

    if flavor not in ACESTREAM_FLAVORS:
        return 0  # nothing to emit

    try:
        payload = load_manifest(manifest_path)
        platform = requested_platform or next(iter(payload["platforms"]))
        pairs = build_args_for(payload, platform)
    except (ManifestError, OSError, ValueError) as exc:
        sys.stderr.write(f"flavor {flavor}: {exc}\n")
        return 1

    sys.stdout.write(format_env(pairs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
