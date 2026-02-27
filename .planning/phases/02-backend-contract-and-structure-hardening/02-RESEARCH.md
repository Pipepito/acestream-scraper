# Phase 2: Backend Contract and Structure Hardening - Research

**Researched:** 2026-02-27  
**Domain:** FastAPI contract normalization, backend boundary hardening, and operational error handling  
**Confidence:** HIGH

<user_constraints>
## User Constraints (derived from PROJECT.md and active migration decisions)

### Locked Decisions

### v2-Only Direction
- Root application in repository root will be replaced by the v2 stack as the single runtime path.
- API/UI backward compatibility with legacy root is not required in v2.
- Big-bang cutover is accepted on a branch before merge.

### Scraper Integrity
- Scraping service behavior is protected and must remain functionally equivalent unless a fix is needed.
- Surrounding architecture can be refactored aggressively as long as scraping outcomes stay stable.

### Architecture and Quality Priority
- Backend contracts must become explicit and consistent.
- Architecture pollution should be reduced with clear endpoint -> service -> repository boundaries.
- Reliability/stability/bug reduction and DB efficiency are prioritized over preserving legacy patterns.

### Platform Context (affects scope sequencing)
- ARM `linux/arm/v7` and `linux/arm64` compatibility is required, but Phase 2 focus remains backend correctness and structure.

### Claude's Discretion
- Exact schema naming and error envelope shape.
- Boundary implementation details (dependency injection modules, repository composition, service facades).
- Verification granularity for contract vs regression tests.

### Deferred Ideas
- Multi-arch build pipeline implementation (planned in later compatibility phase).
- Full frontend UX redesign (planned in Phase 4).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | v2 API contracts are explicit, typed, and internally consistent | Standardized request/response schemas + contract tests + frontend service typing alignment |
| API-02 | Endpoint -> service -> repository boundaries are clear and enforced | Repository-first data access, endpoint dependency providers, architecture guard checks |
| API-03 | Core operational paths have robust error handling/logging | Shared error envelope, typed domain exceptions, structured logging in scrape/EPG/status/tasks |
| MIGR-03 | Core user-facing capabilities from root remain available in v2 | Functional parity-preserving refactor strategy with targeted regression tests on existing endpoints |
</phase_requirements>

## Summary

Phase 2 should harden backend quality without changing the product surface area. Current v2 behavior mostly works, but contract ambiguity and boundary leakage increase defect risk during migration. The optimal strategy is to establish explicit DTO contracts first, then enforce architectural boundaries, then standardize error/logging behavior.

The highest-value wins in this phase are:
1. Remove untyped payload shapes (`dict`, `Dict[str, Any]`, raw `request.json()`) at API boundaries.
2. Stop endpoint/service direct DB leakage and route persistence through repositories consistently.
3. Make operational failures observable and actionable with consistent error envelopes and structured logs.

## Current Gap Evidence

### Contract Ambiguity
- `v2/backend/app/api/endpoints/tv_channels.py` uses `response_model=Dict[str, Any]` for list responses and multiple `dict` request bodies (`association`, `assignment_data`, `update_data`).
- `v2/backend/app/api/endpoints/channels.py` uses `Dict[str, Any]` for bulk operations (`bulk_edit`, `bulk_activate`).
- `v2/backend/app/api/endpoints/epg.py` string mapping routes accept raw `dict` payloads.
- `v2/backend/app/api/endpoints/config.py` mixes typed payloads and raw `request.json()` parsing.
- `v2/frontend/src/services/channelService.ts` assumes list-return contract while backend returns paginated `{items,total}` for channels.

### Boundary Pollution
- `v2/backend/app/services/url_service.py` performs direct ORM queries even though `URLRepository` exists.
- `v2/backend/app/api/endpoints/urls.py` invokes `URLService` that bypasses repository abstractions.
- `v2/backend/app/api/endpoints/config.py` duplicates dependency provider logic (`get_config_service` defined twice).
- Mixed direct DB usage and layered access patterns increase maintenance overhead and coupling.

### Error/Logging Gaps
- Scrape and refresh paths often catch broad exceptions and return ad-hoc status strings.
- Background tasks (`v2/backend/app/tasks/url_scraping_task.py`, `epg_refresh_task.py`) log failures but do not produce unified failure metadata.
- No unified API error response schema across scrape/EPG/status/task-related routes.

## Recommended Implementation Pattern

### Pattern 1: Contract-First API Hardening
- Create explicit request/response schemas for all currently untyped bodies and envelopes.
- Standardize paginated responses and operation result payloads across channels, TV channels, and config.
- Update frontend service types to consume stable typed envelopes.

### Pattern 2: Boundary Enforcement by Construction
- Enforce endpoint rules: validate/translate HTTP only, no direct data access.
- Enforce service rules: orchestration and domain logic only.
- Enforce repository rules: persistence/query operations only.
- Add lightweight architecture checks to prevent regressions (static or test-based).

### Pattern 3: Unified Failure Contract
- Introduce canonical error schema (`code`, `message`, `context`, `correlation_id`).
- Map domain/integration exceptions to deterministic HTTP responses.
- Log failures with structured fields in scrape/EPG/status/task flows.

## Don’t Hand-Roll

| Problem | Avoid | Use Instead | Why |
|---------|-------|-------------|-----|
| Arbitrary dict payloads | Ad-hoc per-endpoint body parsing | Pydantic request/response DTOs | Keeps contracts explicit and testable |
| Service/endpoint DB queries | Layer bypass for convenience | Repository-backed service methods | Reduces coupling and hidden side effects |
| One-off error JSON formats | Endpoint-specific failure shapes | Shared error envelope + handlers | Improves operability and frontend predictability |

## Common Pitfalls

### Pitfall 1: Contract hardening that silently breaks frontend assumptions
- Mitigation: add backend contract tests and frontend type-level adapter tests in same phase.

### Pitfall 2: Boundary refactor that touches scraper logic
- Mitigation: preserve scraper core behavior and prove parity through existing and new targeted tests.

### Pitfall 3: Logging changes without actionable context
- Mitigation: require `source_id/url_id/channel_id/task_id` fields and correlation id in failure logs.

## Validation Strategy for Phase 2

1. Contract tests for channels/TV/config/EPG request and response shapes.
2. Boundary checks ensuring endpoint modules do not query ORM directly.
3. Failure-path tests for scrape, EPG refresh, status checks, and background tasks.
4. Regression suite run for existing core endpoints to satisfy MIGR-03 continuity.

## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/TESTING.md`
- `v2/backend/app/api/endpoints/channels.py`
- `v2/backend/app/api/endpoints/tv_channels.py`
- `v2/backend/app/api/endpoints/config.py`
- `v2/backend/app/api/endpoints/epg.py`
- `v2/backend/app/api/endpoints/scrapers.py`
- `v2/backend/app/api/endpoints/urls.py`
- `v2/backend/app/services/url_service.py`
- `v2/backend/app/services/scraper_service.py`
- `v2/backend/app/services/epg_service.py`
- `v2/backend/app/repositories/url_repository.py`
- `v2/frontend/src/services/channelService.ts`
- `v2/frontend/src/services/configService.ts`
- `v2/frontend/src/services/tvChannelService.ts`
- `v2/backend/tests/test_channels.py`
- `v2/backend/tests/test_tv_channels.py`
- `v2/backend/tests/test_config.py`
- `v2/backend/tests/test_scrapers.py`
- `v2/backend/tests/test_epg.py`

## Metadata

**Confidence breakdown:**
- Contract normalization path: HIGH
- Boundary hardening strategy: HIGH
- Error/logging standardization strategy: HIGH
- Migration parity alignment (MIGR-03): MEDIUM-HIGH (depends on disciplined regression execution during implementation)

**Research date:** 2026-02-27  
**Valid until:** 2026-03-30
