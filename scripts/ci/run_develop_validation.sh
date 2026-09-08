#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

if [[ ! -x /opt/backend-venv/bin/python || ! -d /opt/frontend-node_modules ]]; then
  echo "Trusted develop runner dependencies are missing." >&2
  exit 1
fi

OUTPUT_DIR="${CI_OUTPUT_DIR:-$ROOT_DIR}"
mkdir -p "$OUTPUT_DIR"

# Use the immutable dependency set built from develop. The copied frontend
# modules live on the size-limited tmpfs because Vite and Jest may write caches.
rm -rf backend/venv frontend/node_modules
ln -s /opt/backend-venv backend/venv
cp -R /opt/frontend-node_modules frontend/node_modules

set +e
CI_USE_PREINSTALLED_DEPS=1 CUTOVER_SKIP_COMPOSE=1 \
  backend/venv/bin/python scripts/phase_gates/phase3_gate_runner.py \
    --profile full \
    --skip-command compose_smoke \
    --log-dir "$OUTPUT_DIR/gate-logs" \
    --json-output > "$OUTPUT_DIR/phase3-gate-report-full.json"
gate_status=$?
set -e

if [[ -f phase3-phase1-full.json ]]; then
  cp phase3-phase1-full.json "$OUTPUT_DIR/phase3-phase1-full.json"
fi

# Print the captured outcome as well as retaining machine-readable artifacts.
backend/venv/bin/python - "$OUTPUT_DIR/phase3-gate-report-full.json" "$OUTPUT_DIR/phase3-phase1-full.json" <<'REPORT'
import json
import sys
from pathlib import Path
from scripts.phase_gates.phase3_gate_runner import print_human_report
with open(sys.argv[1], encoding="utf-8") as report:
    print_human_report(json.load(report))
if Path(sys.argv[2]).is_file():
    from scripts.phase_gates.phase1_gate_runner import print_human_report as print_parity_report
    with open(sys.argv[2], encoding="utf-8") as report:
        print_parity_report(json.load(report))
REPORT

if [[ "$gate_status" -ne 0 ]]; then
  exit "$gate_status"
fi

bash scripts/ci/validate_runtime_contract.sh
echo "Pinned Python 3.12 develop validation passed."
