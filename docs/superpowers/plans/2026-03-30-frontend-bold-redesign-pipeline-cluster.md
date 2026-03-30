# Frontend Bold Redesign Pipeline Cluster Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the measured-bold redesign to `Scraper`, `AcestreamChannels`, and `TVChannels` so they read as one connected source-to-output workflow.

**Architecture:** Reuse the existing phase-1/phase-2 hero and semantic-token pattern, but apply it as a shared pipeline language across three pages: intake (`Scraper`), routing (`AcestreamChannels`), and organization (`TVChannels`). Keep each page independently usable, preserve dense working tables and dialogs, and move supporting tools like filters below the dominant working surface where the spec requires stronger stage emphasis.

**Tech Stack:** React 18, TypeScript, Material UI v5, React Query, Jest, Testing Library, Vite

---

## Required References

- `docs/dev/frontend-design-checklist.md`
- `docs/dev/frontend-theme-reference.md`
- `docs/superpowers/specs/2026-03-30-frontend-bold-redesign-design.md`
- `docs/superpowers/specs/2026-03-30-frontend-bold-redesign-pipeline-cluster-design.md`
- `docs/superpowers/plans/2026-03-30-frontend-bold-redesign-phase-2.md`

## File Map

- Modify: `frontend/src/pages/Scraper.tsx`
- Modify: `frontend/src/pages/AcestreamChannels.tsx`
- Modify: `frontend/src/pages/TVChannels.tsx`
- Modify: `frontend/src/__tests__/Scraper.test.tsx`
- Modify: `frontend/src/__tests__/AcestreamChannelsPage.test.tsx`
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`
- Modify: `docs/dev/frontend-design-review-evidence.md`

## Chunk 1: Scraper Intake Stage

### Task 1: Add a pipeline-ready summary to `Scraper`

**Files:**
- Modify: `frontend/src/__tests__/Scraper.test.tsx`
- Modify: `frontend/src/pages/Scraper.tsx`

- [ ] **Step 1: Write the failing test**

Update `frontend/src/__tests__/Scraper.test.tsx` to assert that `Scraper` opens with:

- a visible shared stage summary containing `Sources`, `Extracted channels`, and `TV organization`
- the current page framed as the intake/source stage
- explicit labels for source readiness and next step
- copy that points the user toward extracted-channel review after scraping

Example assertion shape:

```tsx
it('opens with a source-intake summary that shows the pipeline and next step', () => {
  renderPage();

  expect(screen.getByText('Sources')).toBeInTheDocument();
  expect(screen.getByText('Extracted channels')).toBeInTheDocument();
  expect(screen.getByText('TV organization')).toBeInTheDocument();
  expect(screen.getByText(/source readiness/i)).toBeInTheDocument();
  expect(screen.getByText(/review extracted channels after the scrape completes/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx`
Expected: FAIL because `Scraper` currently starts with a flat header + table and has no pipeline summary.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Scraper.tsx` so it:

- derives safe summary signals from existing URL data only (for example enabled source count, total source count, last processed freshness, and total channels found)
- adds a measured-bold hero using the shared `hero` token pattern already used in `EPG`, `WARP`, and `Settings`
- includes a visible cross-page pipeline summary near the top with the current stage shown as active/current
- labels the page as intake/orientation rather than final output
- keeps the URL table directly below the summary so the page still feels action-ready

Implementation notes:

- Use `useTheme` and `alpha` from `@mui/material/styles`
- Add lightweight derived values only from current `urls`
- Do not invent unsupported backlog or readiness scores
- Keep `Configured URLs` as the primary working section below the hero

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 2: Extracted Channel Routing Stage

### Task 2: Make `AcestreamChannels` the strongest page in the cluster

**Files:**
- Modify: `frontend/src/__tests__/AcestreamChannelsPage.test.tsx`
- Modify: `frontend/src/pages/AcestreamChannels.tsx`

- [ ] **Step 1: Write the failing tests**

Extend `frontend/src/__tests__/AcestreamChannelsPage.test.tsx` to expect:

- the same shared pipeline summary near the top
- the page framed as the `Extracted channels` stage
- plain-language inventory-routing guidance
- `Channels` rendered before `Filters`, so the working table is primary and filters are supporting

Example assertions:

```tsx
it('opens with an extracted-channel routing summary and keeps inventory primary', async () => {
  await renderPageAndWaitForGroups();

  const channelsHeading = screen.getByRole('heading', { level: 2, name: 'Channels' });
  const filtersHeading = screen.getByRole('heading', { level: 2, name: 'Filters' });

  expect(screen.getByText('Sources')).toBeInTheDocument();
  expect(screen.getByText('Extracted channels')).toBeInTheDocument();
  expect(screen.getByText('TV organization')).toBeInTheDocument();
  expect(screen.getByText(/inventory status/i)).toBeInTheDocument();
  expect(screen.getByText(/assign channels to tv entries/i)).toBeInTheDocument();
  expect(channelsHeading.compareDocumentPosition(filtersHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/AcestreamChannelsPage.test.tsx`
Expected: FAIL because the page currently has no pipeline summary and places filters before the inventory.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/AcestreamChannels.tsx` so it:

- adds a shared pipeline summary and measured-bold hero
- uses only safe metrics from current data (for example total visible channels, selection/bulk-action availability, whether groups loaded, whether TV assignment options exist)
- frames the page as the routing stage between scraping and TV organization
- moves the `Channels` section above `Filters`
- keeps bulk actions, assignment flow, and the table as the strongest visual/operational surface

Implementation notes:

- Reuse the same stage labels used in `Scraper`
- Keep failure notices (`InlineStatusNotice`, group load error, snackbar) intact
- Filters remain available, but should sit after the inventory region in DOM order and visual flow
- Avoid fabricated assignment percentages unless they can be derived safely from current data

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/AcestreamChannelsPage.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 3: TV Organization And Output Readiness Stage

### Task 3: Refactor `TVChannels` into the downstream organization stage

**Files:**
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`
- Modify: `frontend/src/pages/TVChannels.tsx`

- [ ] **Step 1: Write the failing tests**

Update `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` so it expects:

- the shared pipeline summary near the top
- the page framed as the `TV organization` stage
- downstream-readiness guidance referencing organization for EPG/output workflows
- the `TV Channel Inventory` section to appear before `Filters`, keeping the inventory primary and filters subordinate
- zero-result recovery guidance to remain explicit after the redesign

Example assertion shape:

```tsx
it('opens with an output-organization summary and keeps inventory ahead of filters', () => {
  renderPage({ isPhone: false, isDesktop: true, isWideDesktop: false });

  const inventorySection = screen.getByRole('region', { name: 'TV Channel Inventory' });
  const filtersSection = screen.getByRole('region', { name: 'Filters' });
  const layoutChildren = Array.from(screen.getByTestId('tv-channels-page-layout').children);

  expect(screen.getByText('Sources')).toBeInTheDocument();
  expect(screen.getByText('Extracted channels')).toBeInTheDocument();
  expect(screen.getByText('TV organization')).toBeInTheDocument();
  expect(screen.getByText(/output readiness/i)).toBeInTheDocument();
  expect(layoutChildren.findIndex((child) => child.contains(inventorySection))).toBeLessThan(
    layoutChildren.findIndex((child) => child.contains(filtersSection))
  );
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/TVChannelsPageResponsive.test.tsx`
Expected: FAIL because `TVChannels` currently has no pipeline summary and still renders filters before the inventory.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/TVChannels.tsx` so it:

- adds a shared pipeline summary and hero framing the page as downstream organization/output preparation
- uses safe catalog-derived signals only (for example total filtered channels, active vs inactive counts if cheaply derived, category spread if already available, and explicit next-step guidance)
- moves the `TV Channel Inventory` section above `Filters`
- preserves phone behavior where filters can still be shown/hidden from the inventory section
- keeps zero-result recovery guidance and create/edit/delete dialog flows intact

Implementation notes:

- Keep inventory dominant and filters supportive in both visual flow and DOM order
- Keep the phone filter toggle attached to the inventory surface if that remains the clearest pattern
- Do not claim exact EPG readiness unless it can be derived from current page data

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/TVChannelsPageResponsive.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 4: Verification And Evidence

### Task 4: Record evidence and verify the pipeline cluster end to end

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`

- [ ] **Step 1: Run targeted verification**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx src/__tests__/AcestreamChannelsPage.test.tsx src/__tests__/TVChannelsPageResponsive.test.tsx`
Expected: PASS.

- [ ] **Step 2: Run broader regression verification**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx src/__tests__/AcestreamChannelsPage.test.tsx src/__tests__/TVChannelsPageResponsive.test.tsx src/__tests__/TVChannelsTable.test.tsx`
Expected: PASS.

- [ ] **Step 3: Run full verification**

Run: `npm test -- --runInBand && npm run build`
Expected: All tests pass and the production build succeeds.

- [ ] **Step 4: Review cross-page hierarchy and responsive requirements**

Review the touched pages and test outputs against the approved cluster rules:

- `Scraper` remains the lightest hero treatment of the cluster
- `AcestreamChannels` is the strongest working surface and keeps inventory ahead of filters
- `TVChannels` feels calmer than `AcestreamChannels` while still presenting downstream readiness clearly
- the shared `Sources` -> `Extracted channels` -> `TV organization` stage summary remains visibly consistent across all three pages
- verification evidence covers one phone-width and one desktop-width path for each touched page, not only the cluster overall
- preserved action accessibility remains intact for scrape actions, assignment actions, and TV-channel organization actions

Expected: the cluster reads as one connected pipeline without collapsing into three identical hero treatments.

- [ ] **Step 5: Update evidence notes**

After the verification commands and hierarchy review succeed, add a new section to `docs/dev/frontend-design-review-evidence.md` covering:

- light-theme verification on `Scraper`, `AcestreamChannels`, and `TVChannels`
- dark-theme token/path inspection for the new hero and pipeline summaries
- one phone-width and one desktop-width path for each touched page
- keyboard path through scrape, assignment, and TV-channel organization controls
- loading, empty, warning/error, and success-feedback states where already present
- cross-page hierarchy validation that `Scraper` is lightest, `AcestreamChannels` is strongest, and `TVChannels` is the calmer downstream stage

- [ ] **Step 6: Review scoped diff**

Run: `git diff -- frontend/src/pages/Scraper.tsx frontend/src/pages/AcestreamChannels.tsx frontend/src/pages/TVChannels.tsx frontend/src/__tests__/Scraper.test.tsx frontend/src/__tests__/AcestreamChannelsPage.test.tsx frontend/src/__tests__/TVChannelsPageResponsive.test.tsx docs/dev/frontend-design-review-evidence.md docs/superpowers/specs/2026-03-30-frontend-bold-redesign-pipeline-cluster-design.md docs/superpowers/plans/2026-03-30-frontend-bold-redesign-pipeline-cluster.md`
Expected: Only pipeline-cluster redesign changes appear.

- [ ] **Step 7: Commit**

Do not commit unless the user explicitly asks.
