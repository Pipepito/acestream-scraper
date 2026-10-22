# v2.2 Gluetun sync and in-app changelog

Plan accepted 2026-10-22; baseline develop `b8b06f7`. Feature branch:
`codex/v22-gluetun-changelog`, PR #254. Releases remain operator-triggered;
GitHub notes publish automatically only after successful latest promotion.

## Implementation scope

1. Add opt-in shared-file Gluetun forwarding for the bundled playback engine.
   Read bounded decimal ports, reject conflicts/symlinks/non-regular files,
   debounce changes, and restart only through the existing supervisor. Preserve
   UI Stop, indefinite recovery, cache cleanup after process-group teardown,
   all packaged architectures and independent checker ownership.
2. Keep custom commands and external engines outside this automatic port owner.
   Keep Gluetun networking/provider configuration operator-owned. Document
   read-only directory mounting, networking, restart impact and failure behavior.
3. Add bundled `/changelog` version history and a dismissible per-browser update
   notice. Use canonical Markdown for the bundled history and post-promotion
   GitHub notes. Add a separate once-per-version published-update notice with
   manual Docker/native instructions. Preserve themes and small screens.
4. Audit all open issues against current develop, reconcile metadata and #207,
   and distinguish implemented work from partial or unverified proposals.
5. Validate parser and supervisor behavior, launch arguments, frontend interaction,
   navigation, responsive layouts, command-builder facts and the cross-stack gate.

## Release history maintenance

Edit the version Markdown in `frontend/changelog/` and run
`cd frontend && npm run changelog`. The committed TypeScript is generated;
builds reject drift. See [release notes](../ops/release-notes.md) for the complete
single-source and publication contract.

The installed-build notice is acknowledged by reading or dismissing it.
A separate published-update notice checks stable GitHub releases through the
cached backend endpoint and announces each newer version once per browser.
It gives manual Docker/native update instructions and never installs updates.
Offline failures do not affect the bundled changelog.

## Open-issue audit

Snapshot 2026-10-22 at develop `b8b06f7`; all 21 open issues were reviewed.
Recheck GitHub and `git log origin/main..origin/develop` before release.

| Issue | Evidence and disposition |
| --- | --- |
| #41 | Action notifications in #228/#230/#231; awaiting main, v2.2.0. |
| #204 | Guide discovery/matching in #205/#206/#215; awaiting main, v2.2.0. |
| #208 | Container port fix #209; awaiting main, v2.2.0. |
| #214 | Kubo 0.43.1 in #215; awaiting main, v2.2.0. |
| #226 | Caller-budget JSON start and cancellation in merged #248 complete the earlier tuner work; awaiting main, v2.2.0. |
| #234, #235 | HTTP/HLS and optional broadcasters in #241; awaiting main, v2.2.0. Mixed-protocol tuner failover remains outside scope. |
| #246 | Accepted for v2.2.0 in this feature branch; not yet integrated into develop/main. |
| #93 | #251 adds explicit WARP host exclusions. Partial: arbitrary public clients and topology-specific return-path verification remain open. |
| #249 | Favorite priority exists, but favorites-only checks do not. Proposal remains open. |
| #253 | New ARM libc resolver report; existing Python/dnsproxyd fixes do not establish a fix for compiled-core lookups. Keep open. |
| #102 | Supervisor recovery does not prove resolution of concurrent Acexy starts. Keep open. |
| #224 | Raw midstream source concatenation is not implemented; current transcoding/reconnect behavior does not fulfill it. |
| #217 | External outpace compatibility still requires the scoped contract/live validation. |
| #216 | Extraction recipes exist; optional AI interpretation/training does not. |
| #233 | HTML-to-guide conversion and overlay semantics remain unimplemented. |
| #158 | Epic remains partial: notifications are awaiting main; VOD/events remain separate. |
| #155 | Alias retirement deliberately deferred; aliases remain supported. |
| #99, #55, #13 | VOD catalogues, sporting-event aggregation and native installers remain unimplemented. |

Warning cleanup #247, startup deadlines #248, repository governance #250/#252
and WARP exclusions #251 have merged; release notes must no longer call them
pending. Local checks on this feature branch do not prove CI on the release head.

## Initial local validation — 2026-10-22, commit 6f6cb6b

Baseline develop `b8b06f7`, feature branch `codex/v22-gluetun-changelog`.

- `CI_USE_PREINSTALLED_DEPS=1 bash scripts/ci/run_v2_test_suite.sh --profile quick`:
  passed (4 Docker documentation contracts, 87 backend contracts, 11 selected
  frontend tests, lint/typecheck, OpenAPI/client generation, production build and
  Pages helper drift). Final run has no React test warnings. The two existing
  Vite chunk-size advisories remain visible; no threshold was changed.
- `npm --prefix frontend test -- --runInBand`: 82 suites, 463 tests passed.
  Jest resolves user-event and React Testing Library through the same DOM Testing
  Library copy, fixing event update wrappers without changing dependency versions.
  A manually invoked mutation callback also now runs inside `act`.
- `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_gluetun_port.py`:
  final 22 tests passed, no warnings. Includes invalid/missing/symlink/FIFO input,
  listener conflicts, active port rotation, Stop/file-change/Start behavior,
  packaged foreground launch arguments, disabled-sync defaults, unsupported
  engine rejection and release-version drift.
- `backend/tests/test_runtime_integration_guards.py` plus the then-current
  Gluetun suite: 60 tests passed. `bash scripts/ci/validate_runtime_contract.sh`
  passed, including engine recovery, mailbox commands and stopped-engine health.
- `env -u NO_COLOR npm run test:mobile -- changelog.spec.ts` in `e2e`: 8 passed
  across Chromium phone/desktop, 320px WebKit and Firefox tablet, in both themes.
  Browser errors were checked; screenshots inspected for desktop light and small
  phone dark. Tests cover notice navigation, history anchors, reload persistence,
  navigation after dismissal and horizontal overflow.
- Frontend and E2E typechecks, documentation validator, command-builder contract,
  Dockerfile/manifest/docs validators, strict legacy-path guard, Bash syntax and
  `git diff --check` passed.

Initial local tests found a blocked-storage dismissal bug and older-Bash empty
array behavior; both were fixed and their focused suites rerun. Existing entrypoint
capture tests and preview-server startup required normal host permissions because
macOS sandbox restrictions blocked `/dev/fd` and localhost listening. No warning
suppression was added. Logs/screenshots remain untracked.

This does not establish live provider forwarding, actual engine reachability on
the assigned public port, new multiarchitecture image builds, or physical ARMv7
runtime. This initial pass did not rerun the full backend suite; see the
follow-up validation below. Jenkins must validate the final feature/release
commits before integration.

## Markdown/publication follow-up — 2026-10-22, after 6f6cb6b

PR #254 now uses canonical Markdown, generated offline history, OCI-bound notes
provenance and post-promotion GitHub publication. The separate published-update
notice uses a cached authenticated endpoint and manual Docker/native instructions.
No release, image publication, merge or Jenkins configuration change was made.

Validation on the follow-up working tree:

- Quick cross-stack gate passed: four documentation contracts, 87 backend
  contracts, 11 selected frontend tests, generated-client drift, lint, types,
  production build and Pages helper drift. Existing Vite size advisories remain.
- Full frontend: 83 suites / 468 tests passed. Final changelog/update UI focus:
  11 tests passed after the dismissal-label clarification.
- Full backend initially exposed absent host FFmpeg tools. With temporary
  production-style binaries built from the vendored source, 2,020 tests passed;
  two remux fixture tests required additional test-only lavfi/libx264/framemd5
  features. All three remux tests then passed using a cached imageio-ffmpeg 0.6.0
  test binary via FFMPEG_TEST_TOOL_PATH. The 36 HTTP/media checks also passed.
  These tools were prepared under /tmp; application/system dependencies did not
  change. This is full-suite coverage plus focused reruns, not a claim that the
  single full-gate invocation completed successfully.
- Final update-discovery, Markdown drift, release provenance/publication and
  promotion tests: 51 passed. Docker/GitHub mutations use fakes. Cases include
  offline/rate-limit responses, token enforcement, historical v2.1 tags, numeric
  comparisons, mismatched notes/tags, partial publication retries and dry runs.
- Browser checks: 16 passed across all four viewport/browser projects, covering
  both themes, Docker/native notices, once-per-version reload behavior and offline
  history. Small-phone notification screenshot inspected; no horizontal overflow.
- E2E types, documentation, Dockerfile/manifest/docs, command-builder, strict
  legacy paths, Bash syntax and diff checks passed. No React/pytest warnings were
  suppressed. A read-only live discovery returned published v2.1 and correctly
  reported no newer release for installed v2.2.0.

Live GitHub publication remains unexercised because no release is authorized.
The existing github-publish credential must allow repository Contents writes and
version-tag creation when the release is eventually run. See
[release notes operations](../ops/release-notes.md) for exact retry instructions.
