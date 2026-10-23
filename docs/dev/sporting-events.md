# Sporting events: shared ingestion and browsing

Development implementation for #55, based on `develop`. The event model, reviewed ingestion, guide adapters, maintenance and player reuse
are implemented here, together with reviewed W3U event imports. Automatic W3U schedule extraction and Telegram ingestion remain in #257/#258;
this is not live-source certification or a claim of arbitrary website support.

## Research and dependency boundaries

Issue #55 and both comments were reread on 2026-10-23. The original request links a
ZeroNet page. A contributor reports that the page wraps futbolenlatv.es through a
CORS proxy and owns no event data; the original public gateway is reportedly dead.
These are contributor observations, **not a new live-source verification**. No
public gateway, CORS proxy, scraped website markup or schedule endpoint is embedded
as a runtime dependency.

PR #259's handoff calls for sharing this event model and reviewing content before
live-channel import. The implementations are now reconciled in that PR; #260 is
superseded. Recheck current CI/review status with `gh pr view 259`. #258 owns
Telegram transport/extraction; #233 owns non-XMLTV guide sources and overlays;
#216 owns optional interpretation; #224 owns broader fallback.

## Contract

`app/schemas/events.py` defines `EventImport` version 1. Every observation declares
`source_id`, `source_name`, `source_kind`, `external_id`, `title` and an IANA
`timezone`. Optional fields include participants, sport, competition, UTC/offset
or local ISO start/end timestamps, state, time assumptions and broadcast variants.
See the synthetic fixture in `backend/tests/fixtures/events/schedule.json`.

- Identity is `(source_id, external_id)`, never title or start time. Adapters must
  retain stable publisher identifiers through postponement. Do not put dates in
  synthetic identity if those dates change with postponement. With no reliable
  identity, require operator review rather than guessing a cross-source match.
- A **new** observation may explicitly associate an existing `event_id`. This is
  a reviewed mapping. It contributes broadcasts/provenance; the original owner
  remains authoritative for schedule fields. Existing observations cannot be
  reassigned by refresh. Same-title unassociated observations stay separate.
- Every incoming observation contains its complete schedule fields. Missing times
  mean unknown, not "keep the old time". Missing events/variants are retained;
  an incoming variant with the same ID replaces that variant. This supports
  partial upstream lists without destructive removal. Adapters must reject a
  parser failure instead of passing invented/default event data.
- Source refresh never overwrites `correction`, `followed` or `archived`. Clearing
  a correction reveals the latest owner schedule. The correction is a complete
  schedule override, not a field-by-field merge.
- A broadcaster label does not select a channel. An explicit `channel_id` refers
  to an existing active channel; nonexistent/disabled mappings remain unavailable.
  A generic “DAZN” remains unresolved. This avoids country/edition ambiguity until
  reviewed guide-matching adapters supply qualified mappings.

## Review and persistence

`POST /api/v1/events/preview` validates and projects without writes or network I/O.
It returns public rows and an opaque token. `POST /apply` requires that token and
explicit selected event IDs. Tokens last 15 minutes, survive at most four newer
previews, are consumed on successful apply and do not survive process restart.

Updates reserve each selected event's original revision with a conditional SQL
update. Any changed selected event rejects the transaction. Inserts have a unique
source identity constraint. Applying the same input again reuses saved event IDs;
new concurrent previews cannot replace each other's source identity. `PATCH
/{event_id}` uses the same revision check for corrections/following/archive state.

Migration `20261023_1200` follows `20261021_1200` and adds `sporting_events`,
`event_observations`, and `event_media`. Revision `20261023_1300` adds private
schedule sources, archive clocks and per-broadcast manual mappings. Existing
archives start their retention clock at upgrade, not at an inferred historical date.
Merge revision `20261023_1400` joins the event history with catalogue revision
`20261022_1200`. Upgrade-path tests preserve both prior heads and shared channel
rows. Keep the original deployed revisions intact.

HTTP inputs live only in private `event_media`, with source-qualified opaque
`url:` IDs. Rotating a URL/header changes that ID, preventing new viewers joining
an obsolete session. Obsolete lookup rows are removed during the same import;
active players already own their source and are not stopped. No AcestreamChannel,
TVChannel, numbering, favorite, guide or playlist assignment is created.

`stored_http_source` resolves event records through the existing session-owned
HTTP proxy. The same pinned fetch client, HLS rewriting, subtitle rules, startup
budget and cancellation teardown apply. Arbitrary websites/extensions are
informative unsupported entries, never handed to FFmpeg as media. Only direct
`.m3u8`/`.ts` and strict AceStream IDs are currently accepted for event-only playback.
Existing channel mappings can reuse existing broadcaster resolvers.

Public DTOs exclude stream URLs, signed queries and header values. Errors strip
input/context; only bounded field paths/messages are returned. All API routes use
the existing API-token enforcement. POST/PATCH bodies receive admission, a 2 MiB
byte limit and a 30-second upload deadline before JSON parsing. Two requests may
be admitted concurrently. Each import has at most 500 observations; each observation
has at most 50 variants. Inventory limits are 2,000 events, 4,000 observations,
10,000 variants and 16 MiB serialized observation payload. Reaching a limit fails
without discarding existing data. Page responses contain at most 100 events.

## Time and status

Local timestamps require a declared timezone. A nonexistent spring-forward time
or ambiguous repeated autumn hour is rejected unless an explicit numeric offset
is supplied. ISO dates without time, relative strings, numeric timestamps and
unrecognized zones are rejected. Adapters must resolve “today,” URL dates and
midnight crossings with documented source context in `time_notes`; this service
does not infer them. End must be explicitly known and later than start. UTC is
stored; browsing uses the selected display timezone, initially the browser's zone.

No clock transition changes event state. `live` is a publisher/operator assertion,
labelled as such. `is_online` and its timestamp come only from existing channel
checks; event-only sources remain unverified. Neither parsing nor opening the
schedule starts an engine or performs a probe.

## Guide sources, refresh and retention

`event_guide_adapter.py` reads a bounded schema.org SportsEvent subset from JSON or
HTML JSON-LD, without scripts or remote context loading. Exact property names,
stable publisher IDs and explicit timestamps are required. Relative/date-only
values and DST ambiguity reject the source. BroadcastEvent joins use indexed
publisher identity; `isLiveBroadcast`, offers and website URLs do not imply signal
or playable media. Tests use `fixtures/events/structured-guide.html`, not scraped
production markup. Semantics follow [SportsEvent](https://schema.org/SportsEvent)
and [BroadcastEvent](https://schema.org/BroadcastEvent).

`POST /events/sources/preview` fetches either normalized EventImport or this
structured subset. `EventSourcePreviewRequest` carries the format/timezone for a
new URL or an opaque saved source ID. It uses `outbound_http.source_session`, which
pins DNS and validates redirects without environment proxies. Limit: 2 MiB / 15s,
5 redirects, 64 JSON-LD blocks, depth 32, 20,000 JSON nodes and 500 observations.
Errors expose neither private inputs nor response bodies.

Preview contexts keep the URL private. Applying explicitly selected rows stores
source approvals and event updates in one transaction, including a source revision
check. Scheduled refresh can update only approved identities still present in the
database; it cannot create new events. User corrections/mappings, following and
archive state survive. A changed source invalidates in-flight work. Source failures
retain data and last-success timestamps; pending counts expose new reviewable IDs.
There are at most 20 sources and 2,000 approvals per source, pruned by retention.

Refresh runs inside `url_scraping`, using its existing FIFO, deduplication, anchors
and startup catch-up. `POST /events/sources/refresh` requests that same scheduled job through
`run_task_now`, preserving running/waiting deduplication; it also scrapes channel
sources. There is no competing event job. A pass
limits fetch time to 120s, checks shutdown between sources and prioritizes oldest
attempts. DB transactions end before network I/O. Results appear in source status,
Overview history and scraping notifications, independently of channel results.

Retention is one validated setting, disabled by default, edited at
`GET/PATCH /events/retention`. It runs in existing daily `channel_cleanup`, with no
startup catch-up. Ended deletion requires finished/cancelled **and** a known end;
archived deletion uses `archived_at`. Followed rows are protected. Conditional
revision reservation prevents a concurrent follow/correction being deleted. Remove
event media/observations and approvals transactionally, never AcestreamChannel or
TVChannel rows. A retained active player already owns its source copy. Deleted
events require fresh explicit approval before reimport.

`PATCH /events/{id}/broadcast` stores a source-qualified broadcast mapping to an
explicit active stream. No broadcaster-name auto-selection is implemented. Mapping
survives feed updates and can be cleared to reveal the source again. API projections
resolve mapping signal in bulk and make disabled/missing mappings unavailable.

Optional artwork stays private in observations. `GET /events/{id}/artwork` uses the
same guarded fetch boundary with 2 admitted requests, 10s, 512 KiB and bounded raster
dimensions (4096 per axis, 4 million pixels). It rejects HTML/SVG and animated WebP,
returns typed bytes with nosniff/no-store, and never changes playback. The UI loads
artwork only on request via the authenticated API and revokes its blob URL on unmount.

## Catalogue integration and follow-ups

PR #259 includes this implementation and the reviewed W3U bridge described in
[W3U catalogues](w3u-catalogues.md#combined-catalogue-and-event-integration).
Both histories upgrade through merge revision `20261023_1400`. Catalogue entries
enter the shared event preview/apply contract without live-channel insertion.
W3U event dates require operator review; automatic W3U schedule extraction and
Telegram transport (#258) remain follow-ups. The existing ingestion contract can
associate source-qualified broadcasts explicitly without inferring matches by title.

Broader host resolvers and automatic fallback remain in their linked work. Guide
overlays/export are not offered: no XMLTV programs, assignments, IDs, playlists or
tokens are changed. Any future overlay needs its own preview and preservation tests.

See [Sports events](../../wiki/Sports-Events.md) for the operator workflow.
