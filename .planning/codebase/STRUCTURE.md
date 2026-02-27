# Codebase Structure

**Analysis Date:** 2026-02-27

## Directory Layout

```
acestream-scraper/
|-- .github/                 # CI workflows and local AI instructions
|-- app/                     # Legacy root app path (currently empty)
|-- docs/                    # Architecture/migration/development docs
|-- migrations/              # Legacy root DB migrations
|-- tests/                   # Legacy/root pytest suite
|-- v2/                      # Active v2 implementation
|   |-- backend/             # FastAPI backend, models/services/tests
|   `-- frontend/            # React + TypeScript frontend
|-- Dockerfile               # Legacy runtime container build
|-- docker-compose.yml       # Legacy full-stack compose
|-- run_dev.py               # Legacy local dev entry
|-- wsgi.py                  # Legacy production entry
`-- pyproject.toml           # Root package metadata (legacy stack)
```

## Directory Purposes

**`v2/backend/`:**
- Purpose: Primary backend implementation.
- Contains: API routes, services, repositories, models, schemas, tasks, migrations, tests.
- Key files: `v2/backend/main.py`, `v2/backend/app/api/api.py`, `v2/backend/app/models/models.py`.
- Subdirectories: `app/`, `migrations/`, `tests/`, `frontend_build/`.

**`v2/frontend/`:**
- Purpose: SPA frontend for channel and system management.
- Contains: React pages/components/hooks/services and build artifacts.
- Key files: `v2/frontend/src/App.tsx`, `v2/frontend/src/index.tsx`, `v2/frontend/package.json`.
- Subdirectories: `src/`, `public/`, `scripts/`, `build/`.

**`tests/`:**
- Purpose: Root/legacy test suite.
- Contains: unit and integration tests that import `app.*` modules.
- Key files: `tests/conftest.py`, `tests/integration/test_api.py`.
- Subdirectories: `tests/unit/`, `tests/integration/`.

**`migrations/`:**
- Purpose: Legacy migration history for root stack.
- Contains: Alembic environment and historical revision files.
- Key files: `migrations/env.py`, `migrations/versions/*.py`.

**`docs/` and `wiki/`:**
- Purpose: Project docs, migration plans, architecture notes, usage docs.
- Contains: markdown references and feature planning docs.

## Key File Locations

**Entry Points:**
- `v2/backend/main.py` - FastAPI app startup and scheduler initialization.
- `v2/frontend/src/index.tsx` - React app bootstrap.
- `wsgi.py` - Legacy ASGI/WSGI entrypoint.
- `run_dev.py` - Legacy development launch path.

**Configuration:**
- `v2/backend/app/config/settings.py` - backend settings model.
- `v2/backend/app/config/database.py` - SQLAlchemy engine/session.
- `v2/frontend/tsconfig.json` - frontend TS compiler options.
- `docker-compose.yml` and `v2/docker-compose.yml` - runtime environment wiring.

**Core Logic:**
- `v2/backend/app/services/` - domain services.
- `v2/backend/app/repositories/` - data access.
- `v2/backend/app/api/endpoints/` - HTTP endpoints.
- `v2/backend/app/scrapers/` - scraping strategy implementations.

**Testing:**
- `tests/` - root test suite (legacy-oriented).
- `v2/backend/tests/` - v2 backend API/integration tests.
- `v2/frontend/src/__tests__/` - frontend component tests.

**Documentation:**
- `README.md` - project overview and legacy run/deploy docs.
- `docs/` - migration/dev/architecture docs.
- `wiki/` - user and contributor docs.

## Naming Conventions

**Files:**
- Python modules use `snake_case.py` (example: `channel_service.py`).
- React components/pages use `PascalCase.tsx` (example: `TVChannelDetail.tsx`).
- TS services/hooks use `camelCase` prefixes (example: `channelService.ts`, `useChannels.ts`).
- Test files use `test_*.py` (Python) and `*.test.tsx` (frontend).

**Directories:**
- Backend uses domain-oriented directories (`api`, `services`, `repositories`, `models`).
- Frontend uses layer grouping (`components`, `pages`, `hooks`, `services`, `types`).

**Special Patterns:**
- API versioning under `/api/v1` in router registration.
- Legacy and v2 code coexist at different roots, so path choice is critical for changes.

## Where to Add New Code

**New backend API feature (v2):**
- Primary code: `v2/backend/app/api/endpoints/` and `v2/backend/app/services/`
- Data/model updates: `v2/backend/app/models/` + `v2/backend/migrations/`
- Tests: `v2/backend/tests/`

**New frontend feature:**
- Page-level UI: `v2/frontend/src/pages/`
- Reusable UI: `v2/frontend/src/components/`
- API client updates: `v2/frontend/src/services/` and hooks in `v2/frontend/src/hooks/`
- Tests: `v2/frontend/src/__tests__/`

**Legacy/root changes (only when required):**
- Runtime/migration scripts: root `wsgi.py`, `manage.py`, `migrations/`
- Legacy tests: `tests/`

## Special Directories

**`v2/backend/frontend_build/`:**
- Purpose: Built frontend assets served by FastAPI.
- Source: produced from `v2/frontend` build.
- Committed: yes (currently present in repository).

**`v2/frontend/build/`:**
- Purpose: local frontend build artifact.
- Source: `react-scripts build`.
- Committed: yes (currently present; verify policy before continuing this pattern).

**`app/`:**
- Purpose: historical root app package path.
- Source: legacy architecture; currently empty.
- Committed: yes, but empty state is a migration risk because tests/workflows still reference it.

---

*Structure analysis: 2026-02-27*
*Update when directory structure changes*
