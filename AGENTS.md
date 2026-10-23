# Codex repository guide

## Private infrastructure authority

Jenkins pipelines and trusted host tooling live in the private
`Pipepito/acestream-scraper-infra` repository. There are no active pipeline sources
in this application repository. Jenkins deploys an owner-reviewed infrastructure
commit as fixed definitions and a checksum-verified tool bundle. Public files,
including any reintroduced Jenkinsfile, cannot select host policy. App tests,
local development commands, dependency manifests and runtime Dockerfiles remain
public. Do not restore retired Jenkins orchestration here. Use
`docs/ops/jenkins-ci.md` for the public CI contract and the private repository for
pipeline changes, policy tests, deployment and release commands. Named runner and publishing helpers below belong to that private repository.
Their public equivalents, where retained for local use, never select host policy.


This is the repository-wide instruction file for Codex. More specific guidance is
layered in `backend/AGENTS.md`, `frontend/AGENTS.md`, and `e2e/AGENTS.md`; Codex
loads the applicable file when working below those directories.

## Start here

- The active integration branch is `develop`; `main` is the release branch.
- The current release PR is GitHub PR #207, `develop` -> `main`, preparing
  v2.2.0. PR #162 is historical and has already merged.
- Treat live PR and CI state as volatile. Before reporting it, run
  `gh pr view 207 --json state,mergeable,mergeStateStatus,statusCheckRollup,updatedAt,url`
  or inspect the PR in GitHub. Local validation is not proof of current CI status.
- `version.txt` records the selected release version (`v2.2.0` for this cycle),
  without a `-dev` suffix. Development images use only floating `develop*` tags;
  versioned tags and `latest` belong exclusively to the manual release from main.
- `backend/` and `frontend/` are the only canonical application roots. Do not
  restore the retired root Flask runtime, root `app/`, root `tests/`, `manage.py`,
  `run_dev.py`, or `wsgi.py`. The root `pyproject.toml` contains legacy package
  metadata and is not the runtime dependency source.
- Read `CLAUDE.md` for the most detailed project narrative. Use this file for
  Codex-specific operating rules and the layered files for implementation details.

## Repository map

- `backend/`: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, APScheduler, pytest.
- `frontend/`: React 18, TypeScript, Vite, MUI v5, React Query v5, Jest/RTL.
- `e2e/`: Playwright/Firefox journeys against the built SPA and real sidecars.
- `Dockerfile`, `docker/`, `entrypoint.sh`: multi-flavor, multi-architecture image.
- the private PR pipeline: administrator-managed isolated PR validation.
- the private owner-approval pipeline: fixed owner-approved revision/image validation.
- the private develop pipeline: trusted `develop` validation and automatic channel image publish.
- the private release pipeline: manual release job, allowed from `main` only.
- `scripts/ci/`: required checks, Docker builds, publishing, and CI helpers.
- `docs/ops/jenkins-ci.md`: authoritative Jenkins and release runbook.
- `docs/migration/development-progress.md`: live migration status.
- `.planning/codebase/`: generated codebase map useful for orientation, not a
  substitute for checking the implementation.

## Working agreements

- Inspect the working tree first. Preserve user changes and unrelated edits.
- Prefer existing patterns and the narrowest change that completes the request.
- Keep the frontend TypeScript-only. Do not add `.js` or `.jsx` application files.
- Keep API endpoint modules thin; business logic belongs in services and DB-only
  access belongs in repositories.
- Use timezone-aware datetimes. Do not introduce `datetime.utcnow()`.
- Do not use `Base.metadata.create_all()` as a production migration strategy.
  Schema changes require an Alembic revision and migration-path tests.
- If an API contract changes, update Pydantic schemas, regenerate
  `frontend/src/types/api-generated.ts`, update services/tests, and verify drift.
- If ports, environment options, or image flavors change, update
  `docs/builder/runtime-options.json` and run the command-builder contract check.
- Changes to sidecar installation/runtime behavior must consider image flavor,
  CPU architecture, supervisor behavior, health probes, and Docker documentation.
- AceStream uses persistent foreground process supervision on every platform:
  retry all exits indefinitely; only UI Stop pauses recovery until Start/Restart
  or container restart. Preserve the supervisor command mailbox, process-group
  cleanup and intentional-stop healthcheck handling. Custom engine commands must
  stay in the foreground. Other sidecars retain their existing fast-exit budget.
- ARM64 and ARMv7 AceStream builds use the matching platform variants from the
  digest-pinned `jopsis/acestream:v3.2.17-fix` OCI image. ARMv7 remains
  experimental until its engine is runtime-tested on real ARMv7 hardware.
- User-facing UI copy is plain, concise, and operational. Preserve both themes,
  responsive behavior, keyboard access, reduced motion, and non-color status cues.
- Do not commit generated/runtime data such as local SQLite databases, E2E stack
  state, Playwright reports, logs, caches, or secrets.

## Verification

Choose checks proportionate to the change and report exactly what ran.

- Routine project-local tests and dependency setup in `backend/venv` or the
  project's `node_modules` are authorized without separate conversational
  confirmation. Prefer cached dependencies on unreliable connections. Respect
  mandatory sandbox controls; this does not authorize global installs or releases.
- Keep validation warning-free. Backend pytest treats warnings as errors,
  including dependency deprecations and SQLAlchemy warnings. Fix the deprecated
  API, dependency or resource lifecycle; do not add global warning ignores,
  disable warnings, or suppress console output to make checks pass.
- Tests deliberately exercising a warning must assert its category and message
  locally with `pytest.warns`. Intentional operator compatibility notices (such
  as the retained legacy environment aliases) remain visible.
- When changing dependencies, verify the resolved versions used in CI, run the
  full gate and retain the warning summary. A cached older local environment is
  not evidence that current CI dependencies are warning-free.

Quick cross-stack gate from the repository root:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/assert_no_legacy_paths.sh --strict
```

Useful focused checks:

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/path/to/test_file.py
cd frontend && npm test -- --runInBand path/to/Test.test.tsx
cd frontend && npm run typecheck && npm run lint -- --max-warnings=0
cd frontend && npm run build:backend
cd e2e && npm run typecheck
python3 scripts/ci/validate_docker_manifest_metadata.py
bash scripts/ci/validate_command_builder.sh
```

Use `bash scripts/ci/run_v2_test_suite.sh --profile full` for broad validation.
Docker packaging/smoke tests are separate and may require Docker/buildx and much
more time. Playwright is valuable for user-visible or integration changes, but is
not part of the required PR gate; see `e2e/AGENTS.md` before running it.

## Branch and release policy

- Feature and hotfix PRs target `develop`.
- Only `develop` may open a PR into `main`; the private PR pipeline enforces this.
- Both protected branches require the `PR Validation` status and disallow direct
  pushes, force-pushes, and deletion.
- A validated trusted `develop` job publishes only floating `:develop*` tags.
  It must never publish `:latest` or version tags.
- Releases are manual through `acestream-scraper-release` on `main`. Publishing
  version tags and promoting `:latest` are separate, deliberate phases.
- Never trigger a release, publish images, promote tags, merge the release PR,
  change branch protection, or mutate Jenkins configuration unless the user has
  explicitly authorized that action.
- Before a release, follow the current checklist in `docs/ops/jenkins-ci.md` and
  `docs/release/v2.2-release-readiness.md`; do not rely on an old PR body.

## Jenkins and infrastructure

- Jenkins is the sole repository validation and release system. GitHub Actions
  application workflows were retired. The PR-assignment workflow only changes
  metadata; GitHub-managed Pages hosting is not the application CI gate.
- The local, git-ignored `infra-details.md` contains the current controller URL,
  operator identity/token, build-agent address, and job names. See
  `docs/ops/codex-infrastructure-access.md` before using it.
- Treat every value in `infra-details.md` as sensitive even if it looks harmless.
  Never quote the file in output, copy values into tracked docs, logs, commands
  likely to be recorded, issue/PR text, screenshots, or test fixtures.
- Infrastructure inspection is read-only by default. Triggering/cancelling jobs,
  replaying builds, changing Jenkins jobs/credentials/nodes, or publishing artifacts
  is an external mutation and needs explicit user authorization.
- PR, trusted `develop`, and release pipelines share the FIFO
  `acestream-scraper-nuc-docker` lock for their full run. Acquire it in the enclosing stage options before allocating an agent, and keep workspace cleanup inside that stage. Although `dorat-nuc-ci`
  has four executors, only one of these Docker/BuildKit workloads may run at once;
  later builds wait and must not abort or prune resources from the lock holder.
- The multibranch PR job and owner-approved image job must live outside the
  trusted publication folder. Neither may inherit publication credentials. Both
  forks and internal branches use administrator-managed definitions; protected
  target commits supply host helpers. Automatic contributor execution stays in
  restricted offline containers with no Docker socket or credentials. Proposed
  dependencies/images require owner approval of immutable head/base/target first.
  See `docs/ops/jenkins-collaborator-safety.md` for mandatory live activation.
- When Jenkins and GitHub disagree, distinguish the Jenkins build result from the
  GitHub commit status and record the commit SHA each result belongs to.

## Code review rules

- Flag any reintroduction of legacy root runtime paths as release-blocking.
- Flag schema/model drift without an Alembic revision or upgrade-path test.
- Flag API changes without generated-client and frontend service/test updates.
- Flag SSRF regressions in scraper/EPG URL handling or accidental weakening of
  optional API-token enforcement.
- Flag secrets, local infrastructure coordinates, or credentials in tracked files.
- Flag release/channel logic that could publish `:latest`, a version tag, or Docker
  credentials from an unvalidated/non-release context.
- Flag blocking I/O added to async request paths or unbounded work moved into app
  startup. The deferred v1 EPG migration must remain resumable and non-blocking.
- Flag platform assumptions that silently drop amd64, arm64, or arm/v7 behavior.

## Documentation expectations

- Update the nearest durable document when behavior, commands, deployment, or
  operator procedure changes.
- Keep `CLAUDE.md` and the applicable `AGENTS.md` aligned when changing a core
  workflow that both agents need to know.
- Do not turn dated CI status into timeless documentation. Label snapshots with a
  date and commit, and include the command/source future agents should recheck.

## Playback routing

TV relay startup limits are saved tuner settings (15 seconds per source and
45 seconds total by default; each accepts 5–180). Stall detection is 25 seconds.
Only client disconnects defer the final direct-engine stop by five seconds;
deadline failures stop immediately. Cancelled timer callbacks must verify they
still own the pending session before stopping anything. Retained sessions stop
exactly once when the final lease is released. Optional `per_source` playlists
retain filters, guide IDs and reverse-proxy prefixes. See `wiki/Media-Servers.md`.

`GET/PUT /api/v1/config/playback-routing` persists `use_acexy` and `acexy_url`
as one JSON setting. Direct mode is the default. Web-player and tuner factories
use `playback_client_from_settings`; engine health/probes remain direct.
Acexy mode reads MPEG-TS from `/ace/getstream?id=…` with no PID or engine JSON
start/stat/stop calls. The session retains its Acexy ownership flag across
configuration changes so cleanup never stops another proxy client. Remote
players use the server relay in Acexy mode, bypassing saved custom link formats;
direct mode honors their formats and adds a unique PID to direct engine links.
Existing shared browser sessions retain their route until teardown. See
`wiki/Remote-Players.md#playback-routing` for operator behavior.

## Runtime diagnostics

All image flavours inherit bounded console capture from `backend/capture_logs.py`
in the shared image layer. Capture scraper, each service and entrypoint output
in separate rotating logs. Prefix Docker console lines with their service tag;
keep local capture content unchanged. WARP TRACE/DEBUG/INFO records are console-filtered only;
retain all levels in `warp.log` and keep issues and lifecycle messages visible.
Preserve other Docker console output, child PIDs/exit codes,
process-group cleanup and intentional-stop behavior. The DB-independent
`GET /api/v1/system/diagnostics` endpoint exports bounded fixed-file tails with
credential masking and normal API-token enforcement, including during startup
failure. Overview provides the download. See `docs/ops/runtime-diagnostics.md`.

## Verified signal and scheduled job history

Catalogue imports do not imply online status. Channel probes separate engine ID
lookup (`network_status`) from media delivery (`is_online`); require identified A/V
packets before claiming signal. Keep timeout/engine errors distinct from explicit
ID-not-found responses. See `docs/ops/stream-check-pid.md`.

Scheduled job launch times and outcomes persist in `scheduled_task_states`; restore
after schema upgrade off the event loop and mark unfinished runs interrupted. Keep
scalar results valid in the status API. See `docs/ops/scheduled-job-history.md`.


## Dedicated checking engine and playback ownership

`ENABLE_ACESTREAM_CHECK_ENGINE=true` opts bundled-engine images into a second
persistent supervised engine (state `/var/lib/acestream-check`, HTTP 6880,
legacy API 62063, P2P 8622). Alternatively, `ACE_CHECK_ENGINE_URL` selects an
external checker. Never fall back to playback when a configured checker fails;
preserve previous channel results. Keep checker supervision, controls and logs
independent; checker outage must not fail whole-container health. Direct playback
uses process-wide source ownership leases across clients; serialize starts with
final stops, release exactly once, and preserve session ownership across settings
changes. Acexy owns its sessions. See `docs/ops/stream-check-pid.md`.

## Live TV and settings navigation

Live TV embeds the existing HLS player alongside a scrollable catalogue. Filtering
does not release playback; changing the channel or Stop watching releases the
current viewer. Other pages retain the player dialog. Navigation groups Watch,
Manage and System, with WARP always discoverable. Settings uses deep-linkable
`?tab=playback|automation|links|access` sections; public address belongs to
Integrations. PID/AppID belong to Stream links, not Automation.


## TV channel inventory and playlist formats

TV Channels combines catalogue-wide filters before sorting and pagination. Number
and Favorite have dedicated controls in the table and phone cards; number changes
save on Enter/blur and blank clears the number. Keep remaining row actions intact.
Playlist shows the selected stream format and expands the shared
`StreamLinkFormatsSection` inline, preserving playlist options. Settings retains
its Stream links entry because formats also affect copied links and supported
remote-player actions. Do not fork the format editor or duplicate its API logic.

TV Channels keeps Search, Category, Status and Favorite filters visible; other
filters live under Advanced filters with an active count. Reorder channels shows
the complete catalogue, supports drag handles and keyboard/arrow controls, and
previews consecutive numbers. Save order uses `POST /api/v1/tv-channels/reorder`
with the complete desired IDs and original order; the backend commits all numbers
atomically and rejects stale/incomplete inventories. Cancel leaves stored numbers
unchanged. Number edits remain available outside reorder mode.


Engines are optional. Settings → Automation stores external checker selection via
`/api/v1/config/check-engine`; disabled dedicated checks use the saved playback
URL, and with neither URL probes are skipped without changing channel results.
A configured dedicated checker never falls back on failure. Bundled checker
configuration remains supervisor-owned and read-only in Settings. New scraper-only
installs default to an empty playback URL; existing saved endpoints are preserved.

Bundled ZeroNet supports amd64 and arm64. Keep its downloaded sites and `.node/`
configuration/private state within `ZERONET_DATA_DIR`. Legacy `sites.json` and
`users.json` are copied into `.node/private` only when absent; never overwrite
migrated state or delete the originals during startup.

GitHub Pages serves `main` at `/docs` (repository settings verified 2026-09-15).
Jenkins must not publish Pages or Docker Hub descriptions. Prepare the standalone
helper with `bash scripts/ci/prepare_pages.sh` and commit `docs/recipes/` alongside
its source changes; full CI checks the built payload for drift. The manual release
job mirrors `wiki/` only after successful, non-dry-run latest promotion, using
`github-publish`. Docker Hub text in `docs/dockerhub/` is copied to the page manually.


Scheduled maintenance jobs share a FIFO queue; due jobs show Waiting and run-now
requests do not duplicate running/waiting jobs. Settings → Automation stores
optional start times/timezone in `schedule_anchors`, preserving existing intervals.
Stream-check results distinguish online/offline/skipped/errors; never label the
exception count as offline. See `docs/ops/scheduled-job-history.md` for clock/DST
semantics, queue scope and database recovery behavior.

## Release version protection

The manual release reads `version.txt`. Phase 1 refuses an existing base version
or versioned flavor image unless `FORCE_VERSION_OVERWRITE=true` is explicitly
selected in Jenkins (CLI: `FORCE_VERSION_OVERWRITE=1`). Registry lookup failures
always block. Checks run before preflight, after login, and before tag assignment;
the FIFO Jenkins lock serializes local publishers, but external publishers must
not race the same version. Channel tags and canary `:latest` promotion remain
separate. Both `PUBLISH_LATEST` and the force option reach dry runs. After successful non-dry-run latest promotion, Jenkins publishes the Git tag
and GitHub release from the promoted image’s commit and canonical Markdown.
Never overwrite mismatched tags/releases. See `docs/ops/jenkins-ci.md`.

## Pipeline artifact retention

Keep develop gate reports/logs once in `.ci-develop-artifacts/`, the aggregate
architecture report, and channel/release metadata. Per-flavor dry-run JSON plans
are temporary validator inputs; per-platform publication option JSONs are no
longer generated. Release dry runs retain one explicitly marked preflight summary.
Clear prior reports before stages, preserve failure diagnostics, and retain manual
full-profile hardware evidence. See `docs/ops/jenkins-ci.md`.

## Engine cache retention

Bundled playback/checker engines use native 64 MiB RAM live caching; other-content
disk-cache limits are 512/256 MiB respectively, not total filesystem/RAM quotas.
The supervisor reclaims default cache files before launch/recovery and after UI
Stop, only after terminating the prior process group. Preserve identity/state,
symlinks, open/mapped files, private per-container cache ownership, and fail-closed
process inspection. Never run this stopped-engine cleanup against a live engine.
Custom cache paths and external engines are not swept. See
`wiki/Docker.md#engine-cache-retention`.

Release phase-1 validation (including dry runs) uses the same prepared runner and
full application gate as develop via `scripts/ci/run_release_validation.sh`. Keep
Python/Node dependencies ready before backend tests, validation isolated from
Docker/credentials, and reports in `.ci-release-artifacts/`. Docker smokes run
later on the trusted host with an explicitly prepared backend virtualenv.

## Documentation and CI scope

Keep README high-level; user/contributor guides live in `wiki/`, and the Docker
Hub overview source is `docs/dockerhub/`. `classify_changes.py` selects lightweight
documentation validation for known docs-only changes. PRs use private-policy
selection/validators; develop compares the last successful build. Missing or
rewritten baselines, symlinks/mode changes, and unknown paths require the full gate.
Develop validates documentation without publishing it. Wiki publication belongs
to release promotion; Pages serves main/docs and Docker Hub text is manual.
Keep manual releases fully validated and preserve the FIFO Docker lock and fork
isolation. See `docs/ops/jenkins-ci.md` for exact paths and retry behavior.


## User-defined extraction recipes

Sources may persist a versioned `extraction_recipe`; null retains automatic
extraction. The installed and Pages helpers share `frontend/src/recipes/` and a
fixture-tested catalogue. The public helper never connects to an installation.
Preview/fetch endpoints write no source or channel data; production regex runs in
a bounded disposable worker. Preserve pairing within records, pinned fetch
destinations, sandboxed HTML previews and existing channels on recipe errors.
Prepare and commit the standalone helper under docs/recipes before release.
See `docs/dev/extraction-recipes.md` and `wiki/Extraction-Recipes.md`.

## v2.1 configuration

v2.1 retains the six deprecated environment names through Settings, including
`.env` support and value-free warnings in logs/Overview. Nonempty canonical names
win. Keep repository defaults on resolved Settings and preserve entrypoint alias
selection before bundled-service defaults. Removal (#155) is deferred by maintainer
decision. See `docs/release/v2.1-release-notes.md`.

## Source fetches and EPG responsibilities

Use `app/utils/outbound_http.py` for user-supplied source fetches, including nested
M3U and iframe URLs. It pins validated DNS answers, guards redirects and preserves
TLS/Host identity without inheriting environment proxies. Keep private-source
defaults and configured gateway exemptions; metadata addresses are always denied.
`EPGService` remains the public interface over `epg_sources`, `epg_xmltv`,
`epg_channels` and `epg_export`; they share its session and method surface.


Stream checks store one nullable `stream_stats` observation (peers, engine
Kbytes/sec download/upload rates and UTC timestamp). Keep it separate from encoded
media bitrate and verified signal. Replace samples atomically, preserve zero vs
unknown, and retain original observation times on skips or missing measurements.
Manual, bulk and scheduled checks share the bounded sampler and existing queue.
See `wiki/Stream-Statistics.md`.


Overview storage uses a DB-independent, authenticated `/api/v1/system/storage`
report. Discover container mount destinations without exposing mount sources or
using the Docker socket. Keep scans cached, isolated, bounded, symlink-safe and
off the event loop; partial/unknown sizes must not be shown as complete or zero.
Free space belongs to a filesystem, not each directory. See `wiki/Storage.md`.
Preview upload admission and byte/deadline limits precede JSON parsing. Keep
32 MiB source support separate from the bounded browser rendering budget; heavy
sources retain raw/manual-field workflows and installed extraction tests.

## ARM engine startup and DNS ownership

Pinned OCI engine payloads must enter through `aceserve.main()`; direct
`Core.run()` skips distribution initialization and can return `mod_detected`
while health checks pass. The preserved `main.py.oci-orig` selects the OCI path;
legacy APKs retain Core. Keep persistent homes, per-install identity and process
supervision intact. Playback/checker processes share `/dev/socket/dnsproxyd` via
`bionic_dns.py`: hold its file lock throughout the listener lifetime, never delete
the lock file, and let the surviving engine take over after owner exit. Never
start competing upstream listeners that can unlink each other's socket. See
`docs/ops/arm64-mod-detected.md` for live-test scope and remaining network limits.

WARP auto-connect (`WARP_ENABLE_NAT=true`) must wait for JSON status Connected,
not merely a successful CLI call, before engines start. The ARM resolver follows
container nameserver changes and retains the last valid configuration during a
partial rewrite. Keep WARP opt-in; direct-route lookup failures must not trigger
automatic routing changes. See `docs/ops/arm64-mod-detected.md`.

## Reviewed guide setup

EPG Matching defaults to a read-only preview with explicit row selection. Apply
rechecks the complete source scope and rejects changed `expected_previews` before
writing. Preserve assignments and source-qualified guide identity; ambiguous
matches are never chosen by row ID. Settings → Automation stores opt-in
`epg_matching` (off by default); successful scrapes/EPG refreshes apply only
unambiguous exact matches off the event loop after ingestion commits. Keep its
last result visible and failures independent of ingestion. Playlists and XMLTV
share collision-safe IDs and validated token propagation for guide discovery.
See `docs/ops/guide-matching.md`.

## CI runner reuse and retention

PR, develop and release share `build_pr_runner.sh` and `docker_lifecycle.py`.
Runner identity includes committed dependency inputs, the pinned Dockerfile and
platform; never select a mutable legacy runner tag or execute fork policy on the
host. Keep the FIFO lock for the full run. Cleanup retains recent runners/warm
cache, escalates under disk pressure, protects explicit keeps and all container
references, and reports failures. Do not restore blanket unused-image pruning or
permanent keep labels. See `docs/ops/jenkins-ci.md` for retention and rollout.


## Pipeline responsibilities

The PR job uses an administrator-managed pipeline, never a branch's Jenkinsfile.
Fork and origin PRs use the same pinned protected-target orchestration and isolated
checks. Application PRs wait for a separate owner-approved job bound to exact head,
base and target; it runs the full gate and every supported image combination without
publication. Dependency changes wait for this approval before installation. The
parent releases its Docker lock before waiting; each job holds the shared FIFO lock
for its complete Docker workload and cleanup. Only owner-merged protected develop
commits may publish floating tags; main releases remain manual. Pipeline definition,
credential/ACL and GitHub ruleset activation is required before inviting writers;
see `docs/ops/jenkins-collaborator-safety.md`. Buildx cleanup enumerates
`.Builder.Name`, deduplicated, never child-node `.Name`.

BuildKit numeric GC limits are bytes: convert the operator MiB settings before
writing `reservedSpace`/`maxUsedSpace`. Under pressure, reclaim unused old cache
without a size floor before recent cache or runners, and allow bounded time for
asynchronous Docker disk reclamation. Never reduce the required free-space gate.

Guide matching treats an imported stream ID as authoritative only if it resolves
in any imported guide, including disabled or out-of-scope sources. Unknown IDs
fall through to names without being overwritten; apply revalidates the complete
ID inventory. Keep indexed ID candidates, bounded name comparisons, ambiguity,
country/edition and assignment guards. Reviewed matching strips publisher text
after `-->`; automation still requires conservative agreement of every name.


Startup catch-up restores persisted launch history before scheduling overdue
interval guide/scrape work after a five-minute grace, staggered five minutes.
Stream checks re-evaluate eligibility after fifteen minutes. Preserve explicit
clock anchors, FIFO/run-now deduplication and launch-based retry semantics; never
bring destructive cleanup forward. See `docs/ops/scheduled-job-history.md`.

Catalogue status passes wait between probes for app-owned relay/web playback,
with a cumulative ten-minute pause budget and no DB transaction while waiting.
Budget expiry or shutdown reports deferred work and a stop reason, releases the
FIFO, and preserves truthful Overview/webhook summaries. Direct external-engine
players are outside this registry-based guard.

Stream-check ordering gives never-checked streams priority, then oldest age
groups measured in saved check intervals. Favorites and TV assignments win
within an age group; they must not starve older loose streams across interrupted
passes. Keep the inventory query in ChannelRepository and ordering in the status
service. See `docs/ops/scheduled-job-history.md`.

Direct-engine JSON startup shares the caller's existing budget: TV relays pass
one deadline capped by per-source and remaining total limits; browser sessions
use their remaining `PLAYER_START_TIMEOUT_SECONDS`. Charge worker/source-lock
waiting to that deadline. Preserve source leases and collect late start replies
on cancellation before releasing clients/slots; disconnect linger remains
separate from immediate deadline cleanup. See `wiki/Media-Servers.md` and
`wiki/Web-Player.md`.

## Repository contribution governance

`.github/rulesets/` records intended live GitHub rules; merging JSON does not apply
it. Baseline main/develop rules require PRs, resolved conversations and the
Jenkins-bound `PR Validation`, without bypass. A separate one-approval rule allows
automatic exemption for Pipepito as the merging user (not by PR author); it
cannot bypass baseline CI. Collaborators still need approval when merging.
Version tags are immutable. `.github/workflows/assign-pull-requests.yml` assigns
other authors' PRs to Pipepito using metadata only: never check out or execute
contributor code in `pull_request_target`. Issue forms and assignment activate
after reaching default branch main. See `docs/ops/repository-governance.md`.

Contribution-only CI recognizes direct issue-form YAML, ruleset JSON, and the
named assignment workflow. A private-policy metadata validator and integrity-locked
YAML parser read them as data; assignment behavior must match the trusted contract.
No application/image work runs for this scope. Unknown workflows, app/dependency
changes, metadata-validator changes and mode/symlink changes keep the full gate.
PR selectors cannot exempt their own changes; the policy must reach the target
branch first. See `docs/ops/jenkins-ci.md`.

## Gluetun forwarding and changelog

`ACESTREAM_GLUETUN_PORT_FILE` opts the bundled playback engine into shared-file
P2P port synchronization. Only its supervisor applies validated, debounced port
changes, preserving UI Stop and process-group cleanup. The checker keeps port
8622; custom commands/external engines are not managed. See `wiki/Gluetun.md`.
The `/changelog` page bundles version history; reading/dismissing its notice is
per browser. Edit `frontend/changelog/vX.Y.Z.md` alongside `version.txt` and run
`cd frontend && npm run changelog`; never hand-edit the generated data.
Never imply development notes establish stable publication. See
`docs/dev/gluetun-changelog-v2.2.md`.

Published stable update checks use the cached, authenticated system API; failures
remain quiet and the changelog stays offline. Announce each newer version once
per browser, with manual Docker/native instructions; never auto-update. Release
notes and promotion provenance are documented in `docs/ops/release-notes.md`.


Browser playback accepts imported `url:` IDs as well as AceStream IDs. Resolve
stored broadcaster links at session start; HTTP input uses a session-owned
loopback proxy over `outbound_http.source_session`. Rewrite every HLS resource,
including keys/maps/audio/subtitles; never hand upstream manifests or URLs directly to
FFmpeg. Preserve source headers, redirect/SSRF guards, bounded manifests and
resource inventories, shared audio/subtitle selection, startup budgets and cancellation
cleanup. HTTP sessions must not start/probe/stop AceStream or expose signed URLs.
See `wiki/Web-Player.md`.

Browser subtitle selection defaults to Off. Share sessions only for identical
channel/audio/subtitle choices; changing either track releases only that viewer.
Text subtitles use the same FFmpeg HLS clock as video. Normalize bounded HLS
WebVTT timestamp maps in the guarded input proxy; preserve `.vtt`/`.webvtt`
extensions and authenticate subtitle playlists/segments, including query-token
propagation for native HLS. Bitmap subtitle conversion is unsupported.

The isolated CI runner builds the same minimal FFmpeg from the runtime manifest
and build script; include both in trusted exports, cache keys and fork guards.
Keep Debian FFmpeg only as `FFMPEG_TEST_TOOL_PATH` for synthetic media fixtures.
See `docs/ops/jenkins-ci.md#ffmpeg-in-the-isolated-validation-runner`.


## W3U catalogues

`/catalogues` keeps W3U hierarchy separate from TV assignments. Preview is read-only;
opaque expiring tokens and catalogue revisions protect save. Traverse only bounded
structured child documents through `outbound_http.source_session`; never execute
publisher scripts or treat arbitrary page/image URLs as media. Imports reuse the
channel repository and shared player. Preserve existing channel metadata and all
channels on partial refresh, deselection and catalogue removal. Scheduled refresh
is opt-in within the existing scrape queue. Public DTOs expose source hosts and
header names only. See `wiki/W3U-Catalogues.md` and `docs/dev/w3u-catalogues.md`;
W3U event imports use the shared reviewed EventImport contract; VOD and unsupported host resolvers remain separate.


## Sporting events foundation

`/events` stores schedules separately from channels. Use versioned `EventImport`
observations, stable source/external IDs, read-only previews and explicit selected
rows. Refresh preserves manual corrections and missing broadcasts; cross-source
association is explicit. Require source timezones, reject ambiguous/nonexistent
local times without an offset, and never infer live state or media signal from
clock/import. Event-only HTTP media uses the shared guarded player without TV
assignments or playlist export. Following is installation-wide; archive is
reversible until opt-in retention deletes eligible rows. W3U entries have an explicit reviewed event bridge; Telegram transport remains separate; no guide overlay is offered here.
See `docs/dev/sporting-events.md` and `wiki/Sports-Events.md`.


Sporting-event URL sources accept reviewed version-1 schedules or bounded
SportsEvent JSON/HTML JSON-LD with stable IDs and explicit timezone/date rules.
Only approved, still-present event identities refresh through `url_scraping`'s
FIFO/catch-up; new rows require review. Retention defaults off and runs during
existing daily cleanup, protects followed events and never deletes permanent
channels. Preserve source revisions, manual broadcaster mappings, archive clocks
and private guarded artwork fetching. See `docs/dev/sporting-events.md`.


Combined catalogues/events use migration revision `20261023_1400`, preserving both
prior histories. Catalogue live imports require explicit confirmation; refresh
imports only previously reviewed entry identities. Explicit event/VOD types cannot
become permanent channels. Catalogue event preview reuses private snapshot inputs;
apply reserves both catalogue revision and source UUID. Never infer times from
folder names or automatically refresh W3U event schedules. See
`docs/dev/w3u-catalogues.md#combined-catalogue-and-event-integration`.


Collaborator-safe CI keeps administration with the owner; other Jenkins logins are
read-only. The approved PR job checks GitHub metadata using the discovery App in
agent-none controller stages before/after the host workload. Never move those
HTTP requests into a node/agent context or bind their token in shell code. Older
targets missing metadata validation or the reusable FFmpeg runner use the fixed
administrator-pinned policy bundle, with dependency comparisons against the
selected runner ref. See `docs/ops/jenkins-collaborator-safety.md`.

## Telegram account sources

Telegram uses one encrypted user-account session outside the DB/config/log tree,
with an independently mounted Fernet key and mandatory `TELEGRAM_ADMIN_TOKEN`.
All Telegram endpoints require this header credential and HTTPS or localhost;
never return/log API hashes, session strings, codes or passwords. Keep transports
separate from the bounded recipe worker and additive ingestion. Source cursor and
message observations commit with imports; never call URL snapshot deletion from
a message consumer. Preserve stable sender IDs, membership checks, bounded queues,
flood waits, session lease and retained-revision reconciliation. New sources default
to new messages only; pause retains progress. See `wiki/Telegram-Sources.md`.

Telegram migration `20261023_1500` follows catalogue/event revision `20261023_1400`.
Keep the W3U `20261022_1200` identity unchanged; Telegram must not reuse it.
See `wiki/Telegram-Sources.md#database-upgrades`.
