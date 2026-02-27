# Acestream Scraper v2 Consolidation

## What This Is

This project replaces the legacy root application with a consolidated v2 platform (`v2/backend` + `v2/frontend`) as the single source of truth. The new version can break API/UI compatibility with the old stack, but it must preserve the current working scraping behavior and all core product capabilities. The goal is a cleaner architecture, better UI/UX, stronger reliability, and broader runtime compatibility (including ARM targets used by Android TV-class devices).

## Core Value

Ship a fully v2-based Acestream Scraper that keeps scraper reliability intact while materially improving architecture quality, UI quality, stability, and platform compatibility.

## Requirements

### Validated

- ✓ Scraping service can extract channels from regular HTTP/M3U and ZeroNet sources and persist results — existing
- ✓ Channel, URL, TV channel, playlist, EPG, search, and status workflows exist in v2 backend/frontend — existing
- ✓ System integrations for Acestream status and WARP controls are implemented in v2 — existing
- ✓ Dockerized runtime and CI/CD patterns exist (currently split across legacy root and v2 paths) — existing

### Active

- [ ] Fully replace legacy root runtime, workflows, and docs with a v2-only production path
- [ ] Preserve scraper service logic/behavior parity while refactoring surrounding architecture
- [ ] Reorganize backend structure for maintainability, reliability, and lower bug surface
- [ ] Refactor and modernize frontend UX (navigation clarity, responsiveness, visual quality, and usability)
- [ ] Improve backend performance and DB efficiency for scraping, EPG, and high-churn operations
- [ ] Reduce defects to near-zero with stronger testing, validation, and cleanup of polluted modules
- [ ] Deliver multi-architecture container support for `linux/arm/v7` and `linux/arm64` (plus compatible Android TV-class deployments)
- [ ] Keep all current functional capabilities while fixing known issues and regressions during migration

### Out of Scope

- Backward API compatibility with legacy root endpoints — v2 is allowed to define a new API contract
- Frontend route/component parity with legacy UI — v2 can ship improved UX and changed flows
- Long-term maintenance of duplicate root and v2 stacks — objective is single-stack v2 ownership

## Context

The repository currently contains both a legacy root stack and a v2 implementation, with migration artifacts in `docs/migration/` documenting prior rewrite work. The scraping logic is considered stable and valuable, while surrounding architecture/UI quality has degraded due to mixed paths and accumulated technical debt. This initiative is intentionally big-bang because delivery occurs on a separate branch before merge, avoiding partial production exposure.

## Constraints

- **Migration Strategy**: Big-bang cutover — users remain on current version until PR merge
- **Compatibility**: API/UI backward compatibility is not required in v2
- **Scraper Integrity**: Scraping logic should remain behaviorally equivalent unless a fix is required
- **Platform**: Must support ARM v7 and ARM64 container builds; prioritize Android TV-class deployment compatibility
- **Scope Discipline**: Root legacy stack should be retired/replaced rather than co-maintained

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Make v2 the only application stack | Current dual-stack layout creates drift and maintenance overhead | — Pending |
| Allow API and frontend breaking changes | Faster cleanup and better architecture than preserving legacy contracts | — Pending |
| Use big-bang cutover on branch | Safe migration without impacting current users pre-merge | — Pending |
| Preserve core scraper logic behavior | Existing scraping behavior is stable and business-critical | — Pending |
| Target ARM v7 and ARM64 artifacts | Required for broader device support including Android TV-class environments | — Pending |

---
*Last updated: 2026-02-27 after initialization*
