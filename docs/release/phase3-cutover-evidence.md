# Phase 3 Cutover Evidence

This file is the branch signoff artifact generated/updated from gate runner output.

## Scope

- Phase 3 big-bang cutover validation on root backend/frontend ownership.
- Profile executed: `full`

## Risks

- No blocking gate failures detected in this report.
- Review non-blocking failures and warnings before final signoff.

## Verification

- Report source: `phase3-gate-report-full.json`
- Generated at: `2026-02-27T19:11:15.345279+00:00`
- Overall passed: `True`

## Gate Results

| Gate ID | Blocking | Status | Exit | Command |
|---------|----------|--------|------|---------|
| parity_full | true | passed | 0 | `python3 scripts/phase_gates/phase1_gate_runner.py --profile full --json-output > phase3-phase1-full.json` |
| root_stack_full | true | passed | 0 | `bash scripts/ci/run_cutover_required_checks.sh --profile full` |
| compose_smoke | true | passed | 0 | `docker compose config -q` |
| legacy_reference_guard | true | passed | 0 | `bash scripts/ci/assert_no_legacy_paths.sh --strict` |
