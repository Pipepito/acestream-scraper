# Technology Stack

**Analysis date:** 2026-09-03
**Mapped revision:** `develop` at `e5bc9e0` (the branch currently proposed for merge into `main`)

## Canonical Application

- `backend/` is the only supported Python application path. It is a FastAPI ASGI app started from `backend/main.py`; the production image runs `uvicorn main:app` on port 8000.
- `frontend/` is the only supported UI path. It is a React 18 + TypeScript single-page app built with Vite and served by FastAPI from `backend/frontend_build/`.
- The root `Dockerfile` is the production packaging source of truth. `backend/Dockerfile` and `frontend/Dockerfile` are useful component images, but releases use the root multi-stage build.
- Root `pyproject.toml` and root `requirements*.txt` describe the retired v1/Flask package and are not the dependency source for the canonical runtime. CI enforces canonical paths through `scripts/ci/assert_no_legacy_paths.sh`.

## Languages and Runtimes

| Area | Runtime | Where pinned or configured |
| --- | --- | --- |
| Backend | Python 3.11+ source; production image currently Python 3.13 | `Dockerfile` (`APP_PYTHON_VERSION`), `backend/requirements.txt` |
| Frontend | TypeScript 5.9, React 18 | `frontend/package.json`, `frontend/tsconfig.json` |
| Frontend build | Node.js 20 in production build | `Dockerfile` (`node:20-slim`) |
| AceStream on amd64 | Native engine 3.2.11 with a separate Python 3.10 runtime | `docker/manifests/acestream.json`, `Dockerfile` |
| AceStream on ARM | Android engine 3.1.80.0 with bundled CPython/bionic runtime | `docker/manifests/acestream.json`, `docker/scripts/acestream-android/` |
| Acexy | Go 1.22 builder; statically linked Acexy 0.2.2 binary | `Dockerfile`, `docker/manifests/acexy.json` |
| ZeroNet | Separate Python 3.11 runtime; zeronet-conservancy v0.7.10 pinned by commit | `Dockerfile`, `docker/zeronet/requirements.txt` |
| Automation | Bash and Python scripts | `scripts/ci/`, `scripts/ops/`, `entrypoint.sh` |

Do not collapse the three Python versions in the root image: the application, native amd64 AceStream engine, and bundled ZeroNet node have independent compatibility constraints.

## Backend Framework and Dependencies

`backend/requirements.txt` is the authoritative Python dependency manifest. It uses lower bounds rather than a lock file.

- API/runtime: FastAPI, Uvicorn, Pydantic v2, and `pydantic-settings`.
- Persistence: SQLAlchemy 2.x and Alembic. The default database is SQLite; production schema creation and upgrades are migration-driven.
- Scraping/parsing: `aiohttp`, Beautiful Soup, and lxml.
- HTTP clients: `httpx` and `requests` remain in service integrations alongside `aiohttp`.
- Scheduling: APScheduler 3.11+; jobs are registered in the FastAPI lifespan in `backend/main.py`.
- Utilities: `python-multipart` and `python-dotenv`.
- Backend tests: pytest and pytest-asyncio are currently included in the same requirements file because Jenkins installs that file for validation.

The application exposes `/api/v1`, public player-oriented playlist/EPG URLs, `/openapi.json`, and the built SPA. FastAPI's lifespan initializes or repairs the database, starts interval jobs, schedules any deferred v1 EPG migration, and shuts the scheduler down cleanly.

## Frontend Framework and Dependencies

`frontend/package.json` and `frontend/package-lock.json` are authoritative; use `npm ci` in reproducible environments.

- React 18 and React Router 6.
- Material UI 5, Emotion, MUI icons, and MUI X Data Grid.
- TanStack React Query 5 for server state and Axios for HTTP.
- `date-fns` and `qrcode.react` for presentation features.
- Vite 8 with the React plugin for development and builds.
- Jest 30, ts-jest, jsdom, React Testing Library, and eslint for frontend quality checks.
- `openapi-typescript` generates `frontend/src/types/api-generated.ts` from `backend/openapi.json`.

`frontend/vite.config.ts` proxies `/api` to port 8000 in development and manually separates React, MUI, data, and TV-channel chunks. `npm run build:backend` copies Vite output into `backend/frontend_build/`; the root Dockerfile copies the Vite stage output there directly.

## Persistence and Configuration

- `backend/app/config/settings.py` uses case-sensitive Pydantic settings and optionally reads `.env`.
- Canonical database setting: `DATABASE_URL`, default `sqlite:///./config/scraper.db`.
- Legacy import source: `LEGACY_DATABASE_URL`, default `sqlite:///./config/acestream.db`.
- One-release compatibility aliases map selected v1 names to canonical names. Canonical values win conflicts; set `ENABLE_LEGACY_ENV_ALIASES=false` to disable this window.
- Alembic lives under `backend/migrations/`. Existing installations are not automatically upgraded to every new revision merely by startup; use the documented deploy preflight/migration workflow.
- Mutable container state is filesystem-backed: `config/`, `/data/ipfs`, `/data/zeronet`, `/var/lib/acestream`, logs, and supervisor marker/PID files.
- There is no Redis, queue broker, object store, or external production database in the current design.

Important runtime settings span application behavior (`CORS_ORIGINS`, retention/cleanup and scheduler intervals), optional API authentication (`API_TOKEN`), scraper endpoints/timeouts, and sidecar install/enable flags. Treat `IMAGE_HAS_*` as image capabilities and `ENABLE_*` as operator intent; they are not interchangeable.

## Container and Platform Matrix

The root `Dockerfile` defines four targets:

| Flavor | Payload | Supported platforms |
| --- | --- | --- |
| `scraper` | App plus platform-available WARP/IPFS/ZeroNet components | amd64, arm/v7, arm64 |
| `scraper-acestream` | App plus AceStream engine | amd64, arm/v7, arm64 |
| `scraper-acexy` | App plus Acexy | amd64, arm/v7, arm64 |
| `scraper-acestream-acexy` | Full payload | amd64, arm/v7, arm64 |

Platform truth lives in `docker/manifests/platforms.json` and engine install truth in `docker/manifests/acestream.json`. ARMv7 AceStream support is marked experimental. Kubo is absent on arm/v7; embedded ZeroNet/Tor is amd64-only; Cloudflare WARP packages are installed only on amd64/arm64. ARM AceStream additionally requires a 4 KB-page kernel.

The engine and bionic archives plus Acexy source are vendored and checksum-verified under `docker/vendor/`; mirrors are recorded in manifests. This is deliberate because Jenkins builds must not depend on anonymous GitHub clones through the runner's WARP egress.

## Development and Verification Tooling

- Backend environment: `python3 -m venv backend/venv`, then install `backend/requirements.txt`.
- Backend server: run Uvicorn from `backend/` so `main:app` and `app.*` imports resolve.
- Backend tests: set `PYTHONPATH=backend` and run `backend/venv/bin/pytest backend/tests`.
- Frontend: `npm ci`, `npm start`, `npm test`, `npm run lint`, `npm run typecheck`, and `npm run build:backend` from `frontend/`.
- E2E: separate npm project under `e2e/`, Playwright 1.62+, Firefox by default, serial one-worker journeys against an isolated live stack. It produces HTML, JUnit, JSON, trace, video, and failure screenshots.
- Canonical quick validation: `bash scripts/ci/run_cutover_required_checks.sh --profile quick` or `bash scripts/ci/run_v2_test_suite.sh --profile quick`.
- Container builds and publication use Docker Buildx with a named builder, QEMU/binfmt where necessary, per-platform digest pushes, and manifest assembly.

## CI and Release Stack on `develop`

Jenkins is the sole CI/release system; there are no active GitHub Actions workflows. The root `Jenkinsfile` runs on agent label `dorat-nuc-ci`, bootstraps Python/Node/Docker/Buildx, validates docs and branch policy, runs quick cutover/phase gates, validates the four-flavor multi-arch plan, executes real AceStream/Acexy smoke tests, and archives gate artifacts.

The branch model is part of the runtime delivery contract:

- Feature PRs target permanent pre-release branch `develop`.
- `main` accepts only a `develop` -> `main` release PR; the Jenkins `Branch Policy` stage enforces this.
- Validated `develop` builds publish floating `:develop` and `:develop-<flavor>` images, plus the docs site and wiki. They never publish a release version or `:latest`.
- `jenkins/release.Jenkinsfile` is a separate manual job on `main`. It requires confirmation, defaults to dry-run, rejects `-dev` versions, publishes version/flavor manifests first, and promotes the canaried version to `:latest` only in a separate `PUBLISH_LATEST=true` run.

Use `docs/ops/jenkins-ci.md` for the full operational procedure and `INTEGRATIONS.md` for safe controller-access guidance.

---

*Refresh this file when runtime pins, canonical paths, image flavors/platform support, or CI ownership change.*
