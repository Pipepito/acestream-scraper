# TV and system dashboards

Implementation record, 2026-10-26. Initial baseline: `221952f`; integrated develop
through PR #269 merge `26ad950`.

Split Overview into a TV dashboard at `/`, where users land, and System status at
`/system`. The landing page answers what is playing, what is coming up, and what
channels and streams are available. System status answers whether the application
and its services are running and what maintenance needs attention.

Implementation in progress on `feat/tv-system-dashboards`: the dashboard split is
implemented, including immediate event selection and browser display preferences.

## Content and navigation

| Destination | Content | Main actions |
| --- | --- | --- |
| **TV dashboard** `/` — first under Watch | Current playback; immediate and tracked events; TV channels, streams and guide coverage; content freshness | Watch TV, view event broadcasts, open channel inventory, open guide |
| **System status** `/system` — under System | Service health and controls; software version; storage; diagnostics; complete scheduled job history and queue | Start/stop/restart supported services, download diagnostics, edit schedules |

Keep Live TV at `/live-tv` as the viewing catalogue and embedded player. Keep
Events as the full agenda and source-management destination. The dashboard is a
summary and starting point for these pages.

Move `/health` to `/system`; keep `/dashboard` and `/stats` pointing to `/`.
Update shell titles, selected navigation, WARP's return link and contextual links
that currently use `/` to mean service administration. Keep startup recovery and
API-token gating ahead of both dashboards. Preserve global update notices and
PR #269's compact release-notes link.

## TV dashboard layout

Use the existing `PageHeader`, `StatusLine`, `ContentSection`, theme and spacing
tokens. Keep IBM Plex Sans, compact rows, accessible status text and equivalent
light/dark hierarchy. On phones, stack sections in reading order without hiding
actions or requiring horizontal scrolling.

1. **Header and summary:** TV dashboard, Watch TV action, channel and stream
   totals. Keep the status line short; detailed counts belong below.
2. **Playing through this app:** visible browser sessions and server relays,
   showing channel name, state, destination/viewers, peers and start time where
   supplied. Collapse a successful empty result to one short line so events move
   up. Loading and failed reads must not say nothing is playing.
3. **Up next:** a compact agenda of at most six events, with start time/date,
   competition, participants/title, reported state and broadcaster names.
   Provide All upcoming / Following / My interests views and View all events.
4. **Channels and streams:** existing inventory totals, with links to TV Channels,
   Acestream Channels and EPG. Preserve online/offline/not checked distinctions.
   Guide assignment is coverage, not evidence that a channel can play.
5. **Next updates:** time until the next source scrape, guide refresh and stream
   check. Show Running now or Waiting to run when applicable, and keep last runs,
   results and job tables exclusively on System status.

When there is no catalogue or schedule, offer the relevant Add sources / Add
events action. A service failure must not replace the entire TV dashboard with
an error page. Keep content and playback errors local to their sections.

## Events and PR 269

[PR #269](https://github.com/Pipepito/acestream-scraper/pull/269),
“Add built-in sports schedules and simplify event browsing”, was inspected at
merged into `develop` as `26ad950424492dcc75924ecf238fb9eb9eaa8ed0` on
2026-10-26, confirmed through GitHub. The feature branch incorporates that merge;
this record makes no CI assertion.

The PR introduces a day-by-day `EventAgenda`, `EventInterestFields`, broadcaster
TV/EPG targets, date-only fixtures, WOSTI/OpenFootball provider options, and
interest filters combining sports, competitions and teams with OR. The dashboard now reuses these merged contracts and the extracted agenda row;
provider implementations remain shared.

### What to track

- **All upcoming** is the initial view, showing the nearest saved events within
  the next seven days, with eligible publisher-reported live events first.
- **Following** uses the existing persisted per-event follow state. It is shared
  installation data, not a private account watchlist.
- **My interests** reuses the PR's sports/competitions/teams selector and OR
  semantics. Save display preferences and timezone per browser, with versioned,
  validated storage and a safe fallback when storage is unavailable. Keep them
  separate from provider import interests, which determine reviewed source scope.
- Remember the selected dashboard view. Empty Following or My interests views
  explain how to populate them and offer All upcoming without silently switching.

The PR's `/events/interests` returns available choices, not saved personal
preferences. The dashboard therefore persists these preferences separately in browser storage.
Viewing or filtering the dashboard must not import events, change source settings,
trigger refreshes or start playback. New provider events still require review.

### Immediate event selection

The default agenda list sorts saved events by start time, and `upcoming` includes earlier
events from today. PR #269 adds a calendar-day window, but does not introduce
nearest-start or live-first ordering. Sorting the first response page in the
browser would miss eligible events on later pages.

The opt-in `selection=dashboard` mode preserves normal agenda behavior. Eligibility,
interests/following and ordering apply to the complete bounded inventory before
limiting the response to six. Business rules live in `EventService`; database access
remains in its repository.

Implemented selection rules:

- Exclude archived, finished and cancelled events. Explicitly past end times also
  exclude events from the immediate list, even if a source still says live.
- Rank eligible `live` assertions first, labelled **Live · reported**. Include
  overnight events when a supplied end is still future; without an end, only
  promote live assertions whose known start is within the preceding 24 hours.
  Older or undated assertions remain available in the full agenda.
- Then show known future starts, nearest first, using the selected timezone for
  the seven-calendar-day window. Break ties deterministically by event ID.
- Keep date-only fixtures separate as **Time TBC**, ordered by their supplied
  calendar date. Do not turn a date into midnight or an invented countdown.
  Fully undated events belong behind a clearly labelled full-agenda link.
- Compute selection on the server from timezone-aware time. Refresh at a modest
  interval and on window focus; invalidate event queries after follow/correction
  changes. Test midnight, DST and events crossing the selection boundary.

The shared `EventAgendaRow` preserves dashboard ranking without the full agenda's
day-group sorting. Links at `/events?event=<id>&zone=<timezone>` open the existing
detail drawer in the selected timezone. Missing and archived links show explicit
states, with Close event details returning to the agenda.

A linked TV or EPG channel is navigation, not proof of playable signal. Preserve
unmatched broadcaster names and the PR's manual regional mappings. Play actions
reuse existing event/channel player flows only when a playable source is available.

## Playback scope and component reuse

`useActiveStreams` already polls `/api/v1/player/streams` every ten seconds using a
shared React Query key. Extract the playback list from
`components/integrations/WebPlayerSection.tsx` into a reusable presentation
component. Integrations keeps configuration/capability details and can reuse the
list; the landing dashboard does not need FFmpeg paths or conversion internals.

The endpoint covers app-owned browser sessions and relays. It does not enumerate
players connected directly to an external engine. Label that scope alongside
the list, preserve null versus zero, and do not count error/stopped sessions as
currently playing. Browser sessions and relay clients also have different viewer
semantics; avoid presenting their sum as a count of distinct people.

Dashboard reads must never call the session heartbeat endpoint, acquire a viewer
lease, probe an engine or stop a session. Do not render private upstream URLs.
Showing event titles for event-only playback may require a separate bounded
name-resolution enhancement; the first version can use a safe unnamed-stream
fallback without guessing a match by title.

## System status layout

Move existing service-health derivation, `ServicesPanel`, `StoragePanel`,
`DiagnosticsDownload` and `ScheduledJobs` from Overview. Add the application
version from the existing health response. Keep service controls and their
confirmation/ownership semantics unchanged.

Preserve external-engine detection, optional engines and intentional UI Stop.
Unavailable health data must read Unknown/Unavailable rather than Healthy.
Service, storage and scheduler reads fail independently; diagnostics remains
available when those queries fail. Preserve bounded storage scans and partial-size
labels. Full maintenance history includes cleanup and migration tasks; the TV
dashboard only surfaces time until the next content updates.

## Implementation sequence

1. **Dashboard split:** introduce `TVDashboard.tsx` and `SystemDashboard.tsx`;
   extract the active-stream list; reuse inventory and scheduler components;
   update routes/navigation and independent loading/error states. No backend
   contract change is needed for this first slice.
2. **Event integration after PR #269:** add the server-side dashboard selection,
   regenerate OpenAPI/client types, add a shared event query hook, and reuse event
   rows/details. Add display preference persistence, event deep links and bounded
   polling. Do not add a second event store or ingestion scheduler.
3. **Verification and documentation:** update user navigation and screenshots in
   `wiki/Usage.md`, event behavior in `wiki/Sports-Events.md`, and the navigation
   contracts in `CLAUDE.md` and `frontend/AGENTS.md`. Update affected Overview
   references in operator docs. Record user-facing changes through the existing
   changelog source/generation workflow.

## Acceptance and checks

- Opening `/` lands on TV dashboard; System status is independently reachable;
  legacy redirects, mobile navigation and shell titles select the right page.
- Playback loading/empty/error/stale states remain distinct. Navigating to either
  dashboard does not mutate playback ownership or keep idle sessions alive.
- Active playback, imminent events and tracked events are visible without opening
  service administration. Long titles and broadcaster names remain usable on phones.
- Event selection is correct across the full inventory, including more than one
  API page, followed/interested views, ties, date-only rows, cancellations,
  overnight events, unknown end times, timezone changes and DST boundaries.
- Failed section requests do not hide successful sections or claim zero/healthy.
  Optional engines and intentionally stopped engines retain existing behavior.
- Verify desktop/phone layouts, both themes, keyboard/focus, status text and reduced
  motion. Preserve PR #269's release-note acknowledgment behavior.

Implementation validation: focused Jest coverage for the two dashboards, shared
playback/event components, routes, navigation and WARP links; focused backend event
tests and generated-client drift checks for the event contract change; frontend
typecheck, warning-free lint and production build; the quick cross-stack gate and
strict legacy-path guard. Update `e2e/tests/01-navigation.spec.ts` and add a mocked
mobile dashboard journey following `e2e/AGENTS.md`. Run the full gate for the
completed cross-stack event integration.

### Dashboard split validation

Local checks on 2026-10-26 against the uncommitted feature branch based on
`221952f` (not a Jenkins status):

- Full frontend Jest suite: 90 suites, 519 tests passed. After the final status
  handling/contrast adjustment, both dashboard suites passed again (18 tests).
- Frontend typecheck and zero-warning ESLint passed; E2E typecheck passed.
- Quick gate with `CI_USE_PREINSTALLED_DEPS=1`: 4 documentation contracts,
  87 backend contracts, generated client, frontend checks, build and Pages helper
  consistency passed. Dependencies were not changed.
- Mocked Playwright dashboard journey: eight cases passed across phone Chromium,
  small-phone WebKit, tablet Firefox and desktop Chromium in both themes. Verified
  routes, content separation, no playback mutations/heartbeats, no horizontal page
  overflow and no browser warnings/errors. Screenshots were inspected locally.
- Strict legacy-path guard and whitespace checks passed.

The production build retains its existing >500 kB chunk advisory for the player
and data-grid vendor bundles. Real media playback and Docker sidecars were not
exercised. At this initial checkpoint, event selection and personalization were
still pending; the subsequent event integration is documented below.

The TV scheduler summary was subsequently reduced to next-update timing only.
The two dashboard suites passed with 21 tests; frontend typecheck, zero-warning
ESLint and all eight mocked browser cases passed again. The production build
retains the same vendor chunk-size advisory.

## Integration setup pages

Integrations is now a fourth navigation category, between Manage and System. Its
five existing setup sections have dedicated lazy-loaded routes under
`/integrations/`: `public-address`, `web-player`, `remote-players`, `media-servers`
and `telegram`. Media servers retains shared tuner settings; WARP stays under
System. The former `/integrations` page redirects to Public address. Settings and
playback actions link straight to the relevant setup. Each page mounts only its
own queries and controls, retaining shared cache invalidation and feedback.

Integration split validation on 2026-10-26: the full frontend suite passed
(90 suites, 536 tests), frontend/E2E typechecks and zero-warning ESLint passed,
and 32 mocked browser cases passed across four device/browser profiles and both
themes. Cases cover independent integration routes/queries, the legacy redirect,
Telegram source setup, VLC Android pairing and dashboard navigation. The production
build passed with the existing vendor chunk-size advisory. Screenshots were
inspected locally; the strict legacy-path and whitespace checks passed. No live
external integrations or Docker sidecars were changed or exercised.

## Event integration after PR #269

Latest develop was merged locally after checkpointing the dashboard and integration
split. The release-note top-bar behavior and intervening stream-order changes are
preserved. Event selection, the shared agenda row, display preferences, event detail
deep links, and shared-query refresh are implemented. See `wiki/Sports-Events.md`
and `docs/dev/sporting-events.md` for the resulting user/API behavior.

Event integration validation on 2026-10-26 (local evidence, not Jenkins status):

- 10 dashboard selection tests passed, plus the 41 existing sporting-event,
  provider and maintenance tests. Cases include more than one result page,
  ordering/ties, corrections, OR interests/following, stale live assertions,
  date-only fixtures, midnight and both DST transitions.
- Full frontend suite: 92 suites, 557 tests passed. Frontend/E2E typechecks and
  zero-warning ESLint passed.
- Quick cross-stack gate passed: documentation/backend contracts, generated-client
  drift, focused frontend checks, production build and Pages helper consistency.
- Sixteen mocked browser cases passed across four device/browser profiles and
  both themes; all eight dashboard cases passed again after timezone deep-link
  handling and shorter date labels. Verified saved preferences, detail navigation,
  separate integration pages, no playback/API mutations, no horizontal overflow,
  and no browser warnings/errors. Phone/desktop screenshots were inspected.
- Strict legacy-path guard and whitespace checks passed. The existing Vite vendor
  chunk-size advisory remains. No live external integrations or Docker sidecars
  were exercised.

The full cross-stack gate reached the full backend suite: 2,036 passed, 24 skipped,
42 failed and 21 setup errors in the restricted sandbox. Retrying those exact 63
cases with localhost socket access passed 52; the remaining 11 media tests require
host FFmpeg/ffprobe, which are unavailable in this environment. The full gate is
therefore not green. No test exclusions or warning suppressions were added; the
independent quick gate and full frontend suite above passed. Logs were retained
locally in `/tmp/dashboard-full-gate.log` and `/tmp/dashboard-backend-retry.log`.
