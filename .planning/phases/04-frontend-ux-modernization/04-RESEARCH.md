# Phase 4: Frontend UX Modernization - Research

**Researched:** 2026-02-27
**Domain:** React + MUI frontend modernization for operator workflows
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Decisions
- Keep existing app functionality while materially improving UI quality and usability.
- Preserve working scraper/business logic behavior; this phase is frontend-focused.
- Maintain canonical root architecture (`backend/`, `frontend/`) introduced in Phase 3.
- Prioritize architecture cleanliness, stability, reliability, and bug reduction.

### UI/Execution Constraints
- Avoid generic/boilerplate UI outcomes; design should feel intentional.
- Keep mobile and constrained-display usability as a first-class requirement.
- Ensure compatibility with current backend v2 API contracts (no ad-hoc shape hacks).

### Deferred to Later Phases
- Multi-arch build/runtime validation belongs to Phase 5.
- Backend performance and DB optimization hardening belongs to Phase 6.
</user_constraints>

## Summary

Phase 4 should modernize the frontend in three focused passes: shell/navigation foundation, core workflow page rework, then responsive/accessibility polish and consistency hardening. The current UI has strong functionality coverage but uneven interaction quality, duplicated patterns, and type hygiene issues (`any`, TODO stubs, debug logging, inconsistent table/filter behaviors). Those are the primary blockers for UI-01..UI-04.

The fastest low-risk approach is to keep React + MUI + react-query stack, introduce a shared UX shell and page primitives, and then migrate high-traffic pages (Dashboard, Acestream Channels, TV Channels, EPG, Scraper) to those primitives with stricter typing and consistent feedback/loading/error states.

### Current Gap Evidence
- `frontend/src/App.tsx` and `frontend/src/components/NavBar.tsx` couple routing/layout and have limited mobile information hierarchy controls.
- Major pages contain mixed quality patterns and debug noise (`console.log`, `any`, TODOs), especially `AcestreamChannels.tsx`, `TVChannels.tsx`, `EPG.tsx`, `Dashboard.tsx`.
- Theme baseline (`frontend/src/theme.ts`) is minimal and does not provide a strong design system contract for spacing, semantic states, or responsive composition.

## Standard Stack

### Core
| Library | Current | Purpose | Why Keep |
|---------|---------|---------|----------|
| react | 18.2.0 | UI runtime | Stable with existing app and test setup |
| @mui/material + @mui/x-data-grid | 5.x / 6.x | UI primitives + dense data workflows | Already deeply integrated across pages |
| react-query | 3.39.3 | async state/query caching | Existing hooks layer uses it consistently |
| react-router-dom | 6.16.0 | app routing | Current routes and deep links already depend on it |

### Supporting
| Library | Current | Purpose | Notes |
|---------|---------|---------|-------|
| date-fns | 2.30.0 | date formatting | Keep for relative/absolute timestamps |
| axios | 1.5.x | HTTP client | Keep centralized in API client/services |

## Architecture Patterns

### Pattern 1: Shell + Page Primitive Standardization
**What:** Introduce a shared app shell contract (header/nav/content/actions) and page-section primitives.
**Why:** Reduces per-page layout drift and accelerates consistent UX changes.

### Pattern 2: Workflow-First Page Composition
**What:** Rebuild each key workflow page around clear intent blocks: controls -> results -> bulk/actions -> detail dialogs.
**Why:** Improves operator task speed and reduces cognitive load.

### Pattern 3: Typed Query Boundary
**What:** Keep service/hook API contracts typed end-to-end; remove `any` from page-level state flows.
**Why:** Prevents runtime shape mismatches and supports UI-04 requirement.

### Pattern 4: Responsive Baseline at Component Level
**What:** Use `xs/sm/md` layout variants and interaction density modes in shared components instead of page-local hacks.
**Why:** Delivers UI-03 consistently across dashboard/tables/forms.

## Don’t Hand-Roll

| Problem | Don’t Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Global async state | Custom event-bus/store | Existing react-query hooks/services | Already proven in codebase |
| Data table behavior | Ad-hoc table pagination/sorting | DataGrid server-mode patterns with typed adapters | Reduces UX inconsistency bugs |
| Cross-page notifications | Per-page bespoke snackbars only | Shared feedback utility/component contract | Consistent action/result messaging |

## Common Pitfalls

### Pitfall 1: Visual-only redesign without workflow simplification
Can look better but still be slow for operators. Phase tasks must optimize actions and decision points, not only aesthetics.

### Pitfall 2: Mixed table/filter semantics
Current pages already show mismatch between filter UIs and backend query params. Standardize query/filter mapping in shared layer.

### Pitfall 3: Responsiveness bolted on at the end
Leads to desktop-first assumptions and broken constrained-display behavior. Build with responsive variants from the first plan.

### Pitfall 4: Type erosion (`any`) in high-churn pages
Breaks API contract confidence and creates bug churn. Require typed DTO pathways during page rework.

## Recommended Plan Structure

1. **04-01 Foundation:** app shell/navigation/layout primitives + theme/token baseline + route-level structure cleanup.
2. **04-02 Core Workflows:** refactor high-impact pages/components to consistent interactions and typed data boundaries.
3. **04-03 Polish:** responsive/accessibility/usability hardening + cross-page consistency + regression checks.

## Verification Strategy for Planning

- Every plan should include executable frontend verification (`npm run build`, targeted tests) and API-contract-safe checks.
- Requirement IDs `UI-01..UI-04` must appear across plan frontmatter requirements fields.
- Plans should cap at 2-3 tasks each to keep execution context quality high.

## Sources

### Primary
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `frontend/src/App.tsx`
- `frontend/src/components/NavBar.tsx`
- `frontend/src/theme.ts`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/AcestreamChannels.tsx`
- `frontend/src/pages/TVChannels.tsx`
- `frontend/src/pages/EPG.tsx`
- `frontend/package.json`

## Metadata

**Confidence breakdown:**
- Stack and dependency direction: HIGH
- UX architecture direction: HIGH
- Risk/pitfall coverage: HIGH

**Research date:** 2026-02-27
**Valid until:** 2026-03-31
