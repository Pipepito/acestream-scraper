# Frontend Bold Redesign Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the measured-bold operational redesign to `EPG`, `WARP`, and `Settings` so these pages match the stronger shell, clearer hierarchy, and explicit next-step guidance established in phase 1.

**Architecture:** Reuse the shared `shell` and `hero` token system already added in phase 1, then apply page-specific focal surfaces and stronger action-led hierarchy to the remaining operational pages. Drive the work with focused tests per page so each redesign remains independently verifiable and does not blur into a single large regression cycle.

**Tech Stack:** React 18, TypeScript, Material UI v5, React Query, Jest, Testing Library, Vite

---

## Required References

- `docs/dev/frontend-design-checklist.md`
- `docs/dev/frontend-theme-reference.md`
- `docs/superpowers/specs/2026-03-30-frontend-bold-redesign-design.md`
- `docs/superpowers/plans/2026-03-30-frontend-bold-redesign.md`

## File Map

- Modify: `frontend/src/pages/EPG.tsx`
- Modify: `frontend/src/pages/WARP.tsx`
- Modify: `frontend/src/pages/Settings.tsx`
- Modify: `frontend/src/__tests__/EPG.test.tsx`
- Modify: `frontend/src/__tests__/SupportingPages.test.tsx`
- Create: `frontend/src/__tests__/WarpBoldLayout.test.tsx`
- Create: `frontend/src/__tests__/SettingsBoldLayout.test.tsx`
- Modify: `docs/dev/frontend-design-review-evidence.md`

## Chunk 1: EPG Hero And Workflow Hierarchy

### Task 1: Make EPG feel like an operational source-control page

**Files:**
- Modify: `frontend/src/__tests__/EPG.test.tsx`
- Modify: `frontend/src/pages/EPG.tsx`

- [ ] **Step 1: Write the failing test**

Update `frontend/src/__tests__/EPG.test.tsx` to expect:

- a top-level hero label or summary focused on source readiness and matching momentum
- plain-language next-step guidance for adding sources, checking inventory, or generating XML
- stronger non-color labels for source count, unmapped channels, or output readiness

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/EPG.test.tsx`
Expected: FAIL because `EPG` still uses the older flatter section structure without the new focal summary.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/EPG.tsx` so the page opens with a measured-bold operational summary that helps the user understand whether sources are ready, what matching work remains, and where to go next.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/EPG.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 2: WARP And Settings Hero Surfaces

### Task 2: Give WARP a stronger connection-readiness hero

**Files:**
- Create: `frontend/src/__tests__/WarpBoldLayout.test.tsx`
- Modify: `frontend/src/pages/WARP.tsx`

- [ ] **Step 1: Write the failing test**

Create a focused WARP test that expects:

- a dominant connection-readiness hero near the top of the page
- explicit labels for current protection state, next step, and mode/account context
- the connect/disconnect path to remain clearly primary and responsive

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/WarpBoldLayout.test.tsx`
Expected: FAIL because `WARP` still uses the older lower-contrast status section.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/WARP.tsx` to emphasize tunnel readiness, next-step guidance, and connection state without losing the existing management controls.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/WarpBoldLayout.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

### Task 3: Give Settings a stronger control-center summary

**Files:**
- Create: `frontend/src/__tests__/SettingsBoldLayout.test.tsx`
- Modify: `frontend/src/pages/Settings.tsx`
- Modify: `frontend/src/__tests__/SupportingPages.test.tsx`

- [ ] **Step 1: Write the failing test**

Create a focused Settings test that expects:

- a top summary explaining the role of Settings in plain language
- explicit guidance for the engine status path and the highest-priority settings actions
- the appearance and automation controls to stay readable but secondary to the main connection summary

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --runInBand src/__tests__/SettingsBoldLayout.test.tsx src/__tests__/SupportingPages.test.tsx`
Expected: FAIL because `Settings` still opens with standard sections only.

- [ ] **Step 3: Write minimal implementation**

Refactor `frontend/src/pages/Settings.tsx` to add a measured-bold summary surface and stronger action-led hierarchy while preserving existing flows and accessibility.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --runInBand src/__tests__/SettingsBoldLayout.test.tsx src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.

## Chunk 3: Verification And Evidence

### Task 4: Record phase-2 evidence and run verification

**Files:**
- Modify: `docs/dev/frontend-design-review-evidence.md`

- [ ] **Step 1: Update evidence notes**

Record verification for:

- light and dark theme checks on `/epg`, `/warp`, and `/settings`
- one phone-width and one desktop-width check
- keyboard path through a primary action or key control on each touched page
- loading, warning/error, and success-feedback states where applicable

- [ ] **Step 2: Run targeted verification**

Run: `npm test -- --runInBand src/__tests__/EPG.test.tsx src/__tests__/WarpBoldLayout.test.tsx src/__tests__/SettingsBoldLayout.test.tsx src/__tests__/SupportingPages.test.tsx`
Expected: PASS.

- [ ] **Step 3: Run full verification**

Run: `npm test -- --runInBand && npm run build`
Expected: All tests pass and the production build succeeds.

- [ ] **Step 4: Review scoped diff**

Run: `git diff -- frontend/src/pages/EPG.tsx frontend/src/pages/WARP.tsx frontend/src/pages/Settings.tsx frontend/src/__tests__/EPG.test.tsx frontend/src/__tests__/WarpBoldLayout.test.tsx frontend/src/__tests__/SettingsBoldLayout.test.tsx frontend/src/__tests__/SupportingPages.test.tsx docs/dev/frontend-design-review-evidence.md docs/superpowers/plans/2026-03-30-frontend-bold-redesign-phase-2.md`
Expected: Only phase-2 measured-bold changes appear.

- [ ] **Step 5: Commit**

Do not commit unless the user explicitly asks.
