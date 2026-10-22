# Sporting events: shared ingestion and browsing

Development implementation for #55, based on `develop`. This is the first delivery
of the event model, reviewed ingestion and existing-player experience, not a claim
that all issue acceptance criteria or live source integrations are complete.

## Research and dependency boundaries

Issue #55 and both comments were read on 2026-10-22. The original request links a
ZeroNet page. A contributor reports that the page wraps futbolenlatv.es through a
CORS proxy and owns no event data; the original public gateway is reportedly dead.
These are contributor observations, **not a new live-source verification**. No
public gateway, CORS proxy, scraped website markup or schedule endpoint is embedded
as a runtime dependency.

PR #259 was open/draft at inspection (head `9177487a3cfd51322d3e74166aa416dcc04eaf63`),
with no discussion comments returned. Its handoff explicitly expects this event
model to land first. Recheck live state with `gh pr view 259` rather than treating
this snapshot as current CI/review status. This branch does not merge or modify
that PR. #258 owns Telegram transport/extraction; #233 owns non-XMLTV guide sources
and overlays; #216 owns optional interpretation; #224 owns broader fallback.

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
`event_observations`, and `event_media`. PR #259 currently has a sibling migration
`20261022_1200`: when integrating there, reconcile Alembic heads and exercise both
prior-head upgrade paths. Do not edit already deployed revision history or drop
catalogue snapshots to resolve the branch. A local database stamped by the W3U
branch cannot run directly on this sibling branch; use an isolated development
database until both migration histories have been integrated.

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

## Retention and remaining work

Current retention is indefinite. Archive hides an event from ordinary browsing
and is reversible; it does not delete media or shared channels. Following is
installation-wide, with no notification or reminder promise. No automatic cleanup,
catch-up job or independent scheduler is introduced in this delivery.

Before closing #55, complete and validate:

1. W3U classification/adaptation in #259 **before** live-channel insertion. Reuse
   traversal provenance; do not infer event semantics from folder names alone.
2. Telegram and HTML/JSON source-specific adapters using this observation contract,
   including persistent reviewed associations and documented source date rules.
   The generic JSON upload is not a general website or raw W3U parser.
3. Opt-in refresh inside the existing FIFO queue and configurable archive/ended
   retention with recovery tests. No earlier destructive maintenance.
4. Richer broadcaster mapping/review, artwork and unsupported host resolvers.
5. Explicit previewable guide overlays/export, if offered, with preservation tests;
   no existing programmes or assignments are modified by this implementation.
6. Advanced fallback only with per-viewer ownership tests and truthful client limits.

See [Sports events](../../wiki/Sports-Events.md) for the operator workflow.
