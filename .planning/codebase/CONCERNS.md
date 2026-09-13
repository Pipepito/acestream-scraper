# Codebase Concerns

**Audit date:** 2026-09-03

**Branch audited:** `develop` at `e5bc9e0`

**Release PR snapshot:** PR #162, `develop` -> `main`, open and mergeable with green reported checks at audit time

This is a risk map, not a claim that every item is currently failing. Re-check branch and CI state before acting because `develop` is a moving pre-release branch.

## Highest-Priority Risks

### P0/P1: release PR blast radius is exceptionally large

- PR #162 is the v1-to-v2 release cutover, not a routine increment: `main...develop` spans about 220 commits, 779 changed files, roughly 108k additions and 113k deletions.
- The diff replaces the Flask/root runtime with FastAPI under `backend/`, a React/Vite SPA under `frontend/`, new database migrations, a multi-stage/multi-platform image, a new supervisor, and Jenkins-owned release automation in one merge.
- Git reports the branch as mergeable and Jenkins reports success, but the PR has no recorded review decision at this audit point. Green automation cannot make this size human-reviewable as one unit.
- Treat merge as a release event. Require database backup/restore rehearsal, an upgrade using a realistic v1 database, container smoke tests, manual UI journeys, and an explicit rollback owner before merging.
- Relevant paths: `backend/migrate_database.py`, `backend/migrations/`, `Dockerfile`, `entrypoint.sh`, `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `docs/release/v2-release-readiness.md`.

### P1: Jenkins is a single CI and publication control plane

- Repository-owned GitHub Actions validation workflows were removed; PR validation and releases now depend on one self-hosted Jenkins executor selected by the `dorat-nuc-ci` label.
- The build node is stateful and disk-constrained. `Jenkinsfile` includes aggressive Docker image/cache pruning and a retry for known cache corruption/ENOSPC behavior.
- PR, pre-release image, wiki, and Pages publication all flow through the same pipeline. A runner/controller outage blocks validation and publishing; a compromised runner has access to publication credentials.
- The Jenkins status link reported to GitHub exposes internal deployment topology. Avoid publishing private controller addresses in public status metadata; front Jenkins with an appropriate safe URL or omit deep links.
- Keep the workstation rollback procedure current and periodically execute it. Relevant paths: `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/cleanup_runner_docker.sh`, `docs/ops/jenkins-ci.md`.

### P1: optional security defaults are permissive

- `API_TOKEN` is optional. When unset, every administrative API route is open, including configuration changes, WARP control, source management, scraping, and supervised service restarts.
- `ALLOW_PRIVATE_SCRAPE_TARGETS` defaults to true for self-hosted/LAN use. This intentionally allows requests to private and loopback networks (except explicitly blocked metadata addresses).
- This combination is acceptable only behind a trusted network boundary. Any internet/reverse-proxy deployment should set a strong API token, enable strict outbound target blocking, restrict CORS, and terminate HTTPS.
- Relevant paths: `backend/app/api/auth.py`, `backend/app/utils/url_guard.py`, `backend/app/config/settings.py`, `docs/ops/reverse-proxy.md`.

## Security and Privacy

### API token exposure paths

- IPTV/XMLTV clients may send `?token=...`; query parameters commonly enter proxy access logs, browser history, monitoring, referrer data, and support captures.
- The SPA stores the API token in `localStorage`, so any same-origin script execution/XSS can read it. There is no per-user identity, role separation, expiry, or revocation beyond changing the single shared environment token.
- Prefer header credentials for interactive/API clients, redact query strings in all proxy/app logs, keep the UI origin tightly controlled, and document shared-token rotation.
- Relevant paths: `backend/app/api/auth.py`, `frontend/src/services/apiToken.ts`, `frontend/src/services/apiClient.ts`.

### SSRF guard is hardening, not isolation

- Strict mode resolves a host for validation but the HTTP client resolves it again when connecting, leaving a documented DNS-rebinding/time-of-check-to-time-of-use gap.
- The configured ZeroNet and IPFS gateway hosts are exempt in strict mode. A compromised or misconfigured local gateway remains a pivot.
- Redirect validation is present for normal HTTP and EPG fetches, but future fetch code must use `validate_outbound_url()` on the initial URL and every redirect.
- Network-level egress restrictions are still required for hostile/multi-user deployments. Relevant paths: `backend/app/utils/url_guard.py`, `backend/app/scrapers/http.py`, `backend/app/services/epg_service.py`.

### Unbounded remote content can exhaust memory/CPU

- Scrapers call `response.text()` and the EPG path buffers `response.content`; there is no response byte cap.
- Gzipped EPG data is fully decompressed with `gzip.decompress()`, then parsed in-memory with `xml.etree.ElementTree.fromstring()`. A large response or compression bomb can exhaust the process.
- Add compressed and decompressed size limits, stream downloads, reject excessive XML depth/counts, and expose metrics for fetched bytes and parse duration.
- Relevant paths: `backend/app/scrapers/http.py`, `backend/app/scrapers/ipfs.py`, `backend/app/scrapers/zeronet.py`, `backend/app/services/epg_service.py`.

### Logs and API errors may disclose operational data

- Scraper and EPG services log full source URLs and sometimes preview remote response bodies. URLs can contain private hostnames, tokens, or user data; response previews are attacker-controlled.
- Several endpoints/services return raw exception text in API responses. Filesystem paths, dependency errors, or upstream details can escape to clients.
- WARP commands are logged in full at debug level; license registration passes the license as a command argument, so enabling debug logging can persist the secret. Some command stderr is also returned to the caller.
- Introduce centralized URL/query redaction and public error mapping. Special-case secret-bearing command arguments before logging. Relevant paths: `backend/app/services/scraper_service.py`, `backend/app/services/epg_service.py`, `backend/app/services/warp_service.py`, `backend/main.py`.

### Local infrastructure details require stronger handling

- `infra-details.md` is correctly ignored by Git, and `.claude/jenkins-api.sh` is also ignored. They must remain local operator inputs and must never be quoted, copied into agent docs, committed, pasted into issues, or included in screenshots/log bundles.
- The local details file is currently readable beyond its owner under normal Unix permissions. Restrict it to owner-only access and prefer a password manager or OS keychain for credentials.
- `.gitignore` prevents future tracking but does not prove the data never entered Git history or another artifact. Run secret scanning on history and CI artifacts, and rotate any credential whose handling is uncertain.
- Relevant policy locations: `.gitignore`, `docs/ops/jenkins-ci.md`. Do not add the sensitive values themselves to repository documentation.

### Privileged sidecar controls expand impact

- WARP-enabled containers require elevated Linux capabilities and `/dev/net/tun`; the API can also restart supervised AceStream, Acexy, IPFS, ZeroNet, and WARP processes.
- If optional auth is disabled or bypassed, an HTTP caller can mutate network state or disrupt sidecars.
- Keep WARP opt-in, avoid exposing the management API publicly, and use the minimum container capabilities per flavor. Relevant paths: `docker-compose.yml`, `entrypoint.sh`, `backend/app/api/endpoints/system.py`, `backend/app/api/endpoints/warp.py`.

## Operational and Reliability Concerns

### Scheduler and API share one process

- APScheduler runs inside the Uvicorn lifespan. Long scrape, status, cleanup, migration, and EPG work competes with API request handling and the SQLite writer.
- Scheduler state is in memory. Restarts lose run/error history and one-off scheduling state (the deferred migration has its own checkpoint, but ordinary task state does not).
- Running multiple Uvicorn/Gunicorn workers would start one scheduler per process and can duplicate maintenance jobs; there is no distributed leader lock. Current Docker commands use one Uvicorn worker and should remain single-worker until scheduling is externalized.
- Relevant paths: `backend/main.py`, `backend/app/services/task_service.py`, `backend/app/tasks/`.

### SQLite is the scaling and contention boundary

- The application, scheduler, and serial E2E suite deliberately share one SQLite database. `check_same_thread=False` permits cross-thread use but does not remove single-writer contention.
- No explicit WAL/busy-timeout configuration is applied in `_build_engine()`. Large EPG refreshes, scrapes, status updates, and UI writes can contend or raise lock errors under load.
- Do not horizontally scale the API against one SQLite file. If concurrency grows, first add lock/contention telemetry and transaction-duration measurements, then move scheduled work and consider a server database.
- Relevant paths: `backend/app/config/database.py`, `backend/app/services/epg_service.py`, `e2e/playwright.config.ts`.

### Startup still mutates production data

- Every application start checks legacy migration state, may run the foreground v1 migration, stamps an existing unstamped database, repairs nullable flags, and schedules deferred EPG migration.
- The deferred copy is checkpointed and the release runbooks require backups, but startup-time mutation increases the consequence of a bad image or incorrect mounted path.
- Preserve backup/preflight gates, test interrupted/resumed upgrades with production-shaped data, and never point an experimental checkout at the only database copy.
- Relevant paths: `backend/main.py`, `backend/migrate_database.py`, `backend/app/config/database.py`, `scripts/ops/preflight_v2_deploy.sh`.

### Sidecar supervision is coupled to shell conventions

- Runtime health and restart depend on PID/start files written by `entrypoint.sh` under `SUPERVISOR_RUN_DIR`. Changes to process launch, listen addresses, pidfile names, or container users can make a live process appear unmanaged/unhealthy.
- Several bundled services have platform-specific absence or limitations: no Kubo/WARP on ARMv7, version-skewed Android AceStream engines on ARM, and no real ARMv7 runtime smoke.
- Preserve the image-flavor/runtime-feature distinction and update probes, healthcheck, entrypoint, manifests, tests, and docs together.
- Relevant paths: `entrypoint.sh`, `healthcheck.sh`, `backend/app/services/system_services_service.py`, `docker/manifests/`.

### Moving `develop` tags are not rollback artifacts

- Jenkins republishes floating `develop` flavor tags after validated branch/release-PR builds. They have no immutable per-commit companion tag.
- A tester cannot reliably pull yesterday's known-good `develop` image after the tag moves. Record image digests in evidence and deploy by digest when reproducibility matters.
- Release `latest` promotion is deliberately two-phase; do not bypass the canary/version-tag step. Relevant paths: `Jenkinsfile`, `scripts/ci/run_jenkins_release.sh`, `scripts/ci/promote_latest.sh`.

## Performance and Maintainability

### Large modules remain change hotspots

- `backend/app/services/epg_service.py` is about 810 lines and mixes CRUD, refresh/fetch, XML parsing, matching, retention, and serialization.
- Other hotspots include `backend/app/repositories/channel_repository.py`, `backend/app/services/warp_service.py`, `frontend/src/pages/Settings.tsx`, `frontend/src/pages/Scraper.tsx`, and `frontend/src/components/TVChannelsTable.tsx`.
- Some large frontend pages were split successfully, but continued extraction should follow cohesive use cases rather than line-count-only refactors. Add focused tests before moving transaction or scheduler boundaries.

### EPG matching and generation load full tables

- Several EPG flows use unbounded `.all()` queries for TV channels, EPG channels, mappings, or programs and perform Python-side matching/serialization.
- This is manageable for a personal instance but grows with feed size and number of sources. Pagination exists for UI inventory, not for every background/output path.
- Profile with production-shaped feeds; batch/stream exports, narrow queries, and keep the hot-path index regression tests representative.
- Relevant paths: `backend/app/services/epg_service.py`, `backend/app/services/playlist_service.py`, `backend/tests/perf/test_high_churn_db_paths.py`.

### Dependency and packaging definitions have drifted

- Root `requirements.txt` still carries Flask-era dependencies and conflicting SQLAlchemy constraints while the active runtime uses `backend/requirements.txt` and FastAPI.
- Most Python requirements use lower bounds rather than an application lock, so clean Jenkins builds can resolve newer transitive versions over time.
- Root `pyproject.toml` declares a nonexistent `src/acestream_scraper` package, a stale version, placeholder project URL, and Flask-era dependencies; it is not an accurate install path.
- Choose one authoritative Python dependency/packaging story, remove dead Flask dependencies, and use a reproducible lock/constraints process for release builds.
- Relevant paths: `requirements.txt`, `requirements-prod.txt`, `requirements-dev.txt`, `backend/requirements.txt`, `pyproject.toml`.

### Vendored runtime payloads increase repository and supply-chain burden

- `docker/vendor/` is roughly 241 MiB and contains third-party engine/APK, bionic, and Acexy archives. This makes clones/history heavy and requires deliberate license, provenance, vulnerability, and checksum maintenance.
- SHA checksum validation protects integrity against accidental substitution but is not authenticity or vulnerability scanning.
- Keep update procedures and upstream provenance current, scan payloads where tooling permits, and consider release assets/LFS if repository growth becomes costly.
- Relevant paths: `docker/vendor/`, `docker/manifests/`, `docker/scripts/install-acestream.sh`.

### Stale developer utilities can mislead agents

- `scripts/dev/epg/` still imports the retired Flask application factory, extensions, and old model/repository modules. These scripts will fail or encourage work against the deleted architecture.
- `backend/run_tests.py` contains hand-maintained endpoint/test inventories and messaging that can drift from canonical pytest/CI commands.
- Delete or port stale scripts and ensure agent instructions point to `scripts/ci/run_v2_test_suite.sh` plus the focused pytest/Jest commands.

## Test and Release Gaps

### Full Playwright journey is not a required Jenkins stage

- The E2E suite exercises the built SPA with live AceStream, Acexy, IPFS, public EPG, and search integration, but `Jenkinsfile` does not run `e2e/`.
- Jenkins runs unit/contract/cutover gates and focused Docker engine/Acexy smoke tests. A green `PR Validation` check therefore does not prove the end-user multi-page journey.
- The suite is serial, stateful across ordered specs, Firefox-only by default, has zero retries, and depends on external/public data. This is valuable release evidence but also potentially flaky and slow.
- Before merging PR #162, run it against the candidate image, archive the HTML/JUnit evidence, and record any approved scenario exceptions. Relevant paths: `e2e/README.md`, `e2e/playwright.config.ts`, `e2e/tests/`, `Jenkinsfile`.

### Cross-platform runtime evidence is uneven

- Multi-arch PR checks validate build plans/manifests and run real engine smoke on amd64 (or arm64 when on such a host), but ARMv7 only receives install/layout validation under emulation.
- The repository explicitly marks ARMv7 engine support experimental and untested on real hardware. Do not interpret manifest presence as runtime proof.
- Capture physical-device smoke evidence before promoting support status. Relevant paths: `Jenkinsfile`, `docker/manifests/acestream.json`, `docs/ops/acestream-arm-engine.md`.

### Generated contracts and built assets can become stale locally

- `frontend/src/types/api-generated.ts` is generated from `backend/openapi.json`; both must be regenerated when API schemas change.
- `backend/frontend_build/`, local databases, logs, Playwright results, and node modules are ignored but can remain in a working tree and make a manual run appear to test newer code than it does.
- Use the codegen/drift gates and rebuild the SPA before screenshots or release evidence. Never infer Git cleanliness from ignored runtime artifacts.

## Safe Change Checklist

- Keep `infra-details.md` and all derived credentials/URLs out of commits, prompts, logs, screenshots, and generated agent documentation.
- For API or schema work: update tests, dump `backend/openapi.json`, regenerate frontend types, and run backend plus frontend gates.
- For Docker/service work: update `Dockerfile`, `entrypoint.sh`, health probes, manifests, flavor tests, command-builder data, and operator docs as one contract.
- For migration/startup work: operate on copies, rehearse interruption/resume, verify backup restoration, and retain the previous image digest.
- For PR #162: treat current green checks as necessary but not sufficient; add human review and full E2E/candidate-upgrade evidence immediately before merge.

---

*Update this document when the release PR merges, security defaults change, the scheduler/database architecture changes, or Jenkins/E2E coverage changes.*
