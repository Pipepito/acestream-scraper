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

if [[ ! -d backend/venv ]]; then
  "$PYTHON_BIN" -m venv backend/venv
fi

if ! backend/venv/bin/pip install --upgrade pip >/dev/null; then
  echo "WARN: Could not upgrade pip (offline or restricted network)."
fi

if ! backend/venv/bin/pip install -r backend/requirements.txt >/dev/null; then
  echo "WARN: Could not install backend requirements from network."
  FALLBACK_BACKEND_PYTEST=$(find . -type f -path "*/backend/venv/bin/pytest" ! -path "./backend/venv/*" | head -n 1 || true)
  if [[ -n "${FALLBACK_BACKEND_PYTEST:-}" && -x "$FALLBACK_BACKEND_PYTEST" ]]; then
    echo "INFO: Falling back to discovered backend virtualenv for checks."
    BACKEND_PYTEST="$FALLBACK_BACKEND_PYTEST"
  else
    echo "ERROR: No fallback backend virtualenv available."
    exit 1
  fi
else
  BACKEND_PYTEST="backend/venv/bin/pytest"
fi

echo "Running backend checks ($PROFILE)..."
PYTHONPATH=backend "$BACKEND_PYTEST" -q \
  backend/tests/contracts/test_channel_contracts.py \
  backend/tests/contracts/test_config_contracts.py \
  backend/tests/test_error_contracts.py

if [[ "$PROFILE" == "full" ]]; then
  PYTHONPATH=backend "$BACKEND_PYTEST" -q \
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
  if ! npm ci >/dev/null; then
    echo "WARN: npm ci failed (offline or restricted network)."
    FALLBACK_NODE_MODULES=$(find .. -type d -path "*/frontend/node_modules" ! -path "../frontend/node_modules" | head -n 1 || true)
    if [[ -n "${FALLBACK_NODE_MODULES:-}" && -d "$FALLBACK_NODE_MODULES" ]]; then
      echo "INFO: Falling back to discovered cached node_modules."
      rsync -a "${FALLBACK_NODE_MODULES}/" node_modules/
    else
      echo "ERROR: No fallback frontend node_modules available."
      exit 1
    fi
  fi
  npm run build
)

docker compose config >/dev/null

echo "Cutover required checks passed for profile=$PROFILE"
