# EPG Channel Pagination And Source Filter Design

## Goal

Make the EPG Channels view usable beyond the first 100 records by adding server-side pagination and a single-select source filter.

## Current Problem

- The backend EPG channels endpoint defaults to `limit=100`.
- The frontend EPG Channels tab calls that endpoint without pagination controls.
- The user can only see the first 100 EPG channels and cannot filter by EPG source.

## Chosen Approach

Implement server-side pagination with a paginated backend response and a frontend table UI that supports:

- global pagination across all EPG channels
- single-select source filtering with `All sources` as the default
- page reset when the source filter changes

## Pagination Contract

- frontend page index is 1-based for display
- backend remains `skip`/`limit` based
- frontend maps page to backend with `skip = (page - 1) * limit`
- default page size is `50`
- allowed page sizes are `25`, `50`, and `100`
- backend clamps invalid values:
  - negative `skip` becomes `0`
  - non-positive `limit` becomes `50`
  - oversized `limit` is capped at `100`

## Backend Design

### Endpoint

Update the EPG channels listing endpoint to accept:

- `skip`
- `limit`
- `source_id` (optional)

Change the response shape from a raw list to:

```json
{
  "items": [],
  "total": 0
}
```

The endpoint must use a stable default sort order to keep pagination deterministic:

- `name ASC`
- `id ASC`

### Service Layer

Update EPG service channel listing to:

- apply optional `source_id` filtering
- count total matching rows before pagination
- apply stable sorting before pagination
- return `(items, total)` consistently

### Schema

Add a paginated response schema for EPG channels so the API contract is explicit and consistent with TV channels and Acestream channels.

## Frontend Design

### Data Fetching

Update the EPG channels hook/service to pass:

- current page
- page size
- selected source filter

Use query keys that include page, page size, and source filter so cache invalidation stays correct.

This is an atomic API contract change: all frontend consumers of `/v1/epg/channels` must be updated from `EPGChannel[]` to `{ items, total }` in the same change.

### UI Changes

On the EPG Channels tab:

- add a single-select dropdown with `All sources` plus each configured source
- add pagination controls for page and page size
- display total count from the backend

The dropdown shows all configured EPG sources, regardless of whether they are enabled or currently populated, so the filter is predictable and matches source management.

### Selection Behavior

- row selection remains local to the currently displayed page
- `Select all` selects all unmapped rows on the current page only
- changing page or filter clears selection to avoid accidental bulk operations on hidden rows

## Error Handling

- if the source filter points to a source with no channels, show the existing empty-state behavior
- if the source filter uses an unknown `source_id`, the backend returns an empty paginated result rather than `404`
- if the paginated request fails, keep the existing error snackbar behavior
- if the current page becomes invalid because filtering, deletion, or refresh reduces `total`, reset to page 1

## Testing

### Backend

- verify EPG channel listing returns `items` and `total`
- verify pagination slices correctly
- verify `source_id` filters correctly

### Frontend

- verify the EPG Channels page requests paginated data
- verify source filter changes trigger refetch and reset page
- verify table renders current page rows only
- verify bulk selection applies only to visible rows

## Non-Goals

- multi-select source filtering
- cross-page bulk selection
- infinite scrolling
- changing EPG channel detail or program listing behavior
