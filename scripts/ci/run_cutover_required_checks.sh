#!/usr/bin/env bash
set -euo pipefail

PROFILE="quick"
if [[ "${1:-}" == "--profile" ]]; then
  PROFILE="${2:-quick}"
fi

if [[ "$PROFILE" != "quick" && "$PROFILE" != "full" ]]; then
  echo "Unsupported profile: $PROFILE"
  exit 1
fi

bash scripts/ci/assert_no_legacy_paths.sh --strict

echo "Running canonical v2 test suite ($PROFILE)..."
bash scripts/ci/run_v2_test_suite.sh --profile "$PROFILE"

if [[ "${CUTOVER_SKIP_COMPOSE:-0}" == "1" ]]; then
  echo "Compose validation delegated to the trusted host."
else
  docker compose config >/dev/null
fi

if [[ "${CUTOVER_INCLUDE_MULTIARCH:-0}" == "1" ]]; then
  echo "Running optional multi-arch matrix validation (dry-run)..."
  bash scripts/ci/build_multiarch_images.sh \
    --dry-run \
    --platforms linux/arm/v7,linux/arm64 \
    --result-file phase5-build-result-cutover.json
  bash scripts/ci/verify_multiarch_manifest.sh \
    --result-file phase5-build-result-cutover.json \
    --required linux/arm/v7,linux/arm64
fi

echo "Cutover required checks passed for profile=$PROFILE"
