# Interaction contracts · review 04

These are implementation-guiding proposals for the existing ten tasks. They do not authorize implementation, change API contracts or approve new typography, color or navigation. Current source is pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`; the design branch intentionally retains its earlier application base. Use the [field specification](workflow-specification.md), [source control map](source-control-map.md) and [traceability matrix](traceability-matrix.md) together.

## Status and fidelity

**Composed** means that a unique workflow has its own content, fields, named actions, consequences and relevant states in the new prototype. **Author-reviewed** means the rendered and automated checks actually recorded in [verification](verification-review-04.md). **Approved** requires the owner's explicit decision. **Implemented** requires application changes and integration evidence. The last two statuses are false for this delivery. No implementation issue is complete.

The prototype simulates interaction contracts with in-memory synthetic data. It contains no API client, real credential, discovery, playback, recorder, regex execution, recovery or background job. A request acknowledgement in it is an illustrative result, never proof of server behavior. Field editors, confirmations, dirty navigation, validation examples, selection expiry, ordering, dependencies and view controls operate locally. State selectors compose unavailable or unsafe-to-exercise states. Static player illustrations intentionally contain no audio/video element. Source schemas, capability responses and ownership checks remain authoritative for implementation.

## Plain language and progressive disclosure

Lead with the task and primary action. Say “Stop recording”, “Cancel schedule”, “Delete files” or “Disable recordings”, never a contextless “Stop”. Put the channel/programme/source name in its original language next to the action. Show consequence before confirmation and operation-specific outcome afterward. A queue acknowledgement is “Waiting”; it is not “Finished”. A missing observation is “Unknown”; it is not zero or offline. Use text plus icons for status; color is supplementary.

Core fields remain visible. Technical routing, patterns, optional metadata and runtime settings use named disclosures with active counts. A collapsed invalid field must expand before focus moves to it. Do not hide an error behind an accordion. A focused control cannot disappear while a request is pending. Copy can mention an internal name when an operator needs to configure that exact value; implementation details belong in handoff notes otherwise.

## Saving and navigation

Each named resource has its own pristine, dirty, invalid, pending, error, accepted and conflict state. Disabled Save must have a readable reason from the field help/error or pending status. A server error keeps the draft and saved baseline; it never silently clears input. Cancel restores that resource's saved values. Compare revision/review tokens on writes; a conflict fetches new data for explicit review and clears authorization selections. Never automatically replay a stale destructive command.

Independent requests remain independent: scraping/guide/check intervals; PID and AppID; WARP mode and licence; engine URL and playback routing; checker selection; exact-match preference; offline-cleanup policy and schedule anchors. There is no global atomic Save. The shared runtime API has one revision: saving a composed section must merge its patch with the current whole resource and preserve unrelated options, or reject a changed revision. It must not send a partial replacement that drops other sections.

Number editing retains its actual Enter/blur save, blank→null and Escape restore semantics. Favorites remain immediate. The dedicated number/favorite composition shows both. Applying explicit Save to settings that currently save immediately is a proposal requiring owner approval and regression coverage, not a statement about current behavior. Original save timing remains authoritative until approved.

Internal links and browser Back use Stay / Discard for dirty drafts; there is no “Save everything”. Safe Cancel receives initial focus. Language, theme and review-direction switches are not navigation: retain draft, selection, current route, expanded fields, focus and scroll. Reopening a one-time credential is not a permitted recovery mechanism. Closing/reloading the page uses the native dirty guard without claiming crash recovery.

## Dialogs, focus and phone layouts

The gallery gives intent dialogs their own canvases so their full content can be reviewed. This does not require new application routes. Implement short confirmations as labelled modal dialogs; use existing dialog hosts for editors and full-height versions on phones. Keep Cancel and the specific primary action visible after scrolling, without covering fields. Long editor dialogs need a title, scrollable body, field-level errors and a predictable close path.

The executable confirmation and phone drawer use native modal dialogs, explicit focus containment, Escape cancellation, safe initial focus and focus return. Every input has an associated label and help/error IDs. Selected rows use real checkbox/radio semantics. Reorder offers drag plus Up/Down buttons and Alt+Arrow on the handle; announce the new ordinal. Native arrow behavior on named export sliders remains available. Preserve normal tab order; no positive tabindex. Prefer a single polite live region; validation should not repeat the full form on every keystroke.

320 CSS-pixel reflow and 200% text enlargement are checked as described in verification. They do not substitute for a real browser zoom, screen reader or device. Reduced motion follows the operating-system preference; no animation is needed to understand a state.

## Recordings and media ownership

Schedule from exact programme instants, keeping the title/channel snapshot. Adjusting times is explicit. A repeated wall time requires an offset/UTC choice; a nonexistent wall time is invalid and is never silently moved. End must follow start, within the current 1–720 minute limit. Editing keeps timezone fixed; active capture keeps start fixed. The idempotency key belongs to the intent and survives retry and presentation changes. The unresolved private-HTTP opener crash must be fixed in the application, not hidden by the prototype.

Starting, recording, recovering, finalizing, interrupted, partial, missed and failed states have different outcomes. Show ready original parts even if another part failed. Show gaps explicitly. Compatibility preparation creates a separate artifact, consumes extra space, can wait behind recording and never replaces the original. Protected and reader-held files need server revalidation before deletion. Stop requests finalization; cancel removes a future capture intent; delete removes eligible media; disabling stops active and cancels future captures while preserving saved files.

Live filtering and the 30-second refresh preserve the selected viewer and player mount, even if the selection leaves the filtered list. Switching channel or Stop watching releases that viewer once. Shared viewers and direct engine source leases retain ownership until final release. Acexy owns its sessions; a settings change cannot transfer ownership of an existing session. The prototype's node-identity test verifies only the local illustration, not real HLS continuity.

## Access and transport

Activation belongs to Settings → Access. Supported private-address HTTP over private connections, including Docker NAT, needs no browser pairing or console code. Public-address HTTP remains blocked for accounts. A Cast trust entry cannot relax that rule. Describe unencrypted private HTTP honestly. Default-deny management, aliases/prefixes, viewer permissions, IPTV credentials and administrator headers remain separate.

Keep all eight permission values, the account administrator/enabled flags, the public-view policy, independent public-playlist/local-IPTV controls and network lists. An administrator does not have a misleading partial permission checklist. Recheck the last active administrator on demotion, disable and deletion. Explain sign-out and credential revocation before consequential permission/password changes. Expired sessions retain a safe return route but do not resubmit mutations after login. One-time secrets appear once, with copy failure handling and a revoke/reissue route. Never expose them in public review captures.

Normal accounts, Cast and IPTV transport rules are not interchangeable with Telegram authorization. The latter currently requires HTTPS or localhost plus its own administrative header. VLC Android's actual pairing flow is separate from prohibited account/browser pairing. Remote control requires an account and explicit opt-in. Cast without accounts remains available to verified home clients.

## Channels, guide and playlist boundaries

Filters apply across the full catalogue before sorting/pagination. Search, Category, Status and Favorite remain visible on phones; the additional filters use Advanced. Reorder loads the complete inventory and sends desired IDs plus original order in one transaction. A stale/incomplete inventory rejects the whole reorder. Source preference order is a separate complete stream list, constrained by current source eligibility. No local ordering demonstration can establish server atomicity.

Manual Add and Search Add and Link preserve atomic stream creation/association and existing-link conflicts. Optional similar-name review stays off initially, with no preselection and one explicit target per stream. Stream-to-TV matching, guide matching and automatic exact guide matching are three separate workflows. Preserve imported guide IDs across all sources, including disabled sources; ambiguous names require source-qualified choices. Guide Apply rechecks the complete scope and expected preview. The blueprint does not resolve ambiguity by numeric row ID.

Playlist options retain favorites/unassigned dependency, per-source relay mode, include/exclude groups, format choice, guide IDs and validated token propagation. The shared format editor serves Playlist and Settings. Effective/saved/runtime player addresses retain reverse-proxy prefixes. Managed accounts force the app relay; they do not expose source credentials. Export start offsets display negative days while the current `days_back` API stores an absolute count; preserve that adapter conversion, zero and the existing defaults (1 past, 7 future). A slider redesign is not permission to alter export semantics.

## Source, extraction and event review

Source types preserve auto/regular/ZeroNet/IPFS and the installed broadcaster registry. Provider selection must use actual server catalogue values; “Synthetic adapter” is a fixture, not a new provider. Save, queue scrape, preview and remove are distinct actions. Source deletion's stream option and orphan cleanup have separate consequences. Failed recipe extraction preserves previous channels.

W3U Save-only remains available. Explicit import requires reviewed compatible live entries; VOD/event/unresolved entries do not become permanent live channels. Favorites and Recent are browsing filters, not import modes. Refresh updates only reviewed identities and does not silently prune absent entries. Saved-search edits pause refresh and require fresh review. Exclusion rules retain exact supported machine enums and apply to future imports, with an explicit bounded manual override where supported.

Installed and standalone helpers share the same recipe editor. Standalone never fetches from an installation or saves a source. HTML, JSON, regex, raw/manual selection and large-sample paths are distinct compositions. Recipe schema version remains 1; recipe version is a separate string. Preserve 32 MiB source support, 512 KiB recipe admission, 1,000 result bound and the smaller browser-rendering budget. Production regex remains in a disposable bounded worker. The design's fixed sample does not execute or validate arbitrary supplier content.

Events retain agenda/date/source/interest filters, unknown/date-only times, source timezone, provider-specific controls, manual/URL/versioned JSON input, reviewed selection, corrections, source refresh, broadcaster mapping and guide-overlay preview/apply. OpenFootball and WOSTI are distinct adapters; a date change is not automatically a reschedule. Preserve `schema_org`, `event_import`, `wosti_es`, `openfootball` and `postponed` values. Revision/fingerprint checks guard overlay writes, and removal of a mapping is distinct from removal of an overlay.

## System, integrations and recovery

Google Cast has bounded automatic discovery; there is no current manual Cast device editor. Manual remote host/port entry belongs to VLC/Kodi. Changed remote host/port invalidates authentication; Android pairing shows its certificate identity and expiry. Cast cleanup revalidates exact media ownership. Original video is default; optional conversion yields to recording. Media-server connection tests, connection/refresh actions and tuner settings retain separate requests and show pending/manual/error outcomes.

WARP mode, registration, connect, exclusions and startup options are distinct. Saved exclusions are not necessarily applied; preserve partial failures. Connected must be observed, not inferred from command acceptance. Startup application waits for restart; WARP stays opt-in. Tuner hiding only affects publication, not source deletion or probe scope.

System service controls distinguish persistent AceStream recovery from intentional UI Stop and from other sidecars' policies. Checker outage is not whole-container outage. Job history preserves scalar results, interruptions and FIFO waiting, with no duplicate run-now. Recording has its own coordinator. Storage describes filesystem free space once and marks partial/unknown scans honestly. Diagnostics remains authenticated and database-independent; exported bounded logs need credential masking.

First-run sources save individually; Finish completes setup only. Loading, database migration, deferred guide migration, connection loss and authenticated failure gates remain distinct. Retry precedes recovery. Readable recovery and fresh-catalogue recovery both make backups, explain skipped/rebuilt data and preserve independent accounts plus the fail-closed marker. A pending/recovery lock is never permission to start a competing operation. The prototype does not inject failures or recover any installation.
