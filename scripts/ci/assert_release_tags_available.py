#!/usr/bin/env python3
"""Fail closed unless every release tag is absent (or overwrite is explicit)."""

import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("tags", nargs="+")
    args = parser.parse_args()
    existing = []
    for tag in args.tags:
        try:
            result = subprocess.run(
                ["docker", "buildx", "imagetools", "inspect", tag],
                capture_output=True, text=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired):
            print(f"Cannot verify {tag}; release blocked (registry check failed).", file=sys.stderr)
            return 1
        if result.returncode == 0:
            existing.append(tag)
            continue
        # buildx reports an absent manifest as '<normalized reference>: not found'.
        # Do not treat auth failures, rate limits, TLS/DNS errors or timeouts as absence.
        references = {tag}
        first = tag.split("/", 1)[0]
        if "." not in first and ":" not in first and first != "localhost":
            references.add("docker.io/" + tag)
        errors = result.stderr.strip().removeprefix("ERROR: ")
        if errors not in {f"{ref}: not found" for ref in references}:
            print(f"Cannot verify {tag}; release blocked. Check registry access/authentication.", file=sys.stderr)
            return 1
    if existing:
        print("Existing versioned images: " + ", ".join(existing))
        if not args.force:
            print("Refusing to overwrite. Choose a new version or explicitly enable FORCE_VERSION_OVERWRITE.", file=sys.stderr)
            return 1
        print("FORCE_VERSION_OVERWRITE enabled: replacing existing versioned images.")
    else:
        print("All versioned image tags are available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
