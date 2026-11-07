# Phase 6 DB Benchmarks

## Scope

This benchmark report tracks high-churn DB paths targeted in phase 6:

- channel bulk activation/update flows
- URL refresh state updates
- repeat EPG XML processing on existing datasets

## Harness

- Script: `scripts/perf/profile_phase6_db_paths.py`
- Output format: JSON (`duration_ms`, `query_count`, row/result counters)
- Command:

```bash
python3 scripts/perf/profile_phase6_db_paths.py --scenario baseline --json-output phase6-db-baseline.json
```

## Baseline (Captured in this branch)

Run artifact: `phase6-db-baseline.json`

| Path | Query Count | Duration (ms) | Notes |
|------|-------------|---------------|-------|
| `bulk_activate_channels` | `2` | `4.09` | Set-based update + single readback |
| `refresh_all_urls` | `1` | `1.17` | Single set-based update |
| `process_epg_xml_repeat` | `4` | `13.64` | Repeat run avoids per-program existence N+1 queries |

## Acceptance Targets

- `bulk_activate_channels` query budget: `<= 3`
- `refresh_all_urls` query budget: `<= 2`
- repeat `process_epg_xml` query budget: `<= 5`

These targets are enforced in `backend/tests/perf/test_high_churn_db_paths.py`.

## Migration Safety Notes

- Indexes are added in `backend/migrations/versions/phase6_add_hotpath_indexes.py`.
- Migration uses idempotent index creation checks to preserve compatibility with existing user databases.
- No table/column drops are introduced in phase 6 optimization migration.
