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
| 1 | Baseline, exact issue criteria, prerequisites, performance | Initial production baseline recorded; isolated FFmpeg prepared; comparable follow-up measurement running; interaction/media evidence remains |
| 2 | Reproduce #315/SRC-F15, fixes, executable API contracts | Defect fixes committed; initial wire contracts pass; operation coverage expansion remains |
| 3 | Shared presets, preferences, EN/ES, components | Shared preferences/tokens and 2,400+ paired resources implemented; dynamic-message and full state coverage remain |
| 4 | Shell, aliases, access/startup, canonical settings | Seven destinations, selected-only Settings, canonical source/guide/account/player editors and dirty/pending guards implemented; remaining editors and complete journeys remain |
| 5 | Sources/extraction, channels, guides, playlists | Canonical source/guide editors, bounded channel browse and complete reorder snapshot implemented; remaining journeys and acceptance in progress |
| 6 | Watch, events, recordings, batched artwork | Watch composition/deferred HLS, recording collections and event draft/validation work implemented; complete media journeys remain |
| 7 | Connections, notifications, System/recovery | Account/remote-player/Cast drafts and stable translated failures implemented; remaining System/notification state coverage remains |
| 8 | Final performance, complete validation, docs, one PR | Single draft PR #325 open; incremental evidence recorded; final full validation and external acceptance outstanding |

## Task ownership

| Issue | Scope | Implemented | Tested | Accepted |
| --- | --- | --- | --- | --- |
| #315 | Recording HTTP/UUID/idempotency, confirmed UI defects, isolated SRC-F15 | Partial | Incremental checks | No |
| #316 | Three shared presets/components, graphics, exception register | Partial | Incremental checks | No |
| #317 | Typed EN/ES, fallback/formatting/pseudo-locale, accessibility | Partial | Incremental checks | No |
| #318 | Seven destinations, aliases/settings/access/setup/gates | Partial | Incremental checks | No |
| #319 | Watch/events/recordings, exact scheduling/media ownership | Partial | Incremental checks | No |
| #320 | Channels/guide/reorder/atomic Add-Link/playlists | Partial | Incremental checks | No |
| #321 | Canonical source journey/search/W3U/extraction/helpers | Partial | Incremental checks | No |
| #322 | Connections/trust/notifications/System/WARP/diagnostics | Partial | Incremental checks | No |
| #323 | Reproducible production baseline and final budgets | Partial | Incremental checks | No |
| #324 | Integrated field/state/permission/preset/locale evidence | Partial | Incremental checks | No |

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
- Isolated arm64 FFmpeg/ffprobe 9.0.2 prepared and hash-verified under `/tmp/ux314-tools/media-bin`; 70 recording/player runtime tests passed. Add that directory to PATH for final media gates.
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

### Integration evidence (not completion)

- Commit `6dbdd99`: initial recording/bulk regressions, fixes and baseline.
- Core preferences: 18 tests passed across preference/bootstrap/theme suites;
  draft, media element, cache and selector survive all preset/theme/language changes.
- First full frontend integration attempt: 660 passed / 18 failed (111 suites;
  failures were old navigation assertions/mocks). Updated expected navigation to
  the approved seven-destination contract; all four affected suites now pass:
  57 tests, no warnings. Full final suite remains required.
- Initial real-wire consumer suite: seven actual service requests validated after
  Axios transport. Real-provider/schema-negative tests: 17 passed. Combined
  contract + existing token/account semantic suites: 81 passed, no warnings.
  More feature scenarios/non-JSON/preset parity remain to implement.
- Shared OpenAPI error/security descriptions now reflect conditional installation
  access without changing enforcement. Schema and generated client regenerated.
  Batched GuideSlot.image_url is additive/nullable; no migration.
- Production build, TypeScript and lint pass at this intermediate point.
- Rendered three presets at 390/1440px: six cases, no page errors or document
  overflow. Screenshots manually inspected. This is an early composition pass;
  bilingual/dark/other-route/physical-device acceptance remains outstanding.
- Owned current browser backend: loopback 18085, `/tmp/ux314-evidence/current`.
  Baseline backend on 18084 stopped; frozen baseline build/data remain untouched.

### Localization integration (continuing)

- One draft PR: https://github.com/Pipepito/acestream-scraper/pull/325, targeting
  develop; no automatic closing references. Foundation commits are pushed.
- 2,200+ typed feature messages now have Spanish resources. UI copy migration,
  chosen-language date/number formatting, initial plural consolidation and MUI
  locale configuration are implemented. Original catalogue names stay verbatim.
- Recipe helper has an independently initialized language preference and generated
  subset catalogue; its build checks subset drift without importing the app.
- Full English regression run: 111 suites passed / 1 failed; 682 tests passed /
  1 failed. Failure was the new test helper spreading a RegExp iterator under the
  existing ES5 compilation target, corrected to Array.from. Focused rerun: 5/5 localization tests passed; TypeScript/lint passed.
- Built Spanish application: 54 cases (three presets × two themes × three widths
  × Watch/network/guide), zero uncaught errors or document overflow. Screenshots
  inspected; visible runtime/enum labels still in English were found and recorded.
- Production app + standalone build passed. Initial localization library growth
  exceeded the existing MUI chunk budget; isolating the translation libraries
  removed that warning without splitting MUI/Emotion or React helpers.
- Runtime labels, protocol reason codes, complete feedback sentences, dirty/pending
  language switching and visual bilingual coverage still need reconciliation.
  Resource key coverage is not full localization acceptance.

Current next action: finish localization migration across actual visible/dynamic
messages, canonical settings/editor ownership and feature-family compositions;
expand contract/parity evidence while preserving current behavior. Do not stop at
these foundations. All task acceptance and final full validation remain open.

### Canonical editors and operational localization checkpoint

- Settings now mounts only the selected canonical editor. Engine, three schedule
  fields, link compatibility, access and network keep independent transactions.
  Scalar drafts no longer get replaced by query refetches. One stable data router
  and one shared dirty/pending registry protect route/query/Back/unload navigation.
- Network, playback routing, checker, schedule anchors, offline cleanup, recording
  settings and stream-link edits register with that guard. Link dialogs also guard
  local Cancel/Escape/backdrop. Remaining editor families still need migration.
- Recording disable, stop, scheduled cancellation and file deletion have distinct
  confirmations. Settings enforce concurrency/byte/retention limits and retain
  drafts on failure. Guide export has two named day controls, retains zero and
  guards duplicate submission. Phone Watch brings the first channel into view.
- Runtime copy uses all 47 stable option names; English source drift and Spanish
  coverage are tested. Application status/reason codes and known API error codes
  use localized resources. Non-string FastAPI validation details no longer crash.
  Unknown errors use safe localized guidance; original user content stays verbatim.
- Full frontend run with native Fetch test environment: 114 suites passed / 1 failed,
  697 tests passed / 1 failed. Only failure was the old WARP conflict-copy assertion;
  updated to the stable-code localized message and all five WARP tests then passed.
  Earlier sandbox-only run could not bind the real-wire test listener; rerunning
  with local socket access passed that contract suite. No skipped tests counted.
- Built Spanish matrix rerun: 54 cases, zero page errors or document overflow.
  Real built-app dirty navigation: six cases (three presets × EN/ES), cancelled
  edits retained, discard navigated with unrelated query preserved, zero writes,
  zero page errors or overflow. Temporary evidence remains under
  `/tmp/ux314-evidence/current`; this is intermediate, not final task acceptance.
- Final focused verification for this checkpoint: 13 suites / 98 tests passed;
  TypeScript and lint passed without warnings. Complete application, Docker,
  browser/E2E and external participant/device acceptance remain outstanding.

### Source/guide and font checkpoint

- Source creation/editing now uses the same SourceEditor in first-run setup and
  Sources, including provider fills, advanced options, independent save, inline
  failures, dirty close and duplicate-submit guards. Setup explicitly imports
  after saving and reuses an existing source on retry. Saved recipe state is not
  overwritten. Telegram is discoverable from Channels section navigation.
- Guide setup/management share GuideSourceFields and the canonical create hook.
  Guide management now protects in-flight saves and dirty local close, shows
  inline errors, and uses the shared delete confirmation instead of window.confirm.
- Runtime and WARP drafts register with navigation protection; Runtime also guards
  local close. Public-address and notification drafts survive query refreshes.
- Converted the approved full-glyph fonts to WOFF2: 986,004 bytes -> 389,596 bytes
  combined (60.5% smaller), with source/output hashes and licences retained.
  Found and fixed a real CssBaseline registration bug: the object-array font-face
  declaration overwrote Inter with Barlow. A CSSOM regression test covers both faces.
  Vite asset imports also fix fonts under a nested standalone-helper deployment.
- TypeScript, lint and production app/helper build passed. Final affected check:
  11 suites / 93 tests passed without warnings. Browser verified actual Inter
  requests/loaded status in all presets and the nested standalone helper; Lime also
  loads Barlow. All font responses were 200, no page errors, and the helper made
  no application API requests. These remain intermediate checks; full acceptance
  is still outstanding for every issue.

### Account and player feedback checkpoint

Account/Cast failures now expose optional stable `X-Error-Code` metadata without
changing their legacy bodies, status, retry headers or security decisions. The
OpenAPI contract and generated client were refreshed. Remote-player probes expose
an optional reason enum; shared player guidance renders in EN/ES and retains
protocol diagnostics separately. Remote-player edits survive query refresh, failed
save, language changes and guarded modal dismissal; one action guard serializes
save/test/pairing. Account setup, password, individual account, policy and credential
forms now register dirty/pending state and retain raw errors for retranslation.

Focused validation against this checkpoint: 160 backend tests passed (accounts,
Cast, token policy, maintained wire contracts and remote-player drivers/services/API),
70 frontend tests passed in six suites; TypeScript, zero-warning ESLint and production
app/standalone builds passed. Evidence: `/tmp/ux314-evidence/access-player-final-*`
and `player-errors-backend-final.log`. An initially incorrect test expectation
for VLC HTTP 403 was corrected to the existing `no_password` semantic; no driver
behaviour changed. This remains incremental evidence, not the required final full
application/Docker/browser or human/hardware acceptance gate.

### Live feedback and modal-language checkpoint

Confirmation descriptors and shared notifications now resolve their wording in the
current language while retaining the same dialog/notification and pending action.
The translation hook no longer captures a language in an in-flight callback.
Canonical discard/delete/stop/cancel dialogs, guide import/refresh outcomes and
search import feedback use that contract. Search import has an immediate guard
across single/bulk actions. Failed guide-editor saves retain raw errors.

Final frontend run for this checkpoint: **119 suites / 714 tests passed**, no
warnings; typecheck, zero-warning lint and production app/helper builds passed.
The earlier run exposed a legacy guide-detail snackbar and a playback-copy
expectation; both were resolved before the complete rerun. Logs:
`/tmp/ux314-evidence/live-feedback-full-frontend-final.log`,
`feedback-typecheck-fixed.log`, `feedback-lint.log`, `live-feedback-build.log`.
Built Spanish smoke matrix with actual Inter/Barlow fonts: 54 combinations across
three presets, two themes, widths 320/390/1440 and Watch/Network/XML export; zero
page errors or document overflow. Screenshots/results are under
`/tmp/ux314-evidence/current/spanish-fonts-feedback/`. These are browser smoke
checks, not claims of full visual, screen-reader or human acceptance.

### Recording collections and deferred HLS checkpoint

Recordings now separates saved Library, Upcoming and active, and History through
one canonical list/controller. Backend filters precede count/pagination and preserve
legacy `collection=all`; new values are documented/generated in OpenAPI. Multipart
and missing/deleted-file cases retain history, while deleted/deleting rows expose
no media actions. Part labels track the original when derivatives are added.
Conversion and removal of protection have distinct confirmations and pending gates.
The list batches artifacts/attempts: a regression asserts four SQL reads for a page.

HLS code now loads only when a viewer opens. Built Chromium network evidence shows
zero media-bundle requests before opening Watch, then exactly the two existing HLS
chunks. No playback controller/provider was replaced. Regression tests cover a
late decoder load after close and retaining the exact video/HLS/viewer across
language/theme changes. Real playback and complete performance acceptance remain
separate outstanding checks.

Focused results: 35 backend recording/wire tests; 40 frontend tests in five suites;
typecheck, zero-warning lint and production build passed. Logs are under
`/tmp/ux314-evidence/recording-*`, `deferred-player-*`; the initial browser locator
was corrected to the channel-specific accessible Watch name before rerunning.
FFmpeg and ffprobe 9.0.2 for arm64 are prepared in `/tmp/ux314-tools/media-bin`,
verified against the publisher's SHA-256 values and executable locally. Provenance:
`/tmp/ux314-evidence/media-tool-provenance.json`; publisher
https://www.osxexperts.net/. No global installation or application dependency changed.

### Casting and event draft checkpoint

Casting settings remain mounted after home-trust updates. Trust changes wait for
unsaved preferences, and capabilities carry stable translated denial reasons.
Casting/login actions have immediate pending guards and retain raw failures for
language changes; receiver ownership and transport/permission rules are unchanged.
Event validation exposes stable reason types with bounded redacted locations and
messages, documented in OpenAPI. Private input/context never enters the response.
Event import retains raw failures, guards duplicate operations and local dismissal.
Corrections survive background revisions and language changes, retaining their
original reviewed revision for conflict checks instead of remounting and losing edits.

Final focused checks: 96 backend tests and 45 frontend tests in four suites passed;
TypeScript, zero-warning lint and app/standalone production builds passed. Evidence:
`/tmp/ux314-evidence/event-cast-backend.log`, `event-cast-*-verified.log`.
An old cancellation test was updated to explicitly discard; a test naming warning
and missing typed translation were fixed before rerunning the affected checks.
Separately, all 70 recording/player runtime tests passed with verified FFmpeg and
the required local socket/process-inspection access (`recording-player-runtime-permitted.log`).
Final full gates and human/hardware acceptance remain outstanding.

### Bounded catalogue and editor checkpoint

Channels now reads one filtered/sorted page and independent global facet/count
metadata. Watch loads 50 rows at a time and guide reads only cover loaded batches.
The new `/tv-channels/browse` contract applies every existing filter before
pagination; the legacy complete read remains available for reorder and other
consumers. Stream relationships load in batches (three SQL reads for a 100-row
serialized page). Complete reorder snapshots and atomic stale rejection are intact.
Primary Search/Category/Status/Favorite controls stay visible on phones. Channel
forms and reorder previews retain raw errors, protect dirty/pending dismissal,
and translate table/filter labels and notices without translating catalogue values.

Checkpoint validation: **119 frontend suites / 721 tests passed**, **89 backend
catalogue/provider-contract tests passed**, TypeScript, zero-warning lint and
production app/helper builds passed. Actual consumer validation covers 13 wire
requests, including repeated query IDs and false/zero/literal-substring filters.
Built browser matrix: 12 preset/language/390-or-1440 cases with 10,000 channels and
streams; one initial browse request, exactly 50 Watch rows, no writes, no page errors
or document overflow; discarded create drafts remained intact after Cancel.
An initial locator was ambiguous with the table header and was corrected to the
combobox role. Evidence: `/tmp/ux314-evidence/catalogue-check/large-browser.json`,
`catalogue-full-frontend.log`, `tv-browse-backend-verified.log`.

The comparable 100-sample baseline fixture has no streams. At 10,000 channels,
Channels initial API requests changed 24→6, Live TV 25→5, Settings 20→4. Median
cold settled times were 1557→741 ms, 1573→660 ms, 706→614 ms respectively;
these include 500 ms network-idle and uncontrolled host timing. The new Watch home
has different scope (overview plus viewing), so its timing is not like-for-like.
See `performance-catalogue-checkpoint.json`. These are intermediate measurements;
final repeated interaction/media/memory and full validation remain outstanding.

### Integration draft and feedback checkpoint

- Media-server editors retain same-server drafts across query refreshes, keep raw
  probe/save errors for live translation, guard pending requests and confirm local
  discard. Tuner settings use an independent dirty draft and preserve failed saves.
- Telegram source edits stay mounted when the account status refreshes; competing
  edit/lock/removal actions cannot replace that editor. Cancellation confirms
  discard, pending saves cannot be submitted twice, and credentials remain
  memory-only with the existing explicit clearing lifecycle.
- Shared notification callbacks resolve messages in the current language. Media
  server/remote-player feedback and Plex instructions are localized; job summaries
  use complete localized messages and numbers, with distinct offline/error/skipped
  outcomes. Fourteen previously empty runtime help entries now have EN/ES copy.
- Full backend iteration: 2,610 passed and one outdated exact response assertion
  failed. Corrected assertion plus affected integration/checker tests: 67 passed.
  Full frontend iteration: 717 passed and five callback-contract assertions failed;
  corrected tests and affected draft/localization suites: 7 suites, 63 passed.
  TypeScript, zero-warning lint, production SPA and standalone helper builds pass.
- Prepared tracked `docs/recipes/` from its shared source. No Pages publication.
  Full final gate and browser/Docker/participant acceptance remain outstanding.

### Browser and packaging iteration

- Commit `147a6e7` is the frozen initial Docker matrix input. All five ARM64
  production flavours passed both build and private pinned runtime acceptance.
  AMD64/ARMv7 builds and additional packaging/media/scanner checks continue;
  this is not final-revision matrix acceptance.
- First strict Firefox run: 31 passed, 13 failed, 17 dependent tests did not run.
  Initial failures identified stale sidebar/headings/source/guide/notification
  selectors; downstream guide/playlist/recording journeys require their seeding
  predecessors to pass. Media playback, inline switching, reorder and optional
  checker journeys passed. The initial process inherited conflicting color env
  settings; subsequent runs unset NO_COLOR rather than suppress warnings.
- Exploratory mobile run interrupted after 10 passes / 6 failures / 2 interrupted
  tests; old navigation expectations found. Its assets were rebuilt during the
  run, so it is not acceptance evidence. Further runs use a frozen build and
  separate report directories to avoid interference from other validations.
- Fixed missing Playback/Network links in Settings and System/Connections parent
  selection for nested routes. Added durable System links to runtime settings and
  release history, which must remain reachable after dismissing the update notice.
  Focused navigation/System/localization checks: 5 suites, 42 tests passed.
- Build grouping now separates pure language catalogues and router code; latest
  entry 96.9 KB, EN 221.1 KB, ES 242.3 KB, router 93.9 KB, MUI 447.2 KB. Production
  SPA/helper build has no chunk warning; unchanged 500 KB warning threshold.
