#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

DRY_RUN=0
PRINT_PLAN=0
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
    *)
      echo "Usage: bash scripts/ci/run_jenkins_release.sh [--dry-run | --print-publish-plan]"
      exit 1
      ;;
  esac
done

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
VERSION=$(tr -d '\n' < version.txt)

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

publish_tags_for_flavor() {
  # Only the full payload flavor (scraper-acestream-acexy) is eligible for
  # the floating :latest tag, and only when PUBLISH_LATEST=1. Default off so
  # the first publish of a new version touches versioned + flavor-channel
  # tags only; a follow-up run with PUBLISH_LATEST=1 promotes :latest after
  # the canary window.
  local include_latest="${PUBLISH_LATEST:-0}"
  case "$1" in
    scraper-acestream-acexy)
      local tags="pipepito/acestream-scraper:${VERSION} pipepito/acestream-scraper:scraper-acestream-acexy pipepito/acestream-scraper:${VERSION}-scraper-acestream-acexy"
      if [[ "$include_latest" == "1" ]]; then
        tags="pipepito/acestream-scraper:latest $tags"
      fi
      printf '%s\n' "$tags"
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

if [[ "$PRINT_PLAN" -eq 1 ]]; then
  echo "Release publish plan (PUBLISH_LATEST=${PUBLISH_LATEST:-0}, VERSION=${VERSION}):"
  for flavor in "${PUBLISH_FLAVORS[@]}"; do
    printf '  %s: %s\n' "$flavor" "$(publish_tags_for_flavor "$flavor")"
  done
  exit 0
fi

GIT_SHA=$(git rev-parse HEAD)

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  echo "Required buildx builder not found: $BUILDER"
  exit 1
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
