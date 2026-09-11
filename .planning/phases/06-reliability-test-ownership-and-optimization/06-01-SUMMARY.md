---
phase: 06-reliability-test-ownership-and-optimization
plan: "01"
subsystem: testing
tags: [ci, regression, ownership, backend-tests, frontend-tests]
requires:
  - phase: 05-multi-arch-build-and-runtime-validation
    provides: CI gate structure and cutover required-check flow
provides:
  - Canonical v2 regression runner used by PR and cutover checks
  - Legacy-to-canonical test ownership matrix
  - Migrated backend/frontend parity assertions in canonical test locations
affects: [phase-06-plan-02, phase-06-plan-03, pr-gates, cutover-checks]
tech-stack:
  added: []
  patterns: [single-test-entrypoint, canonical-test-ownership, legacy-suite-quarantine]
key-files:
  created: [scripts/ci/run_v2_test_suite.sh, backend/tests/contracts/test_urls_contracts.py, backend/tests/regression/test_legacy_behavior_parity.py, docs/testing/test-ownership-matrix.md, tests/README.md]
  modified: [.github/workflows/pull_request.yml, scripts/ci/run_cutover_required_checks.sh, frontend/src/__tests__/AcestreamChannelsPage.test.tsx]
key-decisions:
  - "All required backend/frontend regression checks now run through a single script (`run_v2_test_suite.sh`)."
  - "Root `tests/` is explicitly marked legacy/reference-only and removed from required-check authority."
  - "CI quick profile targets contract/error/parity coverage plus operational frontend smoke tests."
patterns-established:
  - "PR/cutover checks should call canonical suite script, not ad-hoc test command copies."
  - "Coverage migration from legacy paths must land under `backend/tests` or `frontend/src/__tests__`."
requirements-completed: [QUAL-01, QUAL-02]
duration: 1h
completed: 2026-02-27
---

# Phase 06 Plan 01 Summary

**Canonical v2 regression ownership was centralized with CI wiring, migrated parity tests, and explicit legacy-suite retirement guidance.**

## Performance

- **Duration:** 1h
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Added `scripts/ci/run_v2_test_suite.sh` with `quick` and `full` profiles, backend/frontend execution, and offline-friendly fallback behavior.
- Rewired `.github/workflows/pull_request.yml` and `scripts/ci/run_cutover_required_checks.sh` to use the canonical suite entrypoint.
- Migrated legacy behavior checks into `backend/tests/contracts/test_urls_contracts.py` and `backend/tests/regression/test_legacy_behavior_parity.py`.
- Added operational frontend regression in `frontend/src/__tests__/AcestreamChannelsPage.test.tsx`.
- Documented ownership migration in `docs/testing/test-ownership-matrix.md` and quarantined root `tests/` via `tests/README.md`.

## Verification

- `bash scripts/ci/run_v2_test_suite.sh --profile quick` passed.
- `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests` passed.
- `cd frontend && CI=true npm test -- --watch=false --runInBand Dashboard.test.tsx` passed.
- `test ! -d tests || test -f tests/README.md` passed.

## Deviations from Plan

None.

## Issues Encountered

- Local environment lacked a fully provisioned `backend/venv`; canonical suite fallback to discovered virtualenv was exercised and validated.

## Next Phase Readiness

Reliability hardening and DB optimization work can proceed with a deterministic canonical test gate.
