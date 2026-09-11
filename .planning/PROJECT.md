# Acestream Scraper v2 Consolidation

## What This Is

This project replaced the legacy root application with a consolidated platform (`backend` + `frontend`) as the single source of truth. The new version can break API/UI compatibility with the old stack, but it must preserve the current working scraping behavior and all core product capabilities. The goal is a cleaner architecture, better UI/UX, stronger reliability, and broader runtime compatibility (including ARM targets used by Android TV-class devices).

## Core Value

Ship a fully v2-based Acestream Scraper that keeps scraper reliability intact while materially improving architecture quality, UI quality, stability, and platform compatibility.

## Requirements

### Validated

- ✓ Scraping service can extract channels from regular HTTP/M3U and ZeroNet sources and persist results — existing
- ✓ Channel, URL, TV channel, playlist, EPG, search, and status workflows exist in canonical root backend/frontend paths — existing
- ✓ System integrations for Acestream status and WARP controls are implemented in the canonical stack — existing
- ✓ Dockerized runtime and CI/CD patterns exist in canonical root paths — existing

### Active

- [ ] Continue retiring remaining legacy-root references in favor of the canonical root production path
- [ ] Preserve scraper service logic/behavior parity while refactoring surrounding architecture
- [ ] Reorganize backend structure for maintainability, reliability, and lower bug surface
- [ ] Refactor and modernize frontend UX (navigation clarity, responsiveness, visual quality, and usability)
- [ ] Improve backend performance and DB efficiency for scraping, EPG, and high-churn operations
- [ ] Reduce defects to near-zero with stronger testing, validation, and cleanup of polluted modules
- [ ] Deliver multi-architecture container support for `linux/arm/v7` and `linux/arm64` (plus compatible Android TV-class deployments)
- [ ] Keep all current functional capabilities while fixing known issues and regressions during migration

### Out of Scope

- Backward API compatibility with legacy root endpoints — the consolidated stack is allowed to define a new API contract
- Frontend route/component parity with legacy UI — the consolidated stack can ship improved UX and changed flows
- Long-term maintenance of duplicate legacy and canonical stacks — objective is single-stack ownership

## Context

The repository now uses canonical root `backend/` and `frontend/` paths, while `docs/migration/` and `.planning/phases/` retain historical migration artifacts from the rewrite. The scraping logic is considered stable and valuable, while surrounding architecture/UI quality previously degraded due to mixed paths and accumulated technical debt. The migration strategy was intentionally big-bang to avoid partial production exposure during cutover.

## Constraints

- **Migration Strategy**: Big-bang cutover — users remain on current version until PR merge
- **Compatibility**: API/UI backward compatibility is not required in the consolidated stack
- **Scraper Integrity**: Scraping logic should remain behaviorally equivalent unless a fix is required
- **Platform**: Must support ARM v7 and ARM64 container builds; prioritize Android TV-class deployment compatibility
- **Scope Discipline**: Root legacy stack should be retired/replaced rather than co-maintained

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Make the canonical root stack the only application stack | Dual-stack layout created drift and maintenance overhead | Complete |
| Allow API and frontend breaking changes | Faster cleanup and better architecture than preserving legacy contracts | — Pending |
| Use big-bang cutover on branch | Safe migration without impacting current users pre-merge | — Pending |
| Preserve core scraper logic behavior | Existing scraping behavior is stable and business-critical | — Pending |
| Target ARM v7 and ARM64 artifacts | Required for broader device support including Android TV-class environments | — Pending |

---
*Last updated: 2026-02-27 after initialization*
