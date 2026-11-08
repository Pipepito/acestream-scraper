# Implemented surface and editor ownership

Source snapshot: `cebf5422`, 2026-11-08. This map describes the application, not the
review prototype. Automated evidence is linked below; native accessibility,
physical-device and participant acceptance remains pending in `acceptance.json`.
All rows use the same router, query cache, services, access model and EN/ES resources
under Lime, Coral/navy and Immersive. None owns a presentation-specific controller.

## Routes and hidden entry points

| Destination | Routes / contextual entry | Canonical owner and significant state |
| --- | --- | --- |
| Watch | `/`, `/live-tv` | WatchHome/LiveTV; bounded catalogue, online/search/category/favorite filtering, guide, embedded viewer; filtering retains playback |
| Recordings | `/recordings`, `?tab=settings`, guide/card Record | Recordings, RecordingDialog, RecordingSettingsFields; Library, Upcoming and active, History; immutable programme review, creation intent, Stop/Cancel/Delete/convert/protect |
| Events | `/events`, event/timezone query links | Events and event editors; interests, timezone, following, mapping, overlay and retention; independent reviewed revisions |
| Channels | `/tv-channels`, `/tv-channels/:id` | TVChannels/detail, filter/number/favorite controls, complete reorder draft, association, guide and row actions |
| Channels → Streams | `/acestream-channels` | AcestreamChannels and shared row actions; verified media signal is separate from imported identity |
| Channels → Sources | `/scraper`, `?tab=w3u` | Scraper, SourceEditor, catalogue import/folder matching; Save and Find channels remain separate operations |
| Channels → Search | `/search` | Search and saved searches; import exclusions, original IDs and added/verified distinction |
| Channels → Programme guide | `/epg`, `?tab=rules`, `/epg/channels/:id` | EPG, guide source fields, GuideSetup, schedule/matching; read-only preview and explicit guarded Apply |
| Channels → Playlist | `/playlist` | Playlist and shared StreamLinkFormatsSection; export options persist independently |
| Extraction | `/scraper/builder`, source recipe editor, standalone `docs/recipes/` | Shared recipes components/workers; installed API preview vs local standalone; export identity is language-independent |
| Connections | `/connections` | Destination links; no duplicate configuration form |
| Public address | `/integrations/public-address` | PublicAddressSection; saved/effective/environment address and proxy prefixes |
| Web player | `/integrations/web-player` | WebPlayerSection; bounded player settings and original video default |
| TV casting | `/integrations/tv-casting` | TvCastingSection; discovery, permission and ownership remain distinct from accounts |
| Remote players | `/integrations/remote-players` | RemotePlayerDialog/ChannelPickerDialog; pairing/probe/send, retained credentials and bounded catalogue picker |
| Media servers | `/integrations/media-servers` | MediaServersSection/TunerSection; IPTV links and relay startup limits retain independent saves |
| Notifications | `/connections/notifications` | NotificationsSection; masked saved webhook, explicit test against owned test receiver only |
| Telegram ingestion | `/scraper/telegram` | TelegramSection; account login and source configuration retain separate operations and drafts |
| Settings | `/settings`, `?tab=playback|automation|links|access|network` | Index links or exactly one canonical section; other query keys preserved |
| System | `/system`, `/system/runtime`, `/warp`, `/changelog` | Independent health/storage/jobs/diagnostics, RuntimeSettings, WARP and release notes |
| First run / recovery | `/setup`, `/startup`, login/token/recovery gates | Setup/StartupGate/access; source addition reuses SourceEditor; failed startup remains diagnosable |
| Unknown path | unmatched routes | NotFound; recovery navigation stays within the shared shell |

`App.tsx` retains aliases `/dashboard` and `/stats` → `/`, `/health` → `/system`,
`/integrations` → Public address, `/channels` and `/channels/:id` → TV channels,
`/search-new` → Search, `/epg/mappings` → guide rules, `/catalogues` → W3U, and
`/integrations/telegram` → Telegram ingestion. Target query keys win; unrelated
incoming query values survive. `routes.test.tsx` and real navigation journeys cover
aliases/deep links. A parameterized alias deliberately preserves existing behavior;
it does not invent an identity mapping between legacy channel types.

## Settings owners and transactions

| Concern | Canonical owner | Field families and save boundary |
| --- | --- | --- |
| Playback | PlaybackSettings / shared routing fields | Engine URL, direct/Acexy selection and proxy URL; retain existing endpoint contracts |
| Automation | AutomationSettings | Scrape/check/EPG intervals, schedule anchors/timezone, checker selection, matching opt-in, cleanup; independent scalar/group saves |
| Stream links | LinkSettings / StreamLinkFormatsSection | Format entries, PID/AppID and compatibility; one editor also used by Playlist |
| Access | AccessSection | Setup, accounts, password, permissions, policy and IPTV credentials; each transaction and sensitive reveal is independent |
| Network | NetworkSettings | Trusted proxy/network runtime options with expected revision and explicit restart notice |
| Runtime | RuntimeSettings / setup metadata | Backend runtime-options metadata drives defaults, effective values, units/help and restart consequences; 47 translated option labels/help are checked |
| Recording defaults | RecordingSettingsFields | Enabled, concurrency, space/size/retention; disabling confirms active/future consequences and preserves existing files |
| Recording intent | RecordingDialog | Reviewed programme/revision, timezone/start/end/ambiguous instant and idempotency key; pending controls locked, failure retains values |
| Public address | PublicAddressSection | Effective installation address, saved/environment override; settings and feature entries link here |
| Media servers / tuner | MediaServersSection / TunerSection | Refresh and relay settings; explicit independent Save, retained failed draft |
| Notifications | NotificationsSection | Delivery configuration; server-masked saved baseline, separate test action |
| Source / guide | SourceEditor / GuideSourceFields | Original URLs/IDs/provider configuration; source Save does not imply fetch or verified playback |
| WARP | WARP page/fields | Exclusions/startup options separate from explicit connect/reconnect; engine health independent |

The exact runtime field ledger remains `backend/app/config/runtime-options.json`;
`RuntimeLocalization.test.ts` checks every entry. Application settings are not
converted into a global Save transaction. `docs/dev/settings-editors.md` documents
query/tab/Back/unload protection and modal-specific close guards.

## Terminology and translation boundaries

| English | Spanish | Meaning |
| --- | --- | --- |
| Watch | Ver | Viewing destination, not a management permission |
| Recordings | Grabaciones | Stored/scheduled captures, separate from live viewer sessions |
| Events | Eventos | Events with original titles and explicit display timezone |
| Channels | Canales | Curated TV inventory; original stream IDs remain distinct |
| Connections | Conexiones | Viewing destinations and integrations |
| Settings | Ajustes | Canonical editors and their independent save boundaries |
| System | Sistema | Operational state, diagnostics and runtime configuration |

Typed resources are authoritative for exact operational copy. Original names,
programme/source text, URLs, IDs, machine times and protocol diagnostics are never
translated as application labels. Stable error/reason codes choose translated
feedback. Fluent Spanish review is still required; this terminology draft is not
participant approval.

## Evidence and limits

- Shared component states and exceptions: `docs/dev/frontend-component-catalogue.md`.
- Real 35-request consumer contract capture, selected provider/non-JSON responses
  and separate semantics: `docs/dev/executable-api-contracts.md`. This is not an
  exhaustive operation-by-presentation contract matrix.
- Main application tests, full strict Firefox journeys, responsive Chromium /
  Firefox / WebKit and standalone template/export checks: exact revision/results
  are maintained in `implementation-ledger.md`.
- Actual private HTTP/HTTPS recording evidence: `recording-origin-evidence.json`.
- Six-theme contrast pairings, artwork/font provenance and performance measurements
  are maintained in their respective documents; they do not prove native AT,
  browser zoom, physical keyboards/receivers or participant comprehension.

Every row has an implementation owner. Exhaustive field/state/permission/preset/
locale acceptance remains distinct from this route inventory and must not be
inferred from a passing representative journey.
