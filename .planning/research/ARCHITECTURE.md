# Architecture Research

**Domain:** Brownfield app consolidation (single v2 runtime for scraper + management platform)
**Researched:** 2026-02-27
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
+-------------------------------------------------------------+
|                    Presentation Layer                       |
|  React Pages/Components/Hooks (frontend/src)            |
+-------------------------------+-----------------------------+
                                |
+-------------------------------v-----------------------------+
|                        API Layer                            |
|  FastAPI routers/endpoints (backend/app/api/endpoints)  |
+-------------------------------+-----------------------------+
                                |
+-------------------------------v-----------------------------+
|                     Domain Service Layer                    |
|  channel/scraper/epg/warp/config services + tasks           |
+-------------------------------+-----------------------------+
                                |
+-------------------------------v-----------------------------+
|                   Repository + Persistence                  |
|  repositories + SQLAlchemy models + SQLite/Alembic          |
+-------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| API routers | HTTP contract and validation boundaries | FastAPI endpoint modules |
| Domain services | Business logic orchestration | Class-based services with DB/session access |
| Scraper layer | Source fetch/parse/extract | Base scraper + HTTP/ZeroNet implementations |
| Repositories | Query/write composition | SQLAlchemy session wrappers |
| Frontend hooks/services | UI data orchestration | React Query + typed service clients |

## Recommended Project Structure

```
v2/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- config/
|   |   |-- models/
|   |   |-- repositories/
|   |   |-- schemas/
|   |   |-- scrapers/
|   |   |-- services/
|   |   `-- tasks/
|   |-- migrations/
|   `-- tests/
`-- frontend/
    |-- src/
    |   |-- components/
    |   |-- hooks/
    |   |-- pages/
    |   |-- services/
    |   `-- types/
    `-- package.json
```

### Structure Rationale

- **backend/app split by domain layers:** keeps contracts, logic, and storage concerns isolated.
- **frontend split by UI/data roles:** simplifies refactors and test targeting for large operational screens.

## Architectural Patterns

### Pattern 1: API -> Service -> Repository

**What:** Endpoint modules remain thin; domain logic lives in services; persistence in repositories.
**When to use:** All non-trivial CRUD/operational actions.
**Trade-offs:** Slightly more files, but easier testing and lower coupling.

### Pattern 2: Scraper behavior freeze with wrapper refactor

**What:** Keep extraction behavior stable while improving surrounding orchestration.
**When to use:** During migration parity window.
**Trade-offs:** Limits aggressive rewrite of parser internals initially.

### Pattern 3: Contract-first frontend integration

**What:** Type-safe DTO alignment between backend schemas and frontend service hooks.
**When to use:** Before major UI restructuring.
**Trade-offs:** Requires discipline in schema evolution.

## Data Flow

### Request Flow

```
User action
  -> React page/component
  -> hook/service call
  -> FastAPI endpoint
  -> domain service
  -> repository/model
  -> DB/update response
  -> UI refresh via query invalidation
```

### State Management

- Frontend query state via React Query cache and local component state.
- Backend state via DB persistence and scheduler runtime state.

### Key Data Flows

1. **Scrape ingestion:** URL source -> scraper parse -> channel upsert -> UI list refresh.
2. **EPG refresh:** source fetch/parse -> program/channel updates -> playlist/xml outputs.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k channels / low concurrency | SQLite + in-process scheduler is acceptable |
| 1k-100k channels / heavier refresh jobs | Optimize queries, batching, and task isolation |
| High concurrency + long-running jobs | External workers + stronger DB backend |

### Scaling Priorities

1. **First bottleneck:** DB write/query efficiency on scrape/EPG paths.
2. **Second bottleneck:** In-process scheduled jobs competing with API responsiveness.

## Anti-Patterns

### Anti-Pattern 1: Dual production stacks

**What people do:** Keep root + v2 both active for long periods.
**Why it's wrong:** Creates endless drift and duplicate bug-fix effort.
**Do this instead:** Complete big-bang cutover and retire legacy runtime path.

### Anti-Pattern 2: Mixing API contract changes with undocumented UI assumptions

**What people do:** Change backend responses without typed frontend updates.
**Why it's wrong:** Hidden runtime breakages and brittle pages.
**Do this instead:** Enforce contract alignment in schemas/services/tests.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Acestream engine | HTTP status/control APIs | Critical operational dependency |
| WARP CLI + trace endpoint | subprocess + HTTP verification | Requires robust error handling |
| ZeroNet/HTTP sources | scraper fetch/parse pipeline | Must keep parser reliability |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| frontend -> backend | REST JSON (`/api/v1/*`) | Keep typed DTO parity |
| endpoint -> service | direct method calls | Keep endpoints thin |
| service -> repository | class method calls | Encapsulate query complexity |

## Sources

- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `docs/migration/migration-strategy.md`
- `docs/migration/development-phases.md`

---
*Architecture research for: v2 consolidation migration*
*Researched: 2026-02-27*
