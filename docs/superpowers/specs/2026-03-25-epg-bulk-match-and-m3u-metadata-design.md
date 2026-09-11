# EPG Bulk Match And M3U Metadata Design

## Goal

Add a bulk workflow in EPG Management that analyzes all EPG channels against imported Acestream channels, reports match coverage, supports configurable matching strictness, and creates TV channels from accepted matches. Improve M3U import so channel grouping and logo metadata are preserved and can support matching and browsing.

## Current Problems

- EPG channel creation is currently row-driven and does not support a global "analyze all" flow.
- Matching logic exists only as lightweight auto-association during channel creation and is not exposed as a user-reviewable bulk analysis step.
- Users cannot tune matching strictness.
- Imported Acestream channels are missing useful M3U metadata such as `group-title` and some group-level logo hints.

## Identifier Convention

- the canonical EPG identity used by matching and TV channel creation is the EPG channel XML identifier
- in the EPG domain model this is stored as `channel_xml_id`
- in the TV channel domain this is stored as `epg_id`
- these refer to the same logical identifier and must be treated as equivalent throughout this feature

## Chosen Approach

Implement a two-step workflow in EPG Management -> Channels:

- `Analyze Matches` scans all EPG channels against all Acestream channels using a preset strictness (`Loose`, `Balanced`, `Strict`)
- `Create Matched TV Channels` creates TV channels from the accepted analyzed matches and associates all matched Acestream channels to each created TV channel

In parallel, extend the M3U import pipeline to preserve channel and group metadata from playlist content.

## Matching Model

## Analysis Execution Model

- analysis runs synchronously in v1
- it is designed and tested for up to `5,000 EPG channels x 10,000 Acestream channels`
- target response time is under `10 seconds` on a normal local/dev environment
- if the server estimates the analysis would exceed that operational budget, it must reject the request with a clear message instead of silently timing out
- if future dataset growth makes this too slow, move the same contract behind a background job later without changing the user-visible workflow

### Match Unit

- one EPG channel can match zero, one, or many Acestream channels
- each analyzed row is anchored on an EPG channel
- each row contains the candidate Acestream channels that passed the selected threshold

### Acceptance And Selection Rules

- after analysis, rows are auto-selected for creation only when:
  - the EPG channel has at least one accepted match
  - no existing TV channel already uses that `epg_id`
- users may deselect rows before creation
- v1 does not support per-candidate Acestream selection inside a row
- when a row is created, all accepted Acestream candidates for that row are associated to the created TV channel, subject to uniqueness rules below

### Candidate Uniqueness Rule

- one Acestream channel may be attached to only one created TV channel per bulk-create run
- if the same Acestream channel matches multiple EPG rows, the winner is resolved by:
  1. strongest match stage
  2. highest similarity score
  3. deterministic alphabetical EPG channel name
  4. lowest EPG channel id

### Match Stages

Matching runs in layers, strongest to weakest:

1. exact `EPG channel_xml_id` <-> `Acestream tvg_id`
2. normalized exact name match
3. normalized similarity scoring on names

Normalization removes common noise such as:

- `HD`, `FHD`, `UHD`, `4K`
- punctuation and repeated spaces
- common formatting separators

Canonical normalization order:

1. lowercase
2. strip accents where possible
3. remove common quality tokens such as `hd`, `fhd`, `uhd`, `sd`, `4k`
4. remove bracketed source/noise fragments like `(solo eventos)` and duplicate separator markers where possible
5. replace punctuation/separators with spaces
6. collapse repeated whitespace

Canonical similarity algorithm for v1:

- use Python `difflib.SequenceMatcher`
- score range is `0.0` to `1.0`
- stages 1 and 2 bypass threshold scoring and are always accepted if matched

Preset thresholds:

- `Loose` = `0.70`
- `Balanced` = `0.82`
- `Strict` = `0.92`

The analysis result should record which stage produced each match so the UI can explain confidence.

### Strictness Presets

- `Loose`: broad similarity matching, meant for coverage
- `Balanced`: default threshold, meant for practical daily use
- `Strict`: only high-confidence matches

The UI uses friendly preset labels, while the backend maps them to numeric thresholds internally.

## EPG Management UI

### Placement

Add the workflow to the `Channels` tab in EPG Management.

### Controls

- preset selector: `Loose`, `Balanced`, `Strict`
- `Analyze Matches` button
- `Create Matched TV Channels` button, enabled after analysis

### Analysis Result Summary

Show summary metrics after analysis:

- total EPG channels analyzed
- EPG channels with at least one match
- total matched Acestream channels
- TV channels that would be created
- already-existing TV channels that would be skipped

### Result Table

Show one row per EPG channel that was analyzed, including:

- EPG channel name
- EPG source
- number of matched Acestream channels
- best confidence tier / match type
- whether the row is selected for creation
- whether the TV channel already exists

The table should support filtering the result set to:

- all analyzed
- only matched
- only unmatched
- only creatable

## Creation Behavior

- create one TV channel per selected matched EPG channel
- assign all matched Acestream channels to that TV channel
- skip rows whose EPG channel already maps to an existing TV channel by `epg_id`
- return counts for created, skipped, and associated channels

Creation API contract:

- the client sends:
  - `strictness`
  - selected `epg_channel_ids`
- the server recomputes and revalidates matches before writing
- the client does not send trusted candidate match payloads for persistence

Existing-channel skip behavior:

- primary skip key is exact `epg_id`
- if multiple TV channels already share the same `epg_id`, the row is skipped and reported as a duplicate-existing conflict
- name-only collisions do not block creation in v1; they may be reported as warnings later but are not treated as skips

## M3U Metadata Import

### Metadata To Preserve

From `#EXTINF` lines, preserve when available:

- `group-title`
- `tvg-logo`
- `tvg-id`

From `#EXTGRP` declarations, preserve group-level metadata such as:

- group name
- group logo

Supported parsing patterns in v1:

1. `#EXTINF:-1 ... group-title="DAZN" ...`
2. `#EXTGRP: group-title="DAZN" group-logo="https://...png"`
3. channel entries with `tvg-id`, `tvg-logo`, and `group-title` attributes in the `#EXTINF` line

Unsupported or unknown `#EXTGRP` variants are ignored rather than causing import failure.

### Fallback Rules

- if a channel entry has its own `group-title`, store it directly
- if a channel entry has no logo but its group has a declared logo, use the group logo as fallback
- if both channel-level and group-level logos exist, prefer the channel-level logo

### Storage Impact

Acestream channel records should retain enough imported metadata to:

- display group information in the UI
- improve match quality
- support future filtering/group browsing

## Backend Design

### Analysis Endpoint

Add a backend endpoint to analyze matches across all EPG channels with params for:

- optional `source_id`
- `strictness` preset

It returns:

- summary counts
- analyzed rows with candidate matches
- candidate scores and match stages for transparency

### Creation Endpoint

Add a backend endpoint that accepts:

- `strictness`
- selected `epg_channel_ids`

The server recomputes and revalidates matches before creating TV channels.

### Matching Service

Centralize the matching algorithm in a dedicated service/module so:

- analysis and creation share the same logic
- thresholds live in one place
- future improvements do not fork behavior

## Error Handling

- if analysis finds no matches, show a clean empty result with zero counts
- if creation is requested without selected `epg_channel_ids`, reject it
- if creation is requested with missing or invalid `strictness`, reject it
- if creation revalidation finds no accepted matches for the selected rows, reject it with a clear no-op response
- if some rows fail during creation, return partial success with per-row failures

## Testing

### Backend

- exact ID matches
- normalized exact name matches
- loose/balanced/strict threshold behavior
- one EPG channel matching multiple Acestream channels
- creation from analyzed matches
- skip-existing-TV-channel behavior
- M3U import preserving `group-title`, `tvg-logo`, `tvg-id`, and group fallback logos

### Frontend

- analysis request with selected strictness
- summary rendering
- matched/unmatched filtering
- create action from analyzed rows
- disabled state before analysis

## Non-Goals

- per-row manual scoring edits in the first version
- fuzzy alias dictionaries editable from the UI
- cross-source multi-select filtering for analysis
- redesigning the entire scraper/channel management UX
