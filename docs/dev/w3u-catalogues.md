# Native W3U catalogue implementation

Issue #257, development implementation on `codex/257-w3u-catalogues`.
This is not a stable publication or a live-source playback certification.

`w3u_parser.py` parses structured JSON with an explicit breadth-first queue. Only group links,
explicit imports and W3U/JSON station links are traversed. A root `url` is an
update reference, never a media entry. Unknown HTML/PHP/embed URLs receive an
unsupported reason. No regex over a complete document and no browser script
execution is used. Fixtures are synthetic; the public examples in #257 are not
CI dependencies. The format reference is the
[Wiseplay format overview](https://help.wiseplay.tv/en/article/what-is-a-w3u-list-13yibil/).

`catalogue_service.py` separates read-only preview from import with an opaque,
process-local, bounded, expiring token. Public DTOs whitelist fields; raw source
URLs and header values remain private. Invalid request validation also excludes
input values. A save requires the original catalogue revision. Imports use
`ChannelRepository.create_or_update_channel`; existing channels are not mutated
and no TV rows are fabricated. W3U-owned HTTP entries remain browser-only and
are omitted from playlist exports to protect private input URLs and headers. Migration `20261022_1200` adds only the
`w3u_catalogues` table. Its JSON snapshot is version-owned by the catalogue row;
refresh never deletes channels. See the [operator contract](../../wiki/W3U-Catalogues.md)
for exact retention, identity, limits and compatibility semantics.

The thin `/api/v1/catalogues` routes run blocking parsing/persistence in the
FastAPI worker pool. Every network hop uses `bounded_source.source_get` over
`outbound_http.source_session`. Read transactions end before traversal. Snapshot
writes and channel insertion commit atomically, with optimistic revision checks.
The scheduled URL-scraping task refreshes opted-in catalogues inside its existing
maintenance queue and persists aggregate failure/partial counts. Browser preview
requests are independent read-only operations.

The lazy `/catalogues` page uses generated OpenAPI types, React Query, shared
page surfaces and `ChannelPlayerDialog`. It keeps source variants separate and
passes stored channel IDs to the established player. This deliberately preserves
existing direct/Acexy ownership, guarded HTTP inputs, startup deadlines, audio /
subtitle session sharing and cancellation cleanup. Browsing/filtering does not
release playback; closing the shared player does.

## Compatibility work still owned by the umbrella issue

The operator matrix is intentionally conservative. VOD state and episode navigation (#99), Telegram ingestion (#258), host-specific
website adapters, isolated opt-in browser discovery, DASH/DRM capability design
and broader codec evidence remain separate work. Publisher flags are not proof
that a host resolver exists. This implementation should not close #257 as full
Wiseplay parity. The catalogue's retained unsupported entries provide fixture
candidates for those adapters without fetching arbitrary pages as media.

## Combined catalogue and event integration

PR #259 now includes the sporting-event implementation formerly in #260. Migration
`20261023_1400` joins both original histories without rewriting either revision;
upgrade tests retain channels, catalogue snapshots and followed events from each head.

Content classification precedes channel insertion. Explicit movie/series/episode/VOD
records (including inherited folder types) cannot become live channels, even with
an AceStream ID. Explicit event records are also excluded. Folder names do not
classify content. Saving defaults to catalogue-only; `confirm_live` explicitly
approves compatible entries in the selected folders. Refresh reuses reviewed entry
identities and leaves new unknown entries for review. Existing channels are preserved.

A saved entry's **Add as event** action calls
`POST /catalogues/{id}/events/preview` with catalogue revision, entry IDs and reviewed
`EventFields`. The server builds the shared `EventImport` observation from private
snapshot media and headers; no duplicate fetch or parallel event model is involved.
The shared Events review requires explicit selection before apply. A source-qualified
UUID survives catalogue refresh; deletion/recreation cannot reuse its event identity.
Publisher IDs are hashed and must be unique in the catalogue. Without a publisher
ID, the entry identity depends on its folder/media and changes when those change.
Repeated review of the same identity updates its event and retains manual corrections.
The API can group up to 50 explicitly selected broadcast entries; the UI starts with
one entry. Explicit `event_id` associations use the existing event ingestion contract.

Apply atomically reserves the catalogue revision and source UUID along with event
writes. Concurrent catalogue refresh/removal/recreation invalidates the preview.
Event imports create no permanent channels or TV assignments. Known broadcaster
resolver entries stay unresolved until explicitly mapped to an existing channel;
they are never passed to FFmpeg as direct media.

W3U event schedule metadata is **reviewed manually** in this first bridge. Dates,
timezones and live state are not inferred from titles or folders. Refreshing a
catalogue does not automatically refresh event observations: review the saved entry
again to update it. Structured guide URL sources retain their separate opt-in
reviewed automatic refresh. VOD (#99), Telegram ingestion (#258), broader resolvers
and full Wiseplay parity remain follow-ups; keep #257 open.

## Verification

- `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_w3u_catalogues.py`
- Player regression tests: `test_player_endpoints.py`, `test_player_http_source.py`,
  `test_player_service.py`, `test_player_subtitles.py`, `test_engine_start_deadline.py`.
- `cd frontend && npm test -- --runInBand Catalogues.test.tsx`
- `cd e2e && npx playwright test --config playwright.mobile.config.ts mobile/catalogues.spec.ts`
- Regenerate OpenAPI and TypeScript, run frontend lint/typecheck and the application
  suites. Browser layout checks use mocked APIs and make no live media claim.
