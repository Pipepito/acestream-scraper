#!/usr/bin/env python3
"""Assert the canonical CI surface still references all four image flavors.

Replaces an inline python guard that previously read three GitHub Actions
files and verified flavor tokens + Docker Hub publish tags. Post-cleanup the
publish logic lives in scripts/ci/run_jenkins_release.sh (Jenkins is the
sole publisher); the GA release workflow is validation-only. This guard
checks the surfaces where flavor coverage and tag scheme actually live.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

FLAVORS = [
    "scraper",
    "scraper-acestream",
    "scraper-acexy",
    "scraper-acestream-acexy",
]
FLAVOR_TOKENS = [f"--flavor {flavor}" for flavor in FLAVORS]

# Tags that the publish loop in run_jenkins_release.sh must emit. Any drift
# here means a release would either skip a flavor or stop tagging :latest.
PUBLISH_TAGS = [
    "pipepito/acestream-scraper:latest",
    "pipepito/acestream-scraper:${VERSION}",
    "pipepito/acestream-scraper:scraper-acestream-acexy",
    "pipepito/acestream-scraper:${VERSION}-scraper-acestream-acexy",
    "pipepito/acestream-scraper:scraper",
    "pipepito/acestream-scraper:${VERSION}-scraper",
    "pipepito/acestream-scraper:scraper-acestream",
    "pipepito/acestream-scraper:${VERSION}-scraper-acestream",
    "pipepito/acestream-scraper:scraper-acexy",
    "pipepito/acestream-scraper:${VERSION}-scraper-acexy",
]


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        sys.stderr.write(f"FAIL: required file not found: {rel}\n")
        raise SystemExit(1)
    return path.read_text(encoding="utf-8")


def main() -> int:
    pr = read(".github/workflows/pull_request.yml")
    release_yml = read(".github/workflows/release.yml")
    release_sh = read("scripts/ci/run_jenkins_release.sh")
    release_jenkinsfile = read("jenkins/release.Jenkinsfile")

    checks = [
        ("pull request exercises all flavors",
         all(token in pr for token in FLAVOR_TOKENS)),
        ("release readiness workflow exercises all flavors",
         all(token in release_yml for token in FLAVOR_TOKENS)),
        ("release readiness workflow does not push to Docker Hub",
         "--push" not in release_yml and "DOCKERHUB_TOKEN" not in release_yml),
        ("release script declares all flavors",
         all(f'"{flavor}"' in release_sh for flavor in FLAVORS)),
        ("release script publishes all required tags",
         all(tag in release_sh for tag in PUBLISH_TAGS)),
        ("release script pushes (--push present)",
         "--push" in release_sh),
        ("release script targets pipepito Docker Hub repo",
         "pipepito/acestream-scraper-v2" not in release_sh),
        # Two-phase publish: :latest is gated behind PUBLISH_LATEST so the
        # first publish of a new version touches versioned + flavor-channel
        # tags only and a follow-up run promotes :latest after canary.
        ("release script gates :latest behind PUBLISH_LATEST",
         'include_latest="${PUBLISH_LATEST:-0}"' in release_sh
         and 'if [[ "$include_latest" == "1" ]]; then' in release_sh),
        ("release script supports --print-publish-plan preview",
         "--print-publish-plan" in release_sh),
        ("release Jenkinsfile exposes PUBLISH_LATEST parameter",
         "name: 'PUBLISH_LATEST'" in release_jenkinsfile
         and "PUBLISH_LATEST=${params.PUBLISH_LATEST ? '1' : '0'}" in release_jenkinsfile),
    ]

    failed = []
    for name, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
        if not passed:
            failed.append(name)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
