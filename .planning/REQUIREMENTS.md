# Requirements: Acestream Scraper v2 Consolidation

**Defined:** 2026-02-27
**Core Value:** Ship a fully v2-based Acestream Scraper that keeps scraper reliability intact while materially improving architecture quality, UI quality, stability, and platform compatibility.

## v1 Requirements

### Migration and Cutover

- [ ] **MIGR-01**: Production runtime uses v2 stack only (`v2/backend` + `v2/frontend`) with no dependency on legacy root app runtime.
- [ ] **MIGR-02**: Root legacy deployment/build workflow paths are retired or redirected to v2 equivalents.
- [x] **MIGR-03**: Functional parity checklist confirms all core user-facing capabilities currently used in root stack are available in v2.
- [ ] **MIGR-04**: Big-bang cutover can be executed from a single release branch without dual-stack runtime overlap.

### Scraping and Data Integrity

- [x] **SCRP-01**: Existing HTTP/M3U scraping behavior is preserved in v2 for currently working sources.
- [x] **SCRP-02**: Existing ZeroNet scraping behavior is preserved in v2 for currently working sources.
- [x] **SCRP-03**: Scrape runs persist channels and metadata without regression in core fields (`id`, `name`, `group`, `logo`, `tvg_id`, `tvg_name`, source linkage).
- [x] **SCRP-04**: Playlist and EPG generation workflows produce valid outputs for representative datasets.

### Backend Architecture and API

- [x] **API-01**: v2 API contracts are explicit, typed, and internally consistent (no ambiguous payload shapes across endpoint/service layers).
- [x] **API-02**: Backend modules are reorganized to enforce clear boundaries (endpoint -> service -> repository/model responsibilities).
- [ ] **API-03**: Core backend paths include robust error handling/logging for operational failures (scrape, EPG refresh, status checks, tasks).
- [ ] **API-04**: Database access patterns for high-churn operations are optimized to reduce unnecessary per-record overhead.

### Frontend UX and Usability

- [ ] **UI-01**: v2 frontend delivers improved visual design quality and clearer information hierarchy on core operational pages.
- [ ] **UI-02**: Core workflows (channels, scraping URLs, EPG, config, status) are faster to complete and require fewer friction points than current state.
- [ ] **UI-03**: Frontend is responsive and usable across desktop and constrained display contexts.
- [ ] **UI-04**: Frontend integrates cleanly with stabilized v2 API contracts without ad-hoc runtime shape workarounds.

### Compatibility and Deployment

- [ ] **COMP-01**: Build pipeline can produce multi-arch images including `linux/arm/v7` and `linux/arm64`.
- [ ] **COMP-02**: Runtime smoke checks validate core service startup and key workflows on supported architectures.
- [ ] **COMP-03**: Release documentation reflects v2-only deployment and architecture support expectations.

### Reliability and Quality

- [ ] **QUAL-01**: Regression test coverage for critical flows is rebuilt/owned under v2 test locations (`v2/backend/tests`, `v2/frontend/src/__tests__`).
- [ ] **QUAL-02**: Legacy root tests are retained only as temporary parity references, then removed once v2 coverage is sufficient.
- [ ] **QUAL-03**: Known high-impact bugs in current v2 paths are fixed before cutover.
- [x] **QUAL-04**: Phase acceptance gates require measurable verification before marking migration complete.

## v2 Requirements

### Post-Cutover Enhancements

- **NEXT-01**: Introduce dedicated worker architecture for long-running scrape/EPG jobs if load requires it.
- **NEXT-02**: Add deeper Android TV remote-navigation UX optimizations beyond baseline responsive compatibility.
- **NEXT-03**: Introduce richer performance telemetry dashboards for ongoing capacity planning.
- **NEXT-04**: Evaluate API authentication/authorization model for broader or less-trusted deployment scenarios.

## Out of Scope

Explicitly excluded from this migration milestone.

| Feature | Reason |
|---------|--------|
| Legacy API backward compatibility guarantees | v2 is intentionally allowed to break compatibility for structural cleanup |
| Legacy UI route/component parity | UX improvements may require different flows and layouts |
| Permanent dual maintenance of root + v2 stacks | Contradicts single-source v2 ownership goal |
| Full architectural rewrite of scraper internals | Scraper behavior is a protected baseline during migration |

## Traceability

Which phases cover which requirements.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MIGR-01 | Phase 3 | Pending |
| MIGR-02 | Phase 3 | Pending |
| MIGR-03 | Phase 2 | Complete |
| MIGR-04 | Phase 3 | Pending |
| SCRP-01 | Phase 1 | Complete |
| SCRP-02 | Phase 1 | Complete |
| SCRP-03 | Phase 1 | Complete |
| SCRP-04 | Phase 1 | Complete |
| API-01 | Phase 2 | Complete |
| API-02 | Phase 2 | Complete |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 6 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-02 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| UI-04 | Phase 4 | Pending |
| COMP-01 | Phase 5 | Pending |
| COMP-02 | Phase 5 | Pending |
| COMP-03 | Phase 3 | Pending |
| QUAL-01 | Phase 6 | Pending |
| QUAL-02 | Phase 6 | Pending |
| QUAL-03 | Phase 6 | Pending |
| QUAL-04 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-27*
*Last updated: 2026-02-27 after roadmap mapping*
