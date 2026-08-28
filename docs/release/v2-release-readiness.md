# v2 Release Readiness — Gap Report

**Date:** 2026-05-03 (audit), 2026-05-04 (closure pass)
**Source planning:** `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md` (claimed 100% complete on 2026-02-27).
**Reality check:** Audited all six phase folders, all summaries, all open debug investigations, and verified claimed deliverables against the current branch.
**Closure status:** All identified gaps closed on the `gap-closure-v2` branch (merged into `develop` on 2026-05-04, `e009d61`) — see commit history for the per-item changes. Companion document: `docs/release/v2-release-notes.md`.
**Refresh:** 2026-08-28 — reconciled against the current branch (Jenkins-only CI since `e5657b9` on 2026-08-26, AceStream engine on ARM since `2a82fc8` on 2026-08-27). The `[BLOCKER]` headings below are the 2026-05-03 audit record; each is annotated with its closure. The items that still gate the `v2.0.0` tag are listed in "Current status".

---

## Current status (2026-08-28)

**Closed since the audit** (in addition to the ten items in the TL;DR table):

- CI consolidated on Jenkins: `acestream-scraper-pr` (`Jenkinsfile`) validates PRs, `acestream-scraper-release` (`jenkins/release.Jenkinsfile`) is the sole publisher (of release tags — since 2026-08-28 the PR pipeline also publishes the floating `develop` pre-release channel, see the last section); GitHub Actions retired (`e5657b9`). GitHub branch protection on `main` requires the single `PR Validation` status (and on `develop` since 2026-08-28).
- Two-phase `:latest` publish with `PUBLISH_LATEST` (`5ffed1d`) — see the last section.
- Real Acexy proxy in the acexy flavors, gated by `backend/tests/docker/test_acexy_runtime_smoke.py` on the PR and release paths (`3d568cf`).
- AceStream engine on `linux/arm64` (stable) and `linux/arm/v7` (experimental) via the official Android engine; engine archives and bionic packages vendored under `docker/vendor/` and mirrored on the GitHub release `acestream-binaries-3.2.11-3.1.80.0` (`0d645e6`, `2a82fc8`). Operator guide: `docs/ops/acestream-arm-engine.md`.
- `healthcheck.sh` probes the engine via `get_version`; the engine smoke runs the image's own healthcheck per platform (`1be9fca`).
- Jenkins runner hygiene: no exported smoke image in the PR job (cache-only warm-up; the pytest builds and removes its own run-scoped image), dangling layers pruned in `post { always }`, `scripts/ci/cleanup_runner_docker.sh` at bootstrap and before publish builds, WARP opt-in and non-fatal (`JENKINS_ENABLE_WARP=1`).
- Frontend stack modernized (`@tanstack/react-query` v5, TypeScript 5, lint zero — `8051317`, #154); `EPG.tsx` / `TVChannels.tsx` split (`a911df5`, #153).
- Backend suite: 478 tests collected under `backend/tests` (excluding `backend/tests/docker`, which runs only as explicit Jenkins smoke stages).

**Still open before tagging `v2.0.0`:**

| # | Item | Owner / where |
|---|---|---|
| O1 | Jenkins credential `dockerhub-publish` is not created yet (scope it to the `Acestream-Scraper` folder so both the multibranch job — which publishes the `develop` channel — and the release job can bind it), and the `acestream-scraper-release` job's branch specifier must be re-pointed to `*/main`. Until both are done the publish run cannot bind credentials and `develop` builds finish UNSTABLE at `Publish develop channel`. | Operator — `docs/ops/jenkins-ci.md`, "Manual Release Job" |
| O2 | No `v2.0.0` git tag or GitHub release exists. After PR #162 merges: dry-run, publish phase 1 (`PUBLISH_LATEST=false`), canary the version tag, **then** tag `v2.0.0` on the published commit and create the GitHub release from `docs/release/v2-release-notes.md`, then promote `:latest` (`PUBLISH_LATEST=true`) — runbook step 8 in `docs/ops/jenkins-ci.md`. | Maintainer |
| O3 | Phase 5 full-profile evidence for the release SHA: `python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output > phase5-gate-report-full.json` is manual (not wired into either Jenkins job) and has not been captured; the per-release record in `docs/release/phase5-multiarch-evidence.md` is still the template. | Maintainer — run on the release commit |
| O4 | Real ARMv7 hardware validation: the `linux/arm/v7` engine has never executed (32-bit bionic cannot run under qemu-user); platform stays `support: experimental`. | Needs AArch32 hardware — `docs/ops/acestream-arm-engine.md`, `docs/release/arm-acestream-issue-draft.md` |
| O5 | The arm64 Jenkins node (`malcador`) is offline, so the arm64 engine runtime smoke does not run in CI; the only arm64 evidence is the local 2026-08-27 run recorded in `docs/release/phase5-multiarch-evidence.md`. Re-run `test_acestream_runtime_smoke.py` on an arm64 host before publishing. | Operator |

O4 and O5 do not block the tag (ARM caveats are documented in the release notes); O1–O3 do.

---

## TL;DR

The v2 consolidation is structurally complete: all six phases shipped their planned deliverables, the canonical `backend/` + `frontend/` stack replaces the legacy root, multi-arch image flavors are wired, and the parity, contract, and reliability test surfaces exist. Two genuine release blockers and a basket of hardening items were identified at audit time. **All ten are now closed** on the `gap-closure-v2` branch:

| Status | Item | Closed by |
|---|---|---|
| ✅ Closed | `backend/tests/test_epg.py` was 5 failed + 3 errors due to a test-harness module-reload bug. | B1: redesign harness — lazy engine, `lifespan` context, no module reload. Suite now 364 passed / 0 failed. |
| ✅ Closed | Multi-arch runtime smoke was push/release-only; no fresh ARM evidence. | B2: `multiarch-full` now gates `release.yml::build-image` AND auto-runs on PRs that touch `Dockerfile`/`docker/`/multiarch scripts. Stale checked-in snapshots deleted; evidence lives on the workflow run. *(Superseded 2026-08-26: GitHub Actions retired. The gate is now the `Acestream Engine Runtime Smoke` stage in `Jenkinsfile` on every PR plus the pre-publish smoke in `scripts/ci/run_jenkins_release.sh`; evidence contract in `docs/release/phase5-multiarch-evidence.md`. The QEMU boot of the ARM app images is the manual Phase 5 full profile — see O3.)* |
| ✅ Closed | Phase-5 `phase5-build-result-*.json` snapshots at root were stale. | C1: deleted; pattern added to `.gitignore`. |
| ✅ Closed | `LEGACY_ENV_ALIAS_WINDOW` had no enforced expiry. | H3: version-gated test reads `version.txt` and fails CI when the project reaches v2.1.0 with the shim still present. |
| ✅ Closed | Stray utility scripts at repo root. | C2: moved to `scripts/dev/epg/` with a README. |
| ✅ Closed | `datetime.utcnow()` deprecation across models/repos/services. | H2: full sweep + `UtcDateTime` `TypeDecorator` for normalization at the ORM boundary + Alembic migration. |
| ✅ Closed | Pydantic v1-style `class Config:` blocks. | H1: 12 sites converted to `model_config = ConfigDict(...)`. |
| ⏸ Deferred (S1) | `epg_service.py` ~770 LOC, `EPG.tsx` ~1035 LOC, `TVChannels.tsx` ~630 LOC. | Tracked as stretch in the gap plan; deferred to v2.x since it's a refactor with no behavioral change. *(Update 2026-08-24: `EPG.tsx` and `TVChannels.tsx` were split into components/hooks in #153 (`a911df5`; now ~360 / ~380 lines). `epg_service.py` (~790 LOC) remains deferred.)* |
| ✅ Closed | Frontend types hand-maintained. | H4: OpenAPI codegen pipeline + drift gate (`backend/scripts/dump_openapi.py` + `frontend/src/types/api-generated.ts` + CI `git diff --exit-code` step). |
| ✅ Closed | No frontend lint / CI lint step. | H5: ESLint config + `tsc --noEmit` typecheck wired into `run_v2_test_suite.sh`. Surfaced + fixed several real type/lint issues in `Stats.tsx`, `Settings.tsx`, `Scraper.tsx`, `TVChannels.tsx`, `QuickEditDialog.tsx`. |

---

## Phase-by-phase audit

### Phase 1 — Parity Baseline and Safety Gates ✅

**Plans:** 01-01 (parity harness, manifests, comparators), 01-02 (gate runner + CI workflow).

**Verified:**
- `backend/tests/parity/baseline_sources.yaml`, `parity_compare.py`, `parity_manifest.py` — all present.
- Snapshots: `backend/tests/parity/snapshots/scraper_channels_snapshot.json`, `output_validity_snapshot.json`.
- `backend/tests/parity/test_scraper_parity.py` and `test_output_parity.py` — 10 passed locally.
- Gate runner: `scripts/phase_gates/phase1_gate_runner.py` exits `0/1` based on aggregated result. The runner is invoked from the canonical `Jenkinsfile` ("Phase 1 Safety Gates" stage); failed gates block the Jenkins PR job. (The standalone `.github/workflows/phase1-safety-gates.yml` was retired once the canonical pipelines absorbed the gate.)
- Operator checklist: `docs/migration/phase1-parity-gates.md`.

**Originally failing scraper parity tests** (per `.planning/debug/scraper-failure-domain.md`) — fixed in commit `6c36680 test: fix scraper parity runtime imports` by moving `ScraperService` and `AcestreamChannel` imports inside test functions (workaround for the conftest module-reload bug).

**Outstanding:** snapshot freshness has no changelog/version-log convention — recommended but not blocking.

---

### Phase 2 — Backend Contract and Structure Hardening ✅

**Plans:** 02-01 (typed DTOs), 02-02 (endpoint→service→repository boundaries), 02-03 (error envelope + correlation IDs + structured logging).

**Verified:**
- Schemas: `backend/app/schemas/{channel,config,epg,errors,...}.py`.
- Dependency providers: `backend/app/api/dependencies.py` (`get_url_service`, `get_scraper_service`, `get_stats_service`).
- Repository surfaces: `backend/app/repositories/{url_repository,stats_repository,channel_repository,activity_log_repository}.py`.
- Error contract: `backend/app/schemas/errors.py` + `register_error_handlers()` in `main.py`; `correlation_id_middleware` echoes `X-Correlation-ID`.
- Architecture guard: `backend/tests/architecture/test_layer_boundaries.py`.
- Contract tests: `backend/tests/contracts/test_{channel,config,urls}_contracts.py` — green.
- `backend/tests/test_error_contracts.py` — **green now** (3/3 pass), despite the open debug doc; the test-harness fix landed.

**Outstanding:**
- `epg_service.py` ~770 LOC, 27 methods — never split. Functional but a maintenance liability (CONCERNS.md called it out). *(Still open 2026-08-28: ~790 LOC; deferred, see S1.)*
- Pydantic v1 `class Config:` style in `schemas/scraper.py`, `schemas/search.py`. Will break on Pydantic v3. *(Closed 2026-05-04, H1 — `3f9ac4e`.)*
- Frontend service interfaces are hand-maintained against backend Pydantic models. No codegen pipeline. *(Closed 2026-05-04, H4 — `253ba5b`; drift gate runs in `scripts/ci/run_v2_test_suite.sh`.)*

---

### Phase 3 — v2-Only Cutover and Legacy Retirement ✅

**Plans:** 03-01 (root ownership + strict gates), 03-02 (legacy file deletion + env aliasing + docs), 03-03 (cutover checklist + gate runner + evidence).

**Verified:**
- Root legacy entrypoints **deleted**: `wsgi.py`, `run_dev.py`, `manage.py`, root `app/`, root `migrations/`. (`tests/` at root remains and is intentional — different concern.)
- `scripts/ci/assert_no_legacy_paths.sh` — strict guard present, forbids `wsgi.py`, `run_dev.py`, `manage.py`, `v2/`.
- Env aliasing: `apply_legacy_env_aliases()` in `backend/app/config/settings.py`; covered by `backend/tests/test_settings_env_compat.py`.
- Docs: `docs/migration/migration-strategy.md`, `docs/migration/phase3-cutover-checklist.md`, `docs/architecture/deployment.md` — all aligned to root-only.
- Phase-3 evidence: `docs/release/phase3-cutover-evidence.md`.

**Outstanding:**
- `LEGACY_ENV_ALIAS_WINDOW = "v2-cutover-r1"` is metadata only. Nothing schedules removal. Recommend a one-shot cleanup task for the post-v2 release. *(Closed 2026-05-04, H3 — `c592ea6`: `backend/tests/test_settings_env_compat.py` fails CI once `version.txt` reaches v2.1.0 with the shim present. The shim itself is still in place and intentionally transitional.)*
- Stray dev scripts at repo root (`check_epg_data.py`, `force_epg_refresh.py`, `test_epg_xml.py`, `test_epg_time.py`, `list.m3u`, `generated_epg.xml`) make the root noisy. Move to `scripts/dev/` or delete. *(Closed 2026-05-04, C2 — moved to `scripts/dev/epg/`.)*
- `tests/` at repo root still exists with `conftest.py`, `test_config.py`, `test_acexy_api.py`, `test_warp_service.py`, etc. Either canonize into `backend/tests/` or document why a second test root is intentional. *(Closed 2026-05-04 — legacy root `tests/` tree retired in `3251505`.)*

---

### Phase 4 — Frontend UX Modernization ✅

**Plans:** 04-01 (AppShell + theme tokens), 04-02 (page rework around stable contracts), 04-03 (responsive + a11y polish).

**Verified:**
- Layout primitives: `frontend/src/components/layout/{AppShell,PageHeader,ContentSection}.tsx` and centralized `navItems.tsx`.
- Standardized pages: Dashboard, AcestreamChannels, TVChannels, EPG, Scraper, Health, Settings, Stats, Playlist all use `PageHeader` + `ContentSection`.
- Theme: `frontend/src/theme.ts` exports `createAppTheme(mode)`; `AppBootstrap`/`AppThemeModeContext`/`useAppThemeMode` wire light/dark with `localStorage` and `prefers-color-scheme` fallback.
- Reduced motion: `theme.ts` branches motion tokens on `prefers-reduced-motion: reduce`.
- Type drift fixed: `PaginatedAcestreamChannels` is now an exported interface in `frontend/src/services/channelService.ts`.
- Late additions in commit `aeb239e feat: complete remaining v2 admin and monitoring pages` — Health, Stats, Settings, Search, EPGMappings, Channels brought to baseline.

**Outstanding:**
- `EPG.tsx` ~1035 lines, `TVChannels.tsx` ~631 lines — function fine, but both will be painful to evolve. *(Closed 2026-08-24 — split into components/hooks in #153, `a911df5`.)*
- `SearchNew.tsx` is a redirect wrapper for legacy bookmarks; document this in a code comment so future readers don't think it's dead code. *(Closed 2026-05-04 — `22aea34`.)*
- No `npm run lint` script. No frontend lint step in CI. *(Closed 2026-05-04, H5 — `9140269`; `npm run lint -- --max-warnings=0` and `tsc --noEmit` run in `scripts/ci/run_v2_test_suite.sh`.)*
- Bundle warning: `mui-data-grid` chunk ~551kB after minify — not new, but a candidate for dynamic import. *(Still open; not blocking.)*
- No design-review evidence captured (`docs/dev/frontend-design-review-evidence.md` is empty). *(Closed — the evidence file is now populated per page group.)*

---

### Phase 5 — Multi-Arch Build and Runtime Validation ✅

*(Header flipped from ⚠️ to ✅ on 2026-08-28: the release-blocker items below are closed or superseded; what remains is the manual full-profile evidence run (O3) and real-hardware ARM validation (O4/O5), tracked in "Current status".)*

**Plans:** 05-01 (multi-arch build + manifest validation), 05-02 (runtime smoke + checklist + Android TV docs).

**Verified:**
- `Dockerfile` flavor targets: `scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy` (lines 160–183).
- `scripts/ci/build_multiarch_images.sh`, `verify_multiarch_manifest.sh`, `flavor_platforms.py`.
- Manifests: `docker/manifests/{platforms,acestream}.json` (AceStream is amd64-only today). *(Superseded on 2026-08-27 by branch `arm-acestream-engine`: `acestream.json` now declares `linux/amd64` and `linux/arm64` as `stable` and `linux/arm/v7` as `experimental`, backed by the official Android engine — see "Known issues" in `docs/release/v2-release-notes.md`.)*
- Smoke tooling: `scripts/ci/phase5_arch_smoke.sh`, `scripts/phase_gates/phase5_gate_runner.py` + config.
- Docs: `docs/migration/phase5-architecture-smoke-checklist.md`, `docs/architecture/deployment.md` (Multi-Arch + Android TV section), `docs/release/phase5-multiarch-evidence.md`.

**Outstanding (release-blocker territory):**
- The full multi-arch profile (`phase5_gate_runner.py --profile full`) runs only on the manual `Release Pipeline` (`workflow_dispatch`) and on Jenkins `acestream-scraper-release`; it does not fire on PRs (the standalone `multiarch-validation.yml` was retired). **Trigger the manual Release Pipeline once on `develop` to capture fresh `phase5-gate-report-full.json` and runtime smoke output before tagging the release.** *(Superseded on 2026-08-27: GitHub Actions is retired, so `workflow_dispatch` no longer exists; Jenkins `acestream-scraper-release` is the only release path and its preflight runs the cutover full profile plus the real AceStream engine smoke — see "How evidence is produced for a release" in `docs/release/phase5-multiarch-evidence.md`.)*
- Committed `phase5-build-result-*.json` files at repo root are dated 2026-04-19, marked `dry_run: true, push: false, load: false` — they are config snapshots, not build evidence. They should not be relied on for signoff. *(Closed 2026-05-04, C1 — deleted and added to `.gitignore`; evidence now lives on the Jenkins build artifacts.)*
- `docs/release/phase5-multiarch-evidence.md` lists ARMv7 and ARM64 runtime smoke as **Pending**. *(Updated on 2026-08-27: the evidence doc now records a local `linux/arm64` AceStream engine smoke on Apple Silicon; `linux/arm/v7` engine execution and real-hardware validation remain pending.)*
- No documented manifest-update procedure for `docker/manifests/acestream.json` when AceStream gains ARM platforms. *(Closed on 2026-08-27 by branch `arm-acestream-engine`: ARM is enabled in the manifest via the official Android engine, and the pin/update procedure lives in `docker/vendor/acestream/README.md`; `python3 scripts/ci/validate_docker_manifest_metadata.py` checks the manifest, vendored files, `SHA256SUMS` and mirror URLs.)*

---

### Phase 6 — Reliability, Test Ownership, and Optimization ✅

*(Header flipped from ⚠️ to ✅ on 2026-08-28: the `test_epg.py` blocker below was closed by the harness redesign on 2026-05-04; the suite has been green since.)*

**Plans:** 06-01 (canonical test ownership + runner), 06-02 (reliability hardening, scheduler), 06-03 (DB hot-path indexes + perf baseline).

**Verified:**
- `backend/tests/` subtree: `contracts/`, `parity/`, `regression/`, `architecture/`, `perf/`.
- `frontend/src/__tests__/` — expanded coverage including `Dashboard.test.tsx`, `AcestreamChannelsPage.test.tsx`, etc.
- `scripts/ci/run_v2_test_suite.sh --profile {quick,full}`, `scripts/perf/profile_phase6_db_paths.py`, `phase6-db-baseline.json`.
- `backend/migrations/versions/phase6_add_hotpath_indexes.py` — 7 idempotent indexes.
- `docs/ops/reliability-runbook.md`, `docs/testing/test-ownership-matrix.md`.
- Background tasks centralized; duplicate route removed; status backed by scheduler.

**Outstanding (release blocker — see top section):** *(Closed 2026-05-04, B1 — `9250494` redesigned `backend/tests/conftest.py` around dependency overrides and a lazy engine, no module reload; `test_epg.py` and the full profile are green. Kept as the historical diagnosis.)*
- `backend/tests/test_epg.py`: **5 failed + 3 errors** in current branch. Failure mode confirmed verbatim from `.planning/debug/epg-test-failure-domain.md`:
  ```
  sqlalchemy.exc.InvalidRequestError: When initializing mapper Mapper[TVChannel(tv_channels)],
  expression 'AcestreamChannel' failed to locate a name ('AcestreamChannel').
  ```
  The conftest fixture `_load_backend_runtime()` clears and re-imports `app.models*` and `app.config.database` per test. `test_epg.py` imports model classes at module-import time, holding the pre-reload class. SQLAlchemy mapper config later resolves the relationship name against the *new* registry, can't find the *old* class, and explodes.

- This breaks `run_v2_test_suite.sh --profile full` and therefore any Jenkins release path that uses the full profile.

- Same root cause was diagnosed for `test_scrapers.py`/`test_scraper_parity.py` and `test_error_contracts.py`. Scraper parity got a workaround in `6c36680` (move imports inside test functions). Error contracts now passes (presumably from earlier alignment). EPG didn't get the same fix.

---

## Recommended actions before tagging the release

In priority order. Items marked **[BLOCKER]** must land first.

*(2026-08-28: both blockers below are closed — annotations on each heading. The items that currently gate the tag are O1–O3 in "Current status".)*

### 1. ~~**[BLOCKER]**~~ Fix `backend/tests/test_epg.py` — **closed 2026-05-04 (B1, `9250494`)**

Two paths, pick one:

**Quick fix (mirrors `6c36680` for parity):** move every `from app.models.models import …` and `from app.services.epg_service import …` *out of* module scope and *into* each test function or class fixture. This is what unblocked the scraper parity suite. Low risk, localized.

**Better fix (root cause):** stop reloading `app.models*` and `app.config.database` in `backend/tests/conftest.py::_load_backend_runtime()`. Test isolation is already provided by the per-test SQLite tempfile + `Base.metadata.create_all(...)` path; reloading the model module just creates a second copy of `Base`/`mapper_registry` and produces the exact crash we're seeing. If settings reload is the only reason for the reload (it usually is), only reload `app.config.settings` and re-bind the engine. This is the durable fix and would also let us drop the parity workaround.

After fixing, run:
```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_epg.py
bash scripts/ci/run_v2_test_suite.sh --profile full
```
Both must be green before tagging.

### 2. ~~**[BLOCKER]**~~ Capture fresh multi-arch runtime smoke evidence — **closed as a blocker 2026-05-04 (B2); re-scoped 2026-08-28**

*(The GitHub Actions gate described below was retired on 2026-08-26. Today: every PR and every publish run boots the amd64 engine, checks the real Acexy proxy and QEMU-builds the arm64/armv7 installer stage (`Jenkinsfile` stage `Acestream Engine Runtime Smoke`; `scripts/ci/run_jenkins_release.sh`). What is still outstanding is O3 — the manual Phase 5 full profile for the release SHA — and the ARM hardware items O4/O5.)*

Either flip `multiarch-full`'s gate to also run on PRs touching `Dockerfile`/`docker/`/`scripts/ci/`, or run it manually on the release branch and attach the artifacts (`phase5-gate-report-full.json` + the four flavor `phase5-build-result-full-*.json`) to `docs/release/phase5-multiarch-evidence.md`. Update the "Pending" markers there to "Complete" with links and timestamps. Pitfall #4 in `.planning/research/PITFALLS.md` flags this exact "build success ≠ runtime works" failure mode.

### 3. **Tighten before merge** (suggested, not blocking)

*(All seven landed on 2026-05-04 in the gap-closure pass — H1–H5, C1, C2 in the TL;DR table.)*

- **Env alias expiry:** add a follow-up issue/task to remove `LEGACY_ENV_ALIAS_MAP` and the compat bootstrap in the next release after v2 (`v2.1` or `v2-cutover-r2`). Track it explicitly so nobody forgets — a stale compat shim turns into permanent debt. *(Closed — H3 expiry gate; the removal itself is a v2.1.0 task.)*
- **Stale Phase-5 build-result JSONs at repo root:** delete them (`phase5-build-result-pr-*.json`, `phase5-build-result-release-*.json`, `multiarch-build-result.json`) and rely on CI artifacts. They're not useful and they're confusing. *(Closed — C1.)*
- **Stray utility scripts at repo root:** move `check_epg_data.py`, `force_epg_refresh.py`, `test_epg_xml.py`, `test_epg_time.py`, `list.m3u`, `generated_epg.xml` to `scripts/dev/` or delete (the `.xml`/`.m3u` look like leftover debug artifacts). *(Closed — C2.)*
- **Pydantic v1 config blocks:** swap `class Config:` for `model_config = ConfigDict(...)` in `backend/app/schemas/scraper.py` and `backend/app/schemas/search.py`. Two-line change, kills warning noise. *(Closed — H1.)*
- **`datetime.utcnow()` deprecation:** ~20 call sites in models/repos/services. Replace with `datetime.now(timezone.utc)`. Not blocking now (Python 3.12 only warns), but every release we delay this it spreads. *(Closed — H2.)*
- **Document `SearchNew.tsx`:** add a one-line comment explaining it's a legacy redirect wrapper, not a duplicate page. *(Closed — `22aea34`.)*
- **Add a frontend lint script + CI step:** `npm run lint` + `eslint --max-warnings=0` in CI catches drift before review. *(Closed — H5.)*

### 4. **Post-release cleanup tasks** (don't gate the release on these)

- Split `backend/app/services/epg_service.py` into source/auto-mapping/program-import sub-services. *(Still open — S1.)*
- Split `frontend/src/pages/EPG.tsx` and `TVChannels.tsx` — extract filter/table subcomponents. *(Done 2026-08-24 — #153, `a911df5`.)*
- Add a `backend/scripts/export_ts_types.py` codegen pass to keep `frontend/src/services/*.ts` types in sync with `backend/app/schemas/`. Removes a recurring drift class. *(Done 2026-05-04 as H4 — `backend/scripts/dump_openapi.py` + `npm run codegen` + drift gate instead of a bespoke exporter.)*
- Capture before/after light/dark + mobile/desktop screenshots into `docs/dev/frontend-design-review-evidence.md`. Useful for changelog and future regression baselining. *(Partially done — the file records per-page-group light/dark/reduced-motion/responsive review evidence as test runs and inspections rather than screenshots.)*

---

## Out-of-scope items (intentionally deferred per `REQUIREMENTS.md`)

These aren't release blockers; they're explicitly marked v2+ in the requirements doc.

- **API authentication** (NEXT-04). Operational endpoints remain unauthenticated. Deploy behind trusted network.
- **SSRF guardrails on user-supplied scrape URLs.** Mitigated only by URL classification today.
- **External worker queue** (NEXT-01) for long-running scrape/EPG jobs. APScheduler in-process is fine for current load.
- **Android TV remote-navigation polish** (NEXT-02). Responsive baseline ships; deeper remote UX is post-v2.
- **Performance telemetry dashboards** (NEXT-03). Today: query budgets via `backend/tests/perf/`.

---

## Definition of "done" for v2 release

Status as of 2026-08-28 in brackets.

- `bash scripts/ci/run_v2_test_suite.sh --profile full` exits 0. [Green on the Jenkins release dry-run path (`run_cutover_required_checks.sh --profile full`); the PR job runs the quick profile.]
- `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/` exits 0. [Green; note `backend/tests/docker` needs Docker/buildx and is exercised by the Jenkins smoke stages.]
- A fresh `phase5-gate-report-full.json` exists from CI for this release SHA, attached or linked from `docs/release/phase5-multiarch-evidence.md`. [Open — O3; the full profile is a manual run, not a Jenkins stage.]
- `bash scripts/ci/assert_no_legacy_paths.sh --strict` exits 0. [Green on every PR.]
- `bash scripts/ops/preflight_v2_deploy.sh` reports SAFE on a representative v1 production DB (or the operator has documented and accepted the UNSAFE path with rescue export in place). [Operator step at deploy time.]
- Added 2026-08-28: Jenkins `dockerhub-publish` credential created (global scope; visible to the multibranch job and the release job) and the release job's branch specifier pointed at `*/main` [Open — O1]; `v2.0.0` tag + GitHub release created from `docs/release/v2-release-notes.md` after PR #162 merges [Open — O2].

---

## Two-phase publish (canary `:latest` promotion)

The Jenkins release pipeline (`jenkins/release.Jenkinsfile`) exposes a
`PUBLISH_LATEST` boolean parameter (default **off**). The underlying
publisher (`scripts/ci/run_jenkins_release.sh`) treats `PUBLISH_LATEST=1`
as a promotion run: it retags the already-published, canary-validated
`pipepito/acestream-scraper:${VERSION}` manifest to `:latest`
(`scripts/ci/promote_latest.sh`, `docker buildx imagetools create`) without
rebuilding; otherwise only the versioned and flavor-channel tags ship. This decouples "publish
the new build" from "promote it to the floating `:latest` tag" so the
floating tag can soak before users on `:latest` are affected.

Added 2026-08-28: pre-release builds are available before the release PR
is even opened — every validated `develop` build publishes the floating
`pipepito/acestream-scraper:develop` tag (full payload) plus
`:develop-<flavor>` for `linux/amd64`, `linux/arm64` and `linux/arm/v7`
(`Publish develop channel` stage in `Jenkinsfile` →
`bash scripts/ci/run_jenkins_release.sh --channel develop`; never a
version tag, never `:latest`). Testers soak the candidate on `:develop`
before the `develop` → `main` release PR is cut; preview the channel tags
with `bash scripts/ci/run_jenkins_release.sh --print-publish-plan --channel develop`.

### Recommended flow per release

Prerequisites (operator, once): the Jenkins credential `dockerhub-publish`
exists (scoped to the `Acestream-Scraper` folder so the multibranch job
can bind it for the `develop` channel too) and the `acestream-scraper-release` job's branch specifier points at
`*/main` (`docs/ops/jenkins-ci.md`, "Manual Release Job"). The job refuses
to run from any branch other than `main`. A `DRY_RUN=true` pass first is
recommended — it stops after the full cutover profile and the four-flavor
dry-run preflight without binding credentials.

1. **Initial publish** — run `acestream-scraper-release` with
   `CONFIRM_RELEASE=true`, `DRY_RUN=false`, `PUBLISH_LATEST=false`. The
   pipeline will:
   - Re-verify HEAD == `origin/main`
   - Run the cutover-required-checks full profile
   - Dry-run build + `verify_multiarch_manifest.sh` per flavor
   - Real AceStream engine runtime smoke (amd64), the Acexy runtime smoke,
     and the arm64/armv7 installer-layout tests, then reclaim runner disk
     (`scripts/ci/cleanup_runner_docker.sh`)
   - Echo the publish plan via `--print-publish-plan`
   - Push the versioned + flavor-channel tags only
     (`pipepito/acestream-scraper:v2.0.0`, `:scraper-acestream-acexy`,
     `:v2.0.0-scraper-acestream-acexy`, plus the partial flavors)
2. **Canary** — pin one or more deployments (your own first) to
   `pipepito/acestream-scraper:v2.0.0` for at least 24–48h. Watch
   `/api/v1/health`, scrape jobs, and EPG refreshes.
3. **Promote `:latest`** — once the canary is green, re-run the same
   pipeline with `PUBLISH_LATEST=true`. Nothing is rebuilt or re-tested:
   the run retags the canaried `:v2.0.0` manifest to `:latest` and
   verifies the platforms, so `:latest` is byte-identical to what soaked.
   The partial flavors never receive `:latest` regardless of this flag.
   (`DRY_RUN=true` together with `PUBLISH_LATEST=true` only prints the
   promotion plan.)

### Operator preview

Run `bash scripts/ci/run_jenkins_release.sh --print-publish-plan` (or
`PUBLISH_LATEST=1 bash scripts/ci/run_jenkins_release.sh --print-publish-plan`)
locally to see exactly which tags would be pushed before authorising the
real run. The flag short-circuits before any docker/buildx work, so it
is safe to run on a workstation.
