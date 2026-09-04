#!/usr/bin/env python3
"""Assert the canonical Jenkins validation and publication boundaries."""

from __future__ import annotations

import os
import subprocess
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

# Tags the release publish plan must emit (checked by running the script's
# --print-publish-plan, so a refactor of the tag functions cannot drift).
PHASE1_TAGS = [
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
CHANNEL_TAGS = [
    "pipepito/acestream-scraper:develop",
    "pipepito/acestream-scraper:develop-scraper",
    "pipepito/acestream-scraper:develop-scraper-acestream",
    "pipepito/acestream-scraper:develop-scraper-acexy",
    "pipepito/acestream-scraper:develop-scraper-acestream-acexy",
]


def publish_plan(*args: str, publish_latest: str | None = None) -> str:
    env = os.environ.copy()
    env.pop("PUBLISH_LATEST", None)
    env.pop("RELEASE_IMAGE_REPO", None)
    if publish_latest is not None:
        env["PUBLISH_LATEST"] = publish_latest
    result = subprocess.run(
        ["bash", str(ROOT / "scripts/ci/run_jenkins_release.sh"), "--print-publish-plan", *args],
        cwd=ROOT, capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        sys.stderr.write(f"FAIL: publish plan exited {result.returncode}: {result.stderr}\n")
        raise SystemExit(1)
    return result.stdout


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        sys.stderr.write(f"FAIL: required file not found: {rel}\n")
        raise SystemExit(1)
    return path.read_text(encoding="utf-8")


def main() -> int:
    pr_jenkinsfile = read("jenkins/pr.Jenkinsfile")
    develop_jenkinsfile = read("jenkins/develop.Jenkinsfile")
    phase5_config = read("scripts/phase_gates/phase5_gate_config.yaml")
    release_sh = read("scripts/ci/run_jenkins_release.sh")
    release_jenkinsfile = read("jenkins/release.Jenkinsfile")
    version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
    phase1_plan = publish_plan()
    promote_plan = publish_plan(publish_latest="1")
    channel_plan = publish_plan("--channel", "develop")
    phase1_tags = [t.replace("${VERSION}", version) for t in PHASE1_TAGS]

    checks = [
        ("PR architecture plan exercises all flavors",
         all(token in phase5_config for token in FLAVOR_TOKENS)),
        ("PR pipeline has no publication or credential binding",
         "withCredentials" not in pr_jenkinsfile
         and "run_jenkins_release.sh" not in pr_jenkinsfile
         and "publish_wiki.sh" not in pr_jenkinsfile
         and "publish_pages.sh" not in pr_jenkinsfile),
        ("PR pipeline confines contributor code to the hardened runner",
         "--network none" in pr_jenkinsfile
         and "--read-only" in pr_jenkinsfile
         and "--cap-drop ALL" in pr_jenkinsfile
         and "no-new-privileges" in pr_jenkinsfile
         and '$WORKSPACE:/source:ro' in pr_jenkinsfile
         and "bash scripts/ci/run_pr_validation.sh" in pr_jenkinsfile
         and "runnerInputsChanged" in pr_jenkinsfile
         and "env.CHANGE_FORK" in pr_jenkinsfile),
        ("PR pipeline rejects PRs into main that do not come from develop",
         "stage('Branch Policy')" in pr_jenkinsfile
         and "env.CHANGE_TARGET == 'main'" in pr_jenkinsfile
         and "env.CHANGE_BRANCH != 'develop'" in pr_jenkinsfile),
        ("develop publication has an exact-branch guard",
         "stage('Current develop guard')" in develop_jenkinsfile
         and "git rev-parse origin/develop" in develop_jenkinsfile),
        ("develop publication is credential-bound in its dedicated pipeline",
         "stage('Publish develop channel')" in develop_jenkinsfile
         and "credentialsId: 'dockerhub-publish'" in develop_jenkinsfile
         and "run_jenkins_release.sh --channel develop" in develop_jenkinsfile),
        ("develop pipeline builds the trusted fork runner",
         "docker/ci/pr-runner.Dockerfile" in develop_jenkinsfile
         and "acestream-scraper-pr-ci:develop" in develop_jenkinsfile),
        ("release script channel mode never emits a version tag or :latest",
         all(tag in channel_plan for tag in CHANNEL_TAGS)
         and "pipepito/acestream-scraper:latest" not in channel_plan
         and f"pipepito/acestream-scraper:{version}" not in channel_plan
         and 'Refusing to release a development version' in release_sh),
        ("release script declares all flavors",
         all(f'"{flavor}"' in release_sh for flavor in FLAVORS)),
        ("release script phase-1 plan publishes all required tags and no :latest",
         all(tag in phase1_plan for tag in phase1_tags)
         and "pipepito/acestream-scraper:latest" not in phase1_plan),
        ("release script promotion plan retags the version manifest to :latest",
         promote_plan.count("pipepito/acestream-scraper:latest") == 1
         and f"<- pipepito/acestream-scraper:{version}" in promote_plan
         and "no flavor rebuild" in promote_plan),
        ("release script pushes by digest, platform-major, with cache pruning",
         "--push-by-digest" in release_sh
         and "publish_platform_major" in release_sh
         and "docker buildx prune --builder" in release_sh),
        ("release script targets pipepito Docker Hub repo by default",
         'IMAGE_REPO="${RELEASE_IMAGE_REPO:-pipepito/acestream-scraper}"' in release_sh
         and "pipepito/acestream-scraper-v2" not in release_sh),
        # Two-phase publish: :latest is gated behind PUBLISH_LATEST so the
        # first publish of a new version touches versioned + flavor-channel
        # tags only and a follow-up run promotes :latest after canary.
        ("release script gates :latest behind PUBLISH_LATEST",
         'PROMOTE_LATEST="${PUBLISH_LATEST:-0}"' in release_sh
         and 'if [[ "$PROMOTE_LATEST" == "1" ]]; then' in release_sh
         # :latest is promoted by retagging the canaried version manifest,
         # never by a rebuild.
         and "scripts/ci/promote_latest.sh" in release_sh),
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
