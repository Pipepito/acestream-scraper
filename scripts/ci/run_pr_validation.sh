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

echo "Running backend parity and contract checks..."
backend/venv/bin/python scripts/phase_gates/phase1_gate_runner.py \
  --profile quick \
  --json-output > phase1-gate-report.json
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/contracts/test_channel_contracts.py \
  backend/tests/contracts/test_config_contracts.py \
  backend/tests/contracts/test_urls_contracts.py \
  backend/tests/test_error_contracts.py \
  backend/tests/regression/test_legacy_behavior_parity.py

echo "Checking the generated API contract..."
PYTHONPATH=backend backend/venv/bin/python backend/scripts/dump_openapi.py
(
  cd frontend
  npm run codegen
  if ! git diff --exit-code src/types/api-generated.ts; then
    echo "Generated API types differ from the committed snapshot." >&2
    exit 1
  fi
)

echo "Running frontend checks..."
(
  cd frontend
  npm run lint -- --max-warnings=0
  npm run typecheck
  npm test -- --watch=false --runInBand Dashboard.test.tsx AcestreamChannelsPage.test.tsx
  npm run build
)

echo "Running architecture and publication-policy dry runs..."
backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py \
  --profile quick \
  --json-output > phase5-gate-report-pr.json

echo "Credential-free PR validation passed."
