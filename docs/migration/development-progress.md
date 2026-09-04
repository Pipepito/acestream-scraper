# Development Progress

## Status Snapshot

- **Date:** 2026-08-28 (previous snapshot of 2026-04-24 kept below as superseded)
- **Current Milestone:** v2.0.0 release preparation — PR #162 (`develop` → `main`)
- **Current Phase:** Phases 1–6 complete; remaining work is release-job operator setup, ARM engine hardware validation, and documentation reconciliation

## Completed Phases

- [x] Phase 1: Parity baseline and safety gates — `scripts/phase_gates/phase1_gate_runner.py --profile quick` runs on every PR (`Jenkinsfile`, stage `Phase 1 Safety Gates`).
- [x] Phase 2: Backend contract and structure hardening — typed DTOs, layer-boundary guard (`backend/tests/architecture/test_layer_boundaries.py`), error envelope + correlation IDs, Pydantic v2 `model_config` everywhere.
- [x] Phase 3: v2-only cutover and legacy retirement — evidence in `docs/release/phase3-cutover-evidence.md`; `scripts/ci/assert_no_legacy_paths.sh --strict` guards regressions.
- [x] Phase 4: Frontend UX modernization — `AppShell` / `PageHeader` / `ContentSection`, light + dark theme with reduced-motion support, ESLint + `tsc --noEmit` gates at zero warnings; stack modernized to `@tanstack/react-query` v5, TypeScript 5 and Vite (`8051317`, #154); oversized `EPG.tsx` / `TVChannels.tsx` split into components and hooks (`a911df5`, #153). Review evidence: `docs/dev/frontend-design-review-evidence.md`.
- [x] Phase 5: Multi-arch build and runtime validation — the four image flavors (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy` = `latest`) build for `linux/amd64`, `linux/arm64` and `linux/arm/v7`; both ARM engine variants now come from digest-pinned jopsis 3.2.17 (`linux/arm64` stable, `linux/arm/v7` experimental, per `docker/manifests/acestream.json`). Evidence contract: `docs/release/phase5-multiarch-evidence.md`; operator guide: `docs/ops/acestream-arm-engine.md`.
- [x] Phase 6: Reliability, test ownership, and optimization — canonical test homes (`docs/testing/test-ownership-matrix.md`), single runner `scripts/ci/run_v2_test_suite.sh`, hot-path indexes and query budgets (`docs/performance/phase6-db-benchmarks.md`, `backend/tests/perf/`), reliability runbook (`docs/ops/reliability-runbook.md`), in-container process supervision for the engine and Acexy (`f2caafa`, #119), rotating application log (`backend/app/utils/logging.py`, `LOG_FILE_MAX_BYTES` / `LOG_FILE_BACKUP_COUNT`).

## Phase 3 Plan Progress

- [x] 03-01: Root ownership promotion + strict cutover CI guards
- [x] 03-02: Legacy retirement guardrails + env compatibility bridge delivered; documentation reconciliation remains in progress
- [x] 03-03: Branch cutover checklist and final verification

## CI And Release Path (current)

- Jenkins is the only CI. The GitHub Actions workflows were retired on 2026-08-26 (`e5657b9`); `.github/workflows/` no longer exists. Operator guide: `docs/ops/jenkins-ci.md`.
- PR validation: multibranch job `acestream-scraper-pr` loads `jenkins/pr.Jenkinsfile`, reports the required `PR Validation` context, and discovers origin and fork PR merge revisions. Fork Jenkinsfiles are trusted from the target branch; every fork job bootstraps a disposable dependency runner from that target ref, so it does not rely on a retained local image. Contributor files execute without credentials, network, capabilities, or the Docker socket; entrypoint/runtime contracts additionally run in isolated amd64, arm64, and arm/v7 userlands. Fork-controlled Dockerfiles and dependency installers remain review-gated; privileged production-image builds and engine smokes stay in the trusted develop job.
- Branching model (adopted 2026-08-28): `develop` is the permanent pre-release branch (renamed from `ai-coding-documentation`) and `main` is the release branch. Feature PRs target `develop`; releases are cut with a `develop` → `main` PR; hotfixes also go through `develop`. Both branches are protected the same way (PRs only, required status `PR Validation`, no force-push or deletion). The `Branch Policy` stage in `jenkins/pr.Jenkinsfile` fails any PR into `main` whose head is not `develop`.
- Secure CI/CD split (2026-09-04): fork-aware PR validation is credential-free and container-confined (`jenkins/pr.Jenkinsfile`); publication moved to the trusted `jenkins/develop.Jenkinsfile` job. Every current `develop` head receives the full application suite, Docker/runtime smokes, and a stale-revision guard before `bash scripts/ci/run_jenkins_release.sh --channel develop` pushes the floating `pipepito/acestream-scraper:develop` and `:develop-<flavor>` tags. Version tags and `:latest` remain exclusive to the manual `main` release job. The develop job also refreshes the trusted PR-runner image and publishes the wiki and Pages; missing publish credentials now fail rather than silently weakening the delivery signal.
- Versioning (from the next cycle): once v2.0.0 ships, `version.txt` on `develop` carries the next version with a `-dev` suffix (e.g. `v2.1.0-dev`) and the `develop` → `main` release PR bumps it to the final version. `scripts/ci/run_jenkins_release.sh` refuses a release (non-channel) run while `version.txt` contains `-dev` ("Refusing to release a development version"); the channel publish accepts it. `version.txt` reads `v2.0.0` today (PR #162 is the v2.0.0 release PR), so the suffix convention starts after this release.
- Release: manual job `acestream-scraper-release` (`jenkins/release.Jenkinsfile` → `scripts/ci/run_jenkins_release.sh`), parameters `CONFIRM_RELEASE` (default off), `DRY_RUN` (default on), `PUBLISH_LATEST` (default off). Runs only from `main` with HEAD == `origin/main`. Publish runs execute the cutover full profile, four-flavor dry-run preflight, the engine + Acexy + ARM installer-layout smoke, then push. Two-phase publish: the first run pushes version + flavor tags; a later run with `PUBLISH_LATEST=true` promotes `:latest` after the canary window (see "Two-phase publish" in `docs/release/v2-release-readiness.md`).
- Cloudflare WARP is enabled only in trusted develop/release pipelines and remains non-fatal in `scripts/ci/bootstrap_jenkins_runner.sh`; fork PR containers have no network. The amd64 engine archive is vendored under `docker/vendor/`, while current ARM builds use the digest-pinned jopsis OCI image.
- `scripts/ci/run_v2_test_suite.sh --profile full` ignores `backend/tests/docker`; those tests run in the trusted develop and manual release smoke stages.

## Recent Deliverables (2026-08)

- v1→v2 migration split into a fast foreground phase (schema via Alembic + small tables, then archive) and a resumable background task `v1_epg_programs_migration` for the EPG programs, after a real upgrade on unraid blocked startup and left the container unhealthy (2026-08-29). Includes the Alembic stamp repair for databases the old `create_all` migrator produced, a `progress` field on `/api/v1/background-tasks/status`, a 60 s healthcheck start-period, `EPG_PROGRAM_RETENTION_HOURS` (migration skips already-ended programs; new hourly `epg_program_cleanup` job purges them) and a bootstrap fix that restarts the buildx builder after re-registering binfmt handlers (post-reboot runner failure).
- AceStream engine 3.2.17 on `linux/arm64` (stable) and `linux/arm/v7` (experimental) via matching variants of digest-pinned `jopsis/acestream:v3.2.17-fix`. Local ARM64 runtime smoke and ARMv7 build/QEMU-limit evidence are recorded in `docs/release/phase5-multiarch-evidence.md`.
- Real Acexy proxy compiled into the acexy flavors (`3d568cf`), gated by `test_acexy_runtime_smoke.py` on both the PR and the release path.
- Health probe: `healthcheck.sh` checks the engine through `/webui/api/service?method=get_version` (works for the native 3.2.x and the Android engine); the engine smoke now runs the image's own healthcheck per platform (`1be9fca`).
- Dockerfile Python pins split: `ARG APP_PYTHON_VERSION=3.13` (the app) vs `ARG ACESTREAM_ENGINE_PYTHON_VERSION=3.10` (the x86_64 engine, pinned by `install.python_version` in `docker/manifests/acestream.json`; the Android engine ships its own CPython 3.8). `.dockerignore` keeps `docs/`, `wiki/`, `samples/`, logs and scratch directories out of the build context.
- Jenkins hygiene: the PR smoke stage only warms the build cache (cache-only output, no exported smoke image; the pytest builds and removes its own run-scoped image), `scripts/ci/cleanup_runner_docker.sh` at bootstrap and before the publish builds, smoke-image build retry after a builder-cache prune.
- Feature batch of 2026-08-24: optional API token (#148), outbound SSRF guard (#149), bare content-ID scraping (#81), named base URLs (#62), curated playlists + legacy player routes, reverse-proxy guide (#150), warp-cli legacy fallback and configurable status-check timeouts, process supervision (#119).

## Remaining Work Before The v2.0.0 Tag

1. Operator: create the Docker Hub credential `dockerhub-publish` in Jenkins — scope it to the `Acestream-Scraper` folder so both the multibranch job (which publishes the `develop` pre-release channel) and the release job can bind it — and re-point the `acestream-scraper-release` job's branch specifier to `*/main` (`docs/ops/jenkins-ci.md`, "Manual Release Job"). Neither is done yet; until the credential exists, `develop` builds finish UNSTABLE at the `Publish develop channel` stage.
2. Merge PR #162, then run `acestream-scraper-release` with `DRY_RUN=true`, then publish with `PUBLISH_LATEST=false` and canary the version tag.
3. After the canary passes: tag `v2.0.0` on the published commit and create the GitHub release from `docs/release/v2-release-notes.md` (no `v2.0.0` tag or GitHub release exists yet; `version.txt` already reads `v2.0.0`), then re-run the release job with `PUBLISH_LATEST=true` to promote `:latest` (runbook step 8 in `docs/ops/jenkins-ci.md`).
4. Fill in the per-release record in `docs/release/phase5-multiarch-evidence.md`. The Phase 5 full profile (`python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output`) is not wired into either Jenkins job and has not been captured for the release commit yet.
5. ARM engine validation gaps: `linux/arm/v7` engine execution has never been tested (needs real AArch32-capable hardware); the arm64 Jenkins node (`malcador`) is offline, so the arm64 engine runtime smoke only has local evidence (2026-08-27, Apple Silicon) and does not run in CI.
6. The legacy env alias bridge stays transitional until the retirement pass; the expiry gate in `backend/tests/test_settings_env_compat.py` fails CI once `version.txt` reaches v2.1.0 with the shim still present.

## Phase 3 Evidence Status

- `docs/release/phase3-cutover-evidence.md` records a full-profile Phase 3 run with `Overall passed: True`.
- Blocking gates passed for:
  - parity full validation
  - root-stack cutover checks
  - compose smoke validation
  - legacy reference guard
- Phase 3 cutover should no longer be described as pending in this repository unless newer evidence contradicts the checked-in signoff artifact.

## Post-v2 Follow-ups

- Split `backend/app/services/epg_service.py` (~790 LOC) into sub-services — deferred (item S1 in `docs/release/v2-release-readiness.md`).
- Remove the legacy env alias shim in v2.1.0.
- Real-hardware ARM validation (Raspberry Pi 4/5, ARMv7): plan in `docs/release/arm-acestream-issue-draft.md`, procedure in `docs/ops/acestream-arm-engine.md`.

## UI Overhaul (2026-09-02)

- Branch `ui-overhaul` merged into `develop`: eight navigation destinations (Overview replaces Dashboard, Health and Stats; Search and EPG consolidated), legacy routes redirect. Every page follows PageHeader → StatusLine → sections; hero blocks and explanatory copy removed.
- Backend: `rescrape_interval` and the new `epg_refresh_interval` settings reschedule the APScheduler jobs at runtime (`TaskService.reschedule_task`); channel cleanup only removes inactive, unlinked, stale channels; scrapes no longer re-activate hidden channels.
- Frontend primitives: `StatusLine`, `ConfirmDialog`/`useConfirm`, `RowActionsMenu`, `ScheduleView` (Now/Next + day tabs), `ChannelFilterBar`, `ChannelCardList`, `PageHeader.overflowActions`.
- Verification: frontend Jest (45 suites), backend pytest, and the Playwright suite in `e2e/` run against the local backend and the arm64 Docker flavour with services on (engine, Acexy, IPFS, WARP) and off.

## Superseded Snapshot (2026-04-24)

> Superseded on 2026-08-28 by the sections above; kept as the historical record.

- Milestone then: post-cutover reconciliation and release-path cleanup; Phase 3 cutover achieved, Phases 4–6 listed as upcoming.
- Deliverables recorded then: root ownership of `backend/` + `frontend/`, CI/release workflows gated on root-stack checks, legacy-path assertion scripts, one-release env alias mapping, Phase 3 cutover evidence.
- Transitional work listed then: finish documentation reconciliation, keep the env alias bridge documented as transitional, reconcile release/migration docs to Jenkins-first ownership — all addressed by the 2026-05-04 gap-closure pass and this 2026-08-28 refresh, except the alias bridge retirement.
