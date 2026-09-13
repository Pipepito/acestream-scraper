# Shared Foundation And Accessibility Backbone Design

## Goal

Bring the frontend's shared shell and the highest-risk audited accessibility surfaces into alignment with the established operational design system by wiring real theme mode support, removing duplicated shell/page hierarchy, and normalizing core interaction patterns.

## Context

- `docs/dev/frontend-design-checklist.md` requires clear low-friction guidance, obvious hierarchy, semantic shared patterns, mobile/desktop support, WCAG AA behavior, restrained motion, and theme integrity in both light and dark themes.
- `docs/dev/frontend-theme-reference.md` defines the semantic token contract (`surface`, `text`, `status`, `action`, `layout`, `motion`), IBM Plex Sans typography roles, and the expectation that shared patterns like `PageHeader`, `ContentSection`, status treatments, form sections, dense data containers, and state surfaces remain the default.
- `frontend/src/bootstrap/AppBootstrap.tsx` already contains a local theme-mode context, but it initializes to light mode only and does not persist user preference or expose a user-facing control path.
- `frontend/src/components/NavBar.tsx` currently repeats the current page title in the top app bar even though pages already establish context via `PageHeader`; this weakens hierarchy and makes the shell feel like a second page header.
- The audit's first-pass target issues are: unreachable dark mode, keyboard-unsafe selection flows, incomplete tab linkage, spinner-only or weakly announced loading states, icon-only actions without names, and responsive dialog logic implemented with `window.innerWidth`.

## Design Principles For This Pass

1. The app shell is a persistent operational frame, not a second content header.
2. Page context belongs to pages through `PageHeader`; the shell should carry identity and global utilities only.
3. Shared semantic tokens remain the only acceptable source for reusable layout and state styling.
4. Accessibility fixes should prefer stronger existing primitives over custom click-only behaviors.
5. The first pass should improve the real user path without broad page-by-page visual redesign beyond what the shared foundation requires.

## Scope

### In Scope

- Real light/dark mode wiring at the app root.
- User-facing theme controls in both the shell and `Settings`.
- Removal of the repeated page title from the top app bar.
- Theme-mode persistence and synchronized controls.
- Keyboard-safe selection patterns in the audited selection dialogs/pages.
- Explicit accessible names for audited icon-only actions missing them.
- Complete tab-to-panel linkage for audited tab sets.
- Stronger, contextual loading/status treatment on the highest-value touched pages and dialogs.
- Replacement of `window.innerWidth` dialog fullscreen checks with responsive hooks.

### Out Of Scope

- A full redesign of every dense data page in the audit.
- Large-scale migration of all legacy pages onto shared primitives.
- Broad anti-pattern cleanup across all admin-style card layouts.
- Deep visual restyling of every table-heavy route.

## Information Architecture And UX

### Shell Hierarchy

- The left navigation continues to carry product identity and section grouping.
- The top app bar becomes a compact global utility row.
- The current page title is removed from the top app bar entirely.
- On phone widths, the app bar still exposes the menu button and global controls.
- On desktop, the app bar acts as a quiet shell strip aligned with the current semantic surfaces and divider treatment.

### Theme Preference Flow

- A quick theme toggle is available in the top app bar for immediate access.
- A matching canonical theme control lives in `Settings` under a dedicated appearance-oriented section or subsection.
- Both controls read and write the same shared theme state.
- The selected mode persists between sessions using a stable local storage key.
- The user-facing model is `light` or `dark` only.
- If no explicit preference has been saved yet, the app may use the system color-scheme preference as the first-run default before persisting the user's first explicit choice.
- The theme applies immediately without reload.

### Page Hierarchy

- `PageHeader` remains the only page-title surface.
- `ContentSection` remains the default grouping surface for operational content.
- No page should depend on the shell to provide its page title or explanatory copy.

## Architecture

### Theme Controller

Create a shared theme-mode controller around the existing `AppThemeModeContext` in `frontend/src/bootstrap/AppBootstrap.tsx`.

Responsibilities:
- determine initial mode from persisted preference, with a system-aware fallback if no stored preference exists
- expose `mode`, `setMode`, and `toggleMode`
- persist explicit user changes
- provide the selected mode to `createAppTheme(mode)`

The controller should remain small and live at the app bootstrap layer rather than being reimplemented page-by-page.

### Shell Integration

`frontend/src/components/NavBar.tsx` should stop calling `getNavTitle(location.pathname)` for top-bar copy. The selected route is already communicated through left-nav selected state and page-local `PageHeader`.

The app bar should instead host:
- phone-only navigation trigger
- a theme toggle control
- optional shell-level spacing/alignment that preserves a compact operational strip

No new decorative hero treatment should be introduced.

### Settings Integration

`frontend/src/pages/Settings.tsx` should add a dedicated theme preference surface that follows the shared section pattern already in use on that page.

The settings control should:
- explain what the mode changes in plain language
- reflect the current value
- update the same shared theme controller used by the shell
- avoid becoming a second implementation of theme state

## Accessibility Backbone

### Keyboard-Safe Selection Flows

`frontend/src/pages/EPGChannelDetail.tsx` and `frontend/src/pages/TVChannelDetail.tsx` contain core selection flows that currently lean on ad hoc or legacy interaction patterns.

This pass should normalize them to accessible interactive structures with:
- native focus behavior
- explicit selected state
- keyboard activation
- clear labeling for assistive technologies

Where there is a choice between a custom clickable `Box` and an accessible MUI primitive, the MUI primitive wins.

### Icon-Only Actions

Audit-listed icon-only actions in touched pages should have explicit `aria-label` values that describe the specific action and target.

This pass should cover the known gaps in `Scraper` and preserve explicit labels on touched audited icon-action surfaces.

### Tabs

Audited tab sets should receive complete `id`, `aria-controls`, and `aria-labelledby` linkage.

This should be done through a stable helper pattern if possible so future tab sets follow the same contract instead of repeating ad hoc ids.

This pass should explicitly cover the audited tab sets in `frontend/src/pages/EPG.tsx` and `frontend/src/pages/EPGChannelDetail.tsx`.

### Loading And Status Messaging

Touched loading states should no longer be spinner-only or context-light.

For the pages and dialogs in scope, loading surfaces should:
- identify what is loading
- use text near the indicator
- use live/status semantics when meaningful
- keep guidance concise and operational

This pass should explicitly cover the shared shell-adjacent and high-risk audited surfaces touched during implementation, including `frontend/src/pages/Settings.tsx`, `frontend/src/pages/TVChannelDetail.tsx`, `frontend/src/pages/EPGChannelDetail.tsx`, and the responsive dialogs updated in this phase.

The minimum shared contract is:
- page-level loading states pair the progress indicator with plain-language status text
- inline loading states near controls or dialogs identify the specific resource or action in progress
- errors and success confirmations remain textual and actionable rather than color-only

This first pass does not need to redesign every loading state in the app, but it should establish the pattern on the shared foundation and the highest-risk audited surfaces.

### Responsive Dialog Behavior

`frontend/src/components/BulkOperations.tsx` and `frontend/src/components/BatchAssignDialog.tsx` currently compute fullscreen behavior with `window.innerWidth < 600`.

They should move to breakpoint-aware responsive hooks so dialog behavior stays correct under resize, zoom, split view, and accessibility text scaling.

## Design-System Alignment Rules

- Reuse `PageHeader`, `ContentSection`, semantic alerts, and shared button patterns before adding page-local structure.
- Keep spacing on touched surfaces tied to semantic theme/layout values or existing MUI spacing scale rather than introducing raw pixel constants.
- Keep the teal/blue operational identity intact across light and dark modes.
- Use semantic theme colors for any shared or reusable state treatment; do not add raw hex values in the normalized surfaces.
- Preserve compact information density while improving scanability and state clarity.

## Responsive Behavior

- Desktop: shell navigation remains persistent, app bar becomes lighter, page headers stay within page content.
- Phone: menu button remains visible, theme toggle remains accessible, dialogs use responsive fullscreen rules via media queries, and touched controls preserve touch-safe sizing.
- Large text / zoom: shell controls and dialog layouts should reflow without relying on fixed viewport assumptions.

## Testing And Verification Expectations

The implementation should add or update tests covering:
- theme controller behavior and mode persistence
- shell rendering without repeated page title in the top bar
- visible theme controls in shell and `Settings`
- responsive dialog behavior without `window.innerWidth`
- keyboard-safe selection flow expectations in the touched pages
- explicit accessible labels for audited icon-only controls in touched pages
- tab linkage helpers/ids for touched tab sets
- loading/status copy for normalized loading states

Verification evidence should be recorded in `docs/dev/frontend-design-review-evidence.md` with concise method/result/notes entries for:
- light theme
- dark theme
- one phone width
- one desktop width
- one keyboard path through a touched core flow
- touched loading/error/success state checks

## Success Criteria

- The app can render in both light and dark mode through a real shared controller.
- Users can change theme mode from both the shell and `Settings`.
- The top app bar no longer duplicates the page title.
- The highest-risk audited accessibility gaps in the chosen first-pass surfaces are removed.
- Touched dialogs and shell interactions behave correctly at mobile widths and under resize/zoom.
- The resulting UI reads more clearly as one operational design system rather than a shell plus page-header duplication layered over legacy interaction patterns.
