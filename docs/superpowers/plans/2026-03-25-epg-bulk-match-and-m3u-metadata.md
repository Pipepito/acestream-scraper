# EPG Bulk Match And M3U Metadata Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bulk EPG-to-Acestream matching workflow with adjustable strictness, match analysis, and TV channel creation, while preserving M3U group/logo metadata during Acestream import.

**Architecture:** Introduce a dedicated backend matching service that performs deterministic multi-stage matching and powers both analysis and creation endpoints. Extend the M3U parsing/import path to persist channel and group metadata, then add an EPG Management UI flow that analyzes all EPG channels, shows match coverage, and creates TV channels from selected matched rows after server-side revalidation.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Python difflib, React, TypeScript, React Query, Material UI, pytest, Jest

---

## File Structure

- Modify: `backend/app/schemas/channel.py` - expose new bulk match request/response contracts and row-level outcome reporting
- Modify: `backend/app/repositories/channel_repository.py` - support deterministic candidate lookups and safe bulk association writes
- Create: `backend/app/services/epg_match_service.py` - centralize normalization, scoring, strictness presets, candidate uniqueness, and revalidation
- Modify: `backend/app/services/tvchannel_service.py` - create TV channels from selected analyzed EPG rows via the shared matcher
- Modify: `backend/app/api/endpoints/tv_channels.py` - add bulk analysis and create-from-analysis endpoints
- Modify: `backend/app/scrapers/base.py` - preserve parsed M3U metadata in normalized channel structures if needed
- Modify: `backend/app/scrapers/http.py` or relevant M3U parser module - parse `group-title`, `tvg-logo`, `tvg-id`, and supported `#EXTGRP` declarations
- Modify: `backend/app/services/m3u_service.py` - persist imported metadata and group fallback logos into Acestream channels
- Modify: `backend/app/services/scraper_service.py` - carry parsed metadata into stored `AcestreamChannel` rows during scrape persistence
- Modify: `backend/tests/test_tv_channels.py` - add analysis/create bulk match coverage
- Modify: `backend/tests/test_scrapers.py` - add M3U metadata parsing and persistence coverage
- Modify: `frontend/src/services/tvChannelService.ts` - add analysis/create-from-analysis API calls and response types
- Modify: `frontend/src/pages/EPG.tsx` - add bulk match controls, summary cards, result table, strictness presets, and create action
- Create: `frontend/src/__tests__/EPGBulkMatch.test.tsx` - add UI regression coverage for analysis, strictness selection, selection rules, and create action

## Chunk 1: Backend Matching Engine And Contracts

### Task 1: Add failing backend tests for deterministic matching analysis

**Files:**
- Modify: `backend/tests/test_tv_channels.py`
- Create or Modify: `backend/tests/factories` or local fixtures in `backend/tests/test_tv_channels.py`
- Reference: `docs/superpowers/specs/2026-03-25-epg-bulk-match-and-m3u-metadata-design.md`

- [ ] **Step 1: Write fixtures for realistic EPG and Acestream candidates**

Add test data covering:
- exact `channel_xml_id` / `tvg_id` matches
- normalized exact name matches
- fuzzy matches that pass `Loose` but fail `Strict`
- one EPG channel matching multiple Acestream channels
- one Acestream channel matching multiple EPG channels

- [ ] **Step 2: Write failing analysis endpoint tests**

```python
def test_analyze_epg_matches_returns_summary_and_rows(client, seeded_match_data):
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced'})
    assert response.status_code == 200
    data = response.json()
    assert data['summary']['epg_channels_analyzed'] > 0
    assert 'rows' in data


def test_analyze_epg_matches_applies_strictness_thresholds(client, seeded_match_data):
    loose = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'loose'}).json()
    strict = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'strict'}).json()
    assert loose['summary']['matched_epg_channels'] >= strict['summary']['matched_epg_channels']


def test_analyze_epg_matches_honors_source_filter(client, seeded_match_data):
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced', 'source_id': 7})
    assert response.status_code == 200
    assert all(row['epg_source_id'] == 7 for row in response.json()['rows'])


def test_analyze_epg_matches_returns_clean_zero_summary_when_no_matches_exist(client, seeded_unmatched_data):
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced'})
    assert response.status_code == 200
    data = response.json()
    assert data['summary']['matched_epg_channels'] == 0
    assert data['summary']['matched_acestream_channels'] == 0


def test_analyze_epg_matches_includes_scores_and_match_stages(client, seeded_match_data):
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced'})
    assert response.status_code == 200
    first_candidate = response.json()['rows'][0]['candidates'][0]
    assert 'match_stage' in first_candidate
    assert 'score' in first_candidate
    assert 'best_match_type' in response.json()['rows'][0]
```

- [ ] **Step 3: Write failing candidate uniqueness tests**

```python
def test_analyze_epg_matches_resolves_shared_acestream_candidates_deterministically(client, seeded_conflict_data):
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced'})
    assert response.status_code == 200
    rows = response.json()['rows']
    # assert one Acestream candidate appears in only one creatable row
```

- [ ] **Step 4: Write a failing operational-budget rejection test**

```python
def test_analyze_epg_matches_rejects_workloads_over_budget(client, monkeypatch):
    monkeypatch.setattr('app.services.epg_match_service.MAX_ANALYSIS_COMPARISONS', 1)
    response = client.post('/api/v1/tv-channels/analyze-epg-matches', json={'strictness': 'balanced'})
    assert response.status_code == 422
```

- [ ] **Step 5: Run tests to verify they fail**

Run: `backend/venv/bin/pytest -q backend/tests/test_tv_channels.py -k epg_matches`
Expected: FAIL because the analysis endpoint/service do not exist yet

- [ ] **Step 6: Add request/response schemas for analysis and creation**

Define explicit Pydantic models for:
- strictness preset input
- match candidate rows with score and stage
- summary counts
- row-level create outcomes and failure reasons
- create-from-analysis request/response

- [ ] **Step 7: Create `backend/app/services/epg_match_service.py` with the canonical matcher**

Implement:
- normalization order from the spec
- `SequenceMatcher` scoring
- preset thresholds `Loose=0.70`, `Balanced=0.82`, `Strict=0.92`
- stage 1/2 bypass thresholds
- deterministic tie-breaking and uniqueness resolution
- workload estimation and explicit rejection when the comparison budget is exceeded

- [ ] **Step 8: Add the analysis endpoint and wire it to the service**

Run analysis over all EPG channels, optionally filtered by source, and return summary + rows.

- [ ] **Step 9: Run tests to verify they pass**

Run: `backend/venv/bin/pytest -q backend/tests/test_tv_channels.py -k epg_matches`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/schemas/channel.py backend/app/services/epg_match_service.py backend/app/api/endpoints/tv_channels.py backend/tests/test_tv_channels.py
git commit -m "feat: add bulk EPG match analysis"
```

## Chunk 2: Backend TV Channel Creation From Analysis

### Task 2: Add failing backend tests for create-from-analysis revalidation

**Files:**
- Modify: `backend/tests/test_tv_channels.py`
- Modify: `backend/app/services/tvchannel_service.py`
- Modify: `backend/app/repositories/channel_repository.py`

- [ ] **Step 1: Write failing create-from-analysis tests**

```python
def test_create_from_epg_analysis_creates_tv_channels_and_associates_all_candidates(client, seeded_match_data):
    response = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={'strictness': 'balanced', 'epg_channel_ids': [1, 2]})
    assert response.status_code == 200
    data = response.json()
    assert data['created_count'] == 2
    assert data['associated_count'] >= 2


def test_create_from_epg_analysis_revalidates_matches_server_side(client, seeded_match_data):
    # mutate candidate data after analysis fixture setup
    response = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={'strictness': 'strict', 'epg_channel_ids': [1]})
    assert response.status_code == 200
    # assert server used fresh matching, not stale client payload


def test_create_from_epg_analysis_reports_row_level_partial_success(client, seeded_match_data):
    response = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={'strictness': 'balanced', 'epg_channel_ids': [1, 2, 3]})
    assert response.status_code == 200
    data = response.json()
    assert 'row_outcomes' in data


def test_create_from_epg_analysis_enforces_candidate_uniqueness_across_created_rows(client, seeded_conflict_data):
    response = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={'strictness': 'balanced', 'epg_channel_ids': [1, 2]})
    assert response.status_code == 200
    # assert the shared Acestream channel is associated to only one created TV channel


def test_create_from_epg_analysis_rolls_back_failed_row_without_orphan_tv_channel(client, seeded_match_data, monkeypatch):
    # force association failure for one selected row after TV channel creation starts
    response = client.post('/api/v1/tv-channels/create-from-epg-analysis', json={'strictness': 'balanced', 'epg_channel_ids': [1, 2]})
    assert response.status_code == 200
    data = response.json()
    # assert failed row is reported and no TVChannel persists for its epg_id
```

- [ ] **Step 2: Write failing skip/conflict tests**

Cover:
- existing `epg_id` skip
- duplicate existing TV channels by same `epg_id`
- invalid strictness rejection
- empty `epg_channel_ids` rejection
- no-op rejection when revalidation yields no accepted matches

- [ ] **Step 3: Run tests to verify they fail**

Run: `backend/venv/bin/pytest -q backend/tests/test_tv_channels.py -k create_from_epg_analysis`
Expected: FAIL because create-from-analysis behavior does not exist yet

- [ ] **Step 4: Implement a dedicated transactional bulk-create path in `tvchannel_service.py`**

Use the shared matcher to:
- recompute candidates
- skip existing TV channels by `epg_id`
- create one TV channel per selected matched EPG channel
- associate all accepted Acestream channels for that row
- report created/skipped/associated/failure counts

Do not reuse the legacy per-row `create_tv_channel()` auto-association path for bulk creation. Instead:
- bypass `auto_associate_acestreams`
- use only the shared bulk matcher
- wrap each row in a transaction/savepoint so a failed association does not leave an orphan `TVChannel`

- [ ] **Step 5: Add the create endpoint in `tv_channels.py`**

Accept only:
- `strictness`
- selected `epg_channel_ids`

Reject missing/invalid input per the spec.

- [ ] **Step 6: Run tests to verify they pass**

Run: `backend/venv/bin/pytest -q backend/tests/test_tv_channels.py -k 'epg_matches or create_from_epg_analysis'`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/tvchannel_service.py backend/app/repositories/channel_repository.py backend/app/api/endpoints/tv_channels.py backend/tests/test_tv_channels.py
git commit -m "feat: create TV channels from bulk EPG matches"
```

## Chunk 3: M3U Metadata Preservation

### Task 3: Add failing scraper tests for group/title/logo preservation

**Files:**
- Modify: `backend/tests/test_scrapers.py`
- Modify: `backend/app/scrapers/base.py`
- Modify: `backend/app/services/m3u_service.py`
- Modify: `backend/app/services/scraper_service.py`
- Modify: relevant M3U parser module(s)

- [ ] **Step 1: Write failing parser tests for supported playlist patterns**

Use the sample shapes from the spec to cover:
- `#EXTINF` with `group-title`, `tvg-logo`, `tvg-id`
- `#EXTGRP: group-title="..." group-logo="..."`
- fallback to group logo when channel logo is missing
- ignore unsupported `#EXTGRP` variants without crashing

Use the existing schema/storage mapping already present in the repo unless a true gap is discovered:
- `group-title -> AcestreamChannel.group`
- `tvg-logo` or resolved group fallback logo -> `AcestreamChannel.logo`
- `tvg-id -> AcestreamChannel.tvg_id`

- [ ] **Step 2: Run tests to verify they fail**

Run: `backend/venv/bin/pytest -q backend/tests/test_scrapers.py -k 'group_title or extgrp or tvg_logo'`
Expected: FAIL because metadata is not fully preserved yet

- [ ] **Step 3: Implement metadata parsing and persistence**

Ensure imported Acestream channels retain:
- `group_title`
- `tvg_logo`
- `tvg_id`
- group fallback logo when applicable

- [ ] **Step 4: Wire parsed metadata through `scraper_service.py` into persisted `AcestreamChannel` rows**

Verify the stored rows, not just the parser output.

- [ ] **Step 5: Only if storage is actually insufficient, add the minimal model/migration changes**

If current columns are insufficient, add:
- an Alembic migration
- the minimal model/schema updates
- any startup migration wiring used by this repo

- [ ] **Step 6: Run tests to verify they pass**

Run: `backend/venv/bin/pytest -q backend/tests/test_scrapers.py -k 'group_title or extgrp or tvg_logo'`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/scrapers/base.py backend/app/services/m3u_service.py backend/app/services/scraper_service.py backend/tests/test_scrapers.py
git commit -m "feat: preserve M3U group metadata on import"
```

## Chunk 4: Frontend Bulk Match Workflow

### Task 4: Add failing frontend tests for analysis and creation UI

**Files:**
- Create: `frontend/src/__tests__/EPGBulkMatch.test.tsx`
- Modify: `frontend/src/services/tvChannelService.ts`
- Modify: `frontend/src/pages/EPG.tsx`

- [ ] **Step 1: Write failing UI tests for bulk analysis controls**

Cover:
- strictness preset selector shows `Loose`, `Balanced`, `Strict`
- clicking `Analyze Matches` triggers the correct API request
- selected source filter is sent into the analyze request
- summary counts render after analysis
- result rows render matched/unmatched state
- `Create Matched TV Channels` is disabled before analysis
- default row selection includes only matched rows without existing `epg_id`
- skipped existing-TV rows are shown but not selected
- result table filters `all`, `matched`, `unmatched`, and `creatable` work as specified
- confidence/match-type text is visible in the result table
- zero-match analysis renders a clean empty summary state

- [ ] **Step 2: Write failing UI tests for creation flow**

Cover:
- row-level deselection
- create action sends `strictness + epg_channel_ids`
- success toast shows created/skipped/associated counts
- unmatched rows remain unselected/uncreatable
- create action includes only selected creatable rows

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPGBulkMatch.test.tsx`
Expected: FAIL because the bulk match UI and service calls do not exist yet

- [ ] **Step 4: Add service methods in `tvChannelService.ts`**

Implement typed API calls for:
- analyze EPG matches
- create TV channels from selected analyzed rows

- [ ] **Step 5: Add the workflow UI in `EPG.tsx`**

Implement:
- strictness selector
- `Analyze Matches`
- summary panel
- filterable analysis table (`all`, `matched`, `unmatched`, `creatable`)
- row-level selection and deselection
- `Create Matched TV Channels`

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPGBulkMatch.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/services/tvChannelService.ts frontend/src/pages/EPG.tsx frontend/src/__tests__/EPGBulkMatch.test.tsx
git commit -m "feat: add bulk EPG match workflow"
```

## Chunk 5: Full Verification

### Task 5: Verify backend, frontend, and integrated build behavior

**Files:**
- Modify only if verification uncovers a real contract gap

- [ ] **Step 1: Run backend regression coverage**

Run: `backend/venv/bin/pytest -q backend/tests/test_tv_channels.py backend/tests/test_scrapers.py`
Expected: PASS

- [ ] **Step 2: Run frontend regression coverage**

Run: `cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPGBulkMatch.test.tsx src/__tests__/EPG.test.tsx src/__tests__/EPGProgramsTable.test.tsx`
Expected: PASS

- [ ] **Step 3: Build the integrated frontend**

Run: `cd frontend && npm run build:backend`
Expected: PASS and copy the latest assets into `backend/frontend_build`

- [ ] **Step 4: Manual verification in the app**

Run: `cd backend && venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000`
Expected:
- EPG Channels tab shows bulk match controls
- analysis returns summary counts across all EPG channels
- strictness changes result coverage
- create action builds TV channels from selected matches
- imported Acestream channels now show improved metadata quality for logos/groups where the playlist provided it

- [ ] **Step 5: If manual verification reveals a mismatch, add a focused regression test before fixing it**

Run the smallest relevant backend or frontend test first, then patch.

- [ ] **Step 6: Commit**

```bash
git add backend frontend
git commit -m "test: verify bulk EPG matching workflow"
```
