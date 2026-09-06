# TV channel automatch

TV Channels → **Auto-match streams** → **Find matches** analyzes the complete
catalog, independently of page filters. Results are grouped by TV station and show the number of distinct stream IDs.
Nothing is selected initially. Select a station or expand its stream list and
select individual IDs, then **Assign selected**. Analysis never writes data. The apply operation only
sets `tv_channel_id`; it does not create TV channels or rewrite EPG metadata.

## V1 analysis

Inspected `main` at `3af8c8c17602ca8d10cce6015700437484a6308a` on 2026-09-06:

- `app/api/controllers/tv_channels_controller.py`, `/find-matches`, delegates to
  `EPGService.find_matching_channels` with a default similarity threshold of 0.3.
- `app/services/epg_service.py` tries EPG ID, cleaned exact name, then
  `difflib.SequenceMatcher`. Cleaning drops quality labels, bracket contents,
  and generic words such as TV/channel, losing useful identity information.
- `app/services/tv_channel_service.py` also has substring-based batch assignment
  and a grouping helper accepting substrings or similarity greater than 0.8.
  Channel generation in that revision uses exact EPG IDs rather than that helper.

These are historical references, not runtime paths to restore in V2.

## V2 rules

`backend/app/services/tv_matching_service.py` owns the algorithm. The existing
EPG creation workflow and per-channel manual assignment remain separate.

1. Only unassigned streams enter analysis; every existing TV channel competes.
2. Every supplied stream name must agree with the full normalized TV station
   name and country. Conflicting names or the absence of any usable name cause the stream to be discarded, even if an
   EPG ID agrees. Conflicting nonempty EPG IDs block assignment.
3. Normalize case, Unicode accents, quality labels (including FHDp/1080p),
   punctuation, digit spacing, and provider suffixes after `-->`.
4. Spelling equivalents cover M+/M./Movistar, La Liga/LaLiga and Sky Sports/Sky
   Sport. No inferred station prefixes, dropped channel numbers, rebrands,
   substring matching or fuzzy similarity. `DAZN LaLiga 1` is not silently
   mapped to `DAZN LaLiga`; `Liga de Campeones` does not acquire an M+ prefix.
5. Full normalized names preserve channel numbers, BAR, TV, plus, HDR, genres
   and every other station identity word. Brand-only DAZN/Movistar labels do not
   identify a station. Acción, Comedia and Peliculas remain separate.
6. Country information must agree, including both being unmarked. An unmarked
   stream with multiple country editions in the TV catalog is ambiguous. An
   exact EPG ID can resolve that ambiguity only when names/countries agree.
   Contradictory country labels or metadata are discarded.
7. Multiple eligible destinations are ambiguous. No score, alphabetical order
   or database ID decides a winner between stations.
8. Apply uses these same rules, so an explicit request cannot attach a discarded
   candidate or assign a valid stream to a different station.

This is identity matching from names/metadata, not verification of broadcast
content. Multiple IDs with the same complete station name remain distinct backup
streams. They are grouped under one station in the review UI, with nothing
preselected. Discarded streams remain available in the manual assignment flow.

## API and persistence

- `POST /api/v1/tv-channels/automatch/preview`: typed summary and candidate pairs.
- `POST /api/v1/tv-channels/automatch/apply`: explicit selected pairs, maximum
  10,000. Recomputes candidates, skips stale/deleted/already-assigned pairs,
  rejects conflicting destinations for a stream, and commits conditional
  `tv_channel_id IS NULL` updates together. Existing assignments are preserved.
- Synchronous FastAPI endpoints run the CPU/DB work in the threadpool. Analysis
  rejects inventories above two million TV/stream comparisons. Names are
  normalized once per TV channel and once per stream variant.
- No schema migration is needed. Pydantic contracts, OpenAPI and generated
  frontend types are updated together. Routes retain the app's API-token gate.

## Read-only sample evaluation

On 2026-09-06, all 397 streams (262 names before provider suffixes) and all 111
TV channels were reviewed in both directions: stream-to-TV, then TV-to-stream.
Expected destinations were specified independently of the matcher and checked
against its output. The exact-only matcher agrees with all reviewed decisions:
125 eligible stream IDs across 38 TV stations, 268 discarded, and four existing
assignments preserved. Of the discarded IDs, 17 are ambiguous editions and 251
have no sufficiently certain match. No live-server data was changed.

For example, the inventory contains 21 distinct IDs explicitly named DAZN F1,
one Movistar Acción ID and two Movistar Comedia IDs. The total of 125 is across
the whole catalog; it is not a per-station count or a target to optimize.

`backend/tests/fixtures/tv_matching_reviewed_catalog.json` is the independently
reviewed, name-only regression corpus, including rejected groups and every TV
station. Real content IDs and infrastructure are excluded; a provider advertising
string is replaced with synthetic text. Tests evaluate all 393 unassigned
entries, reverse inventory order, compare every TV name against every other,
and reject extra station qualifiers. This verifies the identity policy against
reviewed labels, not whether the live content of an ID matches its advertised name.

Regression tests: `backend/tests/test_tv_matching.py` and
`frontend/src/__tests__/TVAutoMatchDialog.test.tsx`.
