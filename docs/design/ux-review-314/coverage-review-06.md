# Whole-app coverage and state catalogue — review 06

146 composed contexts, 473 field occurrences, 47 runtime options, 141 named workflow-specific state entries. Existing 144 contexts were recomposed and retained as stable review links; two small source entry/index contexts connect the simplified setup path. This count is not a navigation or page-count target.

Each context uses the same fields and interaction engine in lime, coral/navy and immersive. EN/ES, light/dark, phone/tablet/desktop and consequential states are rendered by current checks. Exact outcomes and limits are recorded in [verification](verification-review-06.md), not inferred from historical passes.

| Destination | Contexts | Scope |
|---|---|---|
| recordings | 12 | Programme times, DST, active/recovering/finalizing/failed, parts/gaps/copies, storage/protection/retention, stop/cancel/delete/disable |
| settings | 17 | Accounts/activation/all permissions/policy/transport/password/sessions/credentials, background schedules/cleanup, appearance and unsaved navigation |
| channels | 58 | Channel catalogue/detail/stats/bulk/reorder, guide sources/qualification/rules/coverage/export, sources/W3U/search/exclusions/orphans and extraction modes |
| connections | 18 | Browser playback, Cast/remote players, media servers/tuner, playlists/shared formats/address and notifications |
| dashboard | 8 | First use, partial availability, online/Show all, player states/tracks/selection, refresh continuity and not-found |
| events | 10 | Agenda/providers/source review/detail/correction/mapping, broadcast links, guide overlays and explicit artwork |
| system | 23 | Services/jobs/history/storage/diagnostics/WARP, runtime controls, startup/migration/connection/recovery and notices/changelog |

## State composition contract

Shared loading/error/permission/dirty/pending/success/conflict/empty/filtered/partial policies are applied to the actual workflow controls, fields and transaction boundaries. A generic banner is not evidence of backend behavior. Workflow-specific states preserve or replace content as specified: first-use has no populated feature, public HTTP activation has no password entry, unknown statistics do not become zero, date-only events do not invent midnight, finalization/recovery locks capture edits, and oversized extraction skips parsing. Artwork failures reserve space and keep names/actions available.

Review links below open the actual contextual composition. Use the state selector for every listed variant. The full field ledger and source traces remain linked rather than copied into another editor.

| Context | Simplified section | Named consequential states | Specification / owner |
|---|---|---|---|
| [Schedule a programme](workflow-prototype.html?screen=recording-schedule&review=1) | recordings → recordings | capacity, stale | [Fields / actions](workflow-specification.md#recording-schedule); #319 |
| [Choose the exact time](workflow-prototype.html?screen=recording-dst&review=1) | recordings → recordings | gap | [Fields / actions](workflow-specification.md#recording-dst); #319 |
| [Record now](workflow-prototype.html?screen=recording-now&review=1) | recordings → recordings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recording-now); #319 |
| [Recording in progress](workflow-prototype.html?screen=recording-active&review=1) | recordings → recordings | starting, finalizing, interrupted | [Fields / actions](workflow-specification.md#recording-active); #319 |
| [Parts and playback](workflow-prototype.html?screen=recording-parts&review=1) | recordings → recordings | unsupported, preparing, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [Fields / actions](workflow-specification.md#recording-parts); #319 |
| [Prepare a compatible copy](workflow-prototype.html?screen=recording-copy&review=1) | recordings → recordings | failed, ready-copy | [Fields / actions](workflow-specification.md#recording-copy); #319 |
| [Recording settings](workflow-prototype.html?screen=recording-settings&review=1) | recordings → recordings | unavailable | [Fields / actions](workflow-specification.md#recording-settings); #319 |
| [Storage for recordings](workflow-prototype.html?screen=recording-storage&review=1) | recordings → recordings | low | [Fields / actions](workflow-specification.md#recording-storage); #319 |
| [Cancel this schedule](workflow-prototype.html?screen=recording-cancel&review=1) | recordings → recordings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recording-cancel); #319 |
| [Delete saved files](workflow-prototype.html?screen=recording-delete&review=1) | recordings → recordings | held | [Fields / actions](workflow-specification.md#recording-delete); #319 |
| [Disable all recording](workflow-prototype.html?screen=recording-disable&review=1) | recordings → recordings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recording-disable); #319 |
| [Choose who can use this installation](workflow-prototype.html?screen=access-activate&review=1) | settings → access-account | blocked | [Fields / actions](workflow-specification.md#access-activate); #318 |
| [Sign in](workflow-prototype.html?screen=access-login&review=1) | settings → access-account | expired, denied | [Fields / actions](workflow-specification.md#access-login); #318 |
| [Account permissions](workflow-prototype.html?screen=access-account&review=1) | settings → access-account | last-admin | [Fields / actions](workflow-specification.md#access-account); #318 |
| [Create an account](workflow-prototype.html?screen=access-create&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-create); #318 |
| [Viewing without signing in](workflow-prototype.html?screen=access-policy&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-policy); #318 |
| [Change your password](workflow-prototype.html?screen=access-password&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-password); #318 |
| [Login sessions](workflow-prototype.html?screen=access-sessions&review=1) | settings → access-account | empty | [Fields / actions](workflow-specification.md#access-sessions); #318 |
| [Playback and API credentials](workflow-prototype.html?screen=access-credentials&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-credentials); #318 |
| [Save your new credential](workflow-prototype.html?screen=access-secret&review=1) | settings → access-account | copy-failed | [Fields / actions](workflow-specification.md#access-secret); #318 |
| [Remove account protection](workflow-prototype.html?screen=access-disable&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-disable); #318 |
| [Use a supported connection](workflow-prototype.html?screen=access-transport&review=1) | settings → access-account | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#access-transport); #318 |
| [TV channels](workflow-prototype.html?screen=channels&review=1) | channels → channels | filtered | [Fields / actions](workflow-specification.md#channels); #320 |
| [Edit TV channel](workflow-prototype.html?screen=channel-edit&review=1) | channels → channels | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#channel-edit); #320 |
| [Northlight](workflow-prototype.html?screen=channel-detail&review=1) | channels → channels | art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [Fields / actions](workflow-specification.md#channel-detail); #320 |
| [Reorder all TV channels](workflow-prototype.html?screen=channel-reorder&review=1) | channels → channels | conflict | [Fields / actions](workflow-specification.md#channel-reorder); #320 |
| [Preferred streams for Northlight](workflow-prototype.html?screen=channel-preferences&review=1) | channels → channels | conflict | [Fields / actions](workflow-specification.md#channel-preferences); #320 |
| [Streams](workflow-prototype.html?screen=streams&review=1) | channels → streams | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#streams); #320 |
| [Northlight HD · observations](workflow-prototype.html?screen=stream-stats&review=1) | channels → streams | unknown, not-found | [Fields / actions](workflow-specification.md#stream-stats); #320 |
| [Add and link a stream](workflow-prototype.html?screen=stream-edit&review=1) | channels → streams | conflict, excluded | [Fields / actions](workflow-specification.md#stream-edit); #320 |
| [Bulk stream actions](workflow-prototype.html?screen=stream-bulk&review=1) | channels → streams | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#stream-bulk); #320 |
| [Assign existing streams](workflow-prototype.html?screen=channel-assign&review=1) | channels → channels | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#channel-assign); #320 |
| [Match streams to TV channels](workflow-prototype.html?screen=stream-match&review=1) | channels → streams | ambiguous | [Fields / actions](workflow-specification.md#stream-match); #320 |
| [Delete Northlight?](workflow-prototype.html?screen=channel-delete&review=1) | channels → channels | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#channel-delete); #320 |
| [Programme guides](workflow-prototype.html?screen=guide-sources&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-sources); #320 |
| [Edit guide source](workflow-prototype.html?screen=guide-source&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-source); #320 |
| [Northlight · Sample guide](workflow-prototype.html?screen=guide-detail&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-detail); #320 |
| [Choose the correct guide source](workflow-prototype.html?screen=guide-choice&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-choice); #320 |
| [Review guide matches](workflow-prototype.html?screen=guide-match&review=1) | channels → guide-sources | conflict | [Fields / actions](workflow-specification.md#guide-match); #320 |
| [Guide matching rule](workflow-prototype.html?screen=guide-rule&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-rule); #320 |
| [Automatic exact matching](workflow-prototype.html?screen=guide-auto&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-auto); #320 |
| [Export programme guide](workflow-prototype.html?screen=guide-export&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-export); #320 |
| [Guide coverage](workflow-prototype.html?screen=guide-coverage&review=1) | channels → guide-sources | partial | [Fields / actions](workflow-specification.md#guide-coverage); #320 |
| [Your playlist](workflow-prototype.html?screen=playlist&review=1) | connections → playlist | credential, managed, filtered | [Fields / actions](workflow-specification.md#playlist); #320 |
| [Stream link formats](workflow-prototype.html?screen=formats&review=1) | connections → playlist | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#formats); #320 |
| [Edit Demo relay](workflow-prototype.html?screen=format-edit&review=1) | connections → playlist | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#format-edit); #320 |
| [Web or playlist source](workflow-prototype.html?screen=source-web&review=1) | channels → sources | import-failed | [Fields / actions](workflow-specification.md#source-web); #321 |
| [Automatic source detection](workflow-prototype.html?screen=source-auto&review=1) | channels → sources | import-failed | [Fields / actions](workflow-specification.md#source-auto); #321 |
| [ZeroNet source](workflow-prototype.html?screen=source-zeronet&review=1) | channels → sources | import-failed | [Fields / actions](workflow-specification.md#source-zeronet); #321 |
| [IPFS source](workflow-prototype.html?screen=source-ipfs&review=1) | channels → sources | import-failed | [Fields / actions](workflow-specification.md#source-ipfs); #321 |
| [Built-in broadcaster](workflow-prototype.html?screen=source-provider&review=1) | channels → sources | import-failed | [Fields / actions](workflow-specification.md#source-provider); #321 |
| [Import result](workflow-prototype.html?screen=source-results&review=1) | channels → sources | waiting, partial | [Fields / actions](workflow-specification.md#source-results); #321 |
| [Remove Family channels?](workflow-prototype.html?screen=source-remove&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#source-remove); #321 |
| [Streams without a saved source](workflow-prototype.html?screen=sources-orphans&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#sources-orphans); #321 |
| [Review W3U catalogue](workflow-prototype.html?screen=w3u&review=1) | channels → sources | expired | [Fields / actions](workflow-specification.md#w3u); #321 |
| [Save reviewed catalogue](workflow-prototype.html?screen=w3u-save&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#w3u-save); #321 |
| [Catalogue entry details](workflow-prototype.html?screen=w3u-detail&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#w3u-detail); #321 |
| [Assign a catalogue folder](workflow-prototype.html?screen=w3u-folder&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#w3u-folder); #320 |
| [Saved search](workflow-prototype.html?screen=saved-search&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#saved-search); #321 |
| [Preview a saved search](workflow-prototype.html?screen=saved-search-preview&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#saved-search-preview); #321 |
| [Import exclusion rule](workflow-prototype.html?screen=exclusion&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#exclusion); #321 |
| [Find new streams](workflow-prototype.html?screen=search&review=1) | channels → sources | engine | [Fields / actions](workflow-specification.md#search); #321 |
| [Add and link Northlight HD](workflow-prototype.html?screen=search-add-link&review=1) | channels → sources | unresolved, excluded, catalogue-unavailable, conflict | [Fields / actions](workflow-specification.md#search-add-link); #321 |
| [Test a source recipe](workflow-prototype.html?screen=helper-installed&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#helper-installed); #321 |
| [Build a recipe offline](workflow-prototype.html?screen=helper-standalone&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#helper-standalone); #321 |
| [Pick fields in HTML](workflow-prototype.html?screen=helper-html&review=1) | channels → sources | timeout, invalid | [Fields / actions](workflow-specification.md#helper-html); #321 |
| [Read fields from JSON](workflow-prototype.html?screen=helper-json&review=1) | channels → sources | timeout, invalid | [Fields / actions](workflow-specification.md#helper-json); #321 |
| [Read paired text records](workflow-prototype.html?screen=helper-regex&review=1) | channels → sources | timeout, invalid | [Fields / actions](workflow-specification.md#helper-regex); #321 |
| [Select fields manually](workflow-prototype.html?screen=helper-manual&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#helper-manual); #321 |
| [This sample is too large to draw safely](workflow-prototype.html?screen=helper-large&review=1) | channels → sources | too-large | [Fields / actions](workflow-specification.md#helper-large); #321 |
| [Review extraction results](workflow-prototype.html?screen=helper-results&review=1) | channels → sources | stale | [Fields / actions](workflow-specification.md#helper-results); #321 |
| [Watch](workflow-prototype.html?screen=dashboard&review=1) | dashboard → dashboard | first-use, partial, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [Fields / actions](workflow-specification.md#dashboard); #319 |
| [Watch](workflow-prototype.html?screen=live&review=1) | dashboard → dashboard | filtered, refreshing, failed, stalled, empty, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [Fields / actions](workflow-specification.md#live); #319 |
| [Playback options](workflow-prototype.html?screen=player-tracks&review=1) | dashboard → dashboard | capacity | [Fields / actions](workflow-specification.md#player-tracks); #319 |
| [Your viewing access](workflow-prototype.html?screen=viewer&review=1) | dashboard → dashboard | denied | [Fields / actions](workflow-specification.md#viewer); #318 |
| [Event agenda](workflow-prototype.html?screen=events&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#events); #319 |
| [Northlight Cup](workflow-prototype.html?screen=event-detail&review=1) | events → events | unknown, art-absent, art-slow, art-blocked, art-rejected, art-oversized, art-decode-failed, art-changed | [Fields / actions](workflow-specification.md#event-detail); #319 |
| [Add provider events](workflow-prototype.html?screen=event-provider&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-provider); #319 |
| [Add events](workflow-prototype.html?screen=event-import&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-import); #319 |
| [Review new events](workflow-prototype.html?screen=event-review&review=1) | events → events | conflict | [Fields / actions](workflow-specification.md#event-review); #319 |
| [Correct Northlight Cup](workflow-prototype.html?screen=event-correct&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-correct); #319 |
| [Link the broadcaster Atelier](workflow-prototype.html?screen=event-mapping&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-mapping); #319 |
| [Review XMLTV overlay](workflow-prototype.html?screen=event-overlay&review=1) | events → events | conflict | [Fields / actions](workflow-specification.md#event-overlay); #319 |
| [Event sources and retention](workflow-prototype.html?screen=event-sources&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-sources); #319 |
| [Where would you like to watch?](workflow-prototype.html?screen=connections&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#connections); #322 |
| [Browser player](workflow-prototype.html?screen=browser-player&review=1) | connections → connections | unavailable, partial | [Fields / actions](workflow-specification.md#browser-player); #322 |
| [Address for players](workflow-prototype.html?screen=public-address&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#public-address); #322 |
| [TV casting](workflow-prototype.html?screen=casting&review=1) | connections → connections | empty, denied | [Fields / actions](workflow-specification.md#casting); #322 |
| [Casting settings](workflow-prototype.html?screen=casting-settings&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#casting-settings); #322 |
| [Public HTTPS at home](workflow-prototype.html?screen=casting-trust&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#casting-trust); #322 |
| [Living room DEMO](workflow-prototype.html?screen=casting-control&review=1) | connections → connections | ownership-lost, recording-priority | [Fields / actions](workflow-specification.md#casting-control); #322 |
| [Set up VLC or Kodi](workflow-prototype.html?screen=remote-player&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#remote-player); #322 |
| [Pair VLC Android](workflow-prototype.html?screen=remote-android&review=1) | connections → connections | expired, changed-host | [Fields / actions](workflow-specification.md#remote-android); #322 |
| [Find remote players](workflow-prototype.html?screen=remote-discovery&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#remote-discovery); #322 |
| [Send to a player](workflow-prototype.html?screen=remote-control&review=1) | connections → connections | denied, handoff | [Fields / actions](workflow-specification.md#remote-control); #322 |
| [Connect a media server](workflow-prototype.html?screen=media-server&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#media-server); #322 |
| [Tuner settings](workflow-prototype.html?screen=tuner&review=1) | connections → connections | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#tuner); #322 |
| [Authorize Telegram sources](workflow-prototype.html?screen=telegram-auth&review=1) | channels → sources | unavailable, flood | [Fields / actions](workflow-specification.md#telegram-auth); #322 |
| [Complete Telegram sign-in](workflow-prototype.html?screen=telegram-code&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#telegram-code); #322 |
| [Telegram source](workflow-prototype.html?screen=telegram-source&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#telegram-source); #322 |
| [Notifications](workflow-prototype.html?screen=notifications&review=1) | connections → connections | masked-invalid | [Fields / actions](workflow-specification.md#notifications); #322 |
| [WARP](workflow-prototype.html?screen=warp&review=1) | system → warp | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#warp); #322 |
| [WARP excluded hosts](workflow-prototype.html?screen=warp-exclusions&review=1) | system → warp | partial, conflict | [Fields / actions](workflow-specification.md#warp-exclusions); #322 |
| [WARP at startup](workflow-prototype.html?screen=warp-startup&review=1) | system → warp | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#warp-startup); #322 |
| [Settings](workflow-prototype.html?screen=settings&review=1) | settings → settings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#settings); #318 |
| [Playback settings](workflow-prototype.html?screen=playback-settings&review=1) | connections → browser-player | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#playback-settings); #318 |
| [Background updates](workflow-prototype.html?screen=automation&review=1) | settings → automation | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#automation); #318 |
| [Schedule start times](workflow-prototype.html?screen=schedule-anchors&review=1) | settings → automation | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#schedule-anchors); #318 |
| [Offline stream cleanup](workflow-prototype.html?screen=offline-cleanup&review=1) | settings → automation | deferred, refresh-failed | [Fields / actions](workflow-specification.md#offline-cleanup); #318 |
| [Network settings](workflow-prototype.html?screen=network&review=1) | system → runtime-playback | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#network); #318 |
| [System status](workflow-prototype.html?screen=system&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#system); #322 |
| [Service controls](workflow-prototype.html?screen=services&review=1) | system → system | external | [Fields / actions](workflow-specification.md#services); #322 |
| [Scheduled job history](workflow-prototype.html?screen=jobs&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#jobs); #322 |
| [Job run details](workflow-prototype.html?screen=job-detail&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#job-detail); #322 |
| [Storage details](workflow-prototype.html?screen=storage&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#storage); #322 |
| [Logs and diagnostics](workflow-prototype.html?screen=diagnostics&review=1) | system → system | denied, partial | [Fields / actions](workflow-specification.md#diagnostics); #322 |
| [Start with channels](workflow-prototype.html?screen=setup&review=1) | channels → sources | partial | [Fields / actions](workflow-specification.md#setup); #318 |
| [Starting AceStream Scraper](workflow-prototype.html?screen=startup&review=1) | system → system | deferred, connection, token | [Fields / actions](workflow-specification.md#startup); #318 |
| [Startup needs attention](workflow-prototype.html?screen=recovery&review=1) | system → system | busy, interrupted | [Fields / actions](workflow-specification.md#recovery); #318 |
| [Recover readable catalogue](workflow-prototype.html?screen=recovery-readable&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recovery-readable); #318 |
| [Start a fresh catalogue](workflow-prototype.html?screen=recovery-fresh&review=1) | system → system | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recovery-fresh); #318 |
| [Recovery result](workflow-prototype.html?screen=recovery-result&review=1) | system → system | failed | [Fields / actions](workflow-specification.md#recovery-result); #318 |
| [Language and appearance](workflow-prototype.html?screen=preferences&review=1) | settings → preferences | storage-failed | [Fields / actions](workflow-specification.md#preferences); #317 |
| [Notices and session feedback](workflow-prototype.html?screen=notices&review=1) | system → settings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#notices); #318 |
| [This page is not available](workflow-prototype.html?screen=not-found&review=1) | dashboard → settings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#not-found); #318 |
| [What changed](workflow-prototype.html?screen=changelog&review=1) | system → settings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#changelog); #322 |
| [Leave with unsaved changes?](workflow-prototype.html?screen=unsaved&review=1) | settings → settings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#unsaved); #318 |
| [Playback runtime](workflow-prototype.html?screen=runtime-playback&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-playback); #318 |
| [Network runtime](workflow-prototype.html?screen=runtime-network&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-network); #318 |
| [Installed services](workflow-prototype.html?screen=runtime-services&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-services); #318 |
| [Advanced source runtime](workflow-prototype.html?screen=runtime-advanced&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-advanced); #318 |
| [Engine and Acexy connections](workflow-prototype.html?screen=runtime-engine-ports&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-engine-ports); #318 |
| [ZeroNet and IPFS connections](workflow-prototype.html?screen=runtime-gateway-ports&review=1) | system → runtime-playback | conflict, managed | [Fields / actions](workflow-specification.md#runtime-gateway-ports); #318 |
| [Your recordings](workflow-prototype.html?screen=recordings&review=1) | recordings → recordings | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#recordings); #319 |
| [Stream activity](workflow-prototype.html?screen=channel-activity&review=1) | channels → streams | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#channel-activity); #320 |
| [Bulk metadata changes](workflow-prototype.html?screen=stream-bulk-fields&review=1) | channels → streams | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#stream-bulk-fields); #320 |
| [Browse guide channels](workflow-prototype.html?screen=guide-inventory&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#guide-inventory); #320 |
| [Choose what to play](workflow-prototype.html?screen=player-picker&review=1) | dashboard → dashboard | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#player-picker); #319 |
| [Playback sessions](workflow-prototype.html?screen=player-sessions&review=1) | dashboard → dashboard | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#player-sessions); #319 |
| [Events on your home page](workflow-prototype.html?screen=dashboard-events&review=1) | dashboard → dashboard | storage-failed | [Fields / actions](workflow-specification.md#dashboard-events); #319 |
| [Broadcaster links](workflow-prototype.html?screen=event-broadcasters&review=1) | events → events | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#event-broadcasters); #319 |
| [Add your first channel source](workflow-prototype.html?screen=setup-source&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#setup-source); #318 |
| [Optional programme guide](workflow-prototype.html?screen=setup-guide&review=1) | channels → guide-sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#setup-guide); #318 |
| [Number and favorite](workflow-prototype.html?screen=channel-inline&review=1) | channels → channels | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#channel-inline); #320 |
| [Channel sources](workflow-prototype.html?screen=sources&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#sources); #321 |
| [Add channels](workflow-prototype.html?screen=add-channels&review=1) | channels → sources | Shared state policy for this workflow | [Fields / actions](workflow-specification.md#add-channels); #321 |

## Remaining acceptance, not hidden missing pages

All listed capability families have a composed context. Detailed visual approval, nontechnical task observation, fluent Spanish/native screen-reader listening, actual browser zoom at 200/400%, physical phones and real application/media/transport behavior remain separate acceptance evidence under #316/#317/#319–#324. No participants or real receivers are simulated as a pass. The mock helper does not prove extraction success; local preference timers do not prove API success. See [protocols](acceptance-protocols.md) and [source findings](source-findings-06.md).
