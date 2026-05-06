# Acestream Scraper v2 — Release Notes

> Companion document: `docs/release/v2-release-readiness.md` records the gap audit and the closure work that landed before tag.

## Overview

v2 is a **big-bang consolidation**. The legacy root Flask stack is retired and replaced by a single canonical pair: a **FastAPI backend** at `backend/` and a **React + TypeScript SPA** at `frontend/`. The runtime ships as a multi-flavor Docker image with first-class ARMv7 / ARM64 support.

Scraping behavior is preserved against a parity baseline. Channel, TV-channel, EPG, playlist, scraper-URL, search, settings, health, stats, WARP, and Acestream-status workflows continue to work, with a redesigned UI on top.

If you are upgrading from v1, run `bash scripts/ops/preflight_v2_deploy.sh` first — it backs up your databases under `config/backups/` and verifies that v1→v2 data migration will succeed before the new image starts.

---

## What's new

### Architecture

- **Single canonical stack.** Production runtime, build, and release flow run only on `backend/` + `frontend/`. The legacy root entrypoints (`wsgi.py`, `run_dev.py`, `manage.py`, root `app/`, root `migrations/`) are gone.
- **FastAPI replaces Flask.** Typed request/response models, OpenAPI auto-docs at `/docs`, async-friendly endpoints, structured exception handling.
- **Layered backend.** Endpoint → service → repository boundaries are enforced with an architecture-guard test (`backend/tests/architecture/test_layer_boundaries.py`). New code follows the same shape.
- **Unified API contract.** All endpoints under `/api/v1/`; `/api/v1/channels` and `/api/v1/acestream-channels` route to the same handler for parity. Public M3U is exposed (no `/api` prefix) at `/playlists/m3u` for friendlier URLs, and the v1 player URLs keep working as compatibility aliases — `/playlist.m3u`, `/api/playlists/m3u`, `/api/playlists/epg.xml`, `/api/playlists/tv-channels/m3u`, and `/api/playlists/all-streams/m3u` — so IPTV players and XMLTV grabbers configured against v1 do not need to be reconfigured.
- **Curated playlists.** The v1 curated playlists are back with the same semantics: `/api/v1/playlists/tv-channels/m3u` (one entry per TV channel with its assigned streams, quality-ranked, `tvg-chno` numbering) and `/api/v1/playlists/all-streams/m3u` (numbered TV channels followed by unassigned streams from `tvg-chno` 9000). Multi-stream channels are disambiguated as `Name (2)` instead of `Name 2` so they can't be confused with distinct channels, and all streams of a channel keep the channel's own `tvg-id` so EPG mapping stays intact. `refresh=true` on any playlist URL triggers a background rescrape of enabled sources (v1 semantics: fire-and-forget, the playlist itself is served from current data; the trigger is skipped when a scrape is already running).
- **Correlation IDs.** Every request gets an `X-Correlation-ID` (incoming or generated) propagated through logs and into error responses, making operational traces easier to follow.
- **Standard error envelope.** Errors return a consistent shape (`{detail, code, ...}`) across the API surface. Operational failure paths (scrape, EPG refresh, status checks, task lifecycle) emit structured logs.

### Frontend (UX modernization)

- **New app shell.** `AppShell` + `PageHeader` + `ContentSection` give every page the same operational rhythm: clear title, action area, sectioned content. Navigation metadata is centralized in `navItems.tsx`.
- **Refreshed page set.** Dashboard, Acestream channels, TV channels, EPG sources/channels/mappings, Scraper URLs, Settings, Health, Stats, Playlist export, Search, and WARP all standardized around the new primitives.
- **Light + dark theme.** First-class dark mode with `prefers-color-scheme` fallback and `localStorage` persistence. Material UI 5 + IBM Plex Sans, teal/blue primary accents.
- **Reduced motion respected.** Theme honors `prefers-reduced-motion: reduce`.
- **Responsive density.** DataGrid density adapts to viewport; navigation collapses to drawer on narrow screens; keyboard / aria attributes on nav and table actions.
- **Typed API client.** Frontend services are aligned with backend response shapes, including the previously-mismatched `PaginatedAcestreamChannels` model used on the channels page.
- **Vite replaces CRA.** Faster dev startup, hand-tuned bundle splitting (MUI, DataGrid, icons, vendor data libs).

### Multi-architecture deployment

- **Image flavors.** `scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`. `latest` = `scraper-acestream-acexy`.
- **Install / runtime split.** Image flavor controls which optional binaries are *installed*; env flags (`ENABLE_ACESTREAM_ENGINE`, `ENABLE_ACEXY`, `ENABLE_WARP`) control whether they actually *start*. WARP requires `NET_ADMIN` + `SYS_ADMIN` capabilities and refuses to target `localhost:6878` without an in-container engine running.
- **Platform matrix.** Baseline flavors (`scraper`, `scraper-acexy`) build for `linux/amd64`, `linux/arm/v7`, `linux/arm64`. AceStream flavors are gated by `docker/manifests/acestream.json` (currently amd64 only — ARM availability tracks upstream AceStream releases).
- **Android TV deployment notes.** New `docs/architecture/deployment.md` "Android TV Notes" section covers ARM64 preference, ARMv7 caveats, and conservative runtime tuning.

### Reliability and performance

- **Background scheduler hardened.** APScheduler-backed task service with idempotent startup/shutdown, scheduler-backed status (no more in-memory placeholder), and explicit interval registration in `main.py`. Jobs: activity-log cleanup (24h), EPG refresh (1h), URL scraping (15m), channel cleanup (24h), channel status (10m).
- **DB hot-path indexes.** Migration `phase6_add_hotpath_indexes.py` adds 7 indexes on the most-queried columns; idempotent so existing user databases just get the new indexes on first start.
- **Set-based bulk mutations.** Per-record commit/refresh loops in URL/channel updates were replaced by transaction-scoped batch updates. `phase6-db-baseline.json` documents query budgets (e.g., bulk channel activate: 2 queries; refresh-all-URLs: 1 query; idempotent EPG re-import: 4 queries).
- **Operational runbook.** `docs/ops/reliability-runbook.md` is the new starting point for diagnosing stuck tasks, scheduler hangs, or DB lock pressure.

### Security and hardening

- **Optional API token.** Set the `API_TOKEN` environment variable to require a token on every `/api/v1` route and on the player-facing playlist/EPG URLs. Credentials are accepted as `Authorization: Bearer <token>`, `X-Api-Token: <token>`, or `?token=<token>` (the query form exists for IPTV players and XMLTV grabbers that can only be configured with a bare URL). `/api/v1/health` stays public so container health probes keep working. Unset (the default) leaves the API open — the historical trusted-network behavior. For internet exposure, pair it with TLS at a reverse proxy (see `docs/ops/reverse-proxy.md`).
- **Outbound URL guard (SSRF).** Scrape URLs and EPG sources are validated before fetching: only `http`/`https` schemes, and the cloud metadata endpoint (`169.254.169.254`) is always refused. Setting `ALLOW_PRIVATE_SCRAPE_TARGETS=false` additionally blocks destinations resolving to loopback/private/link-local ranges (the configured `ZERONET_URL` host stays exempt). The default is permissive because scraping LAN sources is a first-class self-hosting use case.
- **Reverse proxy / HTTPS guide.** New `docs/ops/reverse-proxy.md` with working nginx, Caddy, and Traefik configs, proxy-level auth patterns for IPTV players, `base_url` interplay, and a per-flavor port-exposure table.
- **Service supervision in the container.** The entrypoint now supervises the AceStream engine and Acexy: a crashed process is restarted after `SUPERVISED_RESTART_DELAY_SECONDS` (default 5), and a crash loop (`SUPERVISED_FAST_EXIT_LIMIT` consecutive exits within `SUPERVISED_FAST_EXIT_WINDOW` seconds) fails the container so orchestrators can act on it.
- **warp-cli compatibility.** WARP status parsing falls back to legacy `warp-cli` subcommands (`account`, `warp-stats`) when the modern ones (`registration show`, `tunnel stats`) are unavailable, so status reporting works across warp-cli generations.
- **Configurable status-check timeouts.** Channel status checks read their timeout from the `acestream_check_timeout` setting (default 10s), the standalone engine probe from `ACESTREAM_STATUS_TIMEOUT`; a timed-out probe is retried once with a doubled timeout before the channel is marked offline, so slow engines stop producing false offline sweeps.

### Playlists

- **Named base URLs.** Base URLs are now stored in the database with a name and a default (`/api/v1/base-urls` CRUD, managed from Settings). A pattern containing `{channel_id}` is rendered as a mask — e.g. `http://host:8080/ace/stream?id={channel_id}&pid={pid}` — while a pattern without placeholders keeps the legacy prefix behavior. Playlist endpoints accept `?base_url_id=<id>` to pick a named entry; an explicit `?base_url=` string still overrides, and existing deployments are seeded with their current `base_url` setting as the default entry so generated links don't change.

### Scraping

- **Bare content-ID harvesting.** A per-URL `scrape_bare_ids` flag (off by default) makes the scraper also collect raw 40-hex acestream IDs from pages that list hashes without the `acestream://` scheme, using the preceding line text as the channel name when present.

### Migration safety net

- **Auto v1→v2 migration.** On startup, if the legacy `acestream.db` exists and isn't yet marked `.migrated`, the data migrator runs in-process and converts it. Subsequent starts skip the migrator. Fresh installs provision the v2 schema via Alembic.
- **Pre-deploy preflight.** `bash scripts/ops/preflight_v2_deploy.sh` backs up your DBs under `config/backups/` and prints SAFE/UNSAFE before v2 boots. UNSAFE runs export your scraped sources to a rescue DB.
- **One-release env compatibility window.** Legacy env names auto-map to canonical equivalents during the `v2-cutover-r1` release window (canonical wins on conflict, with a startup warning):

  | Legacy | Canonical |
  |---|---|
  | `SCRAPER_DB_URL` | `DATABASE_URL` |
  | `LEGACY_DB_URL` | `LEGACY_DATABASE_URL` |
  | `ZERONET_BASE_URL` | `ZERONET_URL` |
  | `CORS_ALLOW_ORIGINS` | `CORS_ORIGINS` |
  | `FRONTEND_STATIC_DIR` | `FRONTEND_BUILD_PATH` |
  | `ACESTREAM_ENGINE_URL` | `ACE_ENGINE_URL` |

  Disable explicitly with `ENABLE_LEGACY_ENV_ALIASES=false`. **The compat shim is removed in the next release** — please move to canonical names.

### Test ownership and CI

- **Canonical test homes.** Backend tests live at `backend/tests/` (with `contracts/`, `parity/`, `regression/`, `architecture/`, `perf/` subtrees); frontend tests at `frontend/src/__tests__/`.
- **Single canonical runner.** `bash scripts/ci/run_v2_test_suite.sh --profile {quick,full}` is the one entry point.
- **Strict legacy guard.** `bash scripts/ci/assert_no_legacy_paths.sh --strict` blocks reintroduction of retired root paths.
- **Cutover checks.** `bash scripts/ci/run_cutover_required_checks.sh --profile quick` for fast pre-deploy validation.
- **Phase gates.** Phase-1 parity safety gates and multi-arch quick (dry-run) profile run on every PR via the canonical pipelines (`Jenkinsfile` and `.github/workflows/pull_request.yml`). Full multi-arch profile runs on the manual `Release Pipeline` (`workflow_dispatch`) and on Jenkins `acestream-scraper-release`.
- **Jenkins.** Canonical PR validation pipeline (`Jenkinsfile`) and manual release pipeline (`jenkins/release.Jenkinsfile`, sole publisher); `.github/workflows/release.yml` is now a manual validation-only mirror.

---

## Breaking changes

These are intentional. v2 is allowed to break v1 compatibility per project scope.

- **API contract is new.** v1 endpoints/payloads are not preserved 1:1. Clients should use the OpenAPI schema at `/docs` or the typed clients in `frontend/src/services/`.
- **Frontend routes redesigned.** Old bookmarks may not resolve; the SPA includes a `LegacyRouteRecovery` component that redirects common legacy paths.
- **Legacy entrypoints removed.** `wsgi.py`, `run_dev.py`, `manage.py`, root `app/`, and root `migrations/` no longer exist. Any third-party tooling that referenced them must move to `backend/main.py` (Uvicorn).
- **Frontend toolchain switched.** CRA → Vite. Build command is `npm run build` (or `npm run build:backend` to copy `dist/` into `backend/frontend_build/`). Dev command is `npm start`.
- **Container env model split.** Image flavor sets which optional binaries are installed; runtime env flags decide whether they start. Old "everything always on" assumptions don't hold — set the flags you actually want.

---

## Upgrade path

1. **Stop the v1 container.**
2. **Run preflight:** `bash scripts/ops/preflight_v2_deploy.sh`. Confirm SAFE; review the rescue export if UNSAFE.
3. **Pull the v2 image** (`pipepito/acestream-scraper:latest` for the full `scraper-acestream-acexy` flavor) or the explicit flavor you want.
4. **Update env vars** to canonical names (legacy aliases still work this release; warnings in startup logs flag any conflicts).
5. **Start the new container.** First boot runs the in-process v1→v2 data migration if a legacy DB is present, then provisions any new schema via Alembic.
6. **Verify** by hitting `/api/v1/health` and the SPA root.

If anything looks wrong, the v1 DB backup under `config/backups/<timestamp>/` is your rollback point — point a v1 image at it and you're back where you started.

---

## Pre-tag gap-closure pass (gap-closure-v2 branch)

The `v2-release-readiness.md` audit identified two release blockers and a
basket of hardening items. All are closed before tag. Headline changes:

- **Test harness redesign.** The previous `backend/tests/conftest.py` cleared
  and reloaded `app.*` modules per fixture, splitting SQLAlchemy's mapper
  registry and crashing `test_epg.py` (and previously `test_scrapers.py`,
  `test_error_contracts.py`) with `expression 'AcestreamChannel' failed to
  locate a name`. Replaced with FastAPI's standard dependency-override
  pattern: lazy engine in `app/config/database.py`, `lifespan` context
  manager in `main.py` (also retiring the deprecated `@app.on_event`
  hooks), no module reload. Backend suite went 354 → 364 passed, 0 failed.
- **Real multi-arch runtime smoke before publish.** `release.yml` now
  requires a `multiarch-runtime-smoke` job (full Phase-5 profile, real
  QEMU build + boot + `/api/v1/health` probe per ARM platform) before
  `build-image` runs. PRs touching `Dockerfile`/`docker/`/multiarch
  scripts/entrypoint scripts auto-trigger the same job. Stale checked-in
  `phase5-build-result-*.json` snapshots removed; evidence now lives on
  the workflow run and `docs/release/phase5-multiarch-evidence.md`
  records it per release SHA.
- **Timezone-aware datetimes throughout.** Replaced 25 `datetime.utcnow()`
  call sites with `datetime.now(timezone.utc)`. Added a `UtcDateTime`
  SQLAlchemy `TypeDecorator` so reads always return tz-aware datetimes
  (SQLite's native naive-only behavior is normalized at the ORM
  boundary). New Alembic migration aligns column types. `_parse_xmltv_time`
  in `epg_service.py` now returns aware UTC so EPG re-import idempotency
  matches values reloaded from the DB.
- **Pydantic v2 config across all schemas.** Twelve `class Config:` v1
  blocks converted to `model_config = ConfigDict(...)` (v3-ready).
- **OpenAPI codegen drift gate.** `npm run codegen` regenerates
  `frontend/src/types/api-generated.ts` from a fresh `backend/openapi.json`;
  CI fails the suite if the result diverges from the committed file.
  Existing services in `frontend/src/services/` consume the generated
  types gradually post-release; the gate ensures any future schema
  change is paired with a regeneration commit.
- **Frontend lint + typecheck gates.** Added ESLint baseline (TS, React,
  React Hooks, jsx-a11y, testing-library) plus `tsc --noEmit` typecheck.
  Both run before Jest in `run_v2_test_suite.sh`. Lint baseline: 0
  errors, 0 warnings — enforced in CI with `--max-warnings=0`.
- **Legacy alias expiry gate.** `LEGACY_ENV_ALIAS_WINDOW = "v2-cutover-r1"`
  is now enforced by a CI test that reads `version.txt` and fails the
  build the moment the project version reaches v2.1.0 with the alias
  shim still present. The shim's removal can no longer slip past a
  release silently.
- **Repo cleanup.** Stray dev scripts (`check_epg_data.py`,
  `force_epg_refresh.py`, `test_epg_xml.py`, `test_epg_time.py`) moved
  to `scripts/dev/epg/`. Legacy Flask-era root `tests/` tree retired
  (everything imported `from flask import Flask` and the canonical
  test runner had stopped invoking it). `version.txt` bumped to v2.0.0.

## Known issues

- ~~Frontend lint warning baseline~~ — resolved: the lint baseline is now
  zero warnings and CI enforces it with `--max-warnings=0`.
- AceStream-bearing flavors (`scraper-acestream`, `scraper-acestream-acexy`,
  `latest`) currently publish for `linux/amd64` only because upstream
  AceStream binaries are amd64-only. ARM availability tracks upstream
  releases; the playbook for enabling ARM lives in
  `docs/ops/multiarch-manifest-updates.md`.
- Cloudflare WARP (`warp-cli`) is only packaged for amd64 upstream, so the
  `linux/arm/v7` and `linux/arm64` images ship without it. Setting
  `ENABLE_WARP=true` on an ARM image fails at startup with a clear error.

---

## Acknowledgements

The v2 consolidation was executed across six planned phases (parity baselines → contract hardening → cutover → UX modernization → multi-arch → reliability/optimization). Phase artifacts and evidence live under `.planning/phases/` and `docs/release/`.
