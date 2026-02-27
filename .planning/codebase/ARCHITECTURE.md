# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Monolithic API + SPA with layered backend architecture, plus legacy root runtime still present.

**Key Characteristics:**
- Active stack lives under `v2/` (FastAPI backend + React frontend).
- Legacy root stack files still exist (`wsgi.py`, `manage.py`, root `Dockerfile`) and CI/release logic still targets them.
- Service/repository pattern in backend (`v2/backend/app/services/`, `v2/backend/app/repositories/`).
- Background scheduling done in-process via APScheduler (`v2/backend/app/services/task_service.py`).

## Layers

**API Layer:**
- Purpose: Expose versioned HTTP endpoints and request contracts.
- Contains: FastAPI routers and endpoint handlers.
- Depends on: service and schema layers.
- Used by: frontend app and external API consumers.
- Key paths: `v2/backend/app/api/api.py`, `v2/backend/app/api/endpoints/*.py`

**Service Layer:**
- Purpose: Business logic orchestration (channels, scraping, EPG, config, WARP).
- Contains: domain services and task executors.
- Depends on: repositories, models, scrapers, external clients.
- Used by: API layer and background tasks.
- Key paths: `v2/backend/app/services/*.py`, `v2/backend/app/tasks/*.py`

**Repository/Data Access Layer:**
- Purpose: DB query/write operations.
- Contains: repository classes over SQLAlchemy session.
- Depends on: model layer and SQLAlchemy session.
- Used by: service layer.
- Key paths: `v2/backend/app/repositories/*.py`

**Model/Schema Layer:**
- Purpose: Persistence models and API serialization/validation contracts.
- Contains: SQLAlchemy models + Pydantic schemas.
- Depends on: SQLAlchemy/Pydantic config.
- Used by: repositories and API endpoints.
- Key paths: `v2/backend/app/models/*.py`, `v2/backend/app/schemas/*.py`

**Frontend Layer:**
- Purpose: SPA views, route composition, and API consumption.
- Contains: pages, components, hooks, service clients.
- Depends on: React, MUI, react-query, axios.
- Used by: browser clients.
- Key paths: `v2/frontend/src/pages/*.tsx`, `v2/frontend/src/components/*.tsx`, `v2/frontend/src/services/*.ts`

## Data Flow

**HTTP API Request Flow:**
1. Request enters FastAPI app in `v2/backend/main.py`.
2. Route matching occurs through `api_router` in `v2/backend/app/api/api.py`.
3. Endpoint handler validates query/body using Pydantic schemas in `v2/backend/app/schemas/`.
4. Endpoint calls a domain service in `v2/backend/app/services/`.
5. Service reads/writes via repository or direct SQLAlchemy session.
6. Response model is serialized back to JSON.

**Scraping Flow:**
1. URL scraping is triggered via `/api/v1/scrapers/*` endpoints.
2. `ScraperService` selects scraper strategy using URL type in `v2/backend/app/services/scraper_service.py`.
3. Scrapers fetch/parse remote content (`v2/backend/app/scrapers/http.py`, `v2/backend/app/scrapers/zeronet.py`).
4. Parsed channels are persisted to `acestream_channels` and related tables.

**Scheduled Task Flow:**
1. Scheduler starts at app startup (`v2/backend/main.py` startup event).
2. Interval jobs are registered using `TaskService.add_interval_task`.
3. Tasks execute service logic (`v2/backend/app/tasks/url_scraping_task.py`, `epg_refresh_task.py`, etc.).

**State Management:**
- Persistent state: SQLite database tables in `v2/backend/app/models/models.py`.
- Process state: APScheduler in-memory job scheduler.
- Frontend state: react-query cache and component local state.

## Key Abstractions

**Service objects:**
- Purpose: Domain orchestration and business operations.
- Examples: `AcestreamChannelService`, `EPGService`, `ConfigService`, `WarpService`.
- Pattern: Class-per-domain with injected DB session where relevant.

**Repository objects:**
- Purpose: Encapsulate DB query patterns.
- Examples: `ChannelRepository`, `SettingsRepository`, `URLRepository`.
- Pattern: SQLAlchemy session wrapper methods.

**Scraper strategy:**
- Purpose: Different handling for regular HTTP and ZeroNet URL types.
- Examples: `HTTPScraper`, `ZeronetScraper`.
- Pattern: Base scraper + concrete implementations.

## Entry Points

**Backend API entry:**
- Location: `v2/backend/main.py`
- Triggers: Uvicorn server start (`uvicorn main:app`)
- Responsibilities: initialize DB, register middleware/routes, mount static assets, schedule background tasks

**Legacy backend entry:**
- Location: `wsgi.py` and `run_dev.py`
- Triggers: legacy Docker/prod/dev commands
- Responsibilities: run root migrations and start Flask/ASGI app

**Frontend entry:**
- Location: `v2/frontend/src/index.tsx`
- Triggers: browser load of SPA build
- Responsibilities: mount React app, router, theme provider, react-query client

## Error Handling

**Strategy:** Mixed approach; API handlers often raise `HTTPException`, while many services return status dicts/messages and catch broad exceptions.

**Patterns:**
- Endpoint-level validation and HTTP status responses in `v2/backend/app/api/endpoints/*.py`
- Broad `try/except` blocks in scraping/task services to prevent scheduler crashes
- Fallback responses for unavailable integrations (Acestream/WARP) instead of hard failures

## Cross-Cutting Concerns

**Logging:**
- Central logging setup in `v2/backend/app/utils/logging.py`
- Additional `print` and ad-hoc debug logging still present in several modules/pages

**Validation:**
- Pydantic schemas at API boundaries (`v2/backend/app/schemas/*.py`)
- Query parameter validation in FastAPI function signatures

**Configuration:**
- Environment-driven settings in `v2/backend/app/config/settings.py`
- Runtime toggles also duplicated in shell scripts and Docker definitions

---

*Architecture analysis: 2026-02-27*
*Update when major patterns change*
