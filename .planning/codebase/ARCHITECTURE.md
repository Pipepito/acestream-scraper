# Architecture

**Analysis date:** 2026-09-03
**Branch snapshot:** `develop` (compared locally with `main`)

## System Shape

Acestream Scraper is a single deployable web application assembled from two source trees:

- `backend/`: a FastAPI application, SQLAlchemy/SQLite persistence, scraper integrations, and in-process scheduled jobs.
- `frontend/`: a React 18 + TypeScript SPA built by Vite.

The root multi-stage `Dockerfile` builds the SPA, copies it into the backend image as `/app/frontend_build`, and starts Uvicorn. FastAPI serves both `/api/v1/*` and the compiled SPA from the same origin. Optional AceStream, Acexy, IPFS, ZeroNet, Tor, and WARP processes may run in the same container under the root `entrypoint.sh` supervisor; ZeroNet can alternatively run as the optional Compose sidecar.

This is a modular monolith, not a distributed backend. SQLite is the durable system of record and APScheduler state is process-local.

## Runtime Boundaries

```text
Browser / IPTV client / XMLTV client
          |
          | HTTP
          v
backend/main.py (FastAPI + SPA/static serving)
          |
          +--> API endpoints --> services --> repositories/SQLAlchemy --> SQLite
          |                       |
          |                       +--> HTTP / ZeroNet / IPFS scrapers
          |                       +--> AceStream / Acexy status and search APIs
          |                       +--> WARP and supervised-service controls
          |
          +--> APScheduler --> task functions --> services --> SQLite/external services

frontend/src/index.tsx
  --> AppBootstrap (router, query cache, MUI theme)
  --> App/AppShell/routes
  --> pages/components
  --> hooks/services/apiClient
  --> /api (development: proxied to localhost:8000)
```

## Backend Layers

### Application composition and delivery

- `backend/main.py` creates the FastAPI app, configures lifespan, CORS, correlation IDs, optional API-token enforcement, error handlers, compatibility routes, static mounts, and SPA fallback.
- `backend/app/api/api.py` composes the canonical routers below `/api/v1`.
- The same process exposes player-facing routes such as `/playlists/m3u`, retained v1 playlist/XMLTV URLs, `/docs`, and `/openapi.json`.
- `backend/openapi.json` is the checked-in API snapshot used to generate `frontend/src/types/api-generated.ts`.

### Transport layer

- `backend/app/api/endpoints/` contains FastAPI routers grouped by domain: channels, TV channels, URLs, scrapers, EPG, playlists, search, configuration, health/stats, activity, background tasks, streams, base URLs, WARP, AceStream, and system services.
- `backend/app/schemas/` contains Pydantic request/response contracts.
- `backend/app/api/dependencies.py` wires shared service providers. Wiring is incremental: some endpoint modules still construct domain services directly.
- `backend/app/api/auth.py` implements opt-in token authentication. When `API_TOKEN` is unset the historical trusted-network behavior remains open; `/api/v1/health` is always public.
- `backend/app/api/error_handlers.py` normalizes application errors. `main.py` adds `X-Correlation-ID` propagation/generation.

### Domain/service layer

- `backend/app/services/` owns orchestration for channels, URLs, scraping, EPG, playlists, search, configuration, statistics, dashboards/activity, optional runtimes, and scheduled-task state.
- Services are mostly synchronous around SQLAlchemy, with async methods where network or subprocess work requires it.
- The repository boundary is established but not universal. Architecture tests explicitly guard selected endpoints and URL/statistics services; several larger services still issue direct ORM queries. Agents should preserve the direction `endpoint -> service -> repository/model` and avoid adding new endpoint-level ORM access.
- Compatibility-named pairs exist (`channel_service.py`/`acestreamchannel_service.py`, `stream_service.py`/`streams_service.py`, `tvchannel_service.py`). Check callers before consolidating them.

### Persistence layer

- `backend/app/config/database.py` lazily creates the SQLAlchemy engine and session factory, exposes the FastAPI `get_db` dependency, and owns Alembic provisioning/stamping repair.
- `backend/app/models/models.py` is the canonical declarative model registry. It includes scraped URLs, AceStream channels, TV channels, EPG sources/channels/programs/mappings, settings, base URLs, activity logs, and dashboard configuration.
- `backend/app/repositories/` encapsulates common channel, URL, settings, activity, base-URL, and statistics queries.
- `backend/migrations/` is the only active Alembic tree. New schema changes belong here; do not restore root `migrations/`.
- The default deployment uses `sqlite:///./config/scraper.db`. The engine currently passes SQLite's `check_same_thread=False`, so another database URL is not a proven drop-in runtime path.

### Scraper/integration layer

- `backend/app/models/url_types.py` parses and normalizes regular, `zero://`, `ipfs://`, and `ipns://` source forms.
- `backend/app/scrapers/__init__.py` selects `HTTPScraper`, `ZeronetScraper`, or `IpfsScraper` via a factory.
- `backend/app/services/scraper_service.py` coordinates fetching, M3U parsing, EPG-assisted TV-channel association, stale-source removal, and channel upserts.
- Outbound URLs must continue through the protections in `backend/app/utils/url_guard.py`; do not bypass them in new fetch paths.

### Background execution

- `backend/app/services/task_service.py` wraps a process-local APScheduler `BackgroundScheduler`, instrumentation, runtime status/progress, immediate triggers, and interval rescheduling.
- `backend/app/tasks/` contains thin job entry points that open/close their own database sessions and invoke services.
- FastAPI lifespan registers URL scraping, EPG refresh/cleanup, channel status/cleanup, activity cleanup, and deferred v1 migration jobs. Jobs are not durable across process restarts and multiple app replicas would each schedule the same work.

## Frontend Layers

### Bootstrap and routing

- `frontend/src/index.tsx` mounts `AppBootstrap`.
- `frontend/src/bootstrap/AppBootstrap.tsx` owns the React Query client, MUI theme mode, CSS reset, and `BrowserRouter`.
- `frontend/src/App.tsx` declares routes inside `components/layout/AppShell.tsx`, including redirects from historical browser URLs.

### UI and data access

- `frontend/src/pages/` contains route-level screens.
- `frontend/src/components/` contains reusable domain UI; `components/layout/`, `components/state/`, `components/channels/`, `components/epg/`, and `components/overview/` hold focused primitives.
- `frontend/src/hooks/` composes page state and React Query operations.
- `frontend/src/services/` is the HTTP boundary. `apiClient.ts` uses Axios, reads `/api` at runtime, attaches an optional stored `X-Api-Token`, and normalizes errors.
- `frontend/src/types/` holds API-derived and UI-specific types. Regenerate the OpenAPI-derived file with the package script when contracts change.
- Server state belongs in React Query; theme preference and API token are browser-local; transient form/dialog state remains component-local.

## Principal Data Flows

### Interactive API request

1. The browser service calls `/api/...`; Vite proxies this to port 8000 in development, while production uses the same FastAPI origin.
2. `main.py` attaches a correlation ID and applies the router-level token dependency.
3. FastAPI validates parameters and Pydantic bodies in an endpoint module.
4. The endpoint calls a domain service, usually with a request-scoped `Session` from `get_db`.
5. The service uses a repository or SQLAlchemy models and commits the unit of work.
6. Pydantic serializes the response; Axios/React Query normalize and cache it for the page.

### URL scrape and channel ingestion

1. A user/API action or `url_scraping` scheduled job selects a configured source.
2. `ScraperService` normalizes the URL and selects the scraper strategy.
3. The scraper fetches through HTTP, a ZeroNet node, or an IPFS gateway and returns parsed channel tuples.
4. `M3UService` enriches results and may create/associate TV channels from EPG metadata.
5. Channels no longer present for that source are removed; current channels are transactionally upserted.
6. API-triggered results return to the client; scheduled results are retained only in in-memory task status while domain changes persist in SQLite.

### Startup and legacy migration

1. Container `entrypoint.sh` validates enabled image features and starts/supervises opted-in auxiliary processes.
2. Uvicorn loads `backend/main.py`; lifespan checks for a v1 database, performs the foreground migration portion, and provisions/repairs the v2 Alembic schema.
3. APScheduler starts and periodic jobs are registered using intervals read from settings.
4. A large legacy EPG-program copy, when required, is queued as a one-off background job so health checks can pass promptly.
5. Shutdown stops APScheduler; the shell supervisor terminates child processes.

## Deployment and CI Architecture

- The root `Dockerfile` is canonical. Its final flavor targets are `scraper`, `scraper-acestream`, `scraper-acexy`, and `scraper-acestream-acexy`; `latest` represents the combined flavor in release tooling.
- `entrypoint.sh` supervises optional bundled services and launches the command passed by the image (`uvicorn main:app ...` by default).
- `docker/manifests/` and `docker/scripts/` define platform-aware optional binary installation. `docker/vendor/` contains pinned build inputs and checksums.
- `docker-compose.yml` runs the unified app and offers a profile-gated external ZeroNet sidecar.
- Root `Jenkinsfile` is the PR/develop validation pipeline; `jenkins/release.Jenkinsfile` is the manual release entry. Supporting implementation lives under `scripts/ci/` and `scripts/phase_gates/`.
- GitHub Actions workflows present on `main` are removed on this branch. Do not add a competing publication path without an explicit CI architecture decision.

## Branch-Specific Delta from `main`

The local `main...develop` comparison shows an architectural replacement:

- The root Flask/Jinja application (`app/`), root entry points (`wsgi.py`, `manage.py`, `run_dev.py`), root Alembic tree, and root test suite are deleted from tracked source.
- The active implementation moves to `backend/` and changes application delivery to FastAPI plus a separately built React/Vite SPA.
- Canonical `/api/v1` contracts, checked-in OpenAPI, compatibility endpoints, optional API-token auth, correlation IDs, Alembic startup repair, deferred migration, activity/background-task status, and base-URL/system-service domains are introduced.
- Docker becomes multi-stage, multi-flavor, and multi-architecture, with optional embedded AceStream/Acexy/IPFS/ZeroNet/WARP/Tor runtime handling.
- Jenkins replaces GitHub Actions as the checked-in validation and publication orchestrator.
- `e2e/` adds a scenario-driven Playwright journey suite against a real app/engine/Acexy/IPFS stack.

Compatibility routes and migration code are deliberate bridges for v1 users; they do not make the removed root Flask tree an active development target.

## Agent Guardrails

- Run backend modules with `PYTHONPATH=backend` (or from `backend/`) because imports use the top-level `app` package name.
- Add backend tests under `backend/tests/`, frontend tests under `frontend/src/__tests__/`, and cross-stack journeys under `e2e/tests/`.
- Keep API, service, repository/model, and frontend-service boundaries directional; extend existing providers rather than importing UI or endpoint code into domain modules.
- Treat `backend/frontend_build/`, `frontend/dist/`, `frontend/build/`, databases, logs, E2E reports, and `.planning/debug/` as generated/local artifacts even if they exist in a working tree.
- Never copy values from the ignored `infra-details.md` into tracked documentation or code. Operational instructions may name Jenkins conceptually; credentials and private endpoints stay local.

---

*Update this map when runtime entry points, layer boundaries, or the main/develop cutover state changes.*
