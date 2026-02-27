# Stack Research

**Domain:** Brownfield migration/refactor of a streaming scraper platform (Flask legacy -> FastAPI + React TypeScript)
**Researched:** 2026-02-27
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12 baseline (3.11+ minimum) | Backend runtime | Modern typing/performance and cleaner long-term support than mixed 3.10/3.11 legacy paths |
| FastAPI | 0.11x line | HTTP API layer | Already adopted in `v2`, strong typing/OpenAPI, lower friction for maintainability |
| SQLAlchemy + Alembic | 2.x + 1.13+ | ORM + migrations | Existing v2 model/repo structure aligns; supports gradual schema hardening |
| React + TypeScript | React 18 / TS 5.x | Frontend UI | Existing v2 UI foundation; strict typing needed for reducing regressions |
| Docker Buildx | current | Multi-arch image build and distribution | Required for `linux/arm/v7` and `linux/arm64` deliverables |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic + pydantic-settings | v2 | Typed schemas + env configuration | All API contracts and runtime config boundaries |
| APScheduler | 3.10+ | Periodic scraping/EPG jobs | Keep for current task model; later replace with worker queue only if needed |
| aiohttp + beautifulsoup4 + lxml | current stable | Scraping/parsing pipeline | Preserve scraper behavior parity while refactoring around it |
| React Query (TanStack migration path) | keep current then upgrade | Data fetching/cache | Stabilize API contract first, then upgrade package family safely |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Backend test and regression coverage | Use old tests as parity reference; rebuild ownership under `v2/backend/tests` |
| Jest + RTL | Frontend behavior tests | Prioritize critical pages/workflows over broad snapshot tests |
| flake8 (short-term) / ruff (target) | Linting | Keep CI green with flake8 first; migrate to ruff once root legacy is removed |
| GitHub Actions + buildx | CI and publish | Unify legacy + v2 pipelines into a single v2 release flow |

## Installation

```bash
# Backend
pip install -r v2/backend/requirements.txt

# Frontend
cd v2/frontend && npm ci

# Dev checks
pytest v2/backend/tests/
cd v2/frontend && npm test -- --watchAll=false
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| SQLite (initially) | PostgreSQL | Move when write concurrency and workload outgrow SQLite safely |
| APScheduler in API process | External queue workers | Use when long-running jobs begin to impact API responsiveness |
| MUI + React stack | Fresh design system rewrite | Only after stabilizing core migration and regression surface |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Maintaining both root and v2 production runtimes | Guarantees drift and duplicate bug surface | Single v2 runtime ownership |
| Preserving legacy API compatibility by default | Slows cleanup and retains accidental complexity | Define explicit v2 API contracts |
| Multi-container release logic split by legacy/v2 | Causes deployment ambiguity | One v2-first build/release path |

## Stack Patterns by Variant

**If immediate migration stabilization:**
- Keep current scraper dependencies and parser logic as-is
- Because scraper reliability is the protected invariant

**If post-cutover optimization phase:**
- Tune DB/access patterns and task architecture incrementally
- Because architecture cleanup is safer after parity is verified

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| FastAPI (0.11x) | Pydantic v2 | Required for modern schema/runtime behavior |
| SQLAlchemy 2.x | Alembic 1.13+ | Supports typed model evolution in v2 backend |
| React 18 | TypeScript 5.x | Suitable for strict typing and modern tooling upgrades |

## Sources

- `.planning/codebase/STACK.md` — current stack inventory
- `docs/migration/development-progress.md` — completed migration work snapshot
- `docs/migration/migration-strategy.md` — target direction and deployment intent
- Repository code in `v2/backend/` and `v2/frontend/` — implementation reality

---
*Stack research for: brownfield v2 consolidation*
*Researched: 2026-02-27*
