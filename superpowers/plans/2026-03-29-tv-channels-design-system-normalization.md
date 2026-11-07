# TV Channels Design System Normalization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Normalize the responsive `TVChannels` workflow and its shared shell/layout surfaces so they match the frontend design-system standards more closely without changing routes or core workflows.

**Architecture:** Tighten the shared theme/layout contract first, then normalize the reusable filter and inventory surfaces, then update the page-level CRUD interactions and verification coverage. Keep the existing responsive shell and page primitives, but remove page-local layout duplication and replace browser-native interaction outliers with MUI-based flows.

**Tech Stack:** React, TypeScript, Material UI, MUI Data Grid, React Testing Library, Jest, npm, Markdown

---

## Skill Application Map

- `@superpowers/test-driven-development` - required for every behavior change
- `@adapt` - required while changing phone/desktop/wide-desktop behavior
- `@normalize` - required while aligning layout, filters, dialogs, and inventory surfaces to shared patterns
- `@superpowers/verification-before-completion` - required before final sign-off

## File Structure

- Modify: `frontend/src/theme.ts` - clarify wide-content shell token naming while preserving the responsive threshold model
- Modify: `frontend/src/theme.d.ts` - keep the theme type contract aligned with the shell token changes
- Modify: `frontend/src/styles/layout.ts` - expose a reusable page split-layout helper instead of page-local wide grid values
- Modify: `frontend/src/components/AdvancedSearch.tsx` - normalize responsive filter layout, spacing, and action hierarchy for shared use
- Modify: `frontend/src/components/TVChannelsTable.tsx` - normalize the desktop container, mobile summaries, and semantic metadata/status treatment
- Modify: `frontend/src/pages/TVChannels.tsx` - consume the shared layout helper, strengthen filter guidance, and replace browser confirm with a design-system dialog
- Modify: `frontend/src/__tests__/layoutPrimitives.test.tsx` - cover the clarified shell contract and shared split-layout helper
- Modify: `frontend/src/__tests__/TVChannelsTable.test.tsx` - cover the richer mobile summary and normalized desktop container behavior
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` - cover filter guidance, shared split layout, and delete-confirmation behavior
- Modify: `docs/dev/frontend-design-review-evidence.md` - append concise verification evidence for the normalization pass
- Reference: `docs/dev/frontend-design-checklist.md`
- Reference: `docs/dev/frontend-theme-reference.md`
- Reference: `docs/superpowers/specs/2026-03-29-tv-channels-design-system-normalization-design.md`

## Command Conventions

- Run targeted and full frontend checks from `frontend/`.
- Use targeted Jest runs during TDD before broader verification.
- Do not commit unless the user explicitly asks for a commit.

## Chunk 1: Shared Layout Contract

### Task 1: Clarify wide shell tokens and add a reusable split-layout helper

**Files:**
- Modify: `frontend/src/theme.ts`
- Modify: `frontend/src/theme.d.ts`
- Modify: `frontend/src/styles/layout.ts`
- Modify: `frontend/src/__tests__/layoutPrimitives.test.tsx`

- [ ] **Step 1: Write the failing layout tests**

Add focused tests to `frontend/src/__tests__/layoutPrimitives.test.tsx` that verify:

- the shell layout contract exposes `standardContentMaxWidth` and `wideContentMaxWidth`
- the old ambiguous `contentMaxWidth` path is no longer the contract the helpers depend on
- a new shared helper returns the expected grid styles for `primary`/`supporting` wide-layout pages

- [ ] **Step 2: Run the targeted layout tests and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/layoutPrimitives.test.tsx
```

Expected: FAIL because the helper/token contract is not implemented yet.

- [ ] **Step 3: Implement the minimal shared layout contract**

Update the shell token names in `frontend/src/theme.ts` and `frontend/src/theme.d.ts`, then add a reusable page split-layout helper in `frontend/src/styles/layout.ts` that `TVChannels` can consume directly.

- [ ] **Step 4: Re-run the targeted layout tests and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/layoutPrimitives.test.tsx
```

Expected: PASS.

## Chunk 2: Shared Filter And Inventory Surface Normalization

### Task 2: Normalize `AdvancedSearch` for shared operational filter sections

**Files:**
- Modify: `frontend/src/components/AdvancedSearch.tsx`
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`

- [ ] **Step 1: Write the failing page-level filter tests**

Extend `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` so the phone-flow test also verifies:

- filter guidance text is present
- the filter section keeps `Apply` and `Reset` visible with clear hierarchy after expansion
- the filter form still renders as a stable shared component in the `TVChannels` page context

- [ ] **Step 2: Run the page-level test file and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: FAIL because the guidance/layout changes are not present yet.

- [ ] **Step 3: Implement the minimal filter normalization**

Update `frontend/src/components/AdvancedSearch.tsx` to use a more consistent responsive layout, semantic spacing, and a stronger action row while keeping the public API compatible with `TVChannels` and `AcestreamChannels`.

- [ ] **Step 4: Re-run the page-level test file and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: PASS.

### Task 3: Normalize `TVChannelsTable` desktop and mobile inventory surfaces

**Files:**
- Modify: `frontend/src/components/TVChannelsTable.tsx`
- Modify: `frontend/src/__tests__/TVChannelsTable.test.tsx`

- [ ] **Step 1: Write the failing table tests**

Extend `frontend/src/__tests__/TVChannelsTable.test.tsx` so it verifies:

- mobile summaries include secondary metadata such as language/country when present
- the desktop data grid sits inside a semantic inventory container
- status treatment remains text-explicit and action labels stay accessible

- [ ] **Step 2: Run the table test file and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsTable.test.tsx
```

Expected: FAIL because the richer surface normalization is not implemented yet.

- [ ] **Step 3: Implement the minimal inventory normalization**

Update `frontend/src/components/TVChannelsTable.tsx` so the mobile summaries feel more native to the design system and the desktop grid is wrapped/styled as a semantic inventory panel without changing the overall workflow.

- [ ] **Step 4: Re-run the table test file and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsTable.test.tsx
```

Expected: PASS.

## Chunk 3: TV Channels Page Normalization

### Task 4: Consume shared layout helpers and strengthen filter guidance on `TVChannels`

**Files:**
- Modify: `frontend/src/pages/TVChannels.tsx`
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`

- [ ] **Step 1: Write the failing page layout tests**

Extend `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` so it verifies:

- `TVChannels` uses the shared split-layout helper rather than page-local wide-grid values
- the filters section includes a short plain-language description
- the inventory section remains the primary region in wide-desktop mode

- [ ] **Step 2: Run the page-level test file and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: FAIL because the page still owns its grid styles directly.

- [ ] **Step 3: Implement the minimal page layout normalization**

Update `frontend/src/pages/TVChannels.tsx` to consume the shared split-layout helper and present clearer filter guidance without changing the page's route or main actions.

- [ ] **Step 4: Re-run the page-level test file and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: PASS.

### Task 5: Replace browser-native delete confirmation with a theme-consistent dialog

**Files:**
- Modify: `frontend/src/pages/TVChannels.tsx`
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`

- [ ] **Step 1: Write the failing delete-confirmation test**

Add a focused test in `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` that:

- opens the delete action from the page context
- verifies a confirmation dialog appears with plain-language guidance
- confirms delete only fires after the explicit destructive action

- [ ] **Step 2: Run the page-level test file and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: FAIL because the page still uses `window.confirm(...)`.

- [ ] **Step 3: Implement the minimal confirmation-dialog flow**

Replace `window.confirm(...)` with a MUI `Dialog` in `frontend/src/pages/TVChannels.tsx`, keep the copy concise and explicit, and preserve the success/error notice behavior after the mutation resolves.

- [ ] **Step 4: Re-run the page-level test file and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: PASS.

### Task 6: Normalize create/edit dialog grouping and mobile-safe form structure

**Files:**
- Modify: `frontend/src/pages/TVChannels.tsx`
- Modify: `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx`

- [ ] **Step 1: Write the failing dialog-structure test**

Extend `frontend/src/__tests__/TVChannelsPageResponsive.test.tsx` so it verifies:

- create and edit dialogs stay full-screen on phone
- the dialog content exposes clear grouped headings or section labels for the form structure
- the primary submit action remains visible and the field set still includes the existing key inputs

- [ ] **Step 2: Run the page-level test file and verify RED**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: FAIL because the dialogs are still one undifferentiated field stack.

- [ ] **Step 3: Implement the minimal dialog normalization**

Update `frontend/src/pages/TVChannels.tsx` so the create/edit dialogs keep the current field coverage but introduce clearer grouped structure, more consistent spacing, and mobile-safe form layout using existing MUI primitives.

- [ ] **Step 4: Re-run the page-level test file and verify GREEN**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: PASS.

## Chunk 4: Verification And Evidence

### Task 7: Run the required checks and record evidence

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`

- [ ] **Step 1: Add a new evidence section**

Append a `## TV Channels Design System Normalization` section to `docs/dev/frontend-design-review-evidence.md` covering light theme, dark theme, phone width, desktop width, wide desktop width, keyboard path, and guided CRUD flow.

- [ ] **Step 2: Run the targeted Jest files**

Run:

```bash
CI=true npm test -- --runInBand --watch=false src/__tests__/layoutPrimitives.test.tsx src/__tests__/TVChannelsTable.test.tsx src/__tests__/TVChannelsPageResponsive.test.tsx
```

Expected: PASS.

- [ ] **Step 3: Run TypeScript verification**

Run:

```bash
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 4: Run the full frontend test suite**

Run:

```bash
CI=true npm test -- --watch=false
```

Expected: PASS.

- [ ] **Step 5: Run the production build**

Run:

```bash
npm run build
```

Expected: PASS.

- [ ] **Step 6: Fill in the evidence section with real results**

Record the exact verification method, result, and notes from the completed checks.

## Final Execution Notes

- Keep `AdvancedSearch` API-compatible with both current consumers.
- Do not spread the delete-confirmation refactor to unrelated pages in this pass.
- Keep changes grounded in semantic theme tokens and shared layout helpers instead of introducing page-local constants.
- Do not commit unless the user explicitly asks for it.
