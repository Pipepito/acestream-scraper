#!/usr/bin/env bash
set -euo pipefail

STRICT=false
if [[ "${1:-}" == "--strict" ]]; then
  STRICT=true
fi

TARGETS=(
  ".github/workflows/pull_request.yml"
  ".github/workflows/release.yml"
  ".github/workflows/phase1-safety-gates.yml"
  "Dockerfile"
  "docker-compose.yml"
  "scripts/ci/run_cutover_required_checks.sh"
)

FORBIDDEN=(
  "wsgi.py"
  "run_dev.py"
  "manage.py"
  "entrypoint.sh"
  "v2/"
)

failures=0

for target in "${TARGETS[@]}"; do
  if [[ ! -f "$target" ]]; then
    continue
  fi
  for pattern in "${FORBIDDEN[@]}"; do
    if rg -n --fixed-strings "$pattern" "$target" >/dev/null 2>&1; then
      echo "FORBIDDEN reference '$pattern' found in $target"
      rg -n --fixed-strings "$pattern" "$target" || true
      failures=$((failures + 1))
    fi
  done
done

if [[ "$STRICT" == "true" ]]; then
  [[ -d backend ]] || { echo "Missing required root directory: backend"; failures=$((failures + 1)); }
  [[ -d frontend ]] || { echo "Missing required root directory: frontend"; failures=$((failures + 1)); }
  [[ -f backend/Dockerfile ]] || { echo "Missing required file: backend/Dockerfile"; failures=$((failures + 1)); }
  [[ -f frontend/Dockerfile ]] || { echo "Missing required file: frontend/Dockerfile"; failures=$((failures + 1)); }
fi

if [[ "$failures" -gt 0 ]]; then
  echo "Legacy path assertion failed with $failures issue(s)."
  exit 1
fi

echo "Legacy path assertion passed."
