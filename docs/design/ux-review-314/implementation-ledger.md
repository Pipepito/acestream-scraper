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

### Telegram diagnostics and browser-discovered save behavior

- Telegram status/source diagnostics now carry stable additive reason codes;
  EN/ES account/source states and extraction outcomes resolve on render. Existing
  details, encrypted storage and authentication/transport rules remain unchanged.
  Source serializers explicitly project writable fields, preserving null/empty/
  false values while excluding response metadata. No database migration required.
- A real-backend Firefox journey found that the webhook draft retained its raw
  token after Save while the server returned a masked URL. The form now adopts
  the persisted masked value, clears its dirty state and enables Send test.
  It never places the raw URL in the query cache. Setup import feedback also
  resolves in the current language without resetting the import result.
- Focused Telegram backend: 33 passed. Telegram/webhook frontend: 3 suites,
  17 passed. Typecheck and zero-warning lint passed; production build passed.
- Full application checkpoint (backend at 147a6e7, frontend at 544eee14):
  2,611 backend tests and 119 frontend suites / 726 tests passed, coverage retained.
  OpenAPI/client drift, lint/types, build, helper drift and all nine separate public
  contract stages passed. This predates the changes in this section.
- Frozen 147a6e7 matrix: all 15 image/platform builds passed. Five native ARM64
  runtime checks and ARMv7 layout passed. AMD64 private runtime validation failed
  because its emulated-platform layout branch asserts ARM OCI installation for
  the native Linux AMD64 engine. Keep this exact infrastructure-validator
  limitation open; successful build does not count as a runtime pass.
- Strict Firefox at 544eee14: 57 passed, 3 failed, 1 dependent test did not run.
  Failures: whitespace-sensitive matching assertion (corrected); webhook saved
  state (application fix above); recording directory supplied through macOS's
  /tmp symlink (must restart isolated backend using /private/tmp real path).
- Frozen mobile matrix: 180 passed, 56 failed from outdated fixtures/selectors.
  Corrected affected flows passed all 18 Chromium cases; the full matrix reruns.
  Monitor transport suite: 30 passed across Firefox, Chromium and WebKit.
- Next: finish real media preference continuity, corrected full browser matrices,
  rerun against the new build and real-path storage, complete Docker packaging/
  service/media/scanner checks and remaining feature/parity/visual acceptance.
  Participant, native screen-reader and physical-device evidence remains open.

- Real HLS playback preference acceptance passed (48.7 seconds): all three
  presets × both themes × EN/ES, same video DOM element and one viewer session;
  filtering advances media, channel switch releases one viewer, Stop reaps both
  test sessions. Uses the frozen 544eee14 SPA and isolated FFmpeg backend.

### Expanded executable contracts and completed browser checkpoint

- Fresh strict Firefox at application `7f539536` / journeys `6a6c4221`: all 61
  passed (5.5 minutes), no skips. This includes real local webhook delivery, guide
  scheduling with real-path recording storage and the expanded HLS preference test.
- Corrected frozen-544eee14 responsive matrix: all 236 passed (4.1 minutes),
  no skips, across phone Chromium, 320 px WebKit, tablet Firefox and desktop Chromium.
  Further application changes still need affected/final browser coverage.
- Actual-wire consumer contracts expanded from 13 to 33 production service calls;
  false/null/empty/omitted values, scoped Telegram headers and independent saves
  are checked with maintained OpenAPI validation. The first iteration correctly
  rejected a test's out-of-range tuner limit; the valid fixture uses its real limit.
- XMLTV and CSV response declarations now describe their actual media types.
  Diagnostics uses the OpenAPI 3.1 binary media-type contract, with separate ZIP
  parsing. Provider tests parse non-JSON formats and assert attachment/cache headers;
  negative tests reject JSON media types. Telegram's separate admin header and
  redacted errors are documented without changing enforcement. Expanded provider/
  synthetic Telegram validation: 62 passed; actual consumer test: 2 cases / 33
  requests passed. See `docs/dev/executable-api-contracts.md` for exact coverage.
- All existing issues #314–#324 and draft PR #325 were updated through `6a6c4221`;
  no issue was closed. Final integrated and manual acceptance remain outstanding.
- Fixed the observed 320 px Spanish guide-section clipping by wrapping tabs on
  phones and retaining a distinct selected background/underline. All 48 actual
  browser combinations (3 presets × EN/ES × both themes × 4 browser/viewports)
  passed label-bound checks, Home/End keyboard focus, zero-write and overflow
  assertions; selected-state screenshots were inspected.

### Editor, artwork and translation-data follow-up

- Channel number and detail editors retain drafts through refreshes; zero is a
  number, blank sends null, pending submits are guarded immediately. Saved searches
  retain the reviewed revision and project only writable fields. Dirty close asks
  before discarding. Stream assignment retains failed selections and removes only
  successful assignments from a retry, preventing duplicate writes.
- Retained inventory/import/service feedback resolves translations at render time.
  Services keep original responses in explicitly labelled technical details.
  Pure feature catalogues now live in typed JSON data, avoiding Babel coverage
  instrumentation of thousands of translation literals without warning suppression.
- Approved Football/Tennis imagery follows actual event sport metadata and carries
  a generic-illustration caption. Coastline decoration is visibly labelled. These
  never imply verified signal or replace guarded event artwork. A changed event
  revision requires another explicit artwork request.
- Focused editor/artwork checks: 69 passed; services/editor/language follow-up:
  34 passed. Full coverage and final integrated checks are still in progress.
  The first coverage attempt was blocked by loopback sandbox permissions and
  exposed a lazy catalogue assertion's short wait; it is not passing evidence.
- Full Docker packaging/service/media suite completed: **60 passed, 0 skipped**
  in 1,624.28 seconds, no warning summary. Command used the task-owned buildx
  builder and the already built ARM64 scraper security image. This does not waive
  the separate AMD64 runtime-validator defect or final-revision image checks.
- Completed frontend follow-up: **119 suites / 735 tests passed** with coverage
  in 79.333 seconds. No Babel deoptimization notes or warnings after the pure-data
  conversion. TypeScript, ESLint (zero warnings), production build and standalone
  helper message drift also passed. Helper output remained byte-identical.
- Saved-search regression covers stale server revision, pending repeated clicks,
  rejected save, retained draft and confirmed discard. Two more actual-wire
  requests validate saved-search create/update projection (35 requests total).

### Contrast and bounded remote-player picker

- Corrected the original light-success text defect at the palette boundary, plus
  warning-icon/destructive-button contrast and essential input/button borders.
  282 exact semantic color pairings across the six preset/theme combinations pass;
  minimum normal-text contrast is 4.98:1, minimum essential icon/control contrast
  is 3.68:1. Exact colors, type sizes and limits are committed in contrast evidence.
- The remote-player channel picker no longer fetches the complete TV catalogue
  while closed. TV and raw-stream modes use 50-item pages and server-side search;
  selected intent survives paging and pending sends block cancellation/repetition.
- Generic sport artwork matrix at `884e8946`: 48/48 browser combinations passed,
  with actual decoded local images, explicit remote-artwork requests, recoverable
  remote-image failure, no writes and no dialog overflow. The initial launcher
  emitted NO_COLOR/FORCE_COLOR environment notices; final browser launch will
  remove that conflicting environment rather than suppress warnings.
- First ARM64 scraper image quality scan (frozen `147a6e7`): completed, report-only,
  427 baseline findings, zero new and zero new priority findings. Remaining image
  scans and final-revision reruns remain required.

### Event, extraction and catalogue editor follow-up

- Event retention retains its independent draft while its panel is hidden and
  provides Cancel to the latest saved policy. Overlay and broadcaster mapping
  editors guard pending operations and retain reviewed revisions/selections.
  Refresh outcomes use their stable status fields, with bilingual interest/search
  hints and plural broadcaster-link summaries. Focused event regressions: 44 passed.
- Extraction drafts report pending/dirty state to the installed page; standalone
  unload protection adds no application router/API dependency. Repeated test/save
  actions are guarded immediately. Success feedback retranslates without losing
  the original recipe, and result counts now use singular/plural resources.
  Focused recipe/language regressions: 9 passed. Shared helper messages regenerated.
- Catalogue reviews preserve drafts while browsing folders; host tabs remain
  guarded. Local replacement/discard asks before losing a review. File/preview/save
  operations have immediate guards and preserve failed inputs. An assignment
  Autocomplete warning exposed a selected option disappearing during close/refetch;
  selection now uses stable IDs and retains its display without enabling removed
  channels. Final focused catalogue/guard/assignment checks: 17 passed, warning-free.
- Supplemental AMD64 emulated runtime at frozen `147a6e7` passed production probes,
  both-engine startup, checker crash/recovery, cache reclamation, independent Stop,
  peer access and container health. The private wrapper's cross-platform layout
  branch still assumes ARM; no private policy was changed. Its peer invocation
  lacked an explicit platform and emitted a Docker platform notice; subsequent
  local supplemental runs must supply that platform explicitly.

### Integrated review follow-up

- Frozen `abee85b2` responsive suite: **332 passed**, no skips, in 5.5 minutes
  across Chromium phone/desktop, 320 px WebKit and Firefox tablet. Browser transport
  monitor: **30 passed** across all three browsers, no skips, in 26.1 seconds.
  Launchers remove the conflicting NO_COLOR environment; no warning suppression.
- The fresh Firefox run exposed an old `Select acestream` test locator after the
  accessible name became `Select stream`. Its failed assignment left a dependent
  playlist empty. Page objects and expected feedback now use the actual names;
  persistence/export assertions remain. A complete fresh rerun is required.
- Folder matching now retains the exact reviewed rows, targets and parent tree
  through background refreshes. The regression changes the server candidate while
  preserving the selected old target and explicit Create choice, switches Spanish,
  then rejects Apply and verifies both selections remain. Focused tests: 11 passed.
- Reconciled obsolete IBM Plex/teal design guidance with the approved Inter/Barlow
  and three-preset contract. The production component catalogue maps shared owners,
  real usage sites, state tests, exceptions and add-a-feature-once steps. It does
  not claim complete native accessibility or participant acceptance.

### Full public gate and measured reorder correction

- Full gate completed with backend source unchanged from `abee85b2` and frontend
  through `de78a0f9`: **2,617 backend tests; 121 frontend suites / 746 tests**,
  no failed/skipped tests or test warnings. Schema/client drift, lint/types,
  production build and standalone payload drift passed. Private report normalization
  passed using the real `/private/tmp` path: backend 86.2% total / 78.64% changed
  lines; frontend 78.42% total / 79.8% changed lines. Coverage goals are advisory.
- Fresh strict Firefox at frozen `de78a0f9`: **61 passed**, no skips, 5.2 minutes.
  The repaired assignment and dependent playlist journeys now pass.
- Standalone committed payload: **36 browser/language/theme/width combinations**,
  108 actual template tests and exports, no external/installation requests,
  page errors, warnings or overflow. This includes Chromium/Firefox/WebKit and
  320/390/1440 px. Initial Python runner could not find its mismatched Firefox;
  the maintained Node suite uses the project's installed browser revisions.
- Private Jest reproduction remains blocked: policy `0955626` lacks the new WOFF2
  module mapping and Node-native browser test environment. Its unchanged config
  fails while importing `theme.ts`. Public full-gate success is not a private-policy
  CI pass. A maintainer policy update is required; no private files were changed.
- Initial 10,000-channel reorder measurement exposed 150,226 DOM elements,
  approximately 793 MB browser-reported heap and 4.47 seconds to open. The editor
  now loads lazily and uses the React-18-compatible maintained TanStack Virtual
  3.14.26 adapter above 100 rows. All IDs and the original order remain in the
  controller; measured rows preserve full names, focused/dragged nodes and positions.
- Focused reorder tests: **25 passed**. Large-order browser matrix: **48 passed**
  across all presets, EN/ES, both themes and four browser/viewports. End focuses
  row 10,000; moving it retains focus; Home/Page Down navigate without reordering;
  Save sends the exact complete 10,000-ID desired and expected arrays once.
  Repeated before/after timing and precise CDP heap evidence is being collected.
- The virtualizer changes dependencies and application code after the full gate
  above. Repeat final full application/image/browser checks before acceptance.
  Existing npm audit findings remain 4 low / 22 moderate, zero high/critical;
  installer deprecation notices are retained in Docker build logs, not suppressed.

- Repeated reorder comparison: five alternating samples per build, median open
  2,842 → 854 ms, keyboard move 2,586 → 23 ms, CDP open-state heap 751 → 31 MB.
  Post-cancel/GC heap is about 20 MB in both, so the evidence identifies peak
  rendering cost rather than a retained leak. Curated measurements and local
  budgets are committed; no universal latency or physical-device claim.
- Final recording-editor review pinned the reviewed programme/revision, locked
  time controls during submission and added dirty-close/navigation protection.
  New regressions reject save after edits, retain exact times, switch Spanish and
  confirm discard; a guide refetch cannot replace the selected programme. Focused
  recording suite: 16 passed; final integrated evidence must include this follow-up.

### Final application checkpoint `cebf5422`

- Full public gate: **2,617 backend tests and 121 frontend suites / 748 tests**,
  zero failures/skips/test warnings. Backend ran from `5054e0a8` and is byte-identical
  at `cebf5422`; frontend, lint/types, generated-artifact drift and both builds ran
  after `cebf5422` was committed. Nine separate public contract stages also passed.
  Private report normalization passed: backend 86.21% total / 78.64% changed;
  frontend 78.40% total / 79.72% changed. Changed-line goals remain advisory.
- Actual private IPv4 HTTP and HTTPS recording checks passed in Chromium 149.
  HTTP reported an insecure context, no `randomUUID`, and working `getRandomValues`;
  HTTPS reported a secure context. Record-now and guide dialogs opened/cancelled
  without writes. Double submit produced one creation; replaying its intent returned
  the same recording. Exact guide times survived, edit/discard worked, and neither
  origin produced page errors or player starts. HTTPS used an isolated self-signed
  certificate accepted only by that test context. The initial copied fixture lacked
  its matching DVR marker; storage correctly rejected it before the clone was fixed.
  See `recording-origin-evidence.json`; no installation address or credentials included.
- `5054e0a8` responsive suite: **380 passed**, no skips. Strict Firefox: 60 passed /
  1 failed because its FFmpeg process exited with signal 9 before playback advanced.
  The full fresh `cebf5422` Firefox and responsive suites are running; the earlier
  failure stays in the evidence and is not counted as a pass.
- Final Docker builds encountered full Docker storage. Removed only 21 obsolete
  task-owned image tags and old cache in the dedicated `ux314-validation` builder;
  unrelated images/cache/volumes were preserved. Original failure logs remain.
  The frozen final matrix is retrying; Docker packaging and final image scans remain.
- Private Jest policy still blocks the trusted validation path. Its reviewed config
  needs WOFF2 mapping and the native Fetch-capable test environment (or equivalent
  pinned trusted implementations); public configuration alone is not applied there.
  Any private policy/runner checksum change belongs to the maintainer-controlled
  infrastructure repository. This application PR does not change that policy.

Next: finish final browser/image/service/media checks, Docker-on/off journeys,
repeat performance measurements, reconcile acceptance evidence, and update the
single PR/issues. Participant, native AT/zoom, physical device and native ARMv7
evidence remains explicitly unaccepted and requires the stated external owners.

### Media isolation diagnosis

- Final application responsive suite: **380 passed**, no skips, 5.6 minutes.
  Final cross-browser monitor: **30 passed**, no skips, 19.7 seconds; E2E types pass.
- The first `cebf5422` strict Firefox run had 60 passes and one failure: a manifest
  returned 404 after FFmpeg exited with signal 9. The previous failure had the same
  process symptom. Investigation found that task backends had separate databases
  but shared default `/tmp/acestream-player`; a newly started backend's intentional
  startup sweep killed another fixture's FFmpeg. This was test isolation, not an
  accepted application failure or reason to weaken error monitoring.
- The repository E2E launcher now explicitly owns `.stack/player-hls`, and the
  final fresh fixture uses its own HLS directory. Complete Firefox rerun retains
  all assertions and strict API/console/backend monitoring. Docker backends have
  separate container namespaces and explicit task HLS directories.

### Rendered accessibility and delayed preload corrections

- A production axe-core 4.14.0 scan covered 21 routes × three combinations:
  Lime/Spanish/dark/320px, Coral/English/light/390px, Cyan/Spanish/light/1440px.
  It found 12 violation instances: filled primary Chip contrast, heading-order
  jumps, pagination controls directly inside the grid role, and unnamed recipe
  accordion regions. Shared fixes removed all 12 in the same 63-state rescan.
  Retained 85 incomplete rule instances are explicitly triaged in
  `a11y-browser-evidence.json`; they are not counted as passes or native AT evidence.
- Shared pagination now sits outside the desktop grid and retains the same DOM
  control across paging; a regression verifies retained keyboard focus. Event and
  schedule headings use the appropriate semantic levels. Recipe accordion names
  and controls use stable React IDs in both installed and standalone entries.
- Filled palette-primary controls use contrast text for their actual background;
  primary action buttons retain their own action tokens. Six-theme coverage now
  records 288 exact contrast pairings. Focused fixes passed 69 tests; the final
  pagination/focus suite separately passed 19 tests, with no warnings.
- A slower WebKit run exposed delayed unused-preload warnings for the already
  executed entry module. Vite now excludes only that redundant late preload hint;
  native imports and other preloads stay intact. All 48 reorder combinations
  passed, including observation beyond the delayed warning window in each browser.
  The interrupted earlier responsive run remains failed/incomplete, not a pass.
- `2b55a46e` strict local Firefox passed 61/61. `cebf5422` Docker-on and Docker-off
  each passed 61/61 with strict monitoring; managed engine restart and external
  disabled-service behavior both ran. Final source changes above require affected
  application/browser/image reruns. The standalone checkpoint passed 36/36.
- Runtime contract initially failed because the sandbox denied `/dev/fd` process
  substitution. Its permitted rerun is being checked; the earlier blanket
  nine-stage statement must be read with this correction until that result is recorded.

### Integrated checkpoint `0e10d63e` and production static fix `7f5ce82d`

- The full public gate at `0e10d63e` passed **2,617 backend tests and 121 frontend
  suites / 749 tests**, with zero failures/skips/test warnings. The backend began
  at `2b55a46e` and was byte-identical; frontend/codegen/lint/types/builds used
  `0e10d63e`. Private report normalization passed: backend 86.20% total / 78.64%
  changed; frontend 78.40% total / 79.73% changed (changed-line goals advisory).
- All nine public contracts passed with the required local shell permission.
  This includes the runtime contract previously denied `/dev/fd` by the sandbox;
  that failed invocation remains recorded and is superseded by the permitted pass.
- Strict Firefox passed **61/61**; monitor checks **30/30**; standalone helper
  **36/36 combinations** with 108 template tests/exports. No skips. Actual private
  HTTP/HTTPS recording checks passed again, including the insecure-context crypto
  fallback, no-write Cancel, one creation on double submit, same-intent replay,
  exact guide times and edit/discard, with no page errors or player starts.
  One harness invocation used Python without Playwright; the configured environment
  corrected it. Another used immediate `uncheck()` against router-deferred state;
  the final harness clicks and awaits both unchecked state and the resulting URL.
- The final 100 production-load samples had no page errors. With 10,000 channels,
  cold medians including 500ms idle were Watch home 1,140ms, Settings 725ms,
  TV channels 938ms, Live TV 764ms, Extraction 768ms. TV/Live TV/Settings made
  6/5/4 API calls versus baseline 24/25/20. Host concurrency affects timings.
- Five alternating reorder comparisons measured median open 3,199 → 876ms,
  keyboard move 2,924 → 33ms, precise open heap 753 → 28MB and DOM 150,226 → 442.
  Post-cancel collected heap was approximately 20MB on both. Thirty repeated
  same-context reorder/filter/scroll cycles made no writes or page errors; DOM
  stabilized at 1,373 and final collected heap was 27.4MB versus initial 14.4MB.
  Warmed caches and sampled variability are retained, not described as proof of
  no leaks. See the three `performance-*-final.json` evidence files.
- The responsive suite through FastAPI found **18 WebKit failures / 362 passes**:
  `/manifest.json` returned SPA HTML. This was hidden by Vite preview, which serves
  root assets correctly. `7f5ce82d` adds explicit manifest/favicon responses and
  missing-asset 404s; four focused backend tests pass. Browser console assertions
  remain unchanged. Full affected application/browser/image validation is rerunning.
- This final serving correction leaves frontend asset bytes identical to
  `0e10d63e`. Performance, standalone, contrast, axe and browser-monitor evidence
  therefore remains applicable to those bytes; production backend behavior is
  verified separately by the reruns. No manual acceptance requirement is waived.

- The corrected `7f5ce82d` private HTTP/HTTPS recording repeat also passed both
  origins. The nine public contracts passed again. The superseded `0e10d63e`
  Docker-on suite passed 61/61; its Docker-off run exposed an eager heading-list
  assertion before the lazy Settings editor mounted. The maintained test now waits
  for the same exact two headings. No timeout, expected heading or console assertion
  was removed. Final Docker-on/off runs use this assertion.

- Corrected production-backend browser results: **380/380 responsive scenarios**
  and **61/61 strict local Firefox journeys**, no skips. Private-origin recording
  repeat passed both HTTP and HTTPS. All nine public contract stages passed.
  The strict runner emitted one Node environment notice because both `NO_COLOR`
  and `FORCE_COLOR` were set; it is retained in the log and does not come from the
  application. Docker browser wrappers remove the conflicting inherited variable.

### Pinned source/security scan follow-up

- The private source/dependency/history scanner completed at `f4694fd8`: 394
  findings, four new, two marked priority. The two priority records refer to the
  same synthetic recording-intent UUID in the current serializer test and its
  commit history; it is not a credential and was never used outside the owned
  listener. The current fixture now uses an explicit zero-filled valid UUID.
  No scanner suppression, policy exception or history rewrite was introduced.
- The two new advisory Ruff findings were an OpenAPI helper import below module
  statements and a test's comparison to `False`. Both were corrected directly.
  Actual serializer contracts pass 3/3 after the fixture change. Integrated
  validation is repeated for the import-order correction; historical scanner
  classification requires owner triage and is not silently counted as clean.

### Scan-corrected application `e40dc853`

- The unchanged pinned source/security scanner completed: 391 findings, one new
  historical synthetic-UUID classification, **zero new current-tree findings**.
  Both Ruff corrections and the current test fixture pass the scan. The historical
  false positive stays visible for owner triage; no private exception or history
  rewriting was used. Focused provider/static contracts passed 33 tests and actual
  consumer serializers passed 3 tests before the full rerun.
- Actual private HTTP and HTTPS recording checks passed on this exact backend.
  All nine public contracts passed. Frontend production assets remain identical
  to `0e10d63e`; the source correction moves an import and clarifies test data.
- At the preceding `7f5ce82d` checkpoint, all 15 image builds passed, all five native
  ARM64 runtime probes passed and the ARMv7 layout probe passed. The private AMD64
  wrapper failed its ARM-layout assumption; the separate full AMD64 emulated probe
  passed. All seven image security comparisons completed with zero new findings
  (427 existing findings per ARM64 image, 431 AMD64, 358 ARMv7). The first scraper scan was
  incomplete and its same-policy diagnostic retry succeeded; its cause was not
  reproduced. Final images/scans are repeated for `e40dc853`.

### Final screenshot and account-race corrections

- Direct inspection of 320px WebKit screenshots found reorder names squeezed into
  a few letters per line despite passing overflow checks. Phone rows now reserve
  the upper row for the complete name and put numbering/arrow controls below.
  Desktop layout and full-order semantics are unchanged. A regression requires an
  ordinary 23-character name to fit within two lines at 320/390px, alongside the
  existing virtualized focus and exact 10,000-ID submission assertions. Curated
  synthetic before/after crops are under `screenshots/reorder-320-*.png`.
- The `e40dc853` local strict run had 60 passes and one unexpected policy 403.
  Its trace showed GET `/auth/policy` beginning before POST `/auth/disable` but
  completing after protection was disabled. Administrative reads now consume query
  AbortSignals and are cancelled before disabling; new reads and editor actions
  pause during submission. Failure retains the form and resumes reads. A deterministic
  regression verifies abort-before-mutation, blocked concurrent edits and retained
  password/confirmation after rejection. Focused Access/reorder tests pass 20/20;
  frontend types, warning-free lint and production builds pass.
- The preceding Docker-off run had 60 passes and one navigation readiness timeout
  under concurrent build load; no timeout or error-monitor allowance was widened.
  The following run was interrupted by the session/environment restart. Docker's
  socket was then absent; the maintainer restarted Docker Desktop and its permitted
  availability check now succeeds. Incomplete application/image/packaging runs and
  the partial 48-case phone fix run are not counted as passes. Resume final checks
  from frozen sources, keeping heavy builds separate from browser timing checks.
