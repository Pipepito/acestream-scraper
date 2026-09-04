# Final verification — feature/media-integrations

Run 2026-09-04 on the branch head, no code changed. This is the document to read
instead of trusting the branch. The gates all pass; the last section is the part
that matters, because it lists what the gates do not cover.

- Branch: `feature/media-integrations`
- Merge-base with `origin/develop`: `0e76c66f10e37f1bddcb69a0d42ba88220e90aa3`
- Head: `1052226bdb2489133e4756765d5abe6824f79978`
- **93 commits, 201 files changed, +24 292 / −3 431**
- Working tree clean before and after the whole verification pass.

By area: 60 files under `frontend/src`, 49 under `backend/app`, 40 under
`backend/tests`, 8 under `e2e/`, 4 `scripts/ci`, 4 `docs/ops`, 5 `wiki/`,
plus Dockerfile / entrypoint / vendor changes.

## Gate results — 11 required, 11 pass, 0 fail

| # | Gate | Result |
|---|------|--------|
| 1 | `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker` | **PASS** — 924 passed, 0 failed, 104 warnings, 146.41 s, exit 0 |
| 2 | `cd frontend && npm run lint -- --max-warnings=0 && npm run typecheck && CI=true npm test -- --watch=false && npm run build` | **PASS** — eslint 0 problems at `--max-warnings=0`; `tsc` clean; 55 suites / 334 tests passed; `vite build` ✓ in 919 ms; exit 0 for the whole chain |
| 3 | `bash scripts/ci/run_v2_test_suite.sh --profile quick` | **PASS** — "Canonical v2 test suite passed for profile=quick", exit 0. The ARM docs-contract guard runs first in this script (line 46) and passed |
| 4 | `bash scripts/ci/assert_no_legacy_paths.sh --strict` | **PASS** — "Legacy path assertion passed.", exit 0 |
| 5 | `bash scripts/ci/validate_command_builder.sh` | **PASS** — 4 flavors, 8 ports, 4 volumes; `app.js` syntax ok; exit 0 |
| 6 | `python3 scripts/ci/validate_docker_manifest_metadata.py` | **PASS** — "Docker manifest metadata validation passed.", exit 0 |
| 7 | `python3 scripts/ci/validate_docker_docs_contract.py` | **PASS** — 25 checks, all PASS, exit 0 |
| 8 | `bash scripts/ci/publish_wiki.sh --dry-run` | **PASS** — flattened page set and rewritten links rendered, exit 0 |
| 9 | `alembic … heads` + `pytest backend/tests/test_schema_parity.py` | **PASS** — exactly one head, `20260903_1200 (head)`; parity 7 passed |
| 10 | `backend/openapi.json` + `frontend/src/types/api-generated.ts` byte-identical to a fresh regeneration | **PASS** — regenerated via `backend/scripts/dump_openapi.py` then `npm run codegen`; `cmp` reports both **IDENTICAL**; originals restored is moot (nothing changed) |
| 11 | `git status --short` clean; commit count vs `origin/develop` | **PASS** — status empty; `git log --oneline origin/develop..HEAD \| wc -l` = **93** |

### Supplementary (not a required gate): `backend/tests/docker`

Excluded from gate 1 by the task, but a Docker daemon is available on this host,
so it was run rather than left as an unknown: **53 passed, 3 failed** in 113 s.

All three failures share one root cause, and it is not this branch:

```
install-zeronet: the amd64 ZeroNet payload can only be built on an amd64 build host
                 (got aarch64); pip would embed wrong-arch wheels
```

This is an Apple-Silicon host; the ZeroNet installer deliberately refuses to
build the amd64 payload here, and the three failing tests
(`test_install_zeronet.py::test_zeronet_installer_stage_produces_working_launcher`,
`test_install_acestream.py::test_scraper_acestream_runtime_has_python310`,
`test_acestream_runtime_smoke.py::test_scraper_acestream_starts_real_engine[linux/amd64]`)
all build a target whose graph includes that stage. `install-zeronet.sh`,
`docker/zeronet/**` and every ZeroNet line in the `Dockerfile` are byte-identical
to `origin/develop`, so the branch cannot be the cause. The honest statement is
that these three are **unverified on this host**, not that they are broken — and
that the tests should skip rather than fail on a non-amd64 builder, which is a
pre-existing hygiene issue on `develop`.

Notably green in that run: `test_ffmpeg_build.py` and `test_ffmpeg_vendor.py`,
8 passed — the real static ffmpeg is built for every image platform and made to
remux, transcode and produce an HLS ladder from the committed
`sample-h264-ac3.m2ts` fixture.

## What on this branch has NEVER been executed anywhere

Read this section as the actual risk register. Everything above is green; these
are the places where green means nothing.

### 1. The two deterministic playback e2e tests — never run, on any machine

`e2e/tests/10-integrations.spec.ts`:
- `'a channel plays end to end against a deterministic engine'` (line 110)
- `'the same channel is attempted against the real engine'` (line 160)

Both begin by reading `/api/v1/player/capabilities` and calling `test.skip()`
when `ffmpeg_available` is false. **This host has no ffmpeg** (`which ffmpeg` →
not found), so both have skipped on every run recorded in the ledgers — the Plan 4
Task 7 entry says "e2e journey 3 passed / 2 skipped (no ffmpeg on this host, so
the two playback tests never ran)", and the Task 7 ruling records it as "the one
outstanding verification gap". Nothing since has changed that. The assertions
inside them have never executed.

**Unproven as a consequence:** the browser-facing half of the web player, as one
chain — `PlayerService` spawning ffmpeg against a live engine stream, the HLS
playlist and segments it writes, the backend serving them, hls.js in Firefox
reaching `readyState >= 2`, the dialog reporting "Playing", and — on close — the
session reaper telling the engine to stop within its 5 s tick.

**Partial mitigations, and their limits:**
- `backend/tests/fake_ffmpeg.py` is a Python stub that writes segment files. It
  proves the session lifecycle but exercises **no real ffmpeg argument**.
- `backend/tests/docker/test_ffmpeg_build.py` *does* run the real static ffmpeg
  with the production player argv against the fixture and asserts an HLS ladder
  comes out, on every image platform (passed here). That closes "the command line
  is wrong" — but `PLAYER_COMMAND` in that test is a **hand-maintained copy** of
  the argv in `player_service.py:143-148`, not an import, and **no test asserts
  the two stay in sync**. They match today; verified by inspection during this
  pass. They can silently diverge on the next edit.
- The stub engine + tuner relay were verified end to end (2.8 MB at ~470 KB/s)
  per the Task 7 ruling, so the relay path is not blind — but that path does not
  involve ffmpeg or a `<video>` element.

**Residual risk: moderate-to-high, and concentrated on the user's first
impression.** The failure mode is a player dialog that never leaves "Preparing"
in a real deployment, and neither the unit suite nor CI would say so. Anyone who
merges this should run `cd e2e && npm test` on a host with ffmpeg, or
`npm run test:docker` (the container has ffmpeg), before calling the web player
verified. Note that the deterministic test additionally self-skips under
`E2E_TARGET=docker` (the stub engine listens on loopback), so `test:docker`
covers the *real*-engine variant only.

### 2. Every third-party integration, against real software — never attempted

Jellyfin, Plex, Kodi and VLC are reached **only** through
`httpx.MockTransport` with hand-written fixtures (`backend/tests/test_media_servers.py`,
`test_remote_player_drivers.py`, and friends). The e2e suite does not close this:
its "unprotected VLC" is a 30-line Node `http.createServer` that answers 403
(`10-integrations.spec.ts:24`). No Jellyfin, Plex, Kodi or VLC instance —
containerised or otherwise — has been contacted by any code on this branch.

**This is the single largest unverified surface on the branch.** The mocks encode
*this implementation's belief* about four external APIs: paths, auth header names
(`X-Emby-Token`, `X-Plex-Token`), query-parameter shapes, DVR discovery, refresh
semantics, and error bodies. A wrong path, a wrong header, an auth scheme that
changed, or a response shape that differs by one level of nesting **passes every
test on this branch and fails on first contact with the real product**.

**Residual risk: high, per integration, and independent.** Four separate chances
to ship something that has never worked. The failure is loud and early (a "Test
connection" that fails for the user immediately), which is the merciful version —
but it will be discovered by a user, not by CI. Recommend a manual smoke against
at least one real Jellyfin and one real Plex before this reaches `main`; Kodi and
VLC are lower stakes but equally unproven.

### 3. HDHomeRun emulation, against a real tuner client — never attempted

`/tuner/discover.json`, `/tuner/lineup.json`, `/tuner/lineup_status.json` and the
`/tuner/{id}` relay are asserted **for JSON shape only** (contract tests plus
`10-integrations.spec.ts` lines 90-108). No Plex DVR, Emby, Channels DVR or real
HDHomeRun client has ever consumed these endpoints. The device-id checksum
algorithm is libhdhomerun's, verified against corrected test vectors — but a
tuner client's actual acceptance criteria (`DeviceAuth`, tuner-count semantics,
the exact `BaseURL` it will follow, whether it tolerates the relay's chunked
response) are unproven.

**Residual risk: high.** "Plex does not see the tuner" is the plausible outcome,
and nothing in the suite can distinguish that from success.

### 4. The LAN scan, against a real network — never attempted

`backend/app/services/remote_players/scan.py` has only ever run against mocked
transports. It has never scanned a real subnet with real VLC/Kodi devices on it.
The 30 s budget bounding only the TCP connect phase was raised as a concern in
Plan 3 and given a `classify()` deadline check in Plan 4's carry-forward wave —
that fix is unit-tested but has never met a real dense subnet.

**Residual risk: moderate.** Worst realistic case is a scan that is slow or finds
nothing, not one that is wrong.

### 5. ARM and ARMv7 runtime, and the amd64 runtime image

Per §"Supplementary" above, the amd64 acestream runtime smoke could not build on
this aarch64 host, so **no full runtime image containing this branch's entrypoint
and ffmpeg changes has been started on amd64 here**. The ARM engine's premium
gate is documented and guarded by `test_docs_contract.py` (prose assertions, not
behaviour). ARMv7 playback remains impossible-by-design (official APK, premium-
gated) and is documented as such.

**Residual risk: moderate.** `entrypoint.sh`'s `FFMPEG_BINARY_PATH` clearing logic
does have tests that actually execute the script in both states (Plan 2 Task 2 fix
round), and `runtime-base` was image-checked (`IMAGE_HAS_FFMPEG=true`, static
ffmpeg 8.1.2) during Plan 2 — so this is thinner than the items above, but the
composed image has not been booted end to end on the branch head.

### 6. The e2e journey as a whole was not re-run in this pass

Gates 1-11 do not include `e2e/`, and it is explicitly not part of the required
`PR Validation` checks. The last recorded full run is Plan 4 Task 7's
(3 passed / 2 skipped for the integrations spec). Roughly 50 commits of polish and
fix waves have landed since, including frontend changes to `Integrations.tsx`,
`TVChannels`, the player relay list and the volume slider. **Nothing has re-run
the browser journey against those changes.** The frontend jest suite (334 tests)
covers them at component level.

**Residual risk: moderate.** Component tests are good here, but selector-level and
navigation-level regressions are exactly what jest does not catch.

## Verdict

Every required gate passes, the working tree is clean, the API artifacts are in
sync with the code that generates them, and there is a single Alembic head. On
the evidence of the automated suites this branch is mergeable into `develop`.

What it is **not** is verified. Three of this feature's four headline user
journeys — play in the browser, cast to a device, appear as a tuner in Plex —
have never been executed against the real thing they exist to talk to. The suites
prove the code does what its authors believed the outside world expects. They
cannot prove the belief. Merge to `develop` on that basis if `develop` is where
that gets found out; do not promote to `main` until the ffmpeg e2e run and at
least one real Jellyfin/Plex smoke have happened.
