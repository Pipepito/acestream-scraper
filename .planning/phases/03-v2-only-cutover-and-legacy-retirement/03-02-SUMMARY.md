---
phase: 03-v2-only-cutover-and-legacy-retirement
plan: "02"
subsystem: infra
tags: [cutover, config, docs, migration, reliability]
requires:
  - phase: 03-v2-only-cutover-and-legacy-retirement
    provides: root ownership and strict cutover gate baseline from 03-01
provides:
  - Legacy root runtime/deployment paths retired with strict deletion policy
  - One-release env alias compatibility mapping with conflict-precedence semantics
  - Root and migration docs reconciled to backend/frontend canonical model
affects: [phase-03-plan-03, release-readiness, operator-docs, deployment-practices]
tech-stack:
  added: [none]
  patterns: [strict-legacy-retirement, bounded-env-compatibility, root-only-doc-truth]
key-files:
  created: [backend/tests/test_settings_env_compat.py]
  modified: [backend/app/config/settings.py, backend/main.py, README.md, docs/README.md, docs/architecture/deployment.md, docs/migration/migration-strategy.md, docs/migration/development-phases.md, docs/migration/development-progress.md]
key-decisions:
  - "Retire legacy root runtime/deploy files directly with no wrappers to enforce one-way cutover behavior."
  - "Implement a bounded one-release env alias bridge with canonical-variable precedence and explicit conflict warnings."
  - "Rewrite active docs to a single root backend/frontend operating model and remove dual-path migration guidance."
patterns-established:
  - "Legacy deletion policy: removed command surfaces are not replaced by compatibility shims."
  - "Compatibility-window discipline: env alias support is explicit, temporary, and warning-backed."
requirements-completed: [MIGR-02, COMP-03]
duration: 6 min
completed: 2026-02-27
---

# Phase 03 Plan 02: Legacy Retirement + Env Compatibility + Docs Reconciliation Summary

**Legacy runtime paths were removed, env alias compatibility was bounded and tested, and operator docs were rewritten to the root backend/frontend deployment truth.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-27T19:51:30+01:00
- **Completed:** 2026-02-27T19:57:41+01:00
- **Tasks:** 3
- **Files modified:** 33

## Accomplishments
- Deleted obsolete root runtime/deployment files and migration scaffolding (`wsgi.py`, `run_dev.py`, `manage.py`, `entrypoint.sh`, `migrations*`).
- Added one-release env alias bridge with deterministic precedence and startup compatibility event logging.
- Replaced outdated docs with root-only `backend/` + `frontend/` deployment and migration guidance.

## Task Commits

Each task was committed atomically:

1. **Task 1: Retire legacy root runtime/deployment code paths** - `5ba7353` (refactor)
2. **Task 2: Implement one-release legacy env alias mapping + tests** - `2a825ac` (feat)
3. **Task 3: Rewrite root and migration docs to post-cutover truth only** - `a06231d` (docs)

## Files Created/Modified
- `backend/app/config/settings.py` - one-release legacy env alias map, canonical precedence logic, and cutover window metadata.
- `backend/main.py` - structured startup warning emission for env compatibility events.
- `backend/tests/test_settings_env_compat.py` - regression tests for alias apply/conflict/disable behavior.
- `README.md` - root-only operator/developer instructions aligned to canonical deployment.
- `docs/README.md` - docs index aligned to root runtime truth.
- `docs/architecture/deployment.md` - canonical deployment model and environment behavior.
- `docs/migration/migration-strategy.md` - strict cutover migration rules and sequence.
- `docs/migration/development-phases.md` - roadmap-aligned phase definitions.
- `docs/migration/development-progress.md` - current phase execution status and remaining work.

## Decisions Made
- Enforced strict legacy retirement by deleting command paths instead of preserving compatibility wrappers.
- Kept env alias compatibility explicitly bounded to the cutover release window (`v2-cutover-r1`) and not as permanent behavior.
- Normalized docs to one deployment truth to avoid operator drift and stale dual-stack instructions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `pytest` binary not available on PATH for required verification command**
- **Found during:** Plan verification (`pytest -q backend/tests/test_settings_env_compat.py`)
- **Issue:** Environment lacks global `pytest` command.
- **Fix:** Executed equivalent verification using available backend venv binary and root import path: `PYTHONPATH=backend v2/backend/venv/bin/pytest -q backend/tests/test_settings_env_compat.py`.
- **Files modified:** None
- **Verification:** Test suite passed (`4 passed`).
- **Committed in:** N/A (verification-path adaptation only)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope change; verification remained deterministic using existing project virtualenv.

## Issues Encountered
- Verification environment does not expose `pytest` globally; resolved by explicit venv pytest path.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `03-02` requirements (`MIGR-02`, `COMP-03`) are covered and verified.
- Ready for `03-03` big-bang cutover branch checklist and final strict verification.

---
*Phase: 03-v2-only-cutover-and-legacy-retirement*
*Completed: 2026-02-27*
