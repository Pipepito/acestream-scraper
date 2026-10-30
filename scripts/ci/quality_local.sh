#!/usr/bin/env bash
# Fast developer feedback. Jenkins uses independently pinned private policy.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
mode="${1:-fast}"
ruff_advisory() {
  local result=0
  ruff check --select E9,F63,F7,F82 -- "$@" || result=$?
  if [[ "$result" -gt 1 ]]; then return "$result"; fi
  if [[ "$result" -eq 1 ]]; then
    echo 'Ruff findings are advisory during rollout; review them before pushing. Jenkins remains authoritative.' >&2
  fi
}
case "$mode" in
  staged)
    command -v gitleaks >/dev/null
    # stdin never writes a report containing the candidate secret.
    git diff --cached --no-ext-diff --no-textconv --unified=0 | \
      gitleaks stdin --redact=100 --no-banner --log-level=error
    while IFS= read -r -d '' path; do
      [[ "$path" != *.py || ! -f "$path" ]] || ruff_advisory "$path"
    done < <(git diff --cached --name-only --diff-filter=ACMR -z)
    ;;
  fast)
    command -v ruff >/dev/null
    ruff_advisory backend
    (cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck)
    ;;
  full)
    export CI_COVERAGE_DIR="$(pwd)/.quality-reports"
    bash scripts/ci/run_v2_test_suite.sh --profile full
    ;;
  *) echo 'Usage: quality_local.sh staged|fast|full' >&2; exit 2 ;;
esac
