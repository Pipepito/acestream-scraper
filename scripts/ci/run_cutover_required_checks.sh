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

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python interpreter not found: $PYTHON_BIN"
  exit 1
fi

"$PYTHON_BIN" -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements.txt

echo "Running backend checks ($PROFILE)..."
backend/venv/bin/pytest -q \
  backend/tests/contracts/test_channel_contracts.py \
  backend/tests/contracts/test_config_contracts.py \
  backend/tests/test_error_contracts.py

if [[ "$PROFILE" == "full" ]]; then
  backend/venv/bin/pytest -q \
    backend/tests/test_channels.py \
    backend/tests/test_tv_channels.py \
    backend/tests/test_config.py \
    backend/tests/test_epg.py \
    backend/tests/test_urls.py \
    backend/tests/test_scrapers.py \
    backend/tests/test_health.py \
    backend/tests/architecture/test_layer_boundaries.py \
    backend/tests/test_background_tasks.py
fi

echo "Running frontend build checks..."
(
  cd frontend
  npm ci
  CI=true npm test -- --watch=false
  npm run build
)

docker compose config >/dev/null

echo "Cutover required checks passed for profile=$PROFILE"
