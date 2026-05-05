#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  shift
fi

if [[ $# -gt 0 ]]; then
  echo "Usage: bash scripts/ci/run_jenkins_release.sh [--dry-run]"
  exit 1
fi

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
VERSION=$(tr -d '\n' < version.txt)
GIT_SHA=$(git rev-parse HEAD)

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

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  echo "Required buildx builder not found: $BUILDER"
  exit 1
fi

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
  case "$1" in
    scraper-acestream-acexy)
      printf '%s\n' "pipepito/acestream-scraper:latest pipepito/acestream-scraper:${VERSION} pipepito/acestream-scraper:scraper-acestream-acexy pipepito/acestream-scraper:${VERSION}-scraper-acestream-acexy"
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
