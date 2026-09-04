---
phase: 03-v2-only-cutover-and-legacy-retirement
plan: "03"
subsystem: infra
tags: [cutover, ci, gates, verification, release]
requires:
  - phase: 03-v2-only-cutover-and-legacy-retirement
    provides: strict root ownership, legacy retirement, and reconciled docs from 03-01 and 03-02
provides:
  - Executable phase-3 cutover checklist and evidence contract
  - Deterministic quick/full gate runner with machine-readable output
  - Automated cutover validation workflow and generated branch evidence
affects: [phase-4-ui-modernization, phase-5-multiarch, release-readiness, merge-policy]
tech-stack:
  added: [none]
  patterns: [deterministic-cutover-gates, report-driven-signoff, ci-artifact-evidence]
key-files:
  created: [docs/migration/phase3-cutover-checklist.md, scripts/phase_gates/phase3_gate_config.yaml, scripts/phase_gates/phase3_gate_runner.py, scripts/ci/collect_cutover_evidence.sh, .github/workflows/cutover-validation.yml]
  modified: [docs/release/phase3-cutover-evidence.md]
key-decisions:
  - "Use one deterministic gate runner command with profile config to enforce consistent quick/full execution order."
  - "Generate release evidence from machine-readable reports rather than manual narrative signoff."
  - "Run quick profile on PRs and full profile on main/release pushes to keep branch gates strict and auditable."
patterns-established:
  - "Gate orchestration pattern: config-defined commands + blocking semantics + JSON summary output."
  - "Evidence pattern: scripted markdown generation from full-profile report artifacts."
requirements-completed: [MIGR-04, COMP-03]
duration: 14 min
completed: 2026-02-27
---

# Phase 03 Plan 03: Cutover Checklist + Gate Runner + Evidence Workflow Summary

**Phase 3 now has an automated, auditable cutover validation system (quick/full profiles, CI workflow wiring, and scripted evidence generation) that blocks merge on required failures.**

## Performance

- **Duration:** 14 min
- **Started:** 2026-02-27T20:02:16+01:00
- **Completed:** 2026-02-27T20:16:44+01:00
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments
- Added a merge-blocking Phase 3 checklist and release evidence contract with explicit Scope/Risks/Verification structure.
- Implemented a phase-3 gate runner and profile config for deterministic quick/full gate execution with JSON reports.
- Added CI workflow (`cutover-validation.yml`) and generated full-profile evidence via scripted collection.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author executable phase-3 cutover checklist and evidence contract** - `7d9c45c` (docs)
2. **Task 2: Build phase-3 gate runner, config, and evidence collector** - `f9e2e56` (feat)
3. **Task 3: Wire cutover validation workflow and run full-profile verification** - `cd7556c` (feat)

## Files Created/Modified
- `docs/migration/phase3-cutover-checklist.md` - branch cutover checklist with blocker semantics and fix-forward rules.
- `docs/release/phase3-cutover-evidence.md` - release evidence contract and generated gate result artifact.
- `scripts/phase_gates/phase3_gate_config.yaml` - quick/full profile definitions and deterministic command order.
- `scripts/phase_gates/phase3_gate_runner.py` - gate orchestration with blocking semantics and JSON output.
- `scripts/ci/collect_cutover_evidence.sh` - report-to-evidence markdown generator.
- `.github/workflows/cutover-validation.yml` - automated CI path for quick/full cutover validation and artifact upload.

## Decisions Made
- Standardized cutover validation through a single profile-driven runner instead of ad-hoc command sequences.
- Made evidence generation script-backed so verification sections cannot be skipped.
- Scoped CI to quick checks on PR and full checks on push/workflow_dispatch to balance strictness and runtime cost.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `python` binary missing for verification commands in current environment**
- **Found during:** Task 2/3 verification commands (`python scripts/phase_gates/phase3_gate_runner.py ...`)
- **Issue:** Environment exposes `python3` but not `python`.
- **Fix:** Ran equivalent verification with `python3` for quick/full profiles.
- **Files modified:** None
- **Verification:** Quick/full reports generated successfully; both profiles passed and evidence collection succeeded.
- **Committed in:** N/A (verification-path adaptation only)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope or behavior change; validation remained deterministic with equivalent interpreter invocation.

## Issues Encountered
- None beyond local interpreter alias availability (`python` vs `python3`).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 goals are fully executable with checklist + automated gates + evidence contract.
- Ready to transition into Phase 4 (frontend UX modernization) while preserving cutover guardrails.

---
*Phase: 03-v2-only-cutover-and-legacy-retirement*
*Completed: 2026-02-27*
