# Reviewed guide setup and optional matching

A playlist needs both a guide address (`url-tvg`) and entry identifiers (`tvg-id`)
that appear in the XMLTV document. Importing XMLTV alone does not assign scraped
streams to stations. TV channels remain the shared station identity used by
playlists, Live TV and integrations.

## Reviewed setup (default)

1. Add and refresh EPG sources.
2. Open **Playlist → Review guide matches** or **EPG → Matching**.
3. Analyze matches. Strict is the initial threshold; lower thresholds offer
   name-similarity suggestions for human review only.
4. Inspect each guide source, station and proposed stream. Nothing is preselected.
5. Select reviewed rows and choose **Apply reviewed matches**. Existing compatible
   TV channels receive unassigned streams; other channel settings are preserved.

Analysis writes no catalogue data. Country/edition conflicts, inactive or
EPG-protected streams, and streams already assigned to TV channels are excluded.
An equal best match across guide channels is ambiguous, never resolved by row ID.
Selecting an EPG source explicitly narrows the matching scope and can resolve
competing providers. Within that scope, apply rechecks the complete inventory;
selecting a subset of rows does not change candidate ownership.

The UI supplies each selected row's `review_token` as `expected_previews` to
`POST /api/v1/tv-channels/create-from-epg-analysis`, along with the same strictness
and source filter used for analysis. A changed selection returns 409 before writes.
Changing a filter clears the UI preview. Older API clients may omit the snapshot,
but matches are still recomputed. Existing explicit-ID M3U import association and
manual channel/guide editing remain available.

## Optional automation

**Settings → Automation → Automatically match guide channels** persists
`epg_matching` as JSON through `GET/PUT /api/v1/config/epg-matching`. It defaults to
`{"enabled":false}` and requires no schema migration or environment change.
Enabling it affects subsequent successful source scrapes and EPG refreshes,
including manual runs. It does not start work immediately or during startup.

Automation uses enabled guide sources and the same preview/apply service. It
accepts only unique matches whose supplied names agree after conservative station
normalization and whose EPG IDs do not conflict. It never applies fuzzy matches,
chooses among tied providers, steals assigned streams, or changes favorites,
numbers, names or existing guide selections. Missing country information cannot
choose an explicitly identified edition. An unqualified existing manual guide
selection needs review before its source is filled in.

Work is bounded by the matching comparison budget and 1,000 guide rows per run.
Later successful ingestions can continue larger batches. Matching runs after the
import has committed, off the async request loop, and completes within that job;
it creates no independent scheduler. Apply operations share a process lock;
conditional repository updates protect stream ownership. Repeated runs reuse
existing source-qualified TV channels. A matching error preserves imported data.
The last result, including errors/partial results, appears below the setting and
at `GET /api/v1/config/epg-matching/last-run`. Disable the switch to stop future
runs; existing assignments remain.

## Export contract

All ordinary, curated and combined playlists prefer the assigned TV channel's
guide ID. They fall back to a stream's imported ID only when no TV guide ID is
selected. XMLTV uses that same identity and emits each guide identity once.
Tuner M3U and its XMLTV use the same rule; HDHomeRun guide numbers are unchanged.

Unique upstream XML IDs are preserved. IDs occurring in multiple sources, IDs
containing quotes/newlines, and the reserved `acestream-scraper:` namespace are
encoded as `acestream-scraper:<source-id>:<percent-encoded-xml-id>`. This resolution
uses the complete guide inventory, so playlist/search/favorite filtering cannot
change IDs. An unassigned stream with a colliding unqualified ID cannot choose a
provider; review it before expecting guide data.

Application playlist URLs advertise `/api/v1/epg/xml` using the public address
resolver. With API token enforcement enabled, an already validated credential
(query, bearer or X-Api-Token) is encoded into the advertised URL so URL-only
players can fetch it. XMLTV stays authenticated. Playlist responses are marked
private/no-store; downloaded playlists contain the credential and should be
handled like their token-bearing download URL. The network-gated tuner playlist
advertises `/tuner/epg.xml` and retains the tuner network policy.

Playlist coverage is catalogue-wide, independent of export filters. A linked
source/channel is not proof that the source currently has programmes. Coverage
errors remain unavailable, never a zero count.
