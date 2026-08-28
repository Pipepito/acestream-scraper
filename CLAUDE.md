# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

Backend (run from repo root unless noted):

- Install: `python3 -m venv backend/venv && source backend/venv/bin/activate && pip install -r backend/requirements.txt`
- Dev server: `cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Full pytest suite: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests`
- Single file: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py`
- Single test: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py::test_name`
- Curated v2 runner: `python backend/run_tests.py [name]` (groups: channels, tv, epg, scrapers, search, playlists, config, health, warp; or `coverage`)
- Alembic (always run from repo root with PYTHONPATH set so `backend/` is importable):
  - History: `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini history`
  - Upgrade: `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini upgrade head`

Frontend (`cd frontend`):

- Install: `npm ci`
- Dev (proxies `/api` → `:8000`): `npm start` (Vite, port 3000)
- Build for backend serving: `npm run build:backend` (runs `vite build` then copies `dist/` → `backend/frontend_build/` via `scripts/copy-build.js`; set `COPY_BUILD_SOURCE`/`COPY_BUILD_DESTINATION` to override)
- Tests: `npm test` (Jest + RTL); single file: `npm test -- Dashboard.test.tsx`

Cutover / CI:

- Quick canonical suite (backend contracts + key frontend tests + frontend build): `bash scripts/ci/run_v2_test_suite.sh --profile quick` (or `--profile full`)
- Same target via the cutover wrapper: `bash scripts/ci/run_cutover_required_checks.sh --profile quick`
- Strict legacy-path guard: `bash scripts/ci/assert_no_legacy_paths.sh --strict`
- Pre-deploy DB safety check (creates timestamped backup under `config/backups/`): `bash scripts/ops/preflight_v2_deploy.sh`

Docker:

- `docker compose up -d` (uses `pipepito/acestream-scraper:latest` = `scraper-acestream-acexy` payload; published flavors: `scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`)
- Optional ZeroNet sidecar: `docker compose --profile zeronet up -d`
- Docker packaging tests (manifest schema, build-arg derivation, installer layout, engine runtime smoke; the installer/smoke tests build images with Docker buildx): `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker`
- Docker manifest + vendored payload validator (schema, `docker/vendor/**/SHA256SUMS`, mirror URLs): `python3 scripts/ci/validate_docker_manifest_metadata.py`

## Architecture

### Top-level layout

`backend/` (FastAPI app, source of truth for runtime) and `frontend/` (React 18 + TypeScript + Vite + MUI v5) are the only canonical app paths. The backend serves the built SPA from `backend/frontend_build/` at `/`; the frontend's build script writes there. Legacy root entrypoints have been retired — `scripts/ci/assert_no_legacy_paths.sh --strict` enforces this.

### Backend startup sequence (`backend/main.py`)

1. `app.config.settings` loads `Settings` (pydantic-settings) and on import calls `apply_legacy_env_aliases()` to map one-release-window legacy env names to canonical ones (e.g., `SCRAPER_DB_URL` → `DATABASE_URL`, `ACESTREAM_ENGINE_URL` → `ACE_ENGINE_URL`); canonical wins on conflict, both-set conflicts log a warning. Disable with `ENABLE_LEGACY_ENV_ALIASES=false`.
2. `initialize_database()` runs inside the `lifespan()` async context manager (passed as `FastAPI(..., lifespan=lifespan)`), i.e. at server startup — after the `app` object exists, before the first request is served:
   - If a v1 SQLite db exists at `LEGACY_DATABASE_URL` and is not yet marked `.migrated`, `migrate_database.DatabaseMigrator` performs the v1→v2 data migration in-process.
   - Otherwise, if the v2 db file is missing, it provisions the schema by calling Alembic `upgrade head` (same path as tests/deployments). Existing v2 dbs are left alone.
3. `api_router` is mounted at `/api/v1`. Routers include a backward-compatible alias: `/api/v1/channels` and `/api/v1/acestream-channels` route to the same router (kept for parity tests).
4. A non-API public M3U route is exposed at `/playlists/m3u` (no `/api` prefix) for user-friendly playlist URLs.
5. SPA fallback: a `StarletteHTTPException` handler returns `frontend_build/index.html` for any non-`/api` 404, enabling client-side routing.
6. APScheduler (`task_service`) is started in the same `lifespan()` right after `initialize_database()` (`task_service.start()` followed by one `task_service.add_interval_task(...)` per job) and stopped with `task_service.shutdown()` when the lifespan exits. Registered fixed-interval jobs: activity-log cleanup (24h), EPG refresh (1h), URL scraping (15m), channel cleanup (24h), channel status (10m). Edit intervals in `main.lifespan()` — there is no separate `start_background_tasks()` function and no `@app.on_event` hooks.

### Backend module shape (`backend/app/`)

- `api/api.py` is the only place routers are wired. Endpoint modules under `api/endpoints/` are thin and call services.
- `services/` holds business logic — one module per domain (channels, tv channels, EPG sources/channels/programs, scrapers, search, playlists, stats, activity log, dashboard config, WARP, streams, task scheduler, etc.). Endpoints inject `Session` via `Depends(get_db)` and instantiate the relevant service.
- `models/models.py` is the SQLAlchemy model hub; some additional models live in sibling files (`activity_log.py`, `dashboard_config.py`, `background_task_status.py`). `Base` comes from `app/config/database.py`.
- `repositories/` — DB-only access helpers (no business logic).
- `schemas/` — Pydantic DTOs for request/response.
- `scrapers/` — `BaseScraper` ABC plus `HTTPScraper` and `ZeronetScraper` concrete implementations. `create_scraper_for_url(url, url_type)` is the factory; `url_type` of `"auto"`, `"zeronet"`, or `"regular"` resolves to a `BaseURL` subclass that controls timeout/retry defaults.
- `tasks/` — function bodies invoked by the APScheduler jobs registered in `main.py`.
- `migrations/` — Alembic; mixed naming style (timestamped + hash slugs). Two recent revisions (`20260423_…align_runtime_schema`, `…align_channel_and_url_runtime_schema`) backfill the runtime model — keep them in any reset path. Tests use `tests/migration_test_utils.upgrade_to_head` rather than `Base.metadata.create_all` to ensure parity with prod.

### Test fixtures (`backend/tests/conftest.py`)

Two parallel runtimes coexist:

- `backend_runtime` / `client` / `db_session` — fast path that creates schema with `Base.metadata.create_all` on a temp SQLite file. Use for most service/endpoint tests.
- `alembic_backend_runtime` / `alembic_client` / `alembic_db_session` — provisions the temp DB by running Alembic `upgrade head`. Use this when behavior depends on real migration state (schema parity, contract tests, regression suites).

The fixtures never reload modules: `_bind_runtime_to(database_url)` re-points the lazy engine at the temp database and `_refresh_settings_cache()` invalidates the settings cache per test, while `override_get_db` / `alembic_override_get_db` inject the test session through FastAPI dependency overrides. Tests that import models or config inside fixtures should still do so lazily, after the fixture has bound the runtime.

### Frontend

- Routing is declared in `src/App.tsx` and wrapped in `components/layout/AppShell`. Pages under `src/pages/` are the route-level views; reusable components live under `src/components/`.
- API access goes through `src/services/*.ts`, all built on `apiClient.ts` (axios). `@tanstack/react-query` v5 is the data layer (see `frontend/package.json`).
- Vite config (`frontend/vite.config.ts`) hand-tunes `manualChunks` for MUI / data-grid / data-vendor / TVChannels page splits. Preserve the chunking rules unless deliberately retuning bundle size.
- Dev server proxies `/api` → `http://localhost:8000`. Backend `CORS_ORIGINS` defaults to `http://localhost:3000` and accepts a comma-separated string in env (normalized in `Settings.normalize_cors_origins`).

### Docker image flavors

The root `Dockerfile` is multi-stage with named targets `scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`. `latest` is the same payload as `scraper-acestream-acexy`. AceStream-enabled flavors (`scraper-acestream`, `scraper-acestream-acexy`, `latest`) are platform-gated by `docker/manifests/acestream.json`, which now covers `linux/amd64,linux/arm/v7,linux/arm64` (`scripts/ci/flavor_platforms.py` resolves this automatically); the baseline flavors (`scraper`, `scraper-acexy`) cover ARMv7/ARM64 as before. The manifest picks an install kind per target platform: `linux/amd64` → `executable` (native Linux engine 3.2.11 tarball, unchanged); `linux/arm64` (support `stable`) and `linux/arm/v7` (support `experimental` — builds and installs, but cannot run under qemu-user and has not been runtime-tested) → `android-apk` (the official Android engine APK 3.1.80, unzipped to `/opt/acestream` and run unmodified on a minimal Android 9 bionic userland copied to `/system` from the Termux `aosp-libs` package — no chroot, no `--privileged`, no extra capabilities). The engine is opt-in (`ENABLE_ACESTREAM_ENGINE=false` by default), so the app itself is unaffected on ARM.

Two interpreters are pinned by `Dockerfile` build args: `ARG APP_PYTHON_VERSION=3.13` is the app's Python (`python-deps` and `runtime-base` stages, so every `scraper*` flavor can track new CPython releases), while `ARG ACESTREAM_ENGINE_PYTHON_VERSION=3.10` is the x86_64 engine's Python (`acestream-installer` and `engine-python` stages) and must match `install.python_version` in `docker/manifests/acestream.json`; the Android engine used on ARM ships its own bionic CPython 3.8 and ignores both.

Every engine archive and the bionic `.deb`s are vendored under `docker/vendor/acestream/` and `docker/vendor/bionic/` (each with `SHA256SUMS`; identical copies are GitHub Release assets on the `acestream-binaries-<versions>` tag). `docker/scripts/install-acestream.sh` resolves vendored copy → upstream URL → `mirror_urls`, sha256-verified, so builds need no egress to download.acestream.media. The `acestream-installer` stage takes `ARG TARGETPLATFORM` and `ARG ACESTREAM_SOURCE=auto` (`auto` = resolve from the manifest via `docker/scripts/acestream_manifest.py`, the shared resolver also used by `scripts/ci/derive_acestream_build_args.py`; explicit `--build-arg ACESTREAM_*` values override; `fixture` = contract-test fixture). `docker/vendor` is bind-mounted into that stage, not copied into a layer. `scripts/ci/build_multiarch_images.sh` no longer injects global `ACESTREAM_*` build-args (they would pin one engine for every platform of a multi-platform build). Bumping the pins: `docker/vendor/acestream/README.md`.

`entrypoint.sh` enforces the install/runtime split: which binaries are installed is set by the chosen flavor (`IMAGE_HAS_ACESTREAM`, `IMAGE_HAS_ACEXY`); whether they actually start is controlled by `ENABLE_ACESTREAM_ENGINE`, `ENABLE_ACEXY`, `ENABLE_WARP`. WARP requires `NET_ADMIN` + `SYS_ADMIN` capabilities. Acexy refuses to target `localhost:6878` if the in-container engine is disabled. On ARM images the engine is launched through `/opt/acestream/start-engine` (`docker/scripts/acestream-android/start-engine`), which requires a 4 KB-page kernel (`getconf PAGESIZE` must be 4096; Raspberry Pi 5 needs `kernel=kernel8.img` in `config.txt`) and keeps state/cache/logs under `ACESTREAM_HOME=/var/lib/acestream` (mount a volume, e.g. `-v acestream-state:/var/lib/acestream`); `ACESTREAM_START_COMMAND` is unchanged for all platforms. Known ARM limitations: engine version skew (3.1.80 vs 3.2.11; `platform` reports `android`), no WebRTC transport, no WARP (cloudflare-warp is amd64-only).

### Engineering norms (project-specific)

- TypeScript-only frontend: no `.js`/`.jsx` files; all components typed via named interfaces, no `any`. See `docs/dev/typescript-standards.md`.
- Backend uses Python 3.11+, pydantic v2, SQLAlchemy 2.x; type hints required; every endpoint round-trips through Pydantic DTOs and surfaces in `/openapi.json`.
- `docs/migration/development-progress.md` is the live status doc; `docs/migration/migration-strategy.md` and `docs/migration/development-phases.md` define cutover rules.

## Design Context

For frontend design guidance in this worktree, also use `docs/dev/frontend-design-checklist.md` and `docs/dev/frontend-theme-reference.md` alongside this context.

### Users
This product is for single users with little or no technical knowledge who need guidance while managing an AceStream setup. They use the interface as an operational control panel for channels, EPG data, playlists, scraper tasks, WARP, and system health, and the product should help them move through each workflow without assuming deep technical expertise.

### Brand Personality
The brand should feel bold, powerful, and operational. The voice should be clear, direct, and supportive so users feel fast, confident, and slightly delighted rather than intimidated by a technical tool.

### Aesthetic Direction
The current product already points toward a structured operational dashboard: Material UI, IBM Plex Sans, a left-nav app shell, light-mode defaults, teal and blue as primary accents, and compact cards and sections for dense information. Future design work should support both light and dark themes, keep the product feeling Linear-like in polish and clarity, introduce warmer accents where they add emphasis or friendliness, and avoid looking like a playful consumer app, a generic admin template, or an overly dark hacker interface.

### Design Principles
- Prefer guided, low-friction flows over expert-only controls so non-technical users can complete operational tasks with confidence.
- Keep information dense but well-structured, using clear hierarchy, sectioning, and status signals to make the system feel fast and controllable.
- Make operational state obvious: health, progress, errors, and next actions should be easy to scan and hard to misunderstand.
- Build a polished dual-theme system that starts from the existing teal/blue foundation and uses warmer accents sparingly for emphasis, feedback, and approachability.
- Meet WCAG AA expectations, respect reduced-motion preferences, and use more than color alone to communicate status or meaning.
