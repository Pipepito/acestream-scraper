# TV channel automatch

TV Channels → **Auto-match streams** → **Find matches** analyzes the complete
catalog, independently of page filters. Review individual stream suggestions,
then **Assign selected**. Analysis never writes data. The apply operation only
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
2. An exact EPG ID restricts candidates to that identity. It is preselected only
   when every supplied stream name also agrees with the TV channel's name and
   country. Conflicting metadata stays unselected for review. Conflicting
   nonempty EPG IDs block name guesses.
3. Normalize case, Unicode accents, quality labels (including FHDp/1080p),
   punctuation, digit spacing, and provider suffixes after `-->`.
4. Spelling equivalents cover M+/M./Movistar, La Liga/LaLiga and Sky Sports/Sky
   Sport. Inferred Liga de Campeones/Hypermotion prefixes and DAZN LaLiga's first
   feed are separate catalog-alias suggestions and are never preselected.
5. Full normalized names must agree, preserving channel numbers, BAR, TV, plus,
   HDR and other identity words. General fuzzy similarity is not used: for
   example, M+ LaLiga TV must not match M+ LaLiga.
6. Name matching requires equal country information, including both being
   unmarked. When an unmarked stream could belong to multiple country editions
   with the same normalized name, it is ambiguous rather than defaulting to the
   unmarked TV channel. An exact EPG ID may resolve that ambiguity.
7. Ties are withheld. Review candidates also require a 0.05 lead over their
   runner-up. No alphabetical or database-ID tie breaking assigns a stream.
8. If `name` and `tvg_name` disagree, a suggestion is not preselected merely
   because one of them happens to match.

Scores are ranking values, not probabilities of correct broadcast content.
Historical rebrands such as BT Sport/TNT or Eleven/DAZN are not assumed.
Unmatched or ambiguous streams can be assigned from channel details. Multiple
IDs for the same station remain valid suggestions; there is no arbitrary cap
that would discard backup streams just to reduce the match count.

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

On 2026-09-06 the user's server supplied 111 TV channels and 397 streams, four
already linked to one TV channel. After tightening the rules, local analysis produced 125
recommended matches, 42 catalog-alias suggestions requiring review, 17 ambiguous
streams and 209 unmatched streams. The earlier iteration had 184 recommended
matches and 39 country-review suggestions; those broader rules are superseded. This measures coverage, not verified content accuracy.
No server data was changed. Raw inventories and infrastructure addresses are
not committed.

Regression tests: `backend/tests/test_tv_matching.py` and
`frontend/src/__tests__/TVAutoMatchDialog.test.tsx`.
