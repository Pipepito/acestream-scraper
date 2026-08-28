#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

DRY_RUN=0
PRINT_PLAN=0
CHANNEL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --print-publish-plan)
      PRINT_PLAN=1
      shift
      ;;
    --channel)
      # Pre-release channel publish (the `develop` branch): push floating
      # channel tags only — never a version tag, never :latest. Validation
      # already ran in the branch's PR pipeline before this is invoked.
      CHANNEL="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: bash scripts/ci/run_jenkins_release.sh [--dry-run | --print-publish-plan] [--channel <name>]"
      exit 1
      ;;
  esac
done

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
VERSION=$(tr -d '\n' < version.txt)

if [[ -n "$CHANNEL" ]] && ! [[ "$CHANNEL" =~ ^[a-z][a-z0-9-]{0,30}$ ]]; then
  echo "Invalid channel name: $CHANNEL (lowercase letters, digits and dashes)" >&2
  exit 1
fi
if [[ -z "$CHANNEL" && "$VERSION" == *-dev* ]]; then
  # develop carries the next version as vX.Y.Z-dev; the bump to vX.Y.Z lands
  # on develop (via PR) right before the develop -> main release PR, so a
  # release run must never see a -dev version.
  echo "Refusing to release a development version (version.txt = $VERSION). Land the version bump on develop (via PR) before the develop -> main release PR." >&2
  exit 1
fi

# Floating pre-release tags for a channel: <channel> is the full payload
# (mirrors what :latest means for releases) plus <channel>-<flavor> for every
# flavor. Immutable per-commit tags are deliberately not pushed.
channel_tags_for_flavor() {
  case "$1" in
    scraper-acestream-acexy)
      printf '%s\n' "pipepito/acestream-scraper:${CHANNEL} pipepito/acestream-scraper:${CHANNEL}-scraper-acestream-acexy"
      ;;
    scraper|scraper-acestream|scraper-acexy)
      printf '%s\n' "pipepito/acestream-scraper:${CHANNEL}-$1"
      ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

FLAVORS=(
  "scraper"
  "scraper-acestream"
  "scraper-acexy"
  "scraper-acestream-acexy"
)

PUBLISH_FLAVORS=(
  "scraper-acestream-acexy"
  "scraper"
  "scraper-acestream"
  "scraper-acexy"
)

preflight_result_file_for_flavor() {
  case "$1" in
    scraper) printf '%s\n' "phase5-build-result-release-scraper.json" ;;
    scraper-acestream) printf '%s\n' "phase5-build-result-release-scraper-acestream.json" ;;
    scraper-acexy) printf '%s\n' "phase5-build-result-release-scraper-acexy.json" ;;
    scraper-acestream-acexy) printf '%s\n' "phase5-build-result-release-scraper-acestream-acexy.json" ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

publish_result_file_for_flavor() {
  case "$1" in
    scraper-acestream-acexy) printf '%s\n' "phase5-build-result-release-full-publish.json" ;;
    scraper) printf '%s\n' "phase5-build-result-release-scraper-publish.json" ;;
    scraper-acestream) printf '%s\n' "phase5-build-result-release-scraper-acestream-publish.json" ;;
    scraper-acexy) printf '%s\n' "phase5-build-result-release-scraper-acexy-publish.json" ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

# The floating :latest tag is never pushed by a build. Phase 1
# (PUBLISH_LATEST=0, the default) pushes versioned + flavor-channel tags only,
# so users on :latest are untouched during the canary window. Phase 2
# (PUBLISH_LATEST=1) RETAGS the canary-validated
# pipepito/acestream-scraper:${VERSION} manifest to pipepito/acestream-scraper:latest
# via scripts/ci/promote_latest.sh — no rebuild, so :latest is byte-identical
# to what was validated. Only the full payload flavor
# (scraper-acestream-acexy, whose manifest the version tag points at) can
# ever become :latest.
LATEST_SOURCE_FLAVOR="scraper-acestream-acexy"

publish_tags_for_flavor() {
  case "$1" in
    scraper-acestream-acexy)
      printf '%s\n' "pipepito/acestream-scraper:${VERSION} pipepito/acestream-scraper:scraper-acestream-acexy pipepito/acestream-scraper:${VERSION}-scraper-acestream-acexy"
      ;;
    scraper)
      printf '%s\n' "pipepito/acestream-scraper:scraper pipepito/acestream-scraper:${VERSION}-scraper"
      ;;
    scraper-acestream)
      printf '%s\n' "pipepito/acestream-scraper:scraper-acestream pipepito/acestream-scraper:${VERSION}-scraper-acestream"
      ;;
    scraper-acexy)
      printf '%s\n' "pipepito/acestream-scraper:scraper-acexy pipepito/acestream-scraper:${VERSION}-scraper-acexy"
      ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

PROMOTE_LATEST="${PUBLISH_LATEST:-0}"

if [[ "$PRINT_PLAN" -eq 1 && -n "$CHANNEL" ]]; then
  echo "Channel publish plan (channel=${CHANNEL}, VERSION=${VERSION}; no version tag, no :latest):"
  for flavor in "${PUBLISH_FLAVORS[@]}"; do
    printf '  %s: %s\n' "$flavor" "$(channel_tags_for_flavor "$flavor")"
  done
  exit 0
fi

if [[ "$PRINT_PLAN" -eq 1 ]]; then
  echo "Release publish plan (PUBLISH_LATEST=${PROMOTE_LATEST}, VERSION=${VERSION}):"
  if [[ "$PROMOTE_LATEST" == "1" ]]; then
    echo "  promote: pipepito/acestream-scraper:latest <- pipepito/acestream-scraper:${VERSION} (retag of the canary-validated ${LATEST_SOURCE_FLAVOR} manifest; no flavor rebuild)"
  else
    for flavor in "${PUBLISH_FLAVORS[@]}"; do
      printf '  %s: %s\n' "$flavor" "$(publish_tags_for_flavor "$flavor")"
    done
  fi
  exit 0
fi

GIT_SHA=$(git rev-parse HEAD)

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  echo "Required buildx builder not found: $BUILDER"
  exit 1
fi

# Pre-release channel publish (develop). The PR pipeline already ran every
# validation and smoke stage on this exact revision; this stage only builds
# the multi-platform flavors and pushes the floating channel tags.
if [[ -n "$CHANNEL" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    for flavor in "${PUBLISH_FLAVORS[@]}"; do
      bash scripts/ci/build_multiarch_images.sh --dry-run --builder "$BUILDER" --flavor "$flavor" \
        --result-file "phase5-build-result-channel-${CHANNEL}-${flavor}.json"
    done
    echo "Dry-run channel publish plan completed."
    exit 0
  fi
  : "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME is required}"
  : "${DOCKERHUB_TOKEN:?DOCKERHUB_TOKEN is required}"
  printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
  channel_tags=()
  for flavor in "${PUBLISH_FLAVORS[@]}"; do
    IFS=' ' read -r -a tags <<< "$(channel_tags_for_flavor "$flavor")"
    build_args=(
      bash scripts/ci/build_multiarch_images.sh
      --flavor "$flavor"
      --push
      --builder "$BUILDER"
      --result-file "phase5-build-result-channel-${CHANNEL}-${flavor}.json"
    )
    for tag in "${tags[@]}"; do
      build_args+=(--tag "$tag")
      channel_tags+=("$tag")
    done
    "${build_args[@]}"
    for tag in "${tags[@]}"; do
      bash scripts/ci/verify_multiarch_manifest.sh --image "$tag" --flavor "$flavor"
    done
  done
  CHANNEL_TAGS_JSON="$(python3 - "${channel_tags[@]}" <<'PY2'
import json, sys
print(json.dumps(sys.argv[1:]))
PY2
)"
  RELEASE_CHANNEL="$CHANNEL" RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_BUILDER="$BUILDER" RELEASE_TAGS_JSON="$CHANNEL_TAGS_JSON" python3 - "phase5-build-result-channel-${CHANNEL}-metadata.json" <<'PY2'
import json, os, sys
from datetime import datetime, timezone
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "channel",
    "channel": os.environ["RELEASE_CHANNEL"],
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "tags": json.loads(os.environ["RELEASE_TAGS_JSON"]),
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY2
  echo "Channel publish completed: ${CHANNEL}"
  exit 0
fi

# Phase 2: promotion run. Nothing is rebuilt or re-tested — the images were
# built, smoke-tested and canaried in phase 1; this only moves :latest.
if [[ "$PROMOTE_LATEST" == "1" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    bash scripts/ci/promote_latest.sh --version "$VERSION" --flavor "$LATEST_SOURCE_FLAVOR" --dry-run
    echo "Dry-run promotion plan completed."
    exit 0
  fi
  : "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME is required}"
  : "${DOCKERHUB_TOKEN:?DOCKERHUB_TOKEN is required}"
  printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
  bash scripts/ci/promote_latest.sh --version "$VERSION" --flavor "$LATEST_SOURCE_FLAVOR"
  RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_BUILDER="$BUILDER" python3 - "phase5-build-result-release-metadata.json" <<'PY2'
import json, os, sys
from datetime import datetime, timezone
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "mode": "promote-latest",
    "tags": ["pipepito/acestream-scraper:latest"],
    "source": "pipepito/acestream-scraper:" + os.environ["RELEASE_VERSION"],
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY2
  echo "Release promotion completed."
  exit 0
fi

bash scripts/ci/run_cutover_required_checks.sh --profile full

for flavor in "${FLAVORS[@]}"; do
  result_file="$(preflight_result_file_for_flavor "$flavor")"

  bash scripts/ci/build_multiarch_images.sh \
    --dry-run \
    --builder "$BUILDER" \
    --flavor "$flavor" \
    --result-file "$result_file"

  bash scripts/ci/verify_multiarch_manifest.sh \
    --result-file "$result_file" \
    --flavor "$flavor"
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run preflight completed."
  exit 0
fi

# Real AceStream engine runtime smoke. Mirrors Jenkinsfile's
# 'Acestream Engine Runtime Smoke' stage so the release path validates that
# the published image will actually start the engine before any tags reach
# Docker Hub. BUILDX_BUILDER=default forces the docker driver because the
# docker-container driver's isolated network breaks curl to
# download.acestream.media on WARP-routed builders.
# scraper-acestream resolves to amd64 + arm64 + arm/v7; --load needs a single
# platform, so pin the runner's native one. The ARM engine layouts are
# verified by the installer-stage tests (QEMU build, no execution).
(
  export BUILDX_BUILDER=default
  bash scripts/ci/build_multiarch_images.sh \
    --flavor scraper-acestream \
    --platforms linux/amd64 \
    --load \
    --network host \
    --tag acestream-scraper:release-smoke
)
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
# The acexy flavors must ship the real upstream proxy, not the build fixture.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k "android_apk_install_layout"
# The ~2 GB smoke image is not needed for the publish step; reclaim the
# runner's disk before the multi-platform builds (see cleanup_runner_docker.sh).
docker image rm -f acestream-scraper:release-smoke >/dev/null 2>&1 || true
bash scripts/ci/cleanup_runner_docker.sh || true

: "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME is required}"
: "${DOCKERHUB_TOKEN:?DOCKERHUB_TOKEN is required}"

printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin

all_tags=()

for flavor in "${PUBLISH_FLAVORS[@]}"; do
  result_file="$(publish_result_file_for_flavor "$flavor")"
  IFS=' ' read -r -a tags <<< "$(publish_tags_for_flavor "$flavor")"

  build_args=(
    bash scripts/ci/build_multiarch_images.sh
    --flavor "$flavor"
    --push
    --builder "$BUILDER"
    --result-file "$result_file"
  )

  for tag in "${tags[@]}"; do
    build_args+=(--tag "$tag")
    all_tags+=("$tag")
  done

  "${build_args[@]}"

  for tag in "${tags[@]}"; do
    bash scripts/ci/verify_multiarch_manifest.sh \
      --image "$tag" \
      --flavor "$flavor"
  done
done

ALL_TAGS_JSON="$(python3 - "${all_tags[@]}" <<'PY'
import json
import sys

print(json.dumps(sys.argv[1:]))
PY
)"

RELEASE_METADATA_FILE="phase5-build-result-release-metadata.json"
RELEASE_BUILDER="$BUILDER" RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_TAGS_JSON="$ALL_TAGS_JSON" python3 - "$RELEASE_METADATA_FILE" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

metadata_file = sys.argv[1]
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "tags": json.loads(os.environ["RELEASE_TAGS_JSON"]),
}
with open(metadata_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY

echo "Release publish completed."
