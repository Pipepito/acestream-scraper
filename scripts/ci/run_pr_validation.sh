#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

if [[ ! -x /opt/backend-venv/bin/python || ! -d /opt/frontend-node_modules ]]; then
  echo "Trusted PR runner dependencies are missing." >&2
  exit 1
fi

# The runner image owns dependencies. Python is read-only; frontend dependencies
# are copied into the size-limited workspace because Vite may write caches there.
# No dependency installation or network access happens while contributor code is
# executing.
rm -rf backend/venv frontend/node_modules
ln -s /opt/backend-venv backend/venv
cp -a /opt/frontend-node_modules frontend/node_modules

echo "Running repository and runtime contract checks..."
bash scripts/ci/assert_no_legacy_paths.sh --strict
bash scripts/ci/validate_runtime_contract.sh
bash scripts/ci/validate_command_builder.sh
bash scripts/ci/publish_wiki.sh --dry-run
bash scripts/ci/publish_pages.sh --dry-run

echo "Running the complete non-Docker backend and frontend suites..."
CI_USE_PREINSTALLED_DEPS=1 \
  bash scripts/ci/run_v2_test_suite.sh --profile full

echo "Running architecture and publication-policy dry runs..."
backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py \
  --profile quick \
  --json-output > phase5-gate-report-pr.json

echo "Credential-free PR validation passed."
