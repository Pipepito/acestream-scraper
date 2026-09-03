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
- **Platform matrix.** All four flavors build for `linux/amd64`, `linux/arm/v7`, `linux/arm64`. AceStream flavors are gated by `docker/manifests/acestream.json`, which declares every platform with a `support` level: `linux/amd64` and `linux/arm64` are **stable**, `linux/arm/v7` is **experimental**.
- **AceStream engine on ARM.** `scraper-acestream`, `scraper-acestream-acexy` and `latest` ship an engine on `linux/arm64` and `linux/arm/v7`. The previous official ARM64 3.1.80 payload required a premium license, so ARM64 now uses the non-premium-gated Android engine 3.2.17 packaged by [`jopsis/acestream:v3.2.17-fix`](https://hub.docker.com/r/jopsis/acestream) ([build sources](https://github.com/jopsis/docker-acestream-aceserve)). The Dockerfile consumes it as a build stage pinned to multi-arch digest `sha256:506c4215115d8b0ac1e24f4c67c954f0dbf86e4b4ea508582e497d8c920e9933`, copies only the engine and bionic runtime into the project image, and replaces its bootstrap with this project's persistent, per-install Linux bridge. ARMv7 remains on the official 3.1.80 APK and is experimental. No chroot, `--privileged`, seccomp profile or extra capabilities are needed. The dashboard shows the engine-reported version and a linked `jopsis/acestream v3.2.17-fix` package attribution. The engine stays opt-in (`ENABLE_ACESTREAM_ENGINE=false` by default); persist engine state, cache and logs with `-v acestream-state:/var/lib/acestream`. ARM caveats are listed under "Known issues". Operator guide: `docs/ops/acestream-arm-engine.md`; manifest schema and pin-update procedure: `docs/ops/multiarch-manifest-updates.md`.
- **Separate Python pins for the app and the engine.** The `Dockerfile` exposes `ARG APP_PYTHON_VERSION=3.13` (the FastAPI app's interpreter, so the `scraper` flavors can track new CPython releases) and `ARG ACESTREAM_ENGINE_PYTHON_VERSION=3.10` (the x86_64 engine's interpreter, pinned by `install.python_version` in `docker/manifests/acestream.json`; the Android engine on ARM ships its own CPython 3.8).
- **Real Acexy in the acexy flavors.** The `scraper-acexy` and `scraper-acestream-acexy` images now compile the upstream Acexy proxy pinned in `docker/manifests/acexy.json` (0.2.2). Previously no build path passed the manifest's `ACEXY_REPO`/`ACEXY_REF` args, so the images silently shipped the build-test stub. A runtime smoke (`backend/tests/docker/test_acexy_runtime_smoke.py`) now gates the Jenkins PR pipeline on the real proxy answering `/ace/status`.
- **Android TV deployment notes.** New `docs/architecture/deployment.md` "Android TV Notes" section covers ARM64 preference, ARMv7 caveats, and conservative runtime tuning.

### Reliability and performance

- **Background scheduler hardened.** APScheduler-backed task service with idempotent startup/shutdown, scheduler-backed status (no more in-memory placeholder), and explicit interval registration in `main.py`. Jobs: activity-log cleanup (24h), EPG refresh (1h), URL scraping (15m), channel cleanup (24h), channel status (10m).
- **DB hot-path indexes.** Migration `phase6_add_hotpath_indexes.py` adds 7 indexes on the most-queried columns; idempotent so existing user databases just get the new indexes on first start.
- **Set-based bulk mutations.** Per-record commit/refresh loops in URL/channel updates were replaced by transaction-scoped batch updates. `phase6-db-baseline.json` documents query budgets (e.g., bulk channel activate: 2 queries; refresh-all-URLs: 1 query; idempotent EPG re-import: 4 queries).
- **Operational runbook.** `docs/ops/reliability-runbook.md` is the new starting point for diagnosing stuck tasks, scheduler hangs, or DB lock pressure.
- **Rotating application log.** The file log (`backend/app/utils/logging.py`) uses a `RotatingFileHandler`: `LOG_FILE_MAX_BYTES` (default 10 MiB) and `LOG_FILE_BACKUP_COUNT` (default 3) bound disk usage instead of growing a single file forever.
- **Container healthcheck covers the engine.** `healthcheck.sh` probes `/api/v1/health`, then — when enabled — the in-container engine through `/webui/api/service?method=get_version` (the one lightweight endpoint both the native 3.2.x and the Android engine serve) and Acexy through `/ace/status`. The CI engine smoke runs the image's own healthcheck per platform so the `HEALTHCHECK` contract is tested, not just declared.

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

- **Auto v1→v2 migration.** On startup, if the legacy `acestream.db` exists and isn't yet marked `.migrated`, the data migrator runs in-process and converts it in two phases: the schema and the small tables (URLs, sources, channels, string mappings, settings) are migrated before the first request (seconds), then `acestream.db` is archived as `acestream.db.migrated` and the EPG programs that have not ended yet (see `EPG_PROGRAM_RETENTION_HOURS`) are copied by the background task `v1_epg_programs_migration` while the dashboard is already usable (progress on the dashboard's *Background Tasks* card; state in `acestream.db.migration.json`; the copy resumes after a restart). Subsequent starts skip the migrator. Fresh installs provision the v2 schema via Alembic, and v1-migrated databases are stamped with the Alembic head as well.
- **EPG program retention.** The new hourly `epg_program_cleanup` job deletes programs that ended more than `EPG_PROGRAM_RETENTION_HOURS` ago (default 24; negative disables), so the `epg_programs` table no longer grows forever.
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
- **Phase gates.** Phase-1 parity safety gates, the Phase-3 cutover quick gate and the multi-arch quick (dry-run) profile run on every PR via the Jenkins PR pipeline (`Jenkinsfile`). The release path runs the cutover **full** profile (`bash scripts/ci/run_cutover_required_checks.sh --profile full`) plus a four-flavor dry-run build/manifest preflight; the heavier Phase-5 full profile (`python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output`, QEMU boot of the ARM app images) is a manual run recorded in `docs/release/phase5-multiarch-evidence.md`.
- **Jenkins.** All CI lives on Jenkins: the PR validation pipeline (`Jenkinsfile`, multibranch job `acestream-scraper-pr`, reported to GitHub as the single required `PR Validation` status) and the manual release pipeline (`jenkins/release.Jenkinsfile`, job `acestream-scraper-release`, sole publisher of release tags; runs only from `main`). The GitHub Actions workflows have been retired (2026-08-26). Operator guide: `docs/ops/jenkins-ci.md`.
- **Branch model and `develop` pre-release channel.** `develop` is the permanent pre-release branch and `main` the release branch: feature PRs target `develop`, releases are cut with a `develop` → `main` PR, and both branches are protected (PRs only, required `PR Validation` status). The PR pipeline's `Branch Policy` stage rejects any PR into `main` whose head is not `develop`. Every validated `develop` build then publishes floating pre-release tags — `pipepito/acestream-scraper:develop` (the full `scraper-acestream-acexy` payload) and `:develop-scraper`, `:develop-scraper-acestream`, `:develop-scraper-acexy`, `:develop-scraper-acestream-acexy` — for `linux/amd64`, `linux/arm64` and `linux/arm/v7` (`Publish develop channel` stage → `bash scripts/ci/run_jenkins_release.sh --channel develop`). Channel tags move on every build and never include a version tag or `:latest`; to try a pre-release, pull `pipepito/acestream-scraper:develop` or set `image: pipepito/acestream-scraper:develop` in `docker-compose.yml`. After v2.0.0, `version.txt` on `develop` carries the next version with a `-dev` suffix and the release script refuses to publish a release from it until the release PR bumps the version.
- **Runtime smoke on every PR and every publish.** The `Acestream Engine Runtime Smoke` stage builds `scraper-acestream` for the runner's platform and runs `backend/tests/docker/test_acestream_runtime_smoke.py` (engine boots, `get_version` matches the manifest, healthcheck passes), `test_acexy_runtime_smoke.py` (the real proxy answers `/ace/status`), and both ARM installer layout tests (`android_apk_install_layout` plus `arm64_oci_image_install_layout`). `scripts/ci/run_jenkins_release.sh` repeats the same checks before any tag is pushed.
- **Reproducible engine inputs.** The amd64 and ARMv7 engine archives and bionic packages are vendored in `docker/vendor/` (with `SHA256SUMS`) and mirrored on the `acestream-binaries-3.2.11-3.1.80.0` GitHub Release. ARM64's `jopsis/acestream` source is an immutable OCI digest, so it requires Docker Hub access on a cold build but cannot drift. Cloudflare WARP on the CI runner is opt-in (`JENKINS_ENABLE_WARP=1`) and non-fatal. Smoke images are tagged per `BUILD_TAG` and removed after each build; `scripts/ci/cleanup_runner_docker.sh` sweeps transient CI images so the shared runner does not run out of disk.
- **Two-phase publish.** The release pipeline exposes a `PUBLISH_LATEST` boolean (default off). The first publish of a new version pushes versioned + flavor-channel tags only (`:v2.0.0`, `:scraper-acestream-acexy`, `:v2.0.0-scraper-acestream-acexy`, plus the partial flavors); a follow-up run with `PUBLISH_LATEST=true` promotes the canary-validated `:v2.0.0` manifest to `:latest` by retagging it (`scripts/ci/promote_latest.sh`), never by rebuilding.

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
  *(Superseded on 2026-08-26: `release.yml` and the other GitHub Actions
  workflows were retired; Jenkins is the sole CI. The equivalent gates are
  the `Acestream Engine Runtime Smoke` stage in `Jenkinsfile` and the
  pre-publish smoke in `scripts/ci/run_jenkins_release.sh` — see "Test
  ownership and CI" above. The QEMU boot of the ARM app images is the
  manual Phase-5 full profile, not a pipeline stage.)*
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
- ~~AceStream-bearing flavors (`scraper-acestream`, `scraper-acestream-acexy`,
  `latest`) publish for `linux/amd64` only~~ — superseded on 2026-08-27 by
  branch `arm-acestream-engine`: these flavors now publish for `linux/arm64`
  (stable) and `linux/arm/v7` (experimental) using Android engine payloads.
  ARM64 uses the digest-pinned `jopsis/acestream` 3.2.17 distribution because
  the official 3.1.80 ARM64 build is premium-gated. Remaining ARM caveats:
  - Engine version skew: ARM64 runs 3.2.17, ARMv7 runs 3.1.80 (both report
    `"platform":"android"`), and amd64 runs 3.2.11.
  - `linux/arm/v7` builds and installs but has not been runtime-tested: the
    32-bit bionic engine cannot execute under qemu-user
    (`personality(PER_LINUX32)`), so it needs real ARMv7/AArch32-capable
    hardware.
  - No WebRTC transport on ARM (`pywebrtc` needs Android GPU/audio libs; the
    engine logs a non-fatal error), and a few CPython accelerator modules
    fall back to pure Python.
  - The Android 9 bionic linker needs a 4 KB-page kernel;
    `/opt/acestream/start-engine` refuses to start otherwise (Raspberry Pi 5:
    set `kernel=kernel8.img` in `config.txt`).
  - Streaming performance and stability have not been validated on real ARM
    hardware yet (plan in `docs/release/arm-acestream-issue-draft.md`).
  - AceStream is proprietary and the jopsis repository publishes no explicit
    license for its packaging code. Its Docker Hub page and public build
    source are attributed in the manifest, dashboard, and operator guide;
    redistribution still requires project-owner review before release.

  - CI runs the Android engine only where the host can execute it: the
    amd64 Jenkins runner covers the ARM installer layout through QEMU builds,
    and the ARM64 engine runtime smoke runs only on an ARM64 host (recorded
    locally in `docs/release/phase5-multiarch-evidence.md`).

  Engine pins are updated per `docker/vendor/acestream/README.md`; the
  operator guide is `docs/ops/acestream-arm-engine.md`.
- Cloudflare WARP (`warp-cli`) is only packaged for amd64 upstream, so the
  `linux/arm/v7` and `linux/arm64` images ship without it. Setting
  `ENABLE_WARP=true` on an ARM image fails at startup with a clear error.

---

## Acknowledgements

The v2 consolidation was executed across six planned phases (parity baselines → contract hardening → cutover → UX modernization → multi-arch → reliability/optimization). Phase artifacts and evidence live under `.planning/phases/` and `docs/release/`.
