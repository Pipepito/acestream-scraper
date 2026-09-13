# Frontend Normalization Design

## Goal

Redesign the frontend so the product reads as one deliberate operational system instead of a mix of newer shared primitives and older admin-template screens.

The normalization work should preserve the current product identity - IBM Plex Sans, teal/blue foundations, compact operational density, and a guided left-nav app shell - while making the experience more coherent, accessible, responsive, and dual-theme-safe.

## Context

- The product serves single users with little or no technical knowledge who need guidance while operating an AceStream setup.
- The persisted design context in `CLAUDE.md` requires a bold, powerful, operational feel with clear hierarchy, strong state visibility, and support for both light and dark themes.
- `docs/dev/frontend-design-checklist.md` and `docs/dev/frontend-theme-reference.md` already define the desired design-system contract, semantic token usage, preferred shared patterns, and review expectations.
- The audit in `docs/dev/frontend-audit-report.md` found systemic drift: incomplete dark-mode wiring, mixed token adoption, generic admin-style card patterns, keyboard-inaccessible selection flows, and desktop-first dense data pages.

## Problem Statement

The repo now has a real semantic theme foundation and shared layout primitives, but the visible product still behaves like two partially overlapping systems:

1. newer shared shell and layout primitives built around semantic tokens
2. legacy pages and dialogs built with page-local spacing, card, table, and interaction decisions

This split creates four major product problems:

- visual inconsistency weakens trust and makes the app feel less intentional
- accessibility gaps concentrate in old flows where custom interactions bypass the shared system
- responsive behavior remains uneven because dense desktop tables were preserved without mobile adaptation
- future frontend work stays expensive because contributors cannot rely on one dominant page structure or state pattern

## Users And UX Direction

Normalization must optimize for non-expert operators first.

That means the frontend should:

- orient users quickly with a clear page title, a short explanation, and obvious next actions
- make operational state easy to scan through hierarchy, copy, iconography, and semantic status treatments
- keep dense information available without forcing users to decode raw data tables before understanding the task
- progressively disclose complexity instead of front-loading every control at once
- remain usable on mobile, zoomed, and keyboard-only paths without hiding core actions

## Chosen Approach

Normalize the frontend in three phases that move from shared system trust to high-risk operational flows and finally to supporting pages.

### Why this approach

This work is too broad for a route-by-route cosmetic sweep. The primary issue is system drift, not isolated page ugliness.

The selected approach:

1. strengthens the shared foundation first so page work inherits better defaults
2. tackles the riskiest dense operational flows next because they carry the heaviest usability, accessibility, and responsive debt
3. normalizes supporting/dashboard pages last so they can adopt the same shared language instead of inventing one more layer of patterns

### Rejected alternatives

#### Rejected: page-by-page sweep

- simpler to start
- likely to duplicate fixes for tokens, dialogs, states, and responsive behavior
- too easy to drift into one-off page decisions

#### Rejected: issue-category sweep only

- consistent for raw accessibility or theming cleanup
- weak at producing coherent user flows because users experience pages, not issue spreadsheets
- risks improving code quality while leaving the product structure confusing

## Design Principles For This Normalization

Every touched surface should follow these product-specific rules:

- use `PageHeader` plus `ContentSection` as the default skeleton unless a page has a strong reason not to
- keep layouts left-aligned, compact, and operational rather than centered, decorative, or marketing-like
- reduce unnecessary cards and avoid card-in-card compositions
- use semantic theme tokens instead of raw hex values or page-local visual constants
- make loading, empty, error, success, and destructive states explicit with both wording and structure
- keep primary actions obvious and secondary actions quieter
- replace implied click areas with explicit, accessible controls
- adapt dense content for smaller widths rather than hiding essential actions

## Phase 1: Foundation And Shared Flow Standards

### Goal

Make the shared frontend contract trustworthy so normalized pages inherit one theme, one layout rhythm, one state language, and one responsive baseline.

### Scope

- `frontend/src/theme.ts`
- `frontend/src/index.tsx`
- `frontend/src/components/layout/PageHeader.tsx`
- `frontend/src/components/layout/ContentSection.tsx`
- `frontend/src/components/layout/AppShell.tsx`
- `frontend/src/components/NavBar.tsx`
- shared patterns repeated in dialogs and dense action areas

### Design decisions

- Real theme mode plumbing must exist so the semantic theme contract works in both light and dark themes.
- Shared layout values must come from semantic theme tokens, not a competing parallel constant system.
- Shared surfaces must lose leftover decorative drift such as avoidable blur/shadow treatments that push the UI toward a generic template feel.
- Shared buttons, section headers, and shell surfaces must reinforce one clear action hierarchy: primary, secondary, destructive, quiet.
- Shared state patterns must standardize copy and structure for loading, empty, error, and success handling.
- Reusable responsive behavior must rely on theme-aware breakpoints and component adaptation rather than `window.innerWidth` checks.

### Expected UX outcome

- the app stops feeling split between old and new systems
- dark mode becomes a real supported mode rather than a token-only aspiration
- future route work becomes faster because contributors can inherit the right defaults

## Phase 2: Dense Operational Flows

### Goal

Normalize the data-heavy operational routes into clearer, more guided control panels without sacrificing density.

### Scope

- `frontend/src/pages/EPG.tsx`
- `frontend/src/pages/EPGChannelDetail.tsx`
- `frontend/src/pages/TVChannelDetail.tsx`
- `frontend/src/pages/Search.tsx`
- `frontend/src/components/EPGProgramsTable.tsx`
- related dense-action and dialog patterns used by these flows

### Design decisions

- Page structure should move from centered tabs and table-first composition toward top-down operational sections.
- Tables remain valid when they are the best representation of dense data, but each must live inside a stronger section pattern with summary, filters, status, and responsive overflow handling.
- Detail pages should share a common information hierarchy: overview first, related actions second, secondary/history/program content last.
- Row-level action density should be reduced so touch and keyboard users can operate the page without hunting through clusters of tiny icon buttons.
- Selection and mapping flows must use explicit accessible controls with visible selected state.
- Empty and loading states must teach the workflow: what exists, what is missing, and what the next useful action is.

### Expected UX outcome

- users can understand each operational route faster
- data screens remain dense but stop feeling hostile or desktop-only
- keyboard and assistive-technology support becomes predictable in critical flows

## Phase 3: Dashboard And Supporting Pages

### Goal

Bring the supporting pages into the same design language so the whole app feels cohesive, guided, and operational.

### Scope

- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/Health.tsx`
- `frontend/src/pages/Playlist.tsx`
- `frontend/src/pages/Settings.tsx`
- `frontend/src/pages/WARP.tsx`
- `frontend/src/pages/NotFound.tsx`

### Design decisions

- Remove generic hero-metric and repeated-card layouts when they flatten hierarchy instead of helping orientation.
- Reframe each page around `PageHeader` and `ContentSection`, with one obvious task path and quieter secondary information.
- Rewrite redundant copy so the interface explains only what users need to act with confidence.
- Treat health, warnings, and summaries as operational status blocks instead of decorative dashboard widgets.
- Group form and settings actions predictably, and tuck advanced or less frequent choices behind progressive disclosure where that improves clarity.

### Expected UX outcome

- supporting pages no longer feel like a separate admin template
- the app communicates urgency, guidance, and next steps more consistently
- non-technical users get clearer help in settings, playlist, and WARP flows

## Accessibility Contract

This normalization must enforce the following across all phases:

- WCAG AA contrast in both light and dark themes, including dense data surfaces, status treatments, and focus-visible states
- keyboard-operable primary flows
- explicit accessible names on icon-only controls
- visible focus treatment aligned with semantic action tokens
- tab and panel relationships that expose proper ARIA linkage
- non-color status cues through text, icon, or structure
- responsive behavior that holds up under zoom and narrow widths
- loading, success, and error states that are announced or described clearly enough for practical screen-reader use

## Responsive Contract

Normalization should not hide core tasks on mobile. Instead it should adapt context.

Required outcomes:

- shared actions wrap cleanly at smaller widths
- dense table areas expose overflow intentionally or transform to mobile-safe structures where needed
- fixed-width assumptions and viewport reads during render are removed from touched flows
- touch targets remain operable in dense views

## Theming Contract

All touched reusable UI must consume semantic tokens.

Required outcomes:

- light and dark theme parity for semantic token keys
- motion behavior uses semantic motion tokens instead of page-local timing values
- no new raw hex values in reusable or normalized page UI
- compact operational spacing and shadow rhythm preserved through shared layout tokens
- warm accent use stays sparse and purposeful
- reduced-motion behavior preserves usability and removes any dependence on animation timing for understanding state changes

## Anti-Pattern Guardrails

This redesign must explicitly avoid:

- generic hero metrics used as filler instead of orientation
- blanket card nesting
- decorative blur or glossy effects without functional purpose
- centered, symmetrical admin-template layouts where left-aligned structure would scan better
- redundant instructional copy that repeats visible headings or controls
- dense clusters of small icon-only actions with no hierarchy

## Verification Expectations

The implementation must include lightweight evidence for:

- light theme and dark theme
- reduced-motion behavior on touched transitions or feedback states
- one mobile width and one desktop width
- one keyboard path for the primary flow of each touched area
- loading, empty, warning, error, and success states where present
- lint, test, and build verification for the frontend after the implementation pass

For each phase or PR that touches shared frontend primitives or normalized UI, record the verification method, result, and notes in `docs/dev/frontend-design-review-evidence.md`.

## Out Of Scope

This normalization does not require:

- inventing a brand-new visual identity
- replacing Material UI with a custom component system
- a marketing-style redesign
- a total rewrite of every route regardless of relevance
- adding new product capabilities unrelated to normalization

## Success Criteria

This work is successful when:

- the frontend visibly reads as one coherent operational product
- shared primitives and theme behavior are the default path rather than the exception
- major dense pages become more usable, accessible, and responsive without losing operational density
- supporting pages stop reading like generic admin templates
- future contributors can follow the documented design system with less room for drift
