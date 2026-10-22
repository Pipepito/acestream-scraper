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

The operator matrix is intentionally conservative. Event presentation (#55),
VOD state and episode navigation (#99), Telegram ingestion (#258), host-specific
website adapters, isolated opt-in browser discovery, DASH/DRM capability design
and broader codec evidence remain separate work. Publisher flags are not proof
that a host resolver exists. This implementation should not close #257 as full
Wiseplay parity. The catalogue's retained unsupported entries provide fixture
candidates for those adapters without fetching arbitrary pages as media.

## Handoff: sporting events and VOD

Continue from this branch/draft PR while it remains unmerged. Read the latest
requirements in [sporting events (#55)](https://github.com/Pipepito/acestream-scraper/issues/55)
and [Scrape lists movies on Acestream (#99)](https://github.com/Pipepito/acestream-scraper/issues/99),
the applicable layered `AGENTS.md` files, and the operator contract above before
extending the implementation. Neither feature is implemented by this foundation.

- Start at `backend/app/services/w3u_parser.py`, `catalogue_service.py`,
  `backend/app/schemas/catalogue.py` and `frontend/src/pages/Catalogues.tsx`.
  Current public entries are catalogue records, not event/movie/episode DTOs.
  Private cached source documents retain richer publisher data, but that is not
  yet a normalized semantic ingestion contract. Introduce shared observations
  with provenance so new importers can reuse traversal without duplicating fetches.
- Add explicit or reviewed content classification before live-channel persistence.
  Today, compatible AceStream IDs and supported direct HTTP streams can be
  imported as channels even under a sports/movie folder; an AceStream ID is
  recognized before record type. Folder names alone must not decide semantics.
  Simply admitting VOD entries into the compatible-live set would mix inventories.
- Give events and VOD their own models and Alembic revisions after
  `20261022_1200`; preserve existing catalogue snapshots and imported channel state.
  Keep preview/revision checks, private headers, bounded guarded traversal,
  partial-refresh retention and manual overrides intact.
- For events, begin with reviewed ingestion and fixtures for UTC/timezone/DST,
  postponements, uncertain times, multiple broadcasts and unresolved broadcasters.
  Model event-to-broadcast relationships separately from TV numbering and guide
  assignments, then add browsing/source choice through existing playback ownership.
- For VOD, begin with movies/series/seasons/episodes and media variants, preserving
  incomplete metadata and distinguishing remakes or alternate cuts. Decide the
  scope of watchlist/progress state explicitly. The current sliding HLS player
  does not establish full VOD seeking: duration, forward/backward seeking,
  pause/idle ownership, resume after restart and completion need a tested playback
  design before exposing those controls.
- Keep W3U-owned HTTP inputs private and browser-only until an explicit safe
  export/external-player contract exists. Preserve subtitle-Off defaults,
  per-viewer track selection, cancellation budgets and shared-session ownership.
  Unsupported websites, DRM and DASH must remain explicit rather than being
  treated as playable because a publisher labels them as an event or movie.

Add migration-path, generated-client, ingestion and UI coverage for each new
contract, plus synthetic-media playback tests for VOD seek/resume. Telegram
transport (#258), host resolvers and guide overlays remain separate follow-ups;
do not close #257, #55 or #99 merely for landing this catalogue foundation.

## Verification

- `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_w3u_catalogues.py`
- Player regression tests: `test_player_endpoints.py`, `test_player_http_source.py`,
  `test_player_service.py`, `test_player_subtitles.py`, `test_engine_start_deadline.py`.
- `cd frontend && npm test -- --runInBand Catalogues.test.tsx`
- `cd e2e && npx playwright test --config playwright.mobile.config.ts mobile/catalogues.spec.ts`
- Regenerate OpenAPI and TypeScript, run frontend lint/typecheck and the application
  suites. Browser layout checks use mocked APIs and make no live media claim.
