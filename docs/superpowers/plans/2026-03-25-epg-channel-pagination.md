# EPG Channel Pagination Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add global server-side pagination and a single-select EPG source filter to the EPG Channels view so users can browse more than 100 channels reliably.

**Architecture:** Convert the backend EPG channel list endpoint from a raw array to a paginated `{ items, total }` response with optional `source_id`, stable sorting, and validated `skip`/`limit`. Update the frontend EPG data service and EPG Management page to drive pagination state, source filtering, page resets, and visible-row selection against the new API contract.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, React, TypeScript, React Query, Material UI, pytest

---

## File Structure

- Modify: `backend/app/schemas/epg.py` - add paginated EPG channel response schema
- Modify: `backend/app/services/epg_service.py` - return paginated EPG channels with stable sorting and optional source filter
- Modify: `backend/app/api/endpoints/epg.py` - expose paginated contract and validate/clamp query params
- Modify: `backend/tests/test_epg.py` - update all existing EPG channel endpoint assertions to the paginated contract and add deeper pagination/filter regression coverage
- Modify: `backend/app/services/epg_service.py` - add exact EPG channel lookup by `(epg_source_id, channel_xml_id)` for non-paginated detail resolution
- Modify: `backend/app/api/endpoints/epg.py` - expose exact lookup endpoint for EPG channel resolution used by TV channel detail
- Modify: `frontend/src/services/epgService.ts` - update channel list service types and request params
- Modify: `frontend/src/hooks/useEPG.ts` - include page, page size, and source filter in the EPG channels query key
- Modify: `frontend/src/pages/EPG.tsx` - add source dropdown, pagination controls, page reset behavior, and page-scoped selection
- Modify: `frontend/src/components/EPGProgramsTable.tsx` - update channel list lookups that depend on the old array contract
- Modify: `frontend/src/pages/TVChannelDetail.tsx` - pass exact EPG lookup context to the programs table
- Create: `frontend/src/__tests__/EPG.test.tsx` - add frontend tests for paginated rendering, page resets, and visible-row selection

## Chunk 1: Atomic API Contract And Frontend Consumer Update

### Task 1: Add failing backend and frontend tests for the new paginated contract

**Files:**
- Modify: `backend/tests/test_epg.py`
- Modify: `frontend/src/components/EPGProgramsTable.tsx`
- Create: `frontend/src/__tests__/EPG.test.tsx`
- Reference: `backend/app/api/endpoints/epg.py`
- Reference: `frontend/src/pages/EPG.tsx`

- [ ] **Step 1: Expand backend test data so pagination is meaningful**

Add a local fixture/helper in `backend/tests/test_epg.py` with 4+ EPG channels across at least 2 sources so the test suite can prove slicing, ordering, filtering, and totals.

- [ ] **Step 2: Rewrite existing channel-list assertions and add failing backend tests**

```python
def test_get_epg_channels_returns_paginated_shape(client, seeded_many_epg_channels):
    response = client.get('/api/v1/epg/channels?skip=0&limit=1')
    assert response.status_code == 200
    data = response.json()
    assert 'items' in data
    assert 'total' in data
    assert len(data['items']) == 1


def test_get_epg_channels_orders_by_name_then_id(client, seeded_many_epg_channels):
    response = client.get('/api/v1/epg/channels?skip=0&limit=50')
    assert response.status_code == 200
    rows = [(item['name'], item['id']) for item in response.json()['items']]
    assert rows == sorted(rows)


def test_get_epg_channels_filters_by_source(client, seeded_many_epg_channels):
    source_id = seeded_many_epg_channels[0].epg_source_id
    response = client.get(f'/api/v1/epg/channels?source_id={source_id}&skip=0&limit=50')
    assert response.status_code == 200
    data = response.json()
    assert all(item['epg_source_id'] == source_id for item in data['items'])


def test_get_epg_channels_unknown_source_returns_empty_page(client):
    response = client.get('/api/v1/epg/channels?source_id=999999&skip=0&limit=50')
    assert response.status_code == 200
    assert response.json() == {'items': [], 'total': 0}


def test_get_epg_channels_clamps_invalid_skip_and_limit(client, seeded_many_epg_channels):
    negative_skip = client.get('/api/v1/epg/channels?skip=-5&limit=2').json()
    zero_skip = client.get('/api/v1/epg/channels?skip=0&limit=2').json()
    oversized_limit = client.get('/api/v1/epg/channels?skip=0&limit=999').json()
    assert negative_skip == zero_skip
    assert len(oversized_limit['items']) <= 100


def test_get_epg_channels_slices_stably_across_pages(client, seeded_many_epg_channels):
    page_one = client.get('/api/v1/epg/channels?skip=0&limit=2').json()
    page_two = client.get('/api/v1/epg/channels?skip=2&limit=2').json()
    assert page_one['total'] == page_two['total']
    assert [item['id'] for item in page_one['items']] != [item['id'] for item in page_two['items']]


def test_get_epg_channels_non_positive_limit_defaults_to_50(client, seeded_many_epg_channels):
    zero_limit = client.get('/api/v1/epg/channels?skip=0&limit=0').json()
    default_limit = client.get('/api/v1/epg/channels?skip=0').json()
    assert zero_limit == default_limit


def test_resolve_epg_channel_by_source_and_xml_id(client, seeded_many_epg_channels):
    target = seeded_many_epg_channels[-1]
    response = client.get(
        f'/api/v1/epg/channels/resolve?source_id={target.epg_source_id}&channel_xml_id={target.channel_xml_id}'
    )
    assert response.status_code == 200
    assert response.json()['id'] == target.id
```

- [ ] **Step 3: Write failing frontend tests for pagination and filtering behavior**

Render `frontend/src/pages/EPG.tsx` with `QueryClientProvider` and `MemoryRouter`. Mock EPG sources, paginated EPG channel responses, and TV channels so tests prove:
- the page reads `{ items, total }`
- page changes update the request parameters
- changing the source filter resets to page 1
- changing page or source clears selection
- `Select all` only selects visible unmapped rows on the current page
- current page resets to 1 when a refetch shrinks `total` enough to invalidate the current page
- selecting a valid source with no channels preserves the existing empty-state message

Add one frontend regression test for `TVChannelDetail`/`EPGProgramsTable` proving the page resolves the correct EPG channel via exact lookup even when that channel would not appear on page 1 of `/v1/epg/channels`.

- [ ] **Step 4: Run tests to verify they fail**

Run: `backend/venv/bin/pytest -q backend/tests/test_epg.py ; (cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPG.test.tsx)`
Expected: FAIL because `/api/v1/epg/channels` still returns a raw list and the frontend still expects the old contract with no pagination/filter UI

- [ ] **Step 5: Add the paginated EPG response schema**

```python
class EPGChannelListResponse(BaseModel):
    items: List[EPGChannelResponse]
    total: int
```

- [ ] **Step 6: Update the backend service and endpoint together**

```python
def get_channels(self, source_id=None, skip=0, limit=50):
    skip = max(skip, 0)
    limit = 50 if limit <= 0 else min(limit, 100)
    query = self.db.query(EPGChannel)
    if source_id is not None:
        query = query.filter(EPGChannel.epg_source_id == source_id)
    total = query.count()
    items = query.order_by(EPGChannel.name.asc(), EPGChannel.id.asc()).offset(skip).limit(limit).all()
    return items, total


def get_channel_by_source_and_xml_id(self, source_id, channel_xml_id):
    return (
        self.db.query(EPGChannel)
        .filter(EPGChannel.epg_source_id == source_id, EPGChannel.channel_xml_id == channel_xml_id)
        .first()
    )
```

- [ ] **Step 7: Update all frontend consumers of `/v1/epg/channels` in the same change**

Update:
- `frontend/src/services/epgService.ts`
- `frontend/src/hooks/useEPG.ts`
- `frontend/src/pages/EPG.tsx`
- `frontend/src/components/EPGProgramsTable.tsx`
- `frontend/src/pages/TVChannelDetail.tsx`

Implement:

```ts
export interface PaginatedEPGChannels {
  items: EPGChannel[];
  total: number;
}

useEPGChannels(sourceId?: number, page = 1, pageSize = 50) =>
  useQuery(['epg-channels', sourceId ?? 'all', page, pageSize], () =>
    epgService.getChannels(sourceId, (page - 1) * pageSize, pageSize)
  )
```

For `EPGProgramsTable`, do not scan the paginated `/v1/epg/channels` list to find one exact match. Add or reuse an exact lookup path by identifier such as `(epg_source_id, channel_xml_id)` and pass the necessary source context from `TVChannelDetail`.

Add a backend endpoint on a non-conflicting static path, such as `'/channels/resolve'`, or place it before `'/channels/{channel_id}'` if the path stays under `/channels/...`:

```python
@router.get('/channels/resolve', response_model=EPGChannelResponse)
async def get_channel_by_source_and_xml_id(source_id: int, channel_xml_id: str, db: Session = Depends(get_db)):
    service = EPGService(db)
    channel = service.get_channel_by_source_and_xml_id(source_id, channel_xml_id)
    if not channel:
        raise HTTPException(status_code=404, detail='EPG Channel not found')
    return channel
```

- [ ] **Step 8: Add source dropdown, pagination controls, and selection rules on `EPG.tsx`**

Implement:
- `All sources` single-select dropdown
- page-size options `25`, `50`, `100`
- reset to page 1 when source or page size changes
- reset to page 1 when refetch makes the current page invalid
- clear selection when page or source changes
- keep `Select all` limited to visible unmapped rows on the current page only

- [ ] **Step 9: Run backend and frontend tests to verify they pass**

Run: `backend/venv/bin/pytest -q backend/tests/test_epg.py && (cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPG.test.tsx)`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/schemas/epg.py backend/app/services/epg_service.py backend/app/api/endpoints/epg.py backend/tests/test_epg.py frontend/src/services/epgService.ts frontend/src/hooks/useEPG.ts frontend/src/pages/EPG.tsx frontend/src/components/EPGProgramsTable.tsx frontend/src/pages/TVChannelDetail.tsx frontend/src/__tests__/EPG.test.tsx
git commit -m "feat: paginate EPG channel management"
```

## Chunk 2: Integration Verification

### Task 2: Verify the paginated screen works end to end

**Files:**
- Modify: `frontend/src/pages/EPG.tsx` if fixes are needed
- Modify: `backend/...` only if integration reveals a contract mismatch

- [ ] **Step 1: Build the integrated frontend**

Run: `cd frontend && npm run build:backend`
Expected: PASS and copy assets into `backend/frontend_build`

- [ ] **Step 2: Run backend EPG and TV regression coverage**

Run: `backend/venv/bin/pytest -q backend/tests/test_epg.py backend/tests/test_tv_channels.py`
Expected: PASS

- [ ] **Step 3: Start the integrated app and verify manually**

Run: `cd backend && venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000`
Expected:
- EPG Channels table shows pagination controls
- selecting `All sources` pages globally
- selecting a source filters results and resets to page 1
- `Create TV Channels` continues to act on visible selected rows

- [ ] **Step 4: If manual verification reveals a page-reset bug, add a focused regression test before fixing it**

Run: `cd frontend && CI=true npm test -- --runInBand --watch=false src/__tests__/EPG.test.tsx`
Expected: PASS after the added regression case

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_epg.py frontend/src/pages/EPG.tsx frontend/src/__tests__/EPG.test.tsx
git commit -m "test: verify paginated EPG channel management"
```
