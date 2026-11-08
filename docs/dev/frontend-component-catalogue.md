# Production component catalogue

These are maintained application components, not the review prototype. Paths
below are relative to `frontend/src/`; browser scenarios live in `e2e/`. Open the
linked route on an isolated installation to inspect real controllers and saves.
Select Lime, Coral/navy or Immersive, then independently select EN/ES and light/dark.
Do not add another page tree or a development-only controller to demonstrate them.

| Family and owner | Production example | State and behavior evidence |
| --- | --- | --- |
| `layout/PageHeader`, `ContentSection`, `StatusLine` | `/system`, `/tv-channels` | `layoutPrimitives.test.tsx`, `StatusLine.test.tsx`; `mobile/dashboards.spec.ts` covers narrow layouts and independent sections |
| `state/EmptyState`, `InlineStatusNotice` | Empty sources, recovery and failed independent panels | `sharedStateComponents.test.tsx`, `StartupGate.test.tsx`; notices use text with alert/status roles and keep actions reachable |
| `InterfaceSelector`, `preferences/AppPreferences` | Interface button in the shell | `AppPreferences.test.tsx`: unknown values, read/write failure and retry, retained query cache/draft/video/dialog; `tests/11-live-tv.spec.ts` checks actual HLS ownership |
| `ConfirmDialog`, `useConfirm`, `UnsavedChanges` | Dirty Settings navigation and destructive row actions | `ConfirmDialog.test.tsx`, `UnsavedChanges.test.tsx`: Stay/Discard, Back/query/unload, pending/failure, retained language-sensitive descriptor |
| `settings/*`, `hooks/useSettingDraft` | `/settings?tab=playback`, automation, links, access, network | `Settings`, `NetworkSettings`, `PlaybackRoutingFields`, `OfflineCleanupFields` tests; independent saves, saved baselines and retained failures |
| `SourceEditor`, shared guide fields | Setup and Channels → Sources/Programme guide | `SourceEditor`, `SetupOnboarding`, `GuideSetup` tests; `mobile/source-management`, `setup`, `guide-setup` scenarios |
| Channel table/cards, filter bar, number field, reorder | `/tv-channels` | `TVChannelFilters`, `ChannelNumberField`, `TVChannelReorder` tests; complete-order stale checks are separate from bounded browsing |
| `RowActionsMenu`, `ChannelRowActions` | Channel tables and phone cards | `RowActionsMenu`, `ChannelRowActions` tests preserve action eligibility and destructive confirmation |
| `ChannelPickerDialog`, `RemotePlayerDialog` | Connections → TVs and players | `ChannelPickerDialog`, `RemotePlayerDialog` tests: bounded pages, retained selection, dirty/pending/failure and probe results |
| `StreamLinkFormatsSection` | Settings → Stream links and Playlist | `Playlist`, `Settings` tests share one format editor; playlist options remain independent |
| `ProgrammeArtwork`, `events/EventArtwork`, `SportIllustration` | Watch/guide and Events details | `UpcomingEvents`, `Events` tests; `mobile/event-illustrations.spec.ts` checks 12 presentation combinations per viewport, decode/failure, generic captions and explicit remote loading |
| `ChannelPlayerDialog`, `StreamPlayerDialog` | Live TV and contextual Play | `ChannelPlayerDialog`, `StreamPlayerDialog`, `LiveTV` tests; real `tests/11-live-tv.spec.ts` covers preference/filter continuity and release |
| Recording intent/editor/settings and collections | `/recordings`, guide Schedule recording | `RecordingIntent`, `Recordings`, `LiveTVGuideRecording` tests; `mobile/recordings.spec.ts` and real guide scheduling cover storage/time/intent boundaries |
| Event retention/overlay/mapping editors | `/events` → management and details | `Events.test.tsx` retains drafts, reviewed revisions, pending guards and errors; `mobile/events.spec.ts` covers responsive controls |
| `recipes/RecipeBuilder` | `/scraper/builder` and standalone `docs/recipes/` | `RecipeBuilder`, `Localization` tests; shared generated resource subset and Pages drift checks; exported recipes retain their machine values |
| `integrations/*`, access forms | `/integrations/*`, `/settings?tab=access` | `Integrations`, `TvCasting`, `Access`, `TelegramSection`, `NotificationsSection` tests; fake delivery and controlled device responses preserve trust boundaries |
| Service/storage/job/recovery panels | `/system`, `/warp`, `/startup` | `ServicesPanel`, `StoragePanel`, `ScheduledJobs`, `Warp`, `StartupGate` tests distinguish unknown/partial/failed/saved-applied states |

Test names without an extension above resolve to `src/__tests__/<name>.test.tsx`.
The table identifies relevant executable evidence; it does not assert that every
family has completed every permutation or native assistive-technology acceptance.
The exact revision and results belong in the epic implementation ledger.

## Add a feature once

1. Put the domain request in the shared service and generated API type chain.
   Reuse the query key/controller; keep permission decisions there or on the server.
2. Give one canonical editor ownership of the draft, reviewed revision and save.
   Register dirty/pending navigation, guard repeated actions immediately and retain
   inputs/errors on failure. A local modal also guards its own close operation.
3. Add complete EN/ES messages and plural forms. Keep retained feedback as data or
   a translation factory. Never translate names, IDs, source text or submitted values.
4. Compose the shared header/section/state/actions. Read semantic tokens from the
   theme; use `action.controlBorder` for essential input boundaries. Preserve
   labels/help, keyboard order and 320 px wrapping before adding presentation detail.
5. Run one behavior scenario with all presets. Assert equivalent request payload,
   permission, transitions and saved result. Add layout checks for each preset,
   both themes and Spanish expansion; do not copy the controller three times.

## Small presentation exceptions

| Owner | Reason and variable presentation | Invariants and parity evidence |
| --- | --- | --- |
| `styles/presets.ts`, `theme.ts` | Palette, density, section spacing, radii and Lime headings distinguish the approved interfaces | Same typed tokens/controls; six-theme tests and 282 contrast pairings |
| Watch composition | Approved coastline imagery has different prominence; compact Lime/phone layouts prioritize catalogue and player | Generic caption, no signal claim; same catalogue, filters and viewer owner; Live TV/media journeys |
| `SportIllustration` | Relevant sport imagery adapts crop/prominence to the preset | Actual sport metadata chooses assets; generic caption; same event and explicitly requested event artwork; 48 browser combinations |

No exception owns requests, permission checks, persistence or media lifecycle.
Any new exception needs a reason, named owner and shared behavior evidence here.

## Review still requiring people or equipment

Automated keyboard/viewport and semantic-token checks support review; they do not
prove spoken announcements, actual browser zoom, virtual-keyboard behavior or
physical receiver operation. Record VoiceOver/NVDA/TalkBack, native 200/400% zoom,
small-device and fluent Spanish/nontechnical participant outcomes separately under
#315/#317/#324. Keep failures and unavailable equipment explicit.
