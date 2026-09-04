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

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "Python interpreter not found: $PYTHON_BIN"
  exit 1
fi

if [[ ! -d backend/venv ]]; then
  "$PYTHON_BIN" -m venv backend/venv
fi

if [[ "${CI_USE_PREINSTALLED_DEPS:-0}" == "1" ]]; then
  if [[ ! -x backend/venv/bin/pytest ]]; then
    echo "ERROR: CI_USE_PREINSTALLED_DEPS=1 requires backend/venv/bin/pytest."
    exit 1
  fi
  BACKEND_PYTEST="backend/venv/bin/pytest"
else
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
fi

echo "Running canonical backend suite ($PROFILE)..."
if [[ "$PROFILE" == "quick" ]]; then
  PYTHONPATH=backend "$BACKEND_PYTEST" -q \
    backend/tests/contracts/test_channel_contracts.py \
    backend/tests/contracts/test_config_contracts.py \
    backend/tests/contracts/test_urls_contracts.py \
    backend/tests/test_error_contracts.py \
    backend/tests/regression/test_legacy_behavior_parity.py
else
  # backend/tests/docker builds images with buildx (QEMU for ARM) and boots
  # the real engines; the Jenkinsfiles run those files as explicit smoke
  # stages, so keep them out of the unit/contract run.
  PYTHONPATH=backend "$BACKEND_PYTEST" -q backend/tests --ignore=backend/tests/docker
fi

echo "Refreshing OpenAPI schema for codegen..."
PYTHONPATH=backend "$BACKEND_PYTEST" --version >/dev/null 2>&1 || true
PYTHONPATH=backend backend/venv/bin/python backend/scripts/dump_openapi.py

echo "Running canonical frontend suite ($PROFILE)..."
(
  cd frontend
  if [[ "${CI_USE_PREINSTALLED_DEPS:-0}" == "1" ]]; then
    if [[ ! -x node_modules/.bin/jest ]]; then
      echo "ERROR: CI_USE_PREINSTALLED_DEPS=1 requires frontend/node_modules."
      exit 1
    fi
  elif ! npm ci >/dev/null; then
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

  # Regenerate the typed OpenAPI client and fail the suite if the result
  # diverges from the committed snapshot. Schema drift between
  # backend/app/schemas/ and frontend/src/types/api-generated.ts is a
  # contract bug that would otherwise only surface at runtime.
  npm run codegen
  if ! git diff --exit-code src/types/api-generated.ts >/dev/null 2>&1; then
    echo "ERROR: openapi-typescript output diverges from committed types."
    echo "Run 'PYTHONPATH=backend backend/venv/bin/python backend/scripts/dump_openapi.py'"
    echo "from the repo root, then 'cd frontend && npm run codegen', and commit the result."
    git diff src/types/api-generated.ts | head -40
    exit 1
  fi

  npm run lint -- --max-warnings=0
  npm run typecheck

  if [[ "$PROFILE" == "quick" ]]; then
    CI=true npm test -- --watch=false --runInBand Dashboard.test.tsx AcestreamChannelsPage.test.tsx
  else
    CI=true npm test -- --watch=false --runInBand
  fi

  npm run build
)

echo "Canonical v2 test suite passed for profile=$PROFILE"
