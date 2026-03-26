# Architecture

**Analysis Date:** 2026-02-27

## Pattern Overview

**Overall:** Monolithic API + SPA with layered backend architecture, plus some legacy root artifacts still present.

**Key Characteristics:**
- Active stack lives under canonical root `backend/` and `frontend/`.
- Some legacy root-era files still exist (`wsgi.py`, `manage.py`), while the root `Dockerfile` remains an active canonical build entrypoint.
- Service/repository pattern in backend (`backend/app/services/`, `backend/app/repositories/`).
- Background scheduling done in-process via APScheduler (`backend/app/services/task_service.py`).

## Layers

**API Layer:**
- Purpose: Expose versioned HTTP endpoints and request contracts.
- Contains: FastAPI routers and endpoint handlers.
- Depends on: service and schema layers.
- Used by: frontend app and external API consumers.
- Key paths: `backend/app/api/api.py`, `backend/app/api/endpoints/*.py`

**Service Layer:**
- Purpose: Business logic orchestration (channels, scraping, EPG, config, WARP).
- Contains: domain services and task executors.
- Depends on: repositories, models, scrapers, external clients.
- Used by: API layer and background tasks.
- Key paths: `backend/app/services/*.py`, `backend/app/tasks/*.py`

**Repository/Data Access Layer:**
- Purpose: DB query/write operations.
- Contains: repository classes over SQLAlchemy session.
- Depends on: model layer and SQLAlchemy session.
- Used by: service layer.
- Key paths: `backend/app/repositories/*.py`

**Model/Schema Layer:**
- Purpose: Persistence models and API serialization/validation contracts.
- Contains: SQLAlchemy models + Pydantic schemas.
- Depends on: SQLAlchemy/Pydantic config.
- Used by: repositories and API endpoints.
- Key paths: `backend/app/models/*.py`, `backend/app/schemas/*.py`

**Frontend Layer:**
- Purpose: SPA views, route composition, and API consumption.
- Contains: pages, components, hooks, service clients.
- Depends on: React, MUI, react-query, axios.
- Used by: browser clients.
- Key paths: `frontend/src/pages/*.tsx`, `frontend/src/components/*.tsx`, `frontend/src/services/*.ts`

## Data Flow

**HTTP API Request Flow:**
1. Request enters FastAPI app in `backend/main.py`.
2. Route matching occurs through `api_router` in `backend/app/api/api.py`.
3. Endpoint handler validates query/body using Pydantic schemas in `backend/app/schemas/`.
4. Endpoint calls a domain service in `backend/app/services/`.
5. Service reads/writes via repository or direct SQLAlchemy session.
6. Response model is serialized back to JSON.

**Scraping Flow:**
1. URL scraping is triggered via `/api/v1/scrapers/*` endpoints.
2. `ScraperService` selects scraper strategy using URL type in `backend/app/services/scraper_service.py`.
3. Scrapers fetch/parse remote content (`backend/app/scrapers/http.py`, `backend/app/scrapers/zeronet.py`).
4. Parsed channels are persisted to `acestream_channels` and related tables.

**Scheduled Task Flow:**
1. Scheduler starts at app startup (`backend/main.py` startup event).
2. Interval jobs are registered using `TaskService.add_interval_task`.
3. Tasks execute service logic (`backend/app/tasks/url_scraping_task.py`, `epg_refresh_task.py`, etc.).

**State Management:**
- Persistent state: SQLite database tables in `backend/app/models/models.py`.
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
- Location: `backend/main.py`
- Triggers: Uvicorn server start (`uvicorn main:app`)
- Responsibilities: initialize DB, register middleware/routes, mount static assets, schedule background tasks

**Legacy backend entry:**
- Location: `wsgi.py` and `run_dev.py`
- Triggers: legacy Docker/prod/dev commands
- Responsibilities: run root migrations and start Flask/ASGI app

**Frontend entry:**
- Location: `frontend/src/index.tsx`
- Triggers: browser load of SPA build
- Responsibilities: mount React app, router, theme provider, react-query client

## Error Handling

**Strategy:** Mixed approach; API handlers often raise `HTTPException`, while many services return status dicts/messages and catch broad exceptions.

**Patterns:**
- Endpoint-level validation and HTTP status responses in `backend/app/api/endpoints/*.py`
- Broad `try/except` blocks in scraping/task services to prevent scheduler crashes
- Fallback responses for unavailable integrations (Acestream/WARP) instead of hard failures

## Cross-Cutting Concerns

**Logging:**
- Central logging setup in `backend/app/utils/logging.py`
- Additional `print` and ad-hoc debug logging still present in several modules/pages

**Validation:**
- Pydantic schemas at API boundaries (`backend/app/schemas/*.py`)
- Query parameter validation in FastAPI function signatures

**Configuration:**
- Environment-driven settings in `backend/app/config/settings.py`
- Runtime toggles also duplicated in shell scripts and Docker definitions

---

*Architecture analysis: 2026-02-27*
*Update when major patterns change*
