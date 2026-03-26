# Project Research Summary

**Project:** Acestream Scraper v2 Consolidation
**Domain:** Brownfield migration to a single v2 scraper-management platform
**Researched:** 2026-02-27
**Confidence:** HIGH

## Executive Summary

The project should be executed as a strict consolidation effort: retire legacy root ownership and make `backend` + `frontend` the only production path. The highest-priority invariant is scraper behavior reliability; architecture and UI can change significantly as long as core scraping outputs and capabilities remain intact.

Research indicates the most effective sequence is: establish parity and contracts first, then perform structural cutover, then modernize UX and optimize performance. Attempting to redesign architecture/UI and parser internals simultaneously is the most likely way to increase regressions.

The largest risks are dual-stack drift, unverified multi-arch assumptions, and quality claims without hard gates. These are addressable with explicit phase acceptance criteria and v2-only CI/runtime ownership.

## Key Findings

### Recommended Stack

The existing FastAPI + SQLAlchemy + React TypeScript base in `v2` is the right target and should be hardened rather than replaced. Multi-arch delivery should rely on Docker Buildx and explicit runtime verification for `linux/arm/v7` and `linux/arm64`.

**Core technologies:**
- Python + FastAPI + SQLAlchemy/Alembic: typed backend contracts and maintainable data layer
- React + TypeScript: frontend reliability and safer refactoring
- Docker Buildx: deterministic multi-arch release pipeline

### Expected Features

**Must have (table stakes):**
- Scraper parity for existing sources and metadata behaviors
- Channel/URL/playlist/EPG/config/status workflows preserved
- Stable Dockerized deployment and operational observability

**Should have (competitive):**
- Cleaner and faster UI with responsive, operationally efficient flows
- Strong architecture cleanup and lower regression surface
- Better ARM deployment compatibility for Android TV-class targets

**Defer (v2+):**
- Heavy async worker architecture and deeper long-term scaling redesign

### Architecture Approach

Use a strict layered approach: FastAPI endpoints -> domain services -> repositories/models, with typed API contracts consumed by frontend hooks/services. Keep scraper parsing behavior stable while refactoring surrounding orchestration and contracts.

**Major components:**
1. API contracts and endpoint boundaries
2. Domain services + scraper orchestration
3. Repository/persistence layer + frontend typed integration

### Critical Pitfalls

1. **Scraper behavior regression during refactor** — freeze parser behavior and enforce parity tests
2. **Dual-stack cutover drift** — retire root paths decisively and consolidate CI/release
3. **UI redesign before contract stabilization** — stabilize typed API contracts first
4. **Multi-arch false confidence** — validate runtime behavior on target architectures
5. **“Bug-free” claims without gates** — enforce measurable acceptance criteria each phase

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Baseline and Parity Guardrails
**Rationale:** Protect core value first.
**Delivers:** Scraper parity baseline, regression harness, migration acceptance gates.
**Addresses:** Core reliability requirement.
**Avoids:** Parser regressions and undefined quality bar.

### Phase 2: Core v2 Contract Stabilization
**Rationale:** UI/backend work depends on stable contracts.
**Delivers:** Stable backend schemas/endpoints and frontend client alignment.
**Uses:** FastAPI/Pydantic/TS contract-first approach.
**Implements:** API-service-repository boundaries.

### Phase 3: Legacy Root Retirement and v2-Only Cutover
**Rationale:** Remove dual ownership before broad improvements.
**Delivers:** Unified build/release/runtime path in v2; root legacy stack retired.

### Phase 4: UI/UX Modernization
**Rationale:** Improve operator experience once contracts are stable.
**Delivers:** Responsive and clearer UX across core workflows.

### Phase 5: Multi-Arch Packaging and Compatibility Validation
**Rationale:** Build and runtime compatibility must be proven.
**Delivers:** `linux/arm/v7` + `linux/arm64` support with validation checklist.

### Phase 6: Performance and Reliability Optimization
**Rationale:** Optimize after structure and compatibility are locked.
**Delivers:** DB efficiency gains, task reliability improvements, defect reduction.

### Phase Ordering Rationale

- Contract stability and cutover precede visual/performance optimization.
- Scraper parity and quality gates are foundational for every subsequent phase.
- ARM compatibility is treated as a deliverable phase, not a side effect.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5:** Architecture-specific runtime validation for ARM devices.
- **Phase 6:** Data-path profiling and targeted optimization choices.

Phases with standard patterns (skip deep research):
- **Phase 2-3:** Consolidation and cutover patterns are already well-documented in this repo.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | v2 implementation already exists and aligns with target |
| Features | HIGH | User-specified goals map clearly to current capabilities + gaps |
| Architecture | HIGH | Existing codebase map and migration docs provide strong context |
| Pitfalls | HIGH | Risks are directly visible in current dual-stack structure |

**Overall confidence:** HIGH

### Gaps to Address

- Explicit ARM v7 runtime test matrix needs implementation details.
- Final UI quality bar and definition of “improved styling” should be captured as measurable UAT criteria per phase.

## Sources

### Primary (HIGH confidence)
- `.planning/codebase/*.md` — current codebase state and concerns
- `docs/migration/development-progress.md` — migration implementation history
- `docs/migration/migration-strategy.md` and `development-phases.md` — intended migration direction

### Secondary (MEDIUM confidence)
- Existing `backend/tests` and `frontend/src/__tests__` patterns for validation strategy

### Tertiary (LOW confidence)
- Broader Android TV runtime assumptions beyond explicit repository evidence

---
*Research completed: 2026-02-27*
*Ready for roadmap: yes*
