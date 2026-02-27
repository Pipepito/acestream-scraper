---
phase: 01-parity-baseline-and-safety-gates
plan: "01"
subsystem: testing
tags: [parity, scraper, playlist, epg, regression]
requires: []
provides:
  - "Baseline parity manifest with source classes and environment tags"
  - "Golden snapshots for scraper and output parity contracts"
  - "Field-level strict/fuzzy comparator utilities"
  - "Automated scraper + playlist/EPG parity regression tests"
affects: [phase-01-02, phase-02, phase-03, migration-gates]
tech-stack:
  added: []
  patterns:
    - "Manifest -> snapshot -> comparator -> gate scoring"
    - "Blocking vs non-blocking source class separation"
key-files:
  created:
    - v2/backend/tests/parity/baseline_sources.yaml
    - v2/backend/tests/parity/parity_manifest.py
    - v2/backend/tests/parity/parity_compare.py
    - v2/backend/tests/parity/test_scraper_parity.py
    - v2/backend/tests/parity/test_output_parity.py
  modified:
    - v2/backend/app/services/playlist_service.py
key-decisions:
  - "Stored baseline and snapshots as JSON-compatible YAML/JSON to avoid adding new parser dependencies."
  - "Made active/critical parity failures blocking while legacy/auth-region classes remain visible but non-blocking by default."
  - "Added deterministic output-parity fixtures to keep playlist/EPG checks stable in CI."
patterns-established:
  - "Phase gates consume reusable parity utilities instead of embedding parity logic in individual tests."
  - "Parity tests report strict field regressions separately from fuzzy metadata drift."
requirements-completed: [SCRP-01, SCRP-02, SCRP-03, SCRP-04]
duration: 52min
completed: 2026-02-27
---

# Phase 01 Plan 01: Parity Baseline and Safety Gates Summary

**Shipped a reusable parity harness with baseline governance, scraper snapshots, and output validity checks that catch regressions before migration changes advance.**

## Performance

- **Duration:** 52 min
- **Started:** 2026-02-27T14:33:00Z
- **Completed:** 2026-02-27T15:25:00Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Created a change-controlled baseline manifest with source class policy and environment tags.
- Added parity comparison utilities supporting strict identity checks plus fuzzy metadata tolerance.
- Added scraper parity and output validity tests covering HTTP/M3U, ZeroNet, playlist, and EPG behaviors.
- Fixed an existing playlist bug surfaced by verification (`base_url` requests no longer crash).

## Task Commits

Each task was committed atomically:

1. **Task 1: Create governed baseline source manifest and snapshot contract** - `ee4d350` (feat)
2. **Task 2: Implement parity comparator utilities for strict and fuzzy field checks** - `747d0e2` (feat)
3. **Task 3: Add automated parity regression tests for scraping, playlist, and EPG outputs** - `9e83650` (test)

**Auto-fixed deviation:** `c40be0f` (fix)

## Files Created/Modified

- `v2/backend/tests/parity/baseline_sources.yaml` - Source inventory and parity policy contract.
- `v2/backend/tests/parity/snapshots/scraper_channels_snapshot.json` - Golden scraper baseline snapshots.
- `v2/backend/tests/parity/snapshots/output_validity_snapshot.json` - Golden playlist/EPG validity assertions.
- `v2/backend/tests/parity/parity_manifest.py` - Manifest loading and validation helpers.
- `v2/backend/tests/parity/parity_compare.py` - Strict/fuzzy parity and gate scoring utilities.
- `v2/backend/tests/parity/test_scraper_parity.py` - Scraper parity regression suite.
- `v2/backend/tests/parity/test_output_parity.py` - Playlist/EPG parity validity suite.
- `v2/backend/app/services/playlist_service.py` - Fixed runtime bug for custom `base_url` handling.

## Decisions Made

- Kept manifest/snapshot parsing dependency-light by using JSON-compatible data files.
- Treated `gate_critical` sources as blocking and separated non-blocking failures by source class.
- Structured output parity tests around deterministic seeded data to avoid flaky snapshot drift.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Playlist endpoint 500 when base_url is provided**
- **Found during:** Plan verification suite (`test_get_m3u_playlist_with_custom_base_url`)
- **Issue:** `settings_repo` was only initialized in one code path, causing `UnboundLocalError` on custom `base_url` requests.
- **Fix:** Initialized `SettingsRepository` before conditional base URL resolution.
- **Files modified:** `v2/backend/app/services/playlist_service.py`
- **Verification:** `v2/backend/venv/bin/python -m pytest -q v2/backend/tests/test_playlists.py::TestPlaylistEndpoints::test_get_m3u_playlist_with_custom_base_url`
- **Committed in:** `c40be0f`

---

**Total deviations:** 1 auto-fixed (1 bug)  
**Impact on plan:** Improved stability while preserving planned parity scope.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 baseline parity harness is ready for gate orchestration in Plan `01-02`.
- Next plan can consume parity tests directly via quick/full gate profiles.

## Self-Check: PASSED

- Parity suites pass:
  - `v2/backend/venv/bin/python -m pytest -q v2/backend/tests/parity/test_scraper_parity.py`
  - `v2/backend/venv/bin/python -m pytest -q v2/backend/tests/parity/test_output_parity.py`
- Existing smoke suites pass:
  - `v2/backend/venv/bin/python -m pytest -q v2/backend/tests/test_scrapers.py v2/backend/tests/test_playlists.py v2/backend/tests/test_epg.py`

---
*Phase: 01-parity-baseline-and-safety-gates*  
*Completed: 2026-02-27*
