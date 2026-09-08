# V2 user-documentation review — 8 September 2026

Source baseline: `develop` at `7a4381f` (PR #188). This is a dated review, not a release sign-off or a statement of current CI status. Recheck the running deployment and latest source before launch. The test instance was inspected through its browser UI; its deployed image digest was not independently matched to the checkout.

## Scope and evidence

Headless Chromium visited Overview, Live TV, Scraper, Search, Acestream Channels, TV Channels, EPG, Playlist, Integrations, WARP and all four Settings tabs. Initial navigation recorded no JavaScript page errors or HTTP responses of 400 or greater. The test instance reported playback/checking engines, Acexy, IPFS, ZeroNet and WARP running. External media-server/player cards were inspected without changing their configuration or sending playback to other devices.

Opened Add URL, channel reorder preview, advanced filters and the inline playlist format editor. The example source form was not submitted; reorder was cancelled. Screenshots under `wiki/usage-*.png` were captured from the running UI, with private URLs/content IDs masked where relevant. The obsolete QR image was removed because generated QR codes can embed access credentials. The phone capture uses a 390 × 844 viewport in dark theme; desktop captures use 1440 × 1000 (some full-page).

Live TV reached Playing and displayed video on one test. A later attempt did not reach Playing within a 55-second observation window. This pass does not establish reliable startup for every stream or identify the cause of that timeout. A further bounded attempt had not produced a decoded frame after 22 seconds. Its catalogue filter preserved the single player-session request, with no page errors. The mobile catalogue measured 390 pixels of document width in a 390-pixel viewport. Test viewers were released using Stop watching. Use the troubleshooting guide and runtime diagnostics to investigate recurrent startup failures.

## Documentation corrections

- Current Settings tab names/deep links, public address in Integrations, optional engines and dedicated checker behavior.
- TV-channel numbering, favorites, catalogue-wide filters and complete-order preview/save/cancel.
- Live TV layout, programme schedule, stream/audio choice, direct send and mobile use.
- Stable station relay versus individual content-ID relay, unassigned playlist tail and client-dependent recovery.
- Signal verification versus engine ID lookup; persisted scheduled-job outcomes.
- Backup-first startup recovery, correct health/diagnostic endpoints and per-service log retention (including checker).
- ARMv7 community engine details and outstanding hardware verification, without outdated Premium-only claims or unsupported resource promises.
- Wiki sidebar/help navigation and repository document links that survive the flattened wiki mirror.

## Docker builder review

The page already offered a bundled checker toggle but had no separate checker-state mount and could emit the conflicting external checker variable. It now makes those selections exclusive, adds the conditional state mount, exposes the optional playback-engine default, and emits host-gateway mapping for external engine/checker addresses using `host.docker.internal`. Next steps link to the current setup and troubleshooting workflows.

Validation completed:

- `bash scripts/ci/validate_command_builder.sh`: runtime schema/platform/settings contract and JavaScript syntax passed.
- Local Playwright browser checks: all 12 flavor/platform combinations; checker on/off and external selection transitions; checker storage; external host mapping; full-service environment/volumes/capabilities; develop tags; Compose output tab; 390-pixel mobile page width; no page errors.
- README/wiki relative-link audit: paths, Markdown anchors and image destinations passed. Repository-document links use the develop source URL rather than nonexistent wiki page names.
- `bash scripts/ci/publish_wiki.sh --dry-run`: flattened pages and assets rendered successfully; no external publish performed.
- `bash scripts/ci/assert_no_legacy_paths.sh --strict` and `git diff --check`: passed.

The full backend/frontend application suites, image builds, ARM hardware playback, destructive recovery, automatic relay-failure injection and external-player/media-server end-to-end playback were not part of this documentation pass.

## Follow-up observations

- At 1440 pixels, the TV Channels Number fields show cramped/clipped floating labels in compact rows; some long signal labels are ellipsized in Acestream Channels. The screenshots preserve the actual UI; these are candidates for a separate UI polish pass.
- The sampled guide contained overlapping entries for a station. Source data versus mapping/import behavior was not isolated; verify the chosen XMLTV source and station mapping before treating it as an application defect.
- Repeated playback startup should be exercised with runtime logs before launch. One successful video session is not a stability test, and this review did not verify decoder continuity during relay failover.
