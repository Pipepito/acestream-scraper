---
phase: 02-backend-contract-and-structure-hardening
plan: "01"
subsystem: api
tags: [fastapi, pydantic, contracts, frontend-typing]
requires:
  - phase: 01-parity-baseline-and-safety-gates
    provides: parity safety baseline and regression expectations
provides:
  - Typed request/response contracts for channel, tv-channel, epg mapping, and config update flows
  - Contract regression tests for channels and config APIs
  - Frontend channel/config service typing alignment with backend payload shapes
affects: [phase-02-02-boundaries, phase-02-03-error-contract]
tech-stack:
  added: []
  patterns:
    - Contract-first endpoint DTOs
    - Explicit paginated response envelopes
key-files:
  created:
    - v2/backend/tests/contracts/test_channel_contracts.py
    - v2/backend/tests/contracts/test_config_contracts.py
  modified:
    - v2/backend/app/schemas/channel.py
    - v2/backend/app/schemas/config.py
    - v2/backend/app/schemas/epg.py
    - v2/backend/app/api/endpoints/channels.py
    - v2/backend/app/api/endpoints/config.py
    - v2/backend/app/api/endpoints/epg.py
    - v2/backend/app/api/endpoints/tv_channels.py
    - v2/backend/app/api/api.py
    - v2/frontend/src/services/channelService.ts
    - v2/frontend/src/services/configService.ts
    - v2/frontend/src/hooks/useChannels.ts
key-decisions:
  - "Retained `/channels` alias alongside `/acestream-channels` to preserve current parity-oriented test expectations while keeping v2 naming."
  - "Config mutation payloads were normalized to typed models while keeping compatibility aliases (`value`, `base_url`, `hours`)."
patterns-established:
  - "Use dedicated body DTOs for bulk and association endpoints instead of dict payloads."
  - "Keep paginated list contracts explicit through typed envelope schemas."
requirements-completed:
  - API-01
  - MIGR-03
duration: 47min
completed: 2026-02-27
---

# Phase 02 Plan 01: Normalize API Contracts and Schemas Summary

**Typed FastAPI contracts now enforce stable channel/config payload shapes, with frontend client typings and regression tests aligned to those contracts.**

## Performance

- **Duration:** 47 min
- **Started:** 2026-02-27T15:20:00Z
- **Completed:** 2026-02-27T16:07:00Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments
- Added explicit DTO schemas for bulk channel operations, TV-channel associations/batch updates, EPG mapping payloads, and config mutations.
- Refactored key endpoints to consume typed request models and explicit response models instead of ambiguous dict/request.json parsing.
- Added backend contract tests and aligned frontend channel/config service typings to backend envelopes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add typed schema DTOs** - `b42875f` (feat)
2. **Task 2: Normalize endpoint payload contracts** - `b7726eb` (refactor)
3. **Task 3: Add contract tests and frontend type alignment** - `549550c` (test)

## Files Created/Modified
- `v2/backend/app/schemas/channel.py` - Added bulk/association/paginated contract schemas.
- `v2/backend/app/schemas/config.py` - Added typed config mutation/update envelopes with compatibility helpers.
- `v2/backend/app/schemas/epg.py` - Added typed mapping update payload schema.
- `v2/backend/app/api/endpoints/config.py` - Replaced mixed parsing with typed body models and normalized mutation responses.
- `v2/backend/app/api/endpoints/channels.py` - Applied typed bulk operation models and fixed static route precedence for bulk endpoints.
- `v2/backend/app/api/endpoints/tv_channels.py` - Applied typed request/response models for list/association/batch/bulk-epg paths.
- `v2/backend/app/api/endpoints/epg.py` - Switched mapping routes from dict payloads to typed models.
- `v2/backend/app/api/api.py` - Added `/channels` compatibility alias for parity continuity.
- `v2/frontend/src/services/channelService.ts` - Updated paginated return type and removed `any` for bulk operations.
- `v2/frontend/src/services/configService.ts` - Normalized rescrape update payload shape.
- `v2/frontend/src/hooks/useChannels.ts` - Updated query type to paginated response.
- `v2/backend/tests/contracts/test_channel_contracts.py` - Added contract assertions for channel/TV-channel payloads.
- `v2/backend/tests/contracts/test_config_contracts.py` - Added contract assertions for config payload compatibility and response shape.

## Decisions Made
- Retained both `/api/v1/acestream-channels/*` and `/api/v1/channels/*` route prefixes for compatibility while contract-hardening proceeds.
- Kept config payload compatibility aliases instead of forcing immediate frontend-breaking mutation payload changes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed unreachable bulk channel endpoints due dynamic-route collision**
- **Found during:** Task 2
- **Issue:** `/channels/bulk_edit` resolved to `/{acestreamchannel_id}` `PUT` route and returned 404.
- **Fix:** Ensured static bulk routes are declared before dynamic `/{acestreamchannel_id}` handlers and verified behavior via new contract tests.
- **Files modified:** `v2/backend/app/api/endpoints/channels.py`
- **Verification:** `v2/backend/venv/bin/pytest -q v2/backend/tests/contracts/test_channel_contracts.py`
- **Committed in:** `b7726eb`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Positive; deviation removed an existing endpoint-resolution defect while preserving intended API behavior.

## Issues Encountered
- Local shell did not have `pytest` on PATH; all verification was run via `v2/backend/venv/bin/pytest`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Contract layer is now explicit for core channel/config flows, enabling cleaner service/repository boundary hardening in 02-02.
- Remaining risk area is architecture coupling in URL/scraper/stats paths, targeted next.

---
*Phase: 02-backend-contract-and-structure-hardening*  
*Completed: 2026-02-27*
