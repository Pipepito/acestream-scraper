# Development Progress

## Status Snapshot

- **Date:** 2026-08-28 (previous snapshot of 2026-04-24 kept below as superseded)
- **Current Milestone:** v2.0.0 release preparation — PR #113 (`ai-coding-documentation` → `main`)
- **Current Phase:** Phases 1–6 complete; remaining work is release-job operator setup, ARM engine hardware validation, and documentation reconciliation

## Completed Phases

- [x] Phase 1: Parity baseline and safety gates — `scripts/phase_gates/phase1_gate_runner.py --profile quick` runs on every PR (`Jenkinsfile`, stage `Phase 1 Safety Gates`).
- [x] Phase 2: Backend contract and structure hardening — typed DTOs, layer-boundary guard (`backend/tests/architecture/test_layer_boundaries.py`), error envelope + correlation IDs, Pydantic v2 `model_config` everywhere.
- [x] Phase 3: v2-only cutover and legacy retirement — evidence in `docs/release/phase3-cutover-evidence.md`; `scripts/ci/assert_no_legacy_paths.sh --strict` guards regressions.
- [x] Phase 4: Frontend UX modernization — `AppShell` / `PageHeader` / `ContentSection`, light + dark theme with reduced-motion support, ESLint + `tsc --noEmit` gates at zero warnings; stack modernized to `@tanstack/react-query` v5, TypeScript 5 and Vite (`8051317`, #154); oversized `EPG.tsx` / `TVChannels.tsx` split into components and hooks (`a911df5`, #153). Review evidence: `docs/dev/frontend-design-review-evidence.md`.
- [x] Phase 5: Multi-arch build and runtime validation — the four image flavors (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy` = `latest`) build for `linux/amd64`, `linux/arm64` and `linux/arm/v7`; the AceStream engine now also ships on ARM (`2a82fc8`, official Android engine on a bionic userland — `linux/arm64` stable, `linux/arm/v7` experimental, per `docker/manifests/acestream.json`). Evidence contract: `docs/release/phase5-multiarch-evidence.md`; operator guide: `docs/ops/acestream-arm-engine.md`.
- [x] Phase 6: Reliability, test ownership, and optimization — canonical test homes (`docs/testing/test-ownership-matrix.md`), single runner `scripts/ci/run_v2_test_suite.sh`, hot-path indexes and query budgets (`docs/performance/phase6-db-benchmarks.md`, `backend/tests/perf/`), reliability runbook (`docs/ops/reliability-runbook.md`), in-container process supervision for the engine and Acexy (`f2caafa`, #119), rotating application log (`backend/app/utils/logging.py`, `LOG_FILE_MAX_BYTES` / `LOG_FILE_BACKUP_COUNT`).

## Phase 3 Plan Progress

- [x] 03-01: Root ownership promotion + strict cutover CI guards
- [x] 03-02: Legacy retirement guardrails + env compatibility bridge delivered; documentation reconciliation remains in progress
- [x] 03-03: Branch cutover checklist and final verification

## CI And Release Path (current)

- Jenkins is the only CI. The GitHub Actions workflows were retired on 2026-08-26 (`e5657b9`); `.github/workflows/` no longer exists. Operator guide: `docs/ops/jenkins-ci.md`.
- PR validation: multibranch job `acestream-scraper-pr` (`Jenkinsfile`) — runner disk sweep (`bash scripts/ci/cleanup_runner_docker.sh --transient-age-hours 0`) + bootstrap, Phase 1 gates, required cutover checks (quick profile, four-flavor dry-run builds + `verify_multiarch_manifest.sh`, strict legacy-path guard), `Acestream Engine Runtime Smoke` (`backend/tests/docker/test_acestream_runtime_smoke.py`, `test_acexy_runtime_smoke.py`, `test_install_acestream.py -k android_apk_install_layout`; smoke image tag scoped to `BUILD_TAG` and removed in `post { always }`), Phase 3 quick gate, Multi-Arch quick profile. GitHub branch protection on `main` requires the single `PR Validation` status; the multibranch job is configured to skip branches that are also filed as PRs, so only `PR-113` builds for this branch.
- Release: manual job `acestream-scraper-release` (`jenkins/release.Jenkinsfile` → `scripts/ci/run_jenkins_release.sh`), parameters `CONFIRM_RELEASE` (default off), `DRY_RUN` (default on), `PUBLISH_LATEST` (default off). Runs only from `main` with HEAD == `origin/main`. Publish runs execute the cutover full profile, four-flavor dry-run preflight, the engine + Acexy + ARM installer-layout smoke, then push. Two-phase publish: the first run pushes version + flavor tags; a later run with `PUBLISH_LATEST=true` promotes `:latest` after the canary window (see "Two-phase publish" in `docs/release/v2-release-readiness.md`).
- Cloudflare WARP on the runner is opt-in (`JENKINS_ENABLE_WARP=1`, set by both Jenkinsfiles) and non-fatal in `scripts/ci/bootstrap_jenkins_runner.sh`; the engine archives and bionic packages are vendored under `docker/vendor/` and mirrored on the GitHub release `acestream-binaries-3.2.11-3.1.80.0`, so image builds no longer depend on reaching `download.acestream.media`.
- `scripts/ci/run_v2_test_suite.sh --profile full` ignores `backend/tests/docker`; those tests run only as the explicit smoke stages above.

## Recent Deliverables (2026-08)

- AceStream engine on `linux/arm64` (stable) and `linux/arm/v7` (experimental) via the official Android engine APK on a minimal Android 9 bionic userland (`0d645e6`, `2a82fc8`, 2026-08-27). Local arm64 engine smoke recorded in `docs/release/phase5-multiarch-evidence.md`.
- Real Acexy proxy compiled into the acexy flavors (`3d568cf`), gated by `test_acexy_runtime_smoke.py` on both the PR and the release path.
- Health probe: `healthcheck.sh` checks the engine through `/webui/api/service?method=get_version` (works for the native 3.2.x and the Android engine); the engine smoke now runs the image's own healthcheck per platform (`1be9fca`).
- Dockerfile Python pins split: `ARG APP_PYTHON_VERSION=3.13` (the app) vs `ARG ACESTREAM_ENGINE_PYTHON_VERSION=3.10` (the x86_64 engine, pinned by `install.python_version` in `docker/manifests/acestream.json`; the Android engine ships its own CPython 3.8). `.dockerignore` keeps `docs/`, `wiki/`, `samples/`, logs and scratch directories out of the build context.
- Jenkins hygiene: BUILD_TAG-scoped smoke tags, `scripts/ci/cleanup_runner_docker.sh` at bootstrap and before the publish builds, smoke-image build retry after a builder-cache prune.
- Feature batch of 2026-08-24: optional API token (#148), outbound SSRF guard (#149), bare content-ID scraping (#81), named base URLs (#62), curated playlists + legacy player routes, reverse-proxy guide (#150), warp-cli legacy fallback and configurable status-check timeouts, process supervision (#119).

## Remaining Work Before The v2.0.0 Tag

1. Operator: create the Docker Hub credential `dockerhub-publish` in Jenkins and re-point the `acestream-scraper-release` job's branch specifier to `*/main` (`docs/ops/jenkins-ci.md`, "Manual Release Job"). Neither is done yet.
2. Merge PR #113, then run `acestream-scraper-release` with `DRY_RUN=true`, then publish with `PUBLISH_LATEST=false` and canary the version tag.
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

## Superseded Snapshot (2026-04-24)

> Superseded on 2026-08-28 by the sections above; kept as the historical record.

- Milestone then: post-cutover reconciliation and release-path cleanup; Phase 3 cutover achieved, Phases 4–6 listed as upcoming.
- Deliverables recorded then: root ownership of `backend/` + `frontend/`, CI/release workflows gated on root-stack checks, legacy-path assertion scripts, one-release env alias mapping, Phase 3 cutover evidence.
- Transitional work listed then: finish documentation reconciliation, keep the env alias bridge documented as transitional, reconcile release/migration docs to Jenkins-first ownership — all addressed by the 2026-05-04 gap-closure pass and this 2026-08-28 refresh, except the alias bridge retirement.
