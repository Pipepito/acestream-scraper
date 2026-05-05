# Shared Foundation And Accessibility Backbone Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire real light/dark theme control into the app, remove duplicated shell page titles, and normalize the highest-risk audited accessibility patterns across shared shell, settings, dialogs, and core detail flows.

**Architecture:** Introduce a small shared theme-mode controller at bootstrap, expose synchronized theme controls in the shell and settings, and keep page context owned by `PageHeader`. Then apply focused accessibility hardening to audited dialogs, selection flows, tab linkage, loading states, and icon-only actions using existing MUI/shared primitives instead of one-off patterns.

**Tech Stack:** React, TypeScript, MUI, React Router, React Query, Jest, Testing Library, Vite

---

## File Map

- Modify: `frontend/src/bootstrap/AppBootstrap.tsx` - own theme-mode persistence, first-run fallback, and context exposure
- Modify: `frontend/src/components/NavBar.tsx` - remove duplicated page title and add shell theme toggle
- Modify: `frontend/src/pages/Settings.tsx` - add canonical appearance/theme control and stronger loading/status treatment
- Modify: `frontend/src/pages/TVChannelDetail.tsx` - normalize loading/status text and keyboard-safe selection behavior in touched detail flow
- Modify: `frontend/src/pages/EPGChannelDetail.tsx` - normalize mapping dialog selection behavior and contextual loading/status states
- Modify: `frontend/src/pages/EPG.tsx` - add stable tab linkage helper usage if tabs are present in current file and preserve explicit icon labels/status copy
- Modify: `frontend/src/pages/Scraper.tsx` - add explicit labels to icon-only row actions
- Modify: `frontend/src/components/BatchAssignDialog.tsx` - replace `window.innerWidth` with responsive hook and remove timer-driven close behavior if touched in this pass
- Modify: `frontend/src/components/BulkOperations.tsx` - replace `window.innerWidth` with responsive hook and improve success/error persistence behavior if touched in this pass
- Modify: `frontend/src/__tests__/layoutPrimitives.test.tsx` - cover shell/app-bar/theme-toggle behavior
- Modify: `frontend/src/__tests__/SupportingPages.test.tsx` - cover settings appearance control and status/loading text
- Create or modify: targeted tests for `EPGChannelDetail`, `TVChannelDetail`, `EPG`, `Scraper`, `BatchAssignDialog`, and `BulkOperations`
- Modify: `docs/dev/frontend-design-review-evidence.md` - append verification evidence for this phase

## Chunk 1: Theme Controller And Shell Hierarchy

### Task 1: Persist real theme mode at bootstrap

**Files:**
- Modify: `frontend/src/bootstrap/AppBootstrap.tsx`
- Test: `frontend/src/__tests__/layoutPrimitives.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- the app theme controller can initialize from saved preference
- first run can fall back to system preference when nothing is saved
- the exposed context still supports `mode`, `setMode`, and `toggleMode`

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx`
Expected: FAIL because persistence/fallback behavior is not implemented yet.

- [ ] **Step 3: Implement minimal bootstrap theme persistence**

Update `frontend/src/bootstrap/AppBootstrap.tsx` to:
- read a stable local storage key on initialization
- fall back to `matchMedia('(prefers-color-scheme: dark)')` only when no saved value exists
- persist explicit `light` / `dark` changes
- keep the user-facing model limited to `light` and `dark`

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx`
Expected: PASS for the new bootstrap-theme tests.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/bootstrap/AppBootstrap.tsx frontend/src/__tests__/layoutPrimitives.test.tsx
git commit -m "feat: persist frontend theme mode"
```

### Task 2: Simplify the top app bar and add the shell theme toggle

**Files:**
- Modify: `frontend/src/components/NavBar.tsx`
- Test: `frontend/src/__tests__/layoutPrimitives.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- the top app bar no longer renders the current page title
- the shell renders a theme toggle control in both light and dark modes
- the phone menu button still appears on narrow widths

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx`
Expected: FAIL because `NavBar` still renders `getNavTitle(location.pathname)` and has no theme toggle.

- [ ] **Step 3: Implement the shell hierarchy cleanup**

Update `frontend/src/components/NavBar.tsx` to:
- remove the top-bar page title text
- keep the app bar as a shell utility strip
- add an accessible theme toggle wired to `useAppThemeMode`
- preserve selected-nav behavior and mobile drawer access

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx`
Expected: PASS for shell hierarchy and theme toggle coverage.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/NavBar.tsx frontend/src/__tests__/layoutPrimitives.test.tsx
git commit -m "refactor: simplify shell app bar hierarchy"
```

## Chunk 2: Canonical Settings Control And Shared Status Pattern

### Task 3: Add canonical theme preference controls in Settings

**Files:**
- Modify: `frontend/src/pages/Settings.tsx`
- Test: `frontend/src/__tests__/SupportingPages.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- `Settings` renders a dedicated appearance/theme section
- the current theme value is visible through an accessible control
- changing the settings control uses the shared theme controller instead of page-local state

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: FAIL because `Settings` currently has no theme preference UI.

- [ ] **Step 3: Implement the appearance section**

Update `frontend/src/pages/Settings.tsx` to:
- add a `ContentSection` for appearance/theme preference
- use the shared bootstrap theme controller
- keep the copy concise and low-technical
- make the control discoverable and synchronized with the shell toggle

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: PASS for the new appearance section.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Settings.tsx frontend/src/__tests__/SupportingPages.test.tsx
git commit -m "feat: add canonical theme settings control"
```

### Task 4: Strengthen touched loading and status messaging in Settings

**Files:**
- Modify: `frontend/src/pages/Settings.tsx`
- Test: `frontend/src/__tests__/SupportingPages.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- the page-level loading state explains what is loading
- the engine-status refresh area uses contextual loading text
- success/error feedback remains textual and actionable

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: FAIL because the top-level settings loading state is spinner-only.

- [ ] **Step 3: Implement the minimal status-treatment normalization**

Update `frontend/src/pages/Settings.tsx` to:
- replace spinner-only loading with a compact status surface
- keep inline engine-status loading explicit
- ensure success/error messages remain readable and non-color-only

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Settings.tsx frontend/src/__tests__/SupportingPages.test.tsx
git commit -m "fix: improve settings loading and status clarity"
```

## Chunk 3: Responsive Dialog Backbone

### Task 5: Replace viewport checks in BatchAssignDialog

**Files:**
- Modify: `frontend/src/components/BatchAssignDialog.tsx`
- Test: `frontend/src/__tests__/SupportingPages.test.tsx` or dedicated dialog test file

- [ ] **Step 1: Write the failing test**

Add a test proving the dialog fullscreen behavior is driven by responsive hooks rather than `window.innerWidth`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: FAIL because the component still uses `window.innerWidth < 600`.

- [ ] **Step 3: Implement minimal responsive dialog logic**

Update `frontend/src/components/BatchAssignDialog.tsx` to:
- use `useTheme` + `useMediaQuery`
- keep success/error messaging visible until the user dismisses or closes the dialog explicitly

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/BatchAssignDialog.tsx frontend/src/__tests__/SupportingPages.test.tsx
git commit -m "fix: make batch assign dialog responsive and persistent"
```

### Task 6: Replace viewport checks in BulkOperations

**Files:**
- Modify: `frontend/src/components/BulkOperations.tsx`
- Test: dedicated dialog test file or `frontend/src/__tests__/SupportingPages.test.tsx`

- [ ] **Step 1: Write the failing test**

Add a test proving the dialog fullscreen behavior is responsive-hook based and success state does not auto-dismiss immediately.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement minimal responsive/hardened dialog behavior**

Update `frontend/src/components/BulkOperations.tsx` to:
- replace `window.innerWidth` with `useMediaQuery`
- remove timer-driven success auto-close
- preserve readable operation result feedback

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/BulkOperations.tsx frontend/src/__tests__/SupportingPages.test.tsx
git commit -m "fix: harden bulk operations dialog behavior"
```

## Chunk 4: Audited Accessibility Flows

### Task 7: Normalize EPG channel mapping selection flow

**Files:**
- Modify: `frontend/src/pages/EPGChannelDetail.tsx`
- Test: create or modify `frontend/src/__tests__/EPGChannelDetail.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- the mapping dialog exposes a keyboard-safe selection control
- loading/error/empty states in the dialog are explicit and contextual
- selected-state semantics remain visible and actionable

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/EPGChannelDetail.test.tsx`
Expected: FAIL because the mapping flow is not yet covered by the normalized accessibility contract.

- [ ] **Step 3: Implement minimal accessible mapping structure**

Update `frontend/src/pages/EPGChannelDetail.tsx` to:
- keep or strengthen a proper radio/list selection pattern
- make the option containers fully keyboard-safe and screen-reader clear
- improve dialog loading/status copy where needed

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/EPGChannelDetail.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EPGChannelDetail.tsx frontend/src/__tests__/EPGChannelDetail.test.tsx
git commit -m "fix: normalize epg channel mapping accessibility"
```

### Task 8: Normalize TV channel detail selection/loading behavior

**Files:**
- Modify: `frontend/src/pages/TVChannelDetail.tsx`
- Test: create or modify `frontend/src/__tests__/TVChannelDetail.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving:
- page loading is announced with contextual text
- touched selection/association flows remain keyboard-safe
- icon-only actions in the touched detail view keep explicit labels

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/TVChannelDetail.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Implement minimal detail-page accessibility improvements**

Update `frontend/src/pages/TVChannelDetail.tsx` to:
- replace weak loading treatment with contextual status text
- preserve or strengthen accessible labels and focus behavior in the touched association flow

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/TVChannelDetail.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/TVChannelDetail.tsx frontend/src/__tests__/TVChannelDetail.test.tsx
git commit -m "fix: harden tv channel detail accessibility states"
```

### Task 9: Complete audited tab linkage

**Files:**
- Modify: `frontend/src/pages/EPG.tsx`
- Modify: `frontend/src/pages/EPGChannelDetail.tsx`
- Test: create or modify corresponding page tests

- [ ] **Step 1: Write the failing tests**

Add tests proving audited tab sets expose matching `id`, `aria-controls`, and `aria-labelledby` pairs.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/EPG*.test.tsx`
Expected: FAIL where linkage is incomplete.

- [ ] **Step 3: Implement minimal stable tab helper or explicit ids**

Update the audited tab sets to use a stable helper or explicit mapping so all tab/panel relationships are complete.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/EPG*.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EPG.tsx frontend/src/pages/EPGChannelDetail.tsx src/__tests__/EPG*.test.tsx
git commit -m "fix: complete epg tab accessibility linkage"
```

### Task 10: Add missing explicit labels to audited icon actions

**Files:**
- Modify: `frontend/src/pages/Scraper.tsx`
- Test: create or modify `frontend/src/__tests__/Scraper.test.tsx`

- [ ] **Step 1: Write the failing tests**

Add tests proving the scrape, edit, and delete icon actions each have explicit accessible names.

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx`
Expected: FAIL because the icon buttons are unlabeled.

- [ ] **Step 3: Implement minimal accessible labeling**

Update `frontend/src/pages/Scraper.tsx` to add action-specific `aria-label` values that include the row target where appropriate.

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm test -- --runInBand src/__tests__/Scraper.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Scraper.tsx frontend/src/__tests__/Scraper.test.tsx
git commit -m "fix: label scraper row actions"
```

## Chunk 5: Verification Evidence And Final Integration

### Task 11: Record frontend review evidence and run integration verification

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`

- [ ] **Step 1: Add concise review evidence**

Append a section covering:
- light theme verification
- dark theme verification
- one phone width
- one desktop width
- one keyboard path through a touched flow
- loading/error/success checks for touched surfaces

- [ ] **Step 2: Run targeted frontend verification**

Run: `npm test -- --runInBand src/__tests__/layoutPrimitives.test.tsx src/__tests__/SupportingPages.test.tsx src/__tests__/Scraper.test.tsx src/__tests__/TVChannelDetail.test.tsx src/__tests__/EPGChannelDetail.test.tsx`
Expected: PASS.

- [ ] **Step 3: Rebuild backend-served frontend assets**

Run: `npm run build:backend`
Expected: PASS with copied assets in `backend/frontend_build`.

- [ ] **Step 4: Commit**

```bash
git add docs/dev/frontend-design-review-evidence.md
git commit -m "docs: record shared foundation accessibility verification"
```

## Chunk 6: Final Review

### Task 12: Final integration pass

**Files:**
- Review only: all touched files in this plan

- [ ] **Step 1: Run a final focused review**

Check that:
- the shell no longer duplicates page titles
- theme controls stay synchronized
- no touched component uses raw colors for reusable UI
- touched dialogs no longer rely on `window.innerWidth`
- touched selection and tab patterns are keyboard-safe and semantically complete

- [ ] **Step 2: Run final verification commands**

Run: `npm test -- --runInBand`
Run: `npm run build:backend`
Expected: PASS, or explicit documentation of any pre-existing unrelated failures.

- [ ] **Step 3: Prepare branch for review**

Use `superpowers:finishing-a-development-branch` after implementation is complete.

Plan complete and saved to `docs/superpowers/plans/2026-03-30-shared-foundation-accessibility-backbone.md`. Ready to execute?
