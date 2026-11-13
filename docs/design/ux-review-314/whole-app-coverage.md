# Whole-app design coverage and handoff contract

> Review 06 is the current design-only continuation: [package](README.md), [simplified ownership](before-after-map.md), [shared presets](shared-foundations-06.md), [graphics](asset-selection-06.md) and [new evidence](verification-review-06.md). Earlier closure/implementation-next language and historical passing counts do not authorize application work or establish current acceptance.
> Review 04 update (7 November 2026): [expanded composed coverage](coverage-review-04.md), [workflow fields/interactions](workflow-specification.md), [current verification](verification-review-04.md) and [task refinements](task-refinements-04.md) supersede historical composition gaps. Prior live defects remain open. No user approval or application implementation is implied.

**Latest source update:** develop advanced to cf952af during review 03. The [current-source delta](current-source-delta.md) adds availability, matching/linking, retention fields and tuner hiding without changing route counts. Read it alongside the coverage delta; post-merge live checks remain pending.

**Review 03 update:** [fresh reconciliation and per-row evidence/status](coverage-review-03.md), [design specification](design-specification.md), [critical fields](field-ledger.md) and [all 47 runtime options](runtime-field-inventory.md). New administration mockups are in review; no row is accepted. The original inventory below remains the scope contract.

The scope is **every existing application surface**, including administration. The supplier's viewing frontend is one reference, not the scope boundary. No route, setting, dialog, advanced flow or recovery state may retain an accidental legacy design because the supplier did not provide it.

This inventory was reconciled on 7 November 2026 against application revision `7ccf16d383758aeeb78845e20e3716ddf97df10d`: `frontend/src/App.tsx`, rendered-navigation definitions, pages, settings/access/startup components and recipe entrypoints. There are **20 navigation destinations, 24 explicit application routes plus the catch-all, nine compatibility redirects, and additional gated/embedded surfaces**. Reconcile again before implementation and final acceptance; a newly discovered surface must receive an owner, not be excluded by this snapshot.

## Ownership and meaning of completion

- **#316 owns design coverage and consistency for the whole app**, including all administration and operational workflows. It produces the complete screen/state/field specification and design handoff, not just sample screens and tokens.
- **#317 owns the shared EN/ES resource, formatting, glossary and text-inventory contract.** Each feature task owns the complete copy migration for its surfaces.
- **#318–#322 own implementation of the surfaces below**, in small PRs, using the same approved design system. A task's design package must be complete before its page implementation is called ready.
- **#324 verifies every row and its states**, with no unowned/unfinished screens. #315 remains the independent reliability/accessibility work; #323 owns delivery performance across all surfaces.
- The backlog remains **ten tasks**. The rows below are work packages and acceptance records, not a request for dozens of new issues.

Current evidence is deliberately labelled: the gallery contains concept examples, current-app evidence and supplier previews. **No row below is a completed or approved design handoff.** A few attractive screens do not satisfy this contract.

## Route-level inventory

Every row inherits the state, responsive, language and interaction requirements below. “Reference” means material to compare, not design coverage or implementation completion. All rows require a full handoff.

| ID | Current route / destination | Required design content | Implementation owner | Available visual reference |
| --- | --- | --- | --- | --- |
| R01 | `/` · TV dashboard | Viewing entry, current app-owned playback, inventory, upcoming/followed events, next updates, independently failing sections | #319 | Supplier catalogue patterns only; dashboard composition still needed |
| R02 | `/live-tv` · Live TV | Embedded player, scrollable catalogue, browsing modes, current/next guide, search/filter/favourite, watch/stop/record/cast/remote handoff | #319 | Boards 02, 05, 12 and supplier player; concept only |
| R03 | `/recordings` · Recordings | Upcoming/active, saved library, history, search/status, schedule/edit, playback/parts, protection, conversion, stop/cancel/delete and storage/settings entry | #319 | Needs dedicated full design |
| R04 | `/events` · Events | Currently under Manage; proposed Watch. Agenda/date/timezone/interests/following, detail, guide overlay, Watch/Record, provider/source administration, import and broadcaster mappings | #319 | Needs dedicated full design |
| R05 | `/acestream-channels` · Streams | Raw stream inventory, filters/sort/pages, bulk controls, add/edit, verified/network states, stats/activity, TV assignment and player/playlist entry | #320 | Shared inventory pattern; dedicated stream states needed |
| R06 | `/tv-channels` · TV channels | Core/advanced filters, table/phone cards, number/favourite, full reorder, CRUD, bulk/source assignment, guide matching, row actions | #320 | Board 04; concept only |
| R07 | `/tv-channels/:id` · Channel detail | Channel identity/editing, associated streams, guide/schedule, actions, status/activity and missing/deleted-channel state | #320, player #319 | Needs dedicated full design |
| R08 | `/scraper` · Channel sources | All four tabs: sources, W3U catalogues, saved searches, import exclusions; source add/edit/update/delete/orphan cleanup and queue/results | #321 | Supplier source screen only; remaining flows need design |
| R09 | `/scraper/builder` · Extraction builder | Sample input/fetch/upload, selectors/fields/paired preview, manual/JSON/regex, validation/test, save/copy, bounded/heavy-source paths | #321 | Needs dedicated full design |
| R10 | `/search` · Discovery search | Provider/scope, advanced search, results/select/add/play, duplicate/exclusion/already-added and unavailable-provider states | #321 | Supplier catalogue filtering is not this capability |
| R11 | `/epg` · Programme guide setup | Sources, channels, matching, rules, export; source CRUD/update, scoped preview/selection/apply, conflict review and coverage | #320 | Needs dedicated full design |
| R12 | `/epg/channels/:id` · Guide channel detail | Source-qualified identity, programme schedule/detail, mapping context and missing/no-programme states | #320 | Needs dedicated full design |
| R13 | `/playlist` · Playlist | Format, filters/options/guide/token context, copy/download, shared inline format editor and effective-address link | #320 | Needs dedicated full design |
| R14 | `/integrations/public-address` · Address for players | Effective/saved/environment address, validation/proxy-prefix help, save/reset and contextual usage | #322 | Needs dedicated full design |
| R15 | `/integrations/web-player` · Web player | Browser playback configuration/capability/help, shared routing where applicable, actionable unavailable states | #322 | Supplier dialog is not this settings page |
| R16 | `/integrations/tv-casting` · TV casting | Inventory, bounded discovery/manual setup, receiver/trust/permissions, cast/reconnect/stop and compatible-copy choice | #322 | Needs dedicated full design |
| R17 | `/integrations/remote-players` · Remote players | List/editor, find players, launch/connect/control, explicit remote-control opt-in and account requirement | #322 | Needs dedicated full design |
| R18 | `/integrations/media-servers` · Media servers | List/editor, tuner/channel/guide/address choices, source/total startup limits, integration-specific instructions/status | #322 | Needs dedicated full design |
| R19 | `/integrations/telegram` · Telegram | Existing bot/notification setup and Telegram source editor, credentials/help and results; distinguish ingestion from notifications | #322, source behavior #321 | Needs dedicated full design |
| R20 | `/system` · System status | Service/playback/checker controls, scheduled queue/history, storage/scan state, logs/diagnostics, partial failure and effective configuration | #322 | Supplier summary dashboard only; full operational design needed |
| R21 | `/warp` · WARP | Status/connect/disconnect, opt-in startup behavior, exclusions/advanced details and failures | #322 | Needs dedicated full design |
| R22 | `/settings` · Settings | All five current deep-linked sections and every field; canonical relocation of recordings/guide/notifications; interface preferences | #318 with #319/#320/#322 field owners | Board 03 and phone example cover one section only |
| R23 | `/setup` · First run / later setup | Add channels, optional guide, review/finish/later, shared source flow, advanced connection settings and failed setup retrieval | #318 with #321/#320 | Needs dedicated full design |
| R24 | `/changelog` · Changelog | Version/history, release language cue, loading/error, update notice handoff and external link behavior | #322 | Needs dedicated full design |
| R25 | `*` · Not found | Clear unavailable destination, return/navigation recovery and preserved useful context | #318 | Needs dedicated full design |

## Tabs, settings and embedded surfaces

These are separate design obligations even when their parent page uses shared layout. Hiding them under “Advanced” does not remove them from scope.

| ID | Surface / source entry point | Required variants and detail | Owner |
| --- | --- | --- | --- |
| S01 | Settings `?tab=playback` | Optional engine URL/status, direct/Acexy routing, links to player/network configuration; unconfigured and managed states | #318 |
| S02 | Settings `?tab=automation` → Background updates | Source/guide/check intervals, optional anchors/timezone, next/last run, Waiting/Running, checker external/bundled/disabled; contextual guide/recording/notification ownership | #318 |
| S03 | Settings `?tab=links` | Shared format list/add/edit/default/delete, PID/AppID, compatibility help and mutation errors | #320 |
| S04 | Settings `?tab=access` | Initial activation, create/edit/disable accounts and permissions, password, viewing policy, IPTV scope, one-time credentials/revoke, sessions/revoke, API-token mode | #318 |
| S05 | Settings `?tab=network` | Schema-driven network/proxy/trust controls, effective/source/read-only values, validation/revision conflict/restart effects | #318 |
| S06 | Shared recording settings | Enabled/consequence disclosure, simultaneous limit, minimum free space, per-recording size, retention toggle/days and persistent-location help | #319 |
| S07 | Shared guide-matching settings | Opt-in exact matching, scope/result/help and safe contextual entry from background updates | #320 |
| S08 | Shared notifications and interface preferences | Webhook/channel configuration with test/result states; language/theme/system-default preference and storage failure | #322; interface #317/#318 |
| S09 | Sources `?tab=sources` | Add/edit URL/provider/type/name/enabled/bare-ID/recipe; saved vs imported vs signal; manual/bulk queue and failures | #321 |
| S10 | Sources `?tab=w3u` | URL/file preview, folders/breadcrumbs/search/types, reviewed import/refresh, entry/detail/history/local favourites/artwork choice, folder assignment and event import | #321; assignment #320; events #319 |
| S11 | Sources `?tab=searches` and `?tab=exclusions` | Saved-search CRUD/run; exclusion CRUD/preview/enable, literal matching help and future-import consequences | #321 |
| S12 | Guide `?tab=sources` / `?tab=channels` | Source CRUD/update, inventory/source filters, mapped status and channel detail | #320 |
| S13 | Guide `?tab=matching` / `?tab=rules` / `?tab=export` | Read-only preview/row selection, ambiguity/staleness, rule editor, analysis/coverage, XMLTV options/copy/download | #320 |
| S14 | `RuntimeSetup` advanced connection dialog | Playback, network access, optional services, review; schema-driven controls, managed/disabled explanations and revision conflicts | #318 |
| S15 | Access gate outside normal routes | Status loading/error/retry, login, account setup, password change, transport/permission denial, signed-out/session-expired | #318 |
| S16 | `/startup` and startup gate/banner | Connecting/preparing, deferred import/progress, lost connection, token entry, diagnostics, retry/salvage/fresh confirmations and recovery results | #318; diagnostic patterns #322 |
| S17 | Standalone extraction helper | Same recipe UI/EN/ES/visual states, independent shell, no installation connection, copy/export handoff and large-input limits | #321 |
| S18 | Global shell | Desktop/phone navigation, titles/breadcrumbs where needed, signed-in identity/sign-out, locale/theme, setup/API-token/update/what's-new notices, route loading/error | #318; content #317/#322 |

The per-field ledger is a required #316 deliverable, with feature-owner review. For **each** control record: stable field ID and source component/API key; current and proposed canonical location; label/help in EN/ES; purpose; default/effective value and source; units/range; visibility/permission/read-only conditions; save/cancel/immediate behavior; dependencies; effect/restart timing; loading/validation/server-conflict states; and contextual links. Include schema-generated runtime options, not only literals found in JSX. Never duplicate the recording, guide-matching, stream-format or address editors.

## Dialogs and transient states

Map every instance to an approved pattern and its exact action/copy/state specification. Shared components reduce repeated work; they do not excuse unspecified consequences.

| Family / source components | Required design coverage | Owner |
| --- | --- | --- |
| `ChannelPlayerDialog`, `StreamPlayerDialog`, `ChannelPickerDialog`, `PlayOnMenu`, `CastControls` | Open/loading/start/wait/playing/stall/error/stop, audio/subtitles, source choice/fallback, cast/remote handoff, focus return and ownership-preserving dismissal | #319/#322 |
| `RecordingDialog`, `GuideRecordingSelector`, recording playback/detail and confirmations | Now/scheduled/edit, timezone/DST, invalid/conflicting times, pending/retry, stop vs cancel vs delete, protection/conversion/parts | #319 |
| `TVChannelFormDialog`, `TVChannelDeleteDialog`, `QuickEditDialog`, `AssignTVChannelDialog`, `BatchAssignDialog`, `BatchAcestreamAssignment`, `TVAutoMatchDialog`, `TVChannelReorder` | Add/edit/select/preview/commit/cancel, stale/ambiguous assignments, complete reorder, deletion consequences and long inventories | #320 |
| `ChannelActivityLogDialog`, stream statistics and status chips | Unknown/zero/online/offline/not-found/error distinctions, observation time, bounded activity and empty history | #320/#322 |
| `EPGSourceDialog`, `RulesTab`, `EPGMatchAnalysisPanel`, XML output | Source add/edit, rule forms/confirmation, reviewed matching, changed-preview rejection and export feedback | #320 |
| Source inline editor, `DeleteSourceDialog`, `OrphanedSourcesDialog`, `SavedSearchDialog`, exclusion dialog, `FolderMatchDialog` | Field help/errors, save/import outcomes, delete/retain choices, preview/select/apply and partial results | #321; folder assignment #320 |
| Event detail/provider/source/import/broadcast-mapping components | Source/provider edits, reviewed import/mapping, conflicts, missing guide/playable channel, timezone and following scope | #319 |
| `FindPlayersDialog`, `RemotePlayerDialog`, `MediaServerDialog`, casting/Telegram editors | Discovery/manual entry, field validation, permission/transport errors, save/delete/connect/result states | #322 |
| `PlaylistDialog`, `StreamLinkFormatsSection` add/edit dialogs | Format/options, token/address context, copy/download, default selection, invalid pattern and deletion consequence | #320 |
| Account/password/credential/session forms | Permission variations, one-time secret display/copy/dismiss, invalid/expired/revoked states and safe recovery | #318 |
| `ConfirmDialog`, row-action menus, snackbars/alerts/tooltips, unsaved form guard | Context-specific EN/ES action and consequences, pending/disabled, dismiss/retry/undo only where real, keyboard/focus/announcement behavior | #316 pattern; each feature owns instances |

## Compatibility is part of the design

Preserve existing aliases and query context: `/dashboard` → `/`; `/integrations` → `/integrations/public-address`; `/health` → `/system`; `/stats` → `/`; `/channels` and `/channels/:id` → `/tv-channels`; `/search-new` → `/search`; `/epg/mappings` → `/epg?tab=rules`; `/catalogues` → `/scraper?tab=w3u`. Legacy-route recovery and useful back links need a designed result. New terminology must not silently break bookmarked URLs.

## Required design handoff for every row

1. **Purpose and actions:** user goal, plain-language page/section name, primary action, secondary/advanced actions, entry/exit/deep links and permission variants. No capability disappears as a side effect of simplifying presentation.
2. **Composed designs:** finished desktop and phone composition for every route, tab, standalone entry and materially distinct modal/step. Provide named component/state variants for shared layouts, with explicit references from each row. A template without the page's real content/actions is incomplete.
3. **Responsive behavior:** 320/390/768/1440 px rules, overflow/long text, list-to-card decisions, pagination, sticky regions and keyboard/touch paths. Specify behavior between mockup widths.
4. **State specification:** populated, first-use empty, filtered-empty, loading, partial/unknown/stale, error/retry, success, disabled/read-only, permission denied, pending, dirty/unsaved, validation, conflict and consequential confirmation wherever applicable. Record justified N/A instead of leaving blanks.
5. **EN/ES and themes:** actual UI copy and accessibility names, Spanish expansion/plurals/date/unit examples, both light/dark token mappings, preserved original provider/user data. A language selector alone does not count.
6. **Interaction and accessibility:** focus order/return/traps, target size, keyboard commands, announcements, contrast in actual components, reduced motion and timing. Explain what saves immediately, what needs Save, and when a change takes effect.
7. **Implementation handoff:** component/token names, field ledger, current service/API mapping, important media/data/permission invariants, asset/font provenance, acceptance scenarios and links to reviewable design artifacts.
8. **Tracking:** each row records Design pending / In review / Accepted, artifact links, unresolved decisions, implementation PR and verification evidence. Acceptance requires an actual review decision, not this document's existence.

## Administration direction

Use the same typography, semantic tokens, controls and navigation across viewing and administration. Viewing pages can feature channel/programme imagery; administration prioritizes readable data, concise help, clear sections and one primary action. Tables, bulk operations, long forms and diagnostics deserve finished designs of their own. Advanced detail remains available with explanations and safe disclosure.

Start the full design package with complementary families—watching, recordings, channel/guide management, source setup, settings/access, connections and system/recovery—then complete every row using those foundations. Representative examples establish the visual language; **they are not a substitute for the complete package**.

## Acceptance gate

- [ ] Every current route, tab, embedded helper, dialog, field and gate has an owner and a linked design/state specification.
- [ ] All administration surfaces use the approved foundations; none is left as an unreviewed legacy iframe/CSS overlay or “future styling” task.
- [ ] Every row meets the handoff requirements above, including both themes and EN/ES. Shared-pattern reuse is explicit; unique content and consequences remain specified.
- [ ] Actual route/component/field inventory is reconciled again before #316 design completion and #324 product completion.
- [ ] Missing designs remain pending work. No percentage-complete claim is inferred from supplier screens or the 13-image gallery.
- [ ] Future implementation preserves existing behavior and passes the repository's required validation; the design/docs-only waiver does not waive application checks.

Related: [visual gallery](README.md), [designer coverage assessment](designer-frontend-assessment.md), [epic #314](https://github.com/Pipepito/acestream-scraper/issues/314).
