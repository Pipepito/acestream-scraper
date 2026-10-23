#!/usr/bin/env python3
"""Fail closed unless an open PR still matches its approved head and protected base."""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request

REPOSITORY = "Pipepito/acestream-scraper"


def validate_identity(pr: str, head: str, base: str, target: str) -> None:
    if not re.fullmatch(r"[1-9][0-9]*", pr):
        raise ValueError("Invalid PR number")
    if not all(re.fullmatch(r"[0-9a-f]{40}", value) for value in (head, base)):
        raise ValueError("Approval requires full immutable commit hashes")
    if target not in {"develop", "main"}:
        raise ValueError("Only protected integration/release targets are accepted")


def verify(data: dict, pr: str, head: str, base: str, target: str) -> None:
    validate_identity(pr, head, base, target)
    if data.get("number") != int(pr) or data.get("state") != "open" or data.get("merged"):
        raise ValueError("PR is no longer open; approval is invalid")
    upstream, proposed = data.get("base", {}), data.get("head", {})
    if (upstream.get("repo") or {}).get("full_name") != REPOSITORY:
        raise ValueError("Unexpected target repository")
    if upstream.get("ref") != target or upstream.get("sha") != base:
        raise ValueError("PR target changed; request a new validation and approval")
    if proposed.get("sha") != head:
        raise ValueError("PR head changed; request a new validation and approval")
    if target == "main" and (proposed.get("ref") != "develop" or
                             (proposed.get("repo") or {}).get("full_name") != REPOSITORY):
        raise ValueError("Only this repository's develop branch may target main")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("pr", "head", "base", "target"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    try:
        validate_identity(args.pr, args.head, args.base, args.target)
        request = urllib.request.Request(
            f"https://api.github.com/repos/{REPOSITORY}/pulls/{args.pr}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "acestream-pr-validation"},
        )
        # Public metadata needs no credential. Rate limits and outages block,
        # never downgrade approval validation. Bound the response and wait.
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read(1024 * 1024 + 1)
        if len(raw) > 1024 * 1024:
            raise ValueError("PR metadata exceeds the response limit")
        verify(json.loads(raw), args.pr, args.head, args.base, args.target)
    except (ValueError, KeyError, TypeError, AttributeError, OSError, urllib.error.URLError):
        print("PR revision verification failed: closed/changed PR, invalid input, or unavailable metadata. Rerun validation; do not reuse approval.")
        return 1
    print("Open PR and protected target still match the approved revision.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
