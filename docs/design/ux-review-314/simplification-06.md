# Simplification decisions and connected journeys

Review 06 · approved execution scope, composed for review; no application implementation. Most users want to watch, record and fix a problem without understanding sources, engines or transport internals.

## One navigation structure

**Watch · Recordings · Events · Channels · Connections · Settings · System**

Watch combines the home overview and Live TV. Both `/` and `/live-tv` remain entry aliases; channel/filter queries keep their meaning. The phone keeps Watch, Recordings and Events visible and puts all seven destinations in a labelled Menu. The same locations apply to lime, coral/navy and immersive. WARP remains an explicitly named System link and a discoverable sidebar/footer entry.

The inspected application has 20 destination links across its navigation groups; the earlier workflow prototype had 19. The proposal has seven primary destinations, plus a WARP utility link. These are structural counts, not a measured usability improvement. The 146 review contexts include editors and consequential states; they are not 146 app pages.

| Current presentation | Proposed ownership | Why it is easier |
|---|---|---|
| Home and Live TV | Watch, with browsing and player context | One place to begin watching; browsing does not stop playback |
| Sources, search, raw streams, channels, guide pages | Channels → TV channels / Sources / Programme guide / Advanced streams | Users first choose their goal; implementation entities remain available when relevant |
| Several ways to add sources and guides | Channels → Add channels → canonical provider editor → import result → optional guide → match review | One connected setup path; each save/import remains an independent action |
| Recording settings among global settings | Recordings → Recording settings, also linked from Settings | Capacity, storage and retention are found beside recordings |
| Cast, remote players, browser, media servers, playlists and address | Connections grouped by where/how the user watches | Shared address and format editors replace duplicated controls; Cast and remote control keep distinct permissions |
| Telegram ingestion and notification controls together conceptually | Telegram sources under Channels; notifications under Connections | Receiving channels and sending alerts are different tasks |
| Many global settings and advanced controls | Concise Settings index; advanced runtime/network under System | Common choices first; no giant accordion page or global Save |
| Separate setup copies of source/guide forms | Alias to source/guide canonical editor | Same validation, defaults and transaction from every entry point |
| Palette × layout laboratory controls | One Interface selector with three described presets | Users choose a complete presentation rather than combining independent design experiments |

[Every current context, source path, proposed location and save boundary](before-after-map.md) is enumerated. Historical application aliases are retained in that map. Future routing accepts the existing `/settings?tab=playback|automation|links|access|network`, source/guide tabs and direct dialogs; it resolves to the canonical context without silently dropping query values. Use replace-navigation for obsolete presentation aliases, preserve back navigation and the caller's return context. A changed location is not a new resource or permission.

## Six task paths

Counts below are authored walkthrough steps from a known starting screen, not participant timing. A step means opening a destination/context or committing a user decision; text entry is not counted per keystroke. Compare the same task, not total page count.

| Task | Earlier prototype route | Composed route | Decision / confirmation impact |
|---|---|---|---|
| Find and watch Northlight | Home → Live TV → choose channel (3) | Watch → Watch Northlight (2 including destination) | Home/Live decision removed; online-only remains default, Show all available |
| Schedule and find a recording | Live TV → programme → recording editor → Schedule → Recordings (5) | Watch → programme Schedule → Schedule → Recordings (4) | Exact programme instants prefilled; editing times optional; no redundant success confirmation |
| Add source and useful guide | Sources → editor → save → import → find Guides → add → matching (7 contexts/actions) | Channels → Add channels → source save → import/result → optional guide save → review matching (6) | Guidance links connect existing transactions; no default guide/source imported silently |
| Watch on another device | Choose between Cast / Remote players / Media servers before context | Connections → TVs and players → choose supported device/action | One purpose-first entry; Cast versus remote control distinction retained. Setup may need the same number of actions |
| Give someone access | Settings → Access → user editor → save | Settings → Accounts and access → user editor → save | Same steps; clearer permission labels and consequential review, not an artificial step reduction |
| Understand and resolve a problem | System status → identify service/log/storage → action | System → affected service/job/storage → safe next action | Same depth; current state and consequence are adjacent. Recovery stays separate and reviewed |

These paths are clickable in [the prototype](workflow-prototype.html?screen=dashboard). “Add channels” is a source chooser; it does not create a new ingestion API. The next-step links after imports/guides use the same editors. No “Finish” button claims a multi-resource transaction: setup completion records only setup completion.

## Settings and review rules

Recording settings, guide matching, stream formats, player address and notification settings each have one canonical owner and contextual links. Settings is an index to them. Existing saved values and safe defaults load unchanged. Runtime controls show saved versus active values and restart implications; supervisor-owned/unavailable controls remain readable.

Advanced options are shown within the relevant editor, with their current values and dependencies. Future implementation must compute an “advanced options active” indicator against authoritative resolved defaults, not guessed empty/zero values. The prototype preserves open disclosures and changed advanced values; runtime/default inference is specified in the field ledger, not simulated as proof of backend logic.

Intervals, checker selection, schedule anchors and cleanup policy retain separate saves. Guide exact-match automation and stream-check scope preserve their immediate-save contracts. Favorites save immediately; channel number saves on Enter/blur, Escape restores and blank clears. Reorder commits the complete inventory atomically and rejects stale/incomplete reviews. The shared format editor is reused by playlists and stream-link entry points.

Remove repetitive confirmation for read/preview, safe navigation, ordinary save, copy and Stop watching. Keep review for deletes, cancelling scheduled recordings, stopping active captures, disabling a capability when consequential, account/security changes, destructive recovery, stale/conflicting state and reviewed match application. “Stop” finalizes captured material; “cancel” prevents a future run; “delete” removes specified files/records subject to protection and leases; “disable” retains data and prevents future work. Never substitute one word for another.

## Review status

Owner preferences: three presets; immersive third direction; shared maintenance; design-only work; supplier reuse first; OpenAPI contract testing. Approved execution plan: seven destinations, Watch consolidation, immersive default and design-only publication. Design hypotheses: detailed task ordering, final labels, card density, typography and individual imagery. Composed and author-checked does not mean participant-tested, owner-approved in detail or implemented.
