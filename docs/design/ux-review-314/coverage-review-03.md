# Whole-app coverage delta — review 03

> Review 04 update (7 November 2026): [expanded composed coverage](coverage-review-04.md), [workflow fields/interactions](workflow-specification.md), [current verification](verification-review-04.md) and [task refinements](task-refinements-04.md) supersede historical composition gaps. Prior live defects remain open. No user approval or application implementation is implied.

Starting baseline: application 7ccf16d; design originally ebadaaf. Final develop cf952af was fetched and source-inspected. **24 explicit app routes + catch-all; nine redirects; 20 navigation destinations** remain unchanged. Startup is an outer gate, not an App.tsx route. Detail routes and embedded entries remain separate. The mandatory [current-source delta](current-source-delta.md) adds online-only/refresh states, similar-name matching, Add and Link, offline cleanup and tuner hiding to the rows below; their live post-merge validation remains pending.

All rows are **design pending** or **in review**. None is accepted; no implementation PR is attached. “Live” means read-only normal-state inspection, not an exercised mutation or every permission/error state. S = source inspected; L = live inspected; M = new composed family. Each row inherits the full handoff/state/field contract in [whole-app-coverage.md](whole-app-coverage.md).

| Existing ID / surface | Evidence | Design artifact / remaining unique compositions | Owner |
| --- | --- | --- | --- |
| R01 dashboard | S/L | Existing supplier reference only; still needs complete first-use/partial data layout. | #319 |
| R02 Live TV | S/L | Old boards 02/05/12; current/next, failed/stalled player, audio/cast/record variants pending. | #319 |
| R03 recordings | S/L/M | [Library](admin-prototype.html?view=recordings), Upcoming/History + delete. Schedule/DST, active/recovering, multipart playback and full settings composition pending. | #319 |
| R04 events | S/L | Agenda/provider/source/detail/overlay/mapping inspected in source; distinct compositions pending. Current nav=Manage; proposed=Watch. | #319 |
| R05 streams | S/L | Inventory baseline; detailed stats, bulk, assignments, unknown/error samples pending. | #320 |
| R06 TV channels | S/L | Old board 04; phone filters discrepancy noted. Full reorder/stale/conflict/bulk design pending. | #320 |
| R07 TV detail | S/L | Read-only detail inspected; stream preferences/guide/activity composition pending. | #320/#319 |
| R08 sources; S09–S11 | S/L/M | [Add source](admin-prototype.html?view=sources), save/import/failure/delete. W3U, searches/exclusions, orphan cleanup, provider-specific forms pending. | #321 |
| R09 builder | S/L/M | [Shared helper anatomy](admin-prototype.html?view=helper); installed fetch/source-save variants and selector/JSON/regex editors pending. | #321 |
| R10 search | S/L | Distinct from loaded-catalogue filter; provider/search-result/resolve/add variants pending. | #321 |
| R11 guide; S12–S13 | S/L/M | [Review/apply](admin-prototype.html?view=guide), explicit selection/stale. Sources/rules/export/coverage and ambiguous-choice details pending. | #320 |
| R12 guide detail | S/L | Source-qualified schedule inspected; unique composition pending. | #320 |
| R13 playlist; S03 | S/L | Format/filter/address/token behavior source-inspected; complete editor/export composition pending. | #320 |
| R14 address | S/L/M context | [Connections context](admin-prototype.html?view=connections) does not complete effective/saved/runtime editor. | #322 |
| R15 browser player | S/L/M entry | Outcome entry only; capability/session editor variants pending. | #322 |
| R16 casting | S/L/M | Device example, empty/permission. Discovery/manual/trust/owned media/compatible copy variants pending. | #322 |
| R17 remote players | S/L/M entry | Entry only; app handoff, explicit remote opt-in and failed connection pending. | #322 |
| R18 media servers | S/L/M entry | Entry only; tuner budgets, compatible audio, hides/filter behavior and per-server editor pending. | #322 |
| R19 Telegram; S08 | S/L/M entry | Bot vs ingestion distinction only; authorization/source editor/notification test states pending. | #322/#321 |
| R20 system | S/L/M | [System](admin-prototype.html?view=system): checker failure, queue, partial storage, diagnostics. Full history/service-control/storage detail variants pending. | #322 |
| R21 WARP | S/L/M context | Off-by-choice example only; exclusions/conflicts/startup applied vs saved pending. | #322 |
| R22 settings; S01–S08 | S/L/M | Old Automation concept plus [Access](admin-prototype.html?view=access). Every runtime/generated field inventoried; full section compositions pending. | #318 with feature owners |
| R23 setup; S14 | S/L/M | [Setup](admin-prototype.html?view=setup) illustrates shared source/optional guide/Finish semantics. Advanced runtime steps and all failure paths pending. | #318 |
| R24 changelog | S/L | Historical body language cue and release chrome specification; composition pending. | #322 |
| R25 catch-all | S/L | Return/context preservation specification; composed 404 pending. | #318 |
| S15 access gate | S; normal access setup L | [Access](admin-prototype.html?view=access) + permission/activation empty example. Live enabled-role, session expiry, password, one-time secret and blocked-transport variants not exercised. | #318 |
| S16 startup gate | S/L ready; M failure | [Recovery](admin-prototype.html?view=recovery), backup/fresh/readable confirmations. No live fault injection/recovery. API-token/loading/deferred-progress variants still pending. | #318/#322 |
| S17 standalone helper | S; isolated new M | [Helper](admin-prototype.html?view=helper), bounded-input explanation. Current standalone entry also inspected in isolation; full field/preview state coverage pending. | #321 |
| S18 shell | S/L/M | Shared prototype shell and two directions. Real drawer/focus traps, every route, preference storage failure, notices and unsaved navigation acceptance pending. | #318/#317 |

## Dialog audit and handoff

The original dialog-family inventory is retained. Source inspection covered player/recording/guide/source/channel/integration/access/confirmation families and entry conditions. **Live interaction did not exercise every dialog**. Record opener, guide sliders, detail links, navigation and read-only tabs were verified. Do not carry forward the earlier audit's broad form coverage as fresh end-to-end evidence.

New modal examples: recording deletion/cancellation, source removal, permission change, readable/fresh recovery, dirty navigation. Named unique variants still needed: track/source picker, cast controls, recording schedule/DST, channel add/edit/reorder/bulk assignment, guide-source/rule editor, source types/orphan cleanup/exclusions/catalogue imports, event/provider/overlay mapping, media-server/remote-player/Telegram authorization, playlist-format editor and credential/session revocation. Owner assignments remain those in the original matrix.

## Field and state coverage

[Field ledger](field-ledger.md) supplies the canonical map and concrete bilingual critical-field decisions. [Runtime field inventory](runtime-field-inventory.md) lists every schema-generated option with current default/range and proposed owner; no runtime option is excluded as “advanced”.

All ordinary routes have a source/live inventory row. Nine families have new composed examples. No route has complete accepted EN/ES/light/dark/all-state handoff. Missing field-level copy, context-specific empty/error/permission states and unique compositions remain visible obligations, not a completion percentage.

Scope corrections: Events is currently Manage. Catalogues is a compatibility redirect into Sources/W3U, not a separate current sidebar destination. Accounts can change visible capabilities; do not derive account-enabled coverage from the owner's current access mode.
