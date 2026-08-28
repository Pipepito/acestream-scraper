#!/usr/bin/env python3
"""Assert the canonical CI surface still references all four image flavors.

Replaces an inline python guard that previously read GitHub Actions
files. All CI now lives on Jenkins: the PR pipeline (Jenkinsfile) must
exercise every image flavor, and the publish logic lives in
scripts/ci/run_jenkins_release.sh (Jenkins is the sole publisher). This
guard checks the surfaces where flavor coverage and tag scheme actually
live.
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
    pr_jenkinsfile = read("Jenkinsfile")
    release_sh = read("scripts/ci/run_jenkins_release.sh")
    release_jenkinsfile = read("jenkins/release.Jenkinsfile")

    checks = [
        ("PR pipeline (Jenkinsfile) exercises all flavors",
         all(token in pr_jenkinsfile for token in FLAVOR_TOKENS)),
        ("PR pipeline does not push to Docker Hub",
         "--push" not in pr_jenkinsfile),
        # The only publish from the PR pipeline is the develop pre-release
        # channel: gated on develop (branch job, or the release PR whose head
        # is develop), credential-bound, channel tags only.
        ("PR pipeline publishes the develop channel only from develop",
         "stage('Publish develop channel')" in pr_jenkinsfile
         and "branch 'develop'" in pr_jenkinsfile
         and "env.CHANGE_BRANCH == 'develop'" in pr_jenkinsfile
         and "credentialsId: 'dockerhub-publish'" in pr_jenkinsfile
         and "run_jenkins_release.sh --channel develop" in pr_jenkinsfile),
        ("PR pipeline rejects PRs into main that do not come from develop",
         "stage('Branch Policy')" in pr_jenkinsfile
         and "env.CHANGE_TARGET == 'main'" in pr_jenkinsfile
         and "env.CHANGE_BRANCH != 'develop'" in pr_jenkinsfile),
        ("release script channel mode never emits a version tag or :latest",
         "channel_tags_for_flavor()" in release_sh
         and 'pipepito/acestream-scraper:${CHANNEL}-scraper-acestream-acexy' in release_sh
         and 'Refusing to release a development version' in release_sh),
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
         'PROMOTE_LATEST="${PUBLISH_LATEST:-0}"' in release_sh
         and 'if [[ "$PROMOTE_LATEST" == "1" ]]; then' in release_sh
         # :latest is promoted by retagging the canaried version manifest,
         # never by a rebuild.
         and "scripts/ci/promote_latest.sh" in release_sh
         and "--tag pipepito/acestream-scraper:latest" not in release_sh),
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
