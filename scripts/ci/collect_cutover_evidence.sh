#!/usr/bin/env bash
set -euo pipefail

REPORT_PATH=""
OUTPUT_PATH="docs/release/phase3-cutover-evidence.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --report)
      REPORT_PATH="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_PATH="${2:-}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "$REPORT_PATH" ]]; then
  echo "Usage: $0 --report <phase3-gate-report.json> [--output <path>]" >&2
  exit 2
fi

if [[ ! -f "$REPORT_PATH" ]]; then
  echo "Report not found: $REPORT_PATH" >&2
  exit 1
fi

python3 - "$REPORT_PATH" "$OUTPUT_PATH" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

report_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
report = json.loads(report_path.read_text(encoding="utf-8"))

lines = []
lines.append("# Phase 3 Cutover Evidence")
lines.append("")
lines.append("This file is the branch signoff artifact generated/updated from gate runner output.")
lines.append("")
lines.append("## Scope")
lines.append("")
lines.append("- Phase 3 big-bang cutover validation on root backend/frontend ownership.")
lines.append(f"- Profile executed: `{report.get('profile', 'unknown')}`")
lines.append("")
lines.append("## Risks")
lines.append("")
if report.get("blocking_failures"):
    lines.append("- Blocking failures present; merge must remain blocked until fix-forward resolution.")
else:
    lines.append("- No blocking gate failures detected in this report.")
lines.append("- Review non-blocking failures and warnings before final signoff.")
lines.append("")
lines.append("## Verification")
lines.append("")
lines.append(f"- Report source: `{report_path.as_posix()}`")
lines.append(f"- Generated at: `{datetime.now(timezone.utc).isoformat()}`")
lines.append(f"- Overall passed: `{report.get('passed', False)}`")
lines.append("")
lines.append("## Gate Results")
lines.append("")
lines.append("| Gate ID | Blocking | Status | Exit | Command |")
lines.append("|---------|----------|--------|------|---------|")
for item in report.get("results", []):
    gate_id = item.get("id", "")
    blocking = str(item.get("blocking", True)).lower()
    status = item.get("status", "")
    exit_code = item.get("exit_code", "")
    command = item.get("command", "").replace("|", "\\|")
    lines.append(f"| {gate_id} | {blocking} | {status} | {exit_code} | `{command}` |")

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Evidence written to {output_path}")
PY
