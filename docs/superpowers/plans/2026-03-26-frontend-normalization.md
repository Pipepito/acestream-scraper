# Frontend Normalization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Normalize the frontend into one coherent operational design system across shared foundations, dense operational routes, and supporting pages.

**Architecture:** Execute normalization in three phases. First make theme and shared primitives trustworthy, then refactor the highest-risk dense operational flows onto those shared patterns, then migrate dashboard and supporting pages so the whole app reads as one product. Preserve existing MUI and route structure, but move touched screens onto semantic tokens, shared headers/sections, accessible state patterns, and mobile-safe layouts.

**Tech Stack:** React, TypeScript, Material UI, React Query, React Router, Jest, React Testing Library, npm

---

## File Structure

- Modify: `frontend/src/theme.ts` - complete theme-mode plumbing, semantic token defaults, shared component polish, and reduced-motion-safe defaults
- Modify: `frontend/src/index.tsx` - provide real light/dark theme wiring
- Modify: `frontend/src/styles/layout.ts` - align layout constants with semantic theme usage or remove redundant values
- Modify: `frontend/src/components/layout/PageHeader.tsx` - standardize header rhythm, description, and actions wrapping
- Modify: `frontend/src/components/layout/ContentSection.tsx` - standardize section rhythm, title, description, actions, and bounded dense containers
- Modify: `frontend/src/components/layout/AppShell.tsx` - consume semantic layout/theme values only
- Modify: `frontend/src/components/NavBar.tsx` - normalize navigation action states and theme behavior
- Modify: `frontend/src/components/QuickEditDialog.tsx` - replace native checkbox usage and timer-based success handling
- Modify: `frontend/src/components/BulkOperations.tsx` - remove viewport reads, normalize actions/state layout, and improve accessibility
- Modify: `frontend/src/components/BatchAssignDialog.tsx` - remove viewport reads and normalize dialog behavior
- Modify: `frontend/src/components/EPGProgramsTable.tsx` - normalize loading/empty states and mobile-safe dense data container
- Modify: `frontend/src/components/ChannelTable.tsx` - improve action density, labels, and responsive row behavior
- Modify: `frontend/src/components/TVChannelsTable.tsx` - improve action density and responsive row behavior
- Modify: `frontend/src/pages/EPG.tsx` - rebuild around shared headers/sections and clearer operational grouping
- Modify: `frontend/src/pages/EPGChannelDetail.tsx` - normalize overview, tab linkage, selection flows, and table structure
- Modify: `frontend/src/pages/TVChannelDetail.tsx` - normalize detail hierarchy, selection patterns, and actions
- Modify: `frontend/src/pages/Search.tsx` - normalize search workflow and dense result presentation
- Modify: `frontend/src/pages/Dashboard.tsx` - replace generic metric/card layout with clearer operational sections
- Modify: `frontend/src/pages/Health.tsx` - normalize hierarchy and status treatment
- Modify: `frontend/src/pages/Playlist.tsx` - normalize copy, layout, and progressive disclosure of advanced controls
- Modify: `frontend/src/pages/Settings.tsx` - move to shared header/section patterns
- Modify: `frontend/src/pages/WARP.tsx` - move to shared header/section patterns and clearer status/action grouping
- Modify: `frontend/src/pages/NotFound.tsx` - align with shared page structure and responsive behavior
- Modify: `docs/dev/frontend-design-review-evidence.md` - record method/result/notes for light/dark, mobile/desktop, keyboard, reduced-motion, and state checks
- Test: `frontend/src/__tests__/theme.test.tsx`
- Test: `frontend/src/__tests__/index.test.tsx`
- Test: `frontend/src/__tests__/layoutPrimitives.test.tsx`
- Test: `frontend/src/__tests__/BulkOperations.test.tsx`
- Test: `frontend/src/__tests__/QuickEditDialog.test.tsx`
- Test: `frontend/src/__tests__/EPGProgramsTable.test.tsx`
- Create or modify focused page tests as needed under `frontend/src/__tests__/`

## Chunk 1: Shared Foundation Normalization

### Task 1: Wire real theme-mode support and shared layout defaults

**Files:**
- Modify: `frontend/src/theme.ts`
- Modify: `frontend/src/index.tsx`
- Modify: `frontend/src/styles/layout.ts`
- Test: `frontend/src/__tests__/theme.test.tsx`
- Test: `frontend/src/__tests__/index.test.tsx`

- [ ] **Step 1: Write the failing tests for theme-mode plumbing**

Add focused tests that verify:
- both `light` and `dark` themes can be created and expose the same semantic token keys
- the app bootstrap can render with a theme provider that is not hard-coded to one static export
- touched shared component defaults expose a visible focus treatment and do not rely on color alone for status emphasis

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `CI=true npm test -- --watch=false theme.test.tsx index.test.tsx`

- [ ] **Step 3: Implement minimal theme-mode plumbing**

Add a theme factory/use-mode path in `frontend/src/index.tsx`, keep light mode as the default initial mode, and make the provider consume the factory output. In `frontend/src/theme.ts`, remove leftover decorative drift that conflicts with the design spec and ensure shared component defaults consume semantic tokens consistently.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `CI=true npm test -- --watch=false theme.test.tsx index.test.tsx`

- [ ] **Step 5: Refactor layout constant usage without changing behavior beyond normalization**

Reduce or remove redundant layout constants so shell/layout values come from semantic theme tokens or one clearly subordinate helper.


### Task 2: Normalize shared shell, header, and section primitives

**Files:**
- Modify: `frontend/src/components/layout/PageHeader.tsx`
- Modify: `frontend/src/components/layout/ContentSection.tsx`
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/components/NavBar.tsx`
- Test: `frontend/src/__tests__/layoutPrimitives.test.tsx`

- [ ] **Step 1: Write the failing tests for shared primitive behavior**

Cover:
- header/section actions wrap correctly at narrow widths
- dark and light themes both render shared primitives with the same semantic structure
- navigation selected states remain readable in both themes

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `CI=true npm test -- --watch=false layoutPrimitives.test.tsx`

- [ ] **Step 3: Implement the normalized shared primitives**

Bring all shell/header/section/navigation surfaces onto the semantic layout and action contract, using left-aligned operational hierarchy, restrained shadow/effect usage, and mobile-safe action wrapping.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `CI=true npm test -- --watch=false layoutPrimitives.test.tsx`


### Task 3: Normalize reusable dialogs and dense shared components

**Files:**
- Modify: `frontend/src/components/QuickEditDialog.tsx`
- Modify: `frontend/src/components/BulkOperations.tsx`
- Modify: `frontend/src/components/BatchAssignDialog.tsx`
- Modify: `frontend/src/components/EPGProgramsTable.tsx`
- Test: `frontend/src/__tests__/QuickEditDialog.test.tsx`
- Test: `frontend/src/__tests__/BulkOperations.test.tsx`
- Test: `frontend/src/__tests__/EPGProgramsTable.test.tsx`

- [ ] **Step 1: Write the failing tests for dialog normalization**

Add or update tests for:
- responsive fullscreen logic using theme breakpoints rather than viewport reads
- accessible form controls instead of native checkbox markup
- no auto-close timing dependency for success state where behavior changes
- explicit loading/empty state copy where needed
- semantic motion or reduced-motion-safe behavior for touched feedback transitions
- loading, success, and error states that are announced or described clearly enough for screen-reader users

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `CI=true npm test -- --watch=false QuickEditDialog.test.tsx BulkOperations.test.tsx EPGProgramsTable.test.tsx`

- [ ] **Step 3: Implement the normalized shared dialog/component behavior**

Use MUI controls consistently, remove `window.innerWidth` checks, improve status messaging, and align layout/action hierarchy with the shared design system.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run: `CI=true npm test -- --watch=false QuickEditDialog.test.tsx BulkOperations.test.tsx EPGProgramsTable.test.tsx`

## Chunk 2: Dense Operational Pages

### Task 4: Normalize EPG management and EPG channel detail

**Files:**
- Modify: `frontend/src/pages/EPG.tsx`
- Modify: `frontend/src/pages/EPGChannelDetail.tsx`
- Modify: `frontend/src/components/EPGProgramsTable.tsx`
- Test: create or modify focused EPG page tests under `frontend/src/__tests__/`

- [ ] **Step 1: Write the failing tests for EPG structure and accessibility**

Cover:
- page renders shared header/section structure
- tabs have proper linkage
- key icon buttons expose accessible names
- selection flows expose explicit keyboard-operable controls
- touched status treatments retain text/icon cues and visible focus behavior rather than relying only on color

- [ ] **Step 2: Run the focused tests to verify they fail**

Run the targeted EPG page tests only.

- [ ] **Step 3: Implement normalized EPG layouts and interaction patterns**

Shift the routes to top-down operational sections, reduce nested surfaces, improve summaries/filters/action grouping, and keep dense data inside clearer containers.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run the targeted EPG page tests only.


### Task 5: Normalize TV channel detail and search flows

**Files:**
- Modify: `frontend/src/pages/TVChannelDetail.tsx`
- Modify: `frontend/src/pages/Search.tsx`
- Modify: `frontend/src/components/ChannelTable.tsx`
- Modify: `frontend/src/components/TVChannelsTable.tsx`
- Test: create or modify focused page/component tests under `frontend/src/__tests__/`

- [ ] **Step 1: Write the failing tests for dense data interaction quality**

Cover:
- shared page structure and section ordering
- explicit accessible names for row actions
- reduced row-action density or clearer action grouping
- mobile-safe layout behavior for the primary content containers
- visible focus treatment, non-color status cues, and acceptable contrast on touched dense action surfaces

- [ ] **Step 2: Run the focused tests to verify they fail**

Run the targeted TV/detail/search tests only.

- [ ] **Step 3: Implement the normalized dense data flows**

Adopt shared headers/sections, improve details-first hierarchy, reduce action clutter, and make the result surfaces scanable and touch-safe.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run the targeted TV/detail/search tests only.

## Chunk 3: Dashboard And Supporting Pages

### Task 6: Normalize dashboard, health, playlist, settings, WARP, and not-found pages

**Files:**
- Modify: `frontend/src/pages/Dashboard.tsx`
- Modify: `frontend/src/pages/Health.tsx`
- Modify: `frontend/src/pages/Playlist.tsx`
- Modify: `frontend/src/pages/Settings.tsx`
- Modify: `frontend/src/pages/WARP.tsx`
- Modify: `frontend/src/pages/NotFound.tsx`
- Test: create or modify focused page tests under `frontend/src/__tests__/`

- [ ] **Step 1: Write the failing tests for shared page skeleton adoption**

Cover:
- `PageHeader` and `ContentSection` usage for the primary page structure
- clearer status and action grouping on at least one dashboard/supporting route
- responsive rendering of the main action path
- visible focus treatment, non-color status cues, and acceptable contrast on touched status surfaces

- [ ] **Step 2: Run the focused tests to verify they fail**

Run the targeted supporting page tests only.

- [ ] **Step 3: Implement normalized supporting page layouts**

Replace generic hero-metric/card repetition with clearer operational sections, progressive disclosure where needed, and stronger next-action hierarchy.

- [ ] **Step 4: Run the focused tests to verify they pass**

Run the targeted supporting page tests only.

## Chunk 4: Verification And Review Evidence

### Task 7: Record review evidence and verify the full frontend

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`
- Verify: `frontend/`

- [ ] **Step 1: Update the design review evidence file**

Record method/result/notes for:
- light theme
- dark theme
- reduced motion
- one mobile width
- one desktop width
- one zoom/reflow check on dense pages or shared action areas
- one keyboard path for the primary flow of each touched area, including shared dialogs/components
- visible focus states on touched interactive controls
- contrast and non-color status communication on touched status surfaces
- screen-reader-friendly loading/success/error announcements or descriptive semantics on touched state surfaces
- warm accent usage staying sparse and purposeful on touched surfaces
- loading/empty/warning/error/success states where present

- [ ] **Step 2: Run the frontend lint command**

Run: `CI=true npx eslint "src/**/*.{ts,tsx}"`

- [ ] **Step 3: Run the full frontend test suite**

Run: `CI=true npm test -- --watch=false`

- [ ] **Step 4: Run the frontend build**

Run: `npm run build`

- [ ] **Step 5: Run a TypeScript verification pass**

Run: `npx tsc --noEmit`

- [ ] **Step 6: Review the diff for token drift, motion drift, warm-accent drift, or leftover one-off patterns**

Inspect changed files and remove any raw hex values, page-local timing values, unnecessary warm-accent usage, duplicate status/layout patterns, or unneeded one-off wrappers introduced during implementation.

- [ ] **Step 7: Re-run the verification commands if any cleanup changed code**

Run the same commands again until the final state is verified.
