# Migration Gaps Status Reference

## Status Snapshot

- Phase 3 cutover is achieved.
- Chunk 1 and Chunk 2 backend migration/runtime parity repair work is complete for the scoped goals covered by the current migration-tail execution.
- Chunk 3 frontend/admin parity work is complete through the current execution state.
- Remaining work is now mainly documentation reconciliation, release-path/release-evidence cleanup, the optional stale-import/module-reload backend-suite follow-up, and later execution-plan cleanup rather than broad backend/frontend migration parity work.

## Backend Schema And Runtime Status

- The backend should no longer be treated as broadly incomplete for the migration-tail scope.
- Recent migration-tail repair work closed the active schema/runtime parity items that had remained open for this scope, including the Alembic-forward repair path needed to align runtime expectations with the migrated schema.
- Old Alembic/model drift notes from earlier migration snapshots are archival only and should not be carried forward as active open gaps unless new evidence reopens them.
- Canonical required regression ownership is now:
  - `backend/tests/`
  - `frontend/src/__tests__/`
  - `scripts/ci/run_v2_test_suite.sh`
- Root `tests/` is legacy reference only and is not authoritative for required regression coverage.
- Current Phase 6 DB benchmark and query-budget status is recorded in `docs/performance/phase6-db-benchmarks.md` and enforced by `backend/tests/perf/test_high_churn_db_paths.py`.
- The legacy env alias bridge remains transitional and must stay documented that way until the final retirement pass is complete.

## Frontend Status

- Chunk 3 frontend/admin parity work is complete through the current execution state recorded in the migration-tail execution plan.
- Settings, Health, Stats, Search, and EPG mappings should not be treated as major missing migration gaps in this repository state.
- No major frontend/admin parity gaps remain open for this migration-tail scope.
- Any broader future UI modernization work belongs to later planned phases and is not evidence that the V1-to-V2 migration tail is still missing these core surfaces.

## Remaining Migration And Release Cleanup

- Documentation reconciliation is still in progress so status and release docs fully match the recorded post-cutover state.
- Jenkins-first release-path reconciliation remains pending in later Chunk 4 tasks.
- Remaining release evidence cleanup is still tracked in the main execution plan.
- The optional full backend suite still has a separate stale-import/module-reload follow-up outside the scoped Chunk 1 and Chunk 2 migration/runtime repairs.
- The legacy env alias bridge still needs final retirement in a later cleanup pass, but it is intentionally transitional for now.
- Later execution-plan cleanup is still pending; this document is a current-status reference, not the execution log source of truth.

## Archival Context

- Earlier versions of this file mixed historical implementation plans, stale percentage tracking, and pre-repair schema/frontend gap lists.
- That older material is now collapsed into this short non-authoritative archival context so resumed executors do not mistake closed migration items for current open work.
