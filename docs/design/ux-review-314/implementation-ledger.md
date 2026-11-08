# UX epic #314 implementation ledger

## Authorization and baseline

Approved 2026-11-08 in the implementation chat: complete #315–#324 together,
including approved review-06 visual decisions, validation, commits, feature branch
push, one PR into develop and precise issue updates. The owner explicitly selected
the existing checkout, not a new worktree. No milestone approvals are needed.
No deployment, protected merge, Jenkins mutation, image/release or Pages publication.

- Checkout: `/Users/pipepito/Code/acestream-scraper-alt`
- Branch: `codex/ux-implementation-314`
- Verified remote develop / implementation base: `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`
- Design reference: `de69e644428abe5d0e4149b4e437d37996c4b769`
- Private validation policy inspected: `0955626eee33149e88e83d5f95901bd131b065b5`
- Other existing worktrees and local develop pointer are preserved.
- All eleven issues remain open; design-only issue prose is superseded by this
  explicit implementation authorization. Prototype results are not app acceptance.

## Approved decisions

Exactly three presentations of one application: Lime (`lime`), Coral/navy
(`coral`), Immersive (`cyan`). Cyan is first-visit/unknown fallback. Independent
theme and EN/ES language preferences; preserve existing light/dark values.
Review-06 palettes; Inter body/editorial text and Barlow Condensed lime headings;
selected optimized images with provenance/licences; no supplier runtime or rebrand.
Calm administration, accessible contrast/focus/help/targets and reduced motion.
Seven destinations: Watch, Recordings, Events, Channels, Connections, Settings,
System; WARP remains explicit. Existing URLs/queries/back/return context survive.
Canonical editors and independent/immediate-save transactions remain authoritative.
One router/bootstrap/query cache/access model/service layer/controller/editor/message
catalogue/media owner. Stateless documented layout exceptions only. Preference
switches preserve drafts, errors, dirty state, focus, reading anchor, selections,
dialogs, pending actions and the player node/session/position.

## Milestones (implemented / tested / accepted are distinct)

| Step | Work | Status |
| --- | --- | --- |
| 1 | Baseline, exact issue criteria, prerequisites, performance | In progress |
| 2 | Reproduce #315/SRC-F15, fixes, executable API contracts | Pending |
| 3 | Shared presets, preferences, EN/ES, components | Pending |
| 4 | Shell, aliases, access/startup, canonical settings | Pending |
| 5 | Sources/extraction, channels, guides, playlists | Pending |
| 6 | Watch, events, recordings, batched artwork | Pending |
| 7 | Connections, notifications, System/recovery | Pending |
| 8 | Final performance, complete validation, docs, one PR | Pending |

## Task ownership

| Issue | Scope | Implemented | Tested | Accepted |
| --- | --- | --- | --- | --- |
| #315 | Recording HTTP/UUID/idempotency, confirmed UI defects, isolated SRC-F15 | No | No | No |
| #316 | Three shared presets/components, graphics, exception register | No | No | No |
| #317 | Typed EN/ES, fallback/formatting/pseudo-locale, accessibility | No | No | No |
| #318 | Seven destinations, aliases/settings/access/setup/gates | No | No | No |
| #319 | Watch/events/recordings, exact scheduling/media ownership | No | No | No |
| #320 | Channels/guide/reorder/atomic Add-Link/playlists | No | No | No |
| #321 | Canonical source journey/search/W3U/extraction/helpers | No | No | No |
| #322 | Connections/trust/notifications/System/WARP/diagnostics | No | No | No |
| #323 | Reproducible production baseline and final budgets | No | No | No |
| #324 | Integrated field/state/permission/preset/locale evidence | No | No | No |

`acceptance.json` records each current issue checkbox separately. Design field,
runtime-option and workflow inventories remain coverage references, not page counts.

## Validation obligations

Run final full backend/frontend suite, lint/typechecks, OpenAPI AND generated TS
drift, documentation/metadata/runtime contracts, production/recipe builds, all five
flavours across three architectures, Docker packaging/service/media checks, complete
Firefox E2E plus Docker-on/off/mobile/monitor suites, and visual/localization/a11y/
performance acceptance. Private policy remains authoritative; do not run shared
cleanup against unrelated resources. Record exact revision, commands, counts,
warnings and blockers; rerun affected/dependent stages after fixes. No silent skips.

## Prerequisites and outstanding external evidence

- Docker checked 2026-11-08: 29.9.2, linux/aarch64; buildx 0.38.1. Initial
  sandbox socket access requires escalation; daemon is running.
- Node/dependencies/Playwright present; lockfile compatibility remains to check.
- Host FFmpeg is absent from PATH: prepare repository-supported isolated tooling.
- Actual AT, native zoom, physical casting/mobile devices and fluent Spanish /
  nontechnical participant review remain unverified. Owner/participants provide
  external evidence; agent prepares reproducible protocols and continues independent
  work. No waiver inferred from plan approval. ARMv7 hardware qualification stays
  distinct from cross-build/emulated checks.

## Evidence and recovery

Transient logs belong outside tracked content. Curated summaries name their exact
revision; never commit DBs, credentials, private captures or raw runtime data.
On resumption inspect branch/status and this ledger, retain completed work and
update the next action. Use coherent commits; one coordinated PR to develop.
Do not close tasks with unresolved acceptance or imply merged/released status.

### Evidence recorded 2026-11-08

- Untouched production baseline: 100 cold/warm samples (5 repeats × 5 routes ×
  2 sizes × 2 cache states), Chromium 149, zero page errors. See
  `performance-baseline.json` and `e2e/scripts/measure-production.py`. Additional
  interaction/media measurements remain outstanding. Temporary log root:
  `/tmp/ux314-evidence`. Frozen pre-change build remains there for comparisons.
- Regression reproduction: 6/6 tests failed before fixes, including private HTTP
  UUID absence and duplicate full-selection activation (SRC-F15).
- Focused fixes: 4 frontend suites / 12 tests passed; TypeScript passed. No
  application completion acceptance claimed; full gate remains outstanding.
- Localization peers resolved: i18next 27.0.1, react-i18next 18.0.0, compatible
  React >=18, TS 5/6/7 and Node >=22. npm reports 26 audit findings (4 low,
  22 moderate); triage against unchanged baseline is outstanding.

Current next action: finish executable contract harnesses and shared presentation /
localization preferences, then progress through every milestone above.
