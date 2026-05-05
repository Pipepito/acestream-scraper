# Frontend Bold Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the shared frontend shell and key top-level pages so the product feels more bold, operational, and scraper-led without breaking accessibility, responsiveness, or theme integrity.

**Architecture:** Keep the existing Material UI and shared primitive architecture, but deepen the semantic token system and push more visual personality through the shared shell, shared layout primitives, and top-level page composition. Implement behavior through TDD, starting with test expectations for token changes, shell presentation, and key page hierarchy updates before changing production code.

**Tech Stack:** React 18, TypeScript, Material UI v5, React Query, Jest, Testing Library, Vite

---

## Required References

- `docs/dev/frontend-design-checklist.md`
- `docs/dev/frontend-theme-reference.md`
- `docs/superpowers/specs/2026-03-30-frontend-bold-redesign-design.md`

Use these as hard constraints while implementing and verifying this plan.

## File Map

- Modify: `frontend/src/theme.ts` - expand semantic tokens, typography contrast, shared component treatments
- Modify: `frontend/src/theme.d.ts` - type new semantic token fields
- Modify: `frontend/src/components/layout/AppShell.tsx` - apply stronger shell framing and background composition
- Modify: `frontend/src/components/NavBar.tsx` - strengthen active-state and shell personality
- Modify: `frontend/src/components/layout/PageHeader.tsx` - support stronger title/meta treatment
- Modify: `frontend/src/components/layout/ContentSection.tsx` - support more intentional section framing
- Modify: `frontend/src/pages/Dashboard.tsx` - build scraper-led hero and stronger activity hierarchy
- Modify: `frontend/src/pages/Health.tsx` - replace equal-weight summary cards with clearer readiness composition
- Modify: `frontend/src/pages/Search.tsx` - make search feel more guided and selected-result aware
- Modify: `frontend/src/pages/Playlist.tsx` - emphasize download/share path and simplify guidance
- Modify: `frontend/src/__tests__/theme.test.tsx` - assert expanded semantic token contract and updated shared defaults
- Modify: `frontend/src/__tests__/layoutPrimitives.test.tsx` - assert stronger shared shell and primitive presentation rules
- Modify: `frontend/src/__tests__/NavBarResponsive.test.tsx` - assert shell/navigation visual contract without breaking responsive behavior
- Modify: `frontend/src/__tests__/Dashboard.test.tsx` - assert scraper-led hero hierarchy and supporting section behavior
- Modify: `frontend/src/__tests__/SupportingPages.test.tsx` - assert updated Health, Search, Playlist, and related shared-page behavior
- Modify: `docs/dev/frontend-design-review-evidence.md` - record verification evidence for touched shared frontend work

## Chunk 1: Shared Theme And Shell

### Task 1: Expand the semantic theme contract for the bolder shell

**Files:**
- Modify: `frontend/src/__tests__/theme.test.tsx`
- Modify: `frontend/src/theme.d.ts`
- Modify: `frontend/src/theme.ts`

**Implementation targets:**
- Add a `shell` token group for shell-specific backgrounds, edge treatments, and active-route emphasis
- Add a `hero` token group for scraper/readiness focal surfaces and emphasis borders
- Keep token keys identical across light and dark themes
- Preserve teal/blue as the base identity and reserve warm accent use for attention/freshness emphasis

- [ ] **Step 1: Write the failing test**

Add test expectations for:

- `theme.appTokens.shell` and `theme.appTokens.hero` existing in both themes
- equal key shape between light and dark themes
- updated `MuiAppBar`, `MuiPaper`, `MuiButton`, and `MuiChip` defaults using the new shell/hero emphasis where appropriate
- preservation of focus-visible and non-color alert emphasis rules

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/theme.test.tsx`
Expected: FAIL because the expanded token keys and shared defaults do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add the new semantic token fields in `frontend/src/theme.d.ts` and implement matching light/dark token sets plus shared component styling in `frontend/src/theme.ts`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/theme.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

### Task 2: Strengthen shell, nav, and shared layout primitives

**Files:**
- Modify: `frontend/src/__tests__/layoutPrimitives.test.tsx`
- Modify: `frontend/src/__tests__/NavBarResponsive.test.tsx`
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/components/NavBar.tsx`
- Modify: `frontend/src/components/layout/PageHeader.tsx`
- Modify: `frontend/src/components/layout/ContentSection.tsx`

**Implementation targets:**
- `AppShell` should render a more intentional operational frame through background layering and stronger content-stage separation
- `NavBar` should make the active route clearly more decisive without hurting keyboard order or mobile behavior
- `PageHeader` should support stronger title/meta contrast and preserve primary-actions-first responsive order
- `ContentSection` should feel less like a generic repeated card while keeping section semantics and action layout intact

- [ ] **Step 1: Write the failing tests**

Update tests so they explicitly expect:

- changed shell/nav surface styling through semantic token-backed styles
- preserved `banner`, `main`, and region semantics
- preserved keyboard reachability order for nav and top actions
- stronger but still responsive header and section presentation
- a shell content stage with visible separation from the canvas
- a selected nav item style that is visually stronger than hover state and still token-driven
- page-header and content-section wrappers that keep primary actions first on phones

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx src/__tests__/NavBarResponsive.test.tsx`
Expected: FAIL because the stronger shell and primitive contract is not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Update `AppShell`, `NavBar`, `PageHeader`, and `ContentSection` to reflect the new measured-bold operational shell while preserving responsive and accessibility behavior.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx src/__tests__/NavBarResponsive.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 2: Page-Level Hierarchy Upgrades

### Task 3: Rebuild Dashboard around a scraper-led hero

**Files:**
- Modify: `frontend/src/__tests__/Dashboard.test.tsx`
- Modify: `frontend/src/pages/Dashboard.tsx`

**Implementation targets:**
- The dominant hero must answer: what is the scraper state, how fresh is it, what limits it, and what should the user do next?
- Supporting readiness data such as WARP, streams, and scheduler timing should remain visible but subordinate to the hero decision path
- Recent activity should read like a live feed rather than a generic list block

- [ ] **Step 1: Write the failing test**

Update dashboard tests to expect:

- a hero heading or label centered on scraper/readiness language
- explicit non-color labels such as freshness, next run, or attention needed
- plain-language next-step guidance in the dominant dashboard surface
- recent activity remaining present with stronger live-feed framing
- at least one dedicated heading or status label for scraper activity that is more prominent than the supporting metrics
- WARP/stream/task data still present but no longer rendered as three equal-weight hero metrics

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/Dashboard.test.tsx`
Expected: FAIL because the existing dashboard still uses the older generic readiness layout.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Dashboard.tsx` to create the new hero composition and supporting sections using existing shared primitives.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/Dashboard.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

### Task 4: Upgrade Health composition

**Files:**
- Create: `frontend/src/__tests__/HealthBoldLayout.test.tsx`
- Modify: `frontend/src/pages/Health.tsx`

**Implementation targets:**
- Health should prioritize readiness summary over equal-weight statistic cards
- The primary state should answer whether the system is ready, what is limiting it, and what the user should check next

- [ ] **Step 1: Write the failing test**

Create a focused Health test that expects:

- a dominant readiness summary heading or alert near the top of the page
- plain-language next-step guidance when status is healthy or degraded
- system totals rendered as supporting information rather than three visually equivalent top-level summary cards

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/HealthBoldLayout.test.tsx`
Expected: FAIL because Health still uses the older lower-contrast layout.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Health.tsx` so readiness and next-step guidance dominate the page hierarchy.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/HealthBoldLayout.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

### Task 5: Upgrade Search composition

**Files:**
- Create: `frontend/src/__tests__/SearchBoldLayout.test.tsx`
- Modify: `frontend/src/pages/Search.tsx`

**Implementation targets:**
- Search should feel like a guided acquisition workflow
- Query input and primary search action should be visually dominant
- Selection momentum and batch-add state should be clearer without breaking table accessibility

- [ ] **Step 1: Write the failing test**

Create a focused Search test that expects:

- a visually dominant search action area with plain-language helper copy
- selected-result feedback that exposes how many items are selected before batch add
- the results table still uses accessible checkbox and button controls
- an empty-results message that tells the user what to try next

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/SearchBoldLayout.test.tsx`
Expected: FAIL because Search still uses the older low-contrast form-plus-table composition.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Search.tsx` so the search-and-add path is the clear primary workflow and secondary detail remains subordinate.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/SearchBoldLayout.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

### Task 6: Upgrade Playlist composition

**Files:**
- Create: `frontend/src/__tests__/PlaylistBoldLayout.test.tsx`
- Modify: `frontend/src/pages/Playlist.tsx`

**Implementation targets:**
- Playlist should make download/share the clearest action path
- Advanced options should remain clearly optional
- Redundant how-to copy should be reduced while preserving necessary setup guidance

- [ ] **Step 1: Write the failing test**

Create a focused Playlist test that expects:

- the download/share path to appear before advanced options in the main reading order
- advanced options to remain clearly optional
- the page to reduce redundant step-by-step copy while preserving one setup warning or requirement
- the primary action buttons to remain visible and usable on narrow widths

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/PlaylistBoldLayout.test.tsx`
Expected: FAIL because Playlist still uses the older flatter instructional layout.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Playlist.tsx` so the primary path feels more productized and advanced controls remain visually secondary.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/PlaylistBoldLayout.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 3: Verification And Evidence

### Task 7: Record review evidence and run final verification

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`

- [ ] **Step 1: Write the evidence note template**

Record the verification matrix with these exact checks:

- light theme on `/`, `/health`, `/search`, and `/playlist`
- dark theme on `/`, `/health`, `/search`, and `/playlist`
- one phone-width check at `375px`
- one desktop-width check at `1280px`
- keyboard path for top nav, dashboard primary actions, and one page-level primary action on Search or Playlist
- touched loading, empty, warning/error, and success-feedback states where testable from the current mocked flows

Expected outcomes for the evidence note:

- `375px`: no loss of primary actions, no clipped dominant hero copy, and advanced controls remain reachable
- `1280px`: one dominant focal area is clearly visible on each touched page
- keyboard path: visible focus ring on nav toggle or first nav item, then on dashboard primary action, then on one page-level primary action
- loading state: status text appears alongside progress indicator where implemented
- empty state: Search or activity surfaces explain what is missing and what to do next
- warning/error state: Health or Dashboard warns in plain language, not only through color
- success-feedback state: existing Snackbar/alert feedback remains readable in the redesign

- [ ] **Step 2: Run targeted verification**

Run: `npm test -- --runInBand src/__tests__/theme.test.tsx src/__tests__/layoutPrimitives.test.tsx src/__tests__/NavBarResponsive.test.tsx src/__tests__/Dashboard.test.tsx src/__tests__/HealthBoldLayout.test.tsx src/__tests__/SearchBoldLayout.test.tsx src/__tests__/PlaylistBoldLayout.test.tsx src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 3: Run full frontend verification**

Run: `npm test -- --runInBand && npm run build`
Expected: All tests pass and the production build succeeds.

- [ ] **Step 4: Confirm final diff matches the design scope**

Run: `git diff -- frontend/src/theme.ts frontend/src/theme.d.ts frontend/src/components/layout/AppShell.tsx frontend/src/components/NavBar.tsx frontend/src/components/layout/PageHeader.tsx frontend/src/components/layout/ContentSection.tsx frontend/src/pages/Dashboard.tsx frontend/src/pages/Health.tsx frontend/src/pages/Search.tsx frontend/src/pages/Playlist.tsx frontend/src/__tests__/theme.test.tsx frontend/src/__tests__/layoutPrimitives.test.tsx frontend/src/__tests__/NavBarResponsive.test.tsx frontend/src/__tests__/Dashboard.test.tsx frontend/src/__tests__/HealthBoldLayout.test.tsx frontend/src/__tests__/SearchBoldLayout.test.tsx frontend/src/__tests__/PlaylistBoldLayout.test.tsx frontend/src/__tests__/SupportingPages.test.tsx docs/dev/frontend-design-review-evidence.md`
Expected: Only scoped bold-redesign changes appear.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.
