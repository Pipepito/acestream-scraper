#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
FLAVORS=(
  "scraper"
  "scraper-acestream"
  "scraper-acexy"
  "scraper-acestream-acexy"
)

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  echo "Required buildx builder not found: $BUILDER"
  exit 1
fi

bash scripts/ci/run_cutover_required_checks.sh --profile quick

for flavor in "${FLAVORS[@]}"; do
  result_file="phase5-build-result-pr-${flavor}.json"

  bash scripts/ci/build_multiarch_images.sh \
    --dry-run \
    --builder "$BUILDER" \
    --flavor "$flavor" \
    --result-file "$result_file"

  bash scripts/ci/verify_multiarch_manifest.sh \
    --result-file "$result_file" \
    --flavor "$flavor"
done

echo "Jenkins validation completed."
