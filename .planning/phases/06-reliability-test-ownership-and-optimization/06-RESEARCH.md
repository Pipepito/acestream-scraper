# Phase 6: Reliability, Test Ownership, and Optimization - Research

**Researched:** 2026-02-27  
**Domain:** Reliability hardening, test-suite ownership consolidation, and DB/data-path optimization  
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Decisions
- Root `backend/` + `frontend/` are canonical runtime/build ownership.
- Scraper logic behavior remains protected as a functional baseline.
- Big-bang cutover is already complete; this phase should harden quality and performance, not re-open architecture direction.
- Existing user databases must remain safe; migration/deploy preflight safeguards already exist and should remain compatible.

### Context Availability
- No Phase 6 `CONTEXT.md` exists yet.
- Planning is based on `ROADMAP`, `REQUIREMENTS`, `STATE`, and current repository evidence.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-04 | Optimize high-churn DB access patterns | Current repositories/services show per-record update/delete and N+1-style loops in scrape/EPG paths |
| QUAL-01 | Rebuild critical regression test ownership under v2 locations | Active CI targets `backend/tests`; root `tests/` remains legacy and not canonical |
| QUAL-02 | Retire redundant legacy test dependencies after replacement | Root `tests/` still exists with Flask-era imports and architecture mismatch |
| QUAL-03 | Burn down high-impact bugs before cutover completion | Background task/status reliability and broad-exception hot paths remain in critical modules |
</phase_requirements>

## Summary

Phase 6 should be executed in three sequential plans:

1. **06-01 Test Ownership Reset:** consolidate critical coverage under `backend/tests` and `frontend/src/__tests__`, then decommission legacy root `tests/` as executable authority.
2. **06-02 Reliability Burn-Down:** eliminate high-impact runtime reliability risks in scheduler/background-task/status flows and stabilize failure semantics.
3. **06-03 DB/Data-Path Optimization:** remove high-churn per-record DB patterns, add measurable profiling, and ship indexed/batched data paths.

This order reduces risk: first lock test authority, then fix defects with stronger safety nets, then optimize without losing regression confidence.

## Current Gap Evidence

### Test Ownership Drift
- CI runs `backend/tests` but root `tests/` still exists with Flask-era imports (`from app import create_app`, Flask fixtures) and no canonical role.
- Frontend test ownership is shallow (`4` test files) compared to operational page surface.
- No single script defines canonical cross-stack regression suite ownership.

### Reliability Defects / Fragile Paths
- `backend/main.py` defines an extra `/api/v1/background-tasks/status` route in addition to router-provided endpoint, creating duplicate-path ambiguity.
- `background_task_status_service.py` is an in-memory placeholder; not scheduler-backed or restart-safe.
- Periodic tasks and service flows contain broad catch-all exception patterns with uneven diagnostics and fallback behavior.

### DB/Data-Path Hotspots
- `channel_repository.py` bulk operations call per-record CRUD helpers, causing repeated commits/refreshes.
- `scraper_service.py` mixes repeated ORM lookups and per-record persistence updates in high-churn scrape paths.
- `epg_service.py` performs channel/program existence checks in nested loops, producing avoidable query amplification on large XML inputs.
- No committed performance baseline artifact exists for scrape/EPG/high-churn write paths.

## Recommended Implementation Pattern

### Pattern 1: Canonical Test Ownership Contract
- Define one root-owned regression entrypoint script (`scripts/ci/run_v2_test_suite.sh`) and ownership matrix doc.
- Port any remaining valuable legacy checks into `backend/tests`/`frontend/src/__tests__`.
- Mark/remove root `tests/` as non-authoritative once replacement coverage exists.

### Pattern 2: Reliability First on Operational Flows
- Remove duplicate route ownership and centralize background status API behavior.
- Make scheduler lifecycle idempotent and observable.
- Add targeted regression tests for task scheduling/status and core error paths.

### Pattern 3: Measure-Then-Optimize DB Paths
- Add lightweight profiling harness for query counts/duration in high-churn flows.
- Replace per-record loops with set-based/batched operations where safe.
- Add indexes and migration coverage where query plans show repeated scan hotspots.

## Common Pitfalls

1. **Deleting legacy tests before replacement coverage lands**
   - Mitigation: explicit ownership matrix + replacement tests before retirement.
2. **Optimizing without baseline measurements**
   - Mitigation: record baseline and post-change metrics in committed artifacts.
3. **Changing scrape/EPG internals without parity checks**
   - Mitigation: keep parity/contract tests in required regression suite during optimization.
4. **Reliability fixes that only improve logs but not behavior**
   - Mitigation: require regression tests proving deterministic failure handling.

## Verification Strategy for Planning

- Every requirement ID (`API-04`, `QUAL-01`, `QUAL-02`, `QUAL-03`) must appear in plan frontmatter.
- Plans must define executable verification commands (not narrative-only).
- Plan sequence should enforce: ownership -> defects -> optimization.
- Must-haves should include artifact + link-level checks for execution and phase verification.

## Sources

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/codebase/TESTING.md`
- `.planning/codebase/CONCERNS.md`
- `backend/main.py`
- `backend/app/services/background_task_status_service.py`
- `backend/app/services/task_service.py`
- `backend/app/services/scraper_service.py`
- `backend/app/services/epg_service.py`
- `backend/app/repositories/channel_repository.py`
- `backend/app/repositories/url_repository.py`
- `backend/tests/`
- `tests/`
- `frontend/src/__tests__/`
- `.github/workflows/pull_request.yml`
- `scripts/ci/run_cutover_required_checks.sh`

## Metadata

**Confidence breakdown:**
- Test ownership strategy: HIGH
- Reliability burn-down direction: HIGH
- DB optimization direction: MEDIUM-HIGH (exact gains depend on dataset shape)

**Research date:** 2026-02-27  
**Valid until:** 2026-03-31
