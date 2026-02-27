# Roadmap: Acestream Scraper v2 Consolidation

## Overview

This roadmap delivers a big-bang migration from the legacy root stack to a single v2 architecture while protecting scraper reliability, modernizing UX, and shipping validated ARM compatibility. The sequence intentionally establishes parity and contract stability before cutover and optimization work, reducing regression risk during replacement.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Parity Baseline and Safety Gates** - Lock scraper/output parity and migration acceptance checks.
- [ ] **Phase 2: Backend Contract and Structure Hardening** - Stabilize v2 backend contracts and architecture boundaries.
- [ ] **Phase 3: v2-Only Cutover and Legacy Retirement** - Replace root runtime/build ownership with v2-only paths.
- [ ] **Phase 4: Frontend UX Modernization** - Improve usability, responsiveness, and operational flow clarity.
- [ ] **Phase 5: Multi-Arch Build and Runtime Validation** - Ship and validate ARM v7/ARM64 compatibility.
- [ ] **Phase 6: Reliability, Test Ownership, and Optimization** - Drive bugs down and harden performance/reliability.

## Phase Details

### Phase 1: Parity Baseline and Safety Gates
**Goal**: Preserve working scraper and output behavior while creating objective quality gates for migration.
**Depends on**: Nothing (first phase)
**Requirements**: [SCRP-01, SCRP-02, SCRP-03, SCRP-04, QUAL-04]
**Success Criteria** (what must be TRUE):
  1. Scraping from representative HTTP/M3U and ZeroNet sources matches expected baseline behavior.
  2. Playlist and EPG outputs validate successfully on representative data.
  3. Cutover acceptance checks exist and are executable before each transition.
**Plans**: 2 plans

Plans:
- [ ] 01-01: Define parity baseline datasets and regression checks for scraping + output artifacts.
- [ ] 01-02: Implement migration safety gates and verification checklist used by all later phases.

### Phase 2: Backend Contract and Structure Hardening
**Goal**: Make v2 backend contracts explicit and reduce architecture pollution.
**Depends on**: Phase 1
**Requirements**: [API-01, API-02, API-03, MIGR-03]
**Success Criteria** (what must be TRUE):
  1. v2 API payloads are consistent and typed across endpoint/service/frontend boundaries.
  2. Endpoint -> service -> repository boundaries are clear and enforced in core modules.
  3. Operational failure paths return actionable errors with structured logging.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Normalize API contracts/schemas and remove shape ambiguities.
- [ ] 02-02: Refactor backend module boundaries for maintainability and lower coupling.
- [ ] 02-03: Harden error handling/logging for scrape, EPG, status, and task flows.

### Phase 3: v2-Only Cutover and Legacy Retirement
**Goal**: Complete root-to-v2 replacement for runtime, build, and release ownership.
**Depends on**: Phase 2
**Requirements**: [MIGR-01, MIGR-02, MIGR-04, COMP-03]
**Success Criteria** (what must be TRUE):
  1. Production deployment path runs only on v2 runtime components.
  2. Legacy root build/release/runtime references are removed or redirected to v2 equivalents.
  3. Release docs and cutover steps reflect the new v2-only operating model.
**Plans**: 3 plans

Plans:
- [ ] 03-01: Consolidate CI/build/release workflow to v2-only ownership.
- [ ] 03-02: Retire legacy root runtime/deployment paths and reconcile docs.
- [ ] 03-03: Execute and verify big-bang cutover checklist on branch.

### Phase 4: Frontend UX Modernization
**Goal**: Deliver materially better operator UX while keeping core functionality intact.
**Depends on**: Phase 3
**Requirements**: [UI-01, UI-02, UI-03, UI-04]
**Success Criteria** (what must be TRUE):
  1. Core workflows (channels, URLs, EPG, config/status) are easier and faster to complete.
  2. UI information hierarchy and navigation are clearer than current state.
  3. Frontend behaves responsively on desktop and constrained display contexts.
**Plans**: 3 plans

Plans:
- [ ] 04-01: Redesign layout/navigation primitives for clarity and operational speed.
- [ ] 04-02: Rework core management pages and interactions around stabilized contracts.
- [ ] 04-03: Apply responsive and accessibility/usability polishing across primary flows.

### Phase 5: Multi-Arch Build and Runtime Validation
**Goal**: Provide dependable support for ARM v7 and ARM64 deployment targets.
**Depends on**: Phase 3
**Requirements**: [COMP-01, COMP-02]
**Success Criteria** (what must be TRUE):
  1. CI/build process reliably produces `linux/arm/v7` and `linux/arm64` artifacts.
  2. Runtime smoke checks pass on supported architectures for core workflows.
  3. Architecture-specific caveats are documented for deployment operators.
**Plans**: 2 plans

Plans:
- [ ] 05-01: Implement/verify multi-arch build pipeline and artifact publishing.
- [ ] 05-02: Create architecture smoke-test checklist and validate runtime behavior.

### Phase 6: Reliability, Test Ownership, and Optimization
**Goal**: Reduce bugs and improve DB/runtime efficiency under the new v2-only architecture.
**Depends on**: Phases 4 and 5
**Requirements**: [API-04, QUAL-01, QUAL-02, QUAL-03]
**Success Criteria** (what must be TRUE):
  1. Critical flow tests are owned in v2 test locations and pass consistently.
  2. High-impact defects are resolved and regression risk is reduced with repeatable checks.
  3. DB/data-path performance improvements are measurable in key operations.
**Plans**: 3 plans

Plans:
- [ ] 06-01: Rebuild/expand v2 test ownership and retire redundant legacy test dependencies.
- [ ] 06-02: Run focused defect burn-down and stability hardening for critical flows.
- [ ] 06-03: Optimize database and high-churn processing paths with measurable gains.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Parity Baseline and Safety Gates | 0/2 | Not started | - |
| 2. Backend Contract and Structure Hardening | 0/3 | Not started | - |
| 3. v2-Only Cutover and Legacy Retirement | 0/3 | Not started | - |
| 4. Frontend UX Modernization | 0/3 | Not started | - |
| 5. Multi-Arch Build and Runtime Validation | 0/2 | Not started | - |
| 6. Reliability, Test Ownership, and Optimization | 0/3 | Not started | - |
