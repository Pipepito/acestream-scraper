# Frontend Audit Report

Date: 2026-03-26
Scope: `frontend/src`
Method: code audit only; no fixes applied

## Anti-Patterns Verdict

Fail. The frontend does not read as pure AI slop, but several legacy surfaces still look like a generic admin template rather than a deliberate operational product.

Specific tells found:
- Generic hero-metric cards on `frontend/src/pages/Dashboard.tsx:257` and `frontend/src/pages/Health.tsx:164`
- Nested surface treatment on `frontend/src/pages/Search.tsx:202` and `frontend/src/pages/EPG.tsx:672`
- Centered tab bars and wide table-first layouts on `frontend/src/pages/EPG.tsx:501` and `frontend/src/pages/EPGChannelDetail.tsx:350`
- Redundant instructional copy on `frontend/src/pages/Playlist.tsx:180` and `frontend/src/pages/Playlist.tsx:221`
- Blur-based app bar styling on `frontend/src/theme.ts:287`
- Split design language between newer shared primitives and older ad hoc pages across `frontend/src/pages/*.tsx`

## Executive Summary

- Total issues: 14
- Severity breakdown: 0 Critical, 2 High, 8 Medium, 4 Low
- Most critical issues:
  1. Dark mode is implemented in tokens but not wired into the app
  2. Dialog selection UIs are not reliably keyboard accessible
  3. Several icon-only controls have no accessible name
  4. Large data-heavy pages remain desktop-first and fragile on mobile/text scaling
  5. Layout and theme contracts are split between semantic tokens and ad hoc constants
- Overall quality score: 66/100
- Recommended next steps: fix shared primitives first (`/normalize`, `/harden`, `/adapt`), then address legacy page layouts and table actions, then clean anti-pattern drift with `/distill` and `/polish`

## Detailed Findings By Severity

### Critical Issues

- No verified critical issues were found in this code audit.

### High-Severity Issues

#### 1. Dark mode is not actually reachable
- Location: `frontend/src/theme.ts:159`, `frontend/src/theme.ts:370`, `frontend/src/index.tsx:8`, `frontend/src/index.tsx:27`
- Severity: High
- Category: Theming
- Description: `createAppTheme(mode)` supports light and dark tokens, but the exported theme is hard-coded to light and `ThemeProvider` receives only that static theme.
- Impact: Dark-theme defects can ship unnoticed, theme parity cannot be trusted, and the documented dual-theme contract is effectively broken.
- WCAG/Standard: Internal theme contract in `docs/dev/frontend-theme-reference.md:35`
- Recommendation: Introduce a real theme mode source, pass it into `ThemeProvider`, and verify semantic token parity in both themes.
- Suggested command: `/normalize`

#### 2. Some selection flows are not keyboard-safe
- Location: `frontend/src/pages/EPGChannelDetail.tsx:564`, `frontend/src/pages/TVChannelDetail.tsx:607`
- Severity: High
- Category: Accessibility
- Description: Clickable selection rows rely on `Box onClick` and legacy clickable list items instead of accessible button/listbox primitives.
- Impact: Keyboard and assistive-technology users may be unable to select mapping targets or associated channels reliably in core workflows.
- WCAG/Standard: WCAG 2.1.1 Keyboard, 4.1.2 Name Role Value
- Recommendation: Replace ad hoc clickable containers with accessible list, option, or button primitives that expose focus, role, and selected state.
- Suggested command: `/harden`

### Medium-Severity Issues

#### 3. Icon-only actions are missing accessible names
- Location: `frontend/src/pages/Scraper.tsx:284`, `frontend/src/pages/EPG.tsx:579`, `frontend/src/pages/EPG.tsx:825`, `frontend/src/pages/TVChannelDetail.tsx:551`, `frontend/src/pages/EPGChannelDetail.tsx:275`, `frontend/src/pages/EPGChannelDetail.tsx:529`
- Severity: Medium
- Category: Accessibility
- Description: Several `IconButton` controls rely on icon shape or `title` rather than `aria-label`.
- Impact: Screen reader users cannot tell what these actions do, especially in row-level action groups where multiple unlabeled buttons appear together.
- WCAG/Standard: WCAG 4.1.2 Name Role Value, 2.5.3 Label in Name
- Recommendation: Add explicit accessible names for every icon-only control and keep labels action-specific.
- Suggested command: `/harden`

#### 4. Tabs are missing complete tab-panel linkage
- Location: `frontend/src/pages/EPG.tsx:87`, `frontend/src/pages/EPG.tsx:502`, `frontend/src/pages/EPGChannelDetail.tsx:67`, `frontend/src/pages/EPGChannelDetail.tsx:352`
- Severity: Medium
- Category: Accessibility
- Description: `TabPanel` uses `aria-labelledby`, but the matching `Tab` ids and `aria-controls` are not defined.
- Impact: Screen readers get incomplete relationships between tabs and panels, weakening orientation on multi-panel pages.
- WCAG/Standard: WCAG 4.1.2 Name Role Value
- Recommendation: Add stable `id` and `aria-controls` pairs for every tab and panel.
- Suggested command: `/harden`

#### 5. Repeated loading states are spinner-only or weakly announced
- Location: `frontend/src/pages/Dashboard.tsx:170`, `frontend/src/pages/Health.tsx:66`, `frontend/src/pages/Settings.tsx:156`, `frontend/src/pages/WARP.tsx:86`, `frontend/src/components/ChannelActivityLog.tsx:37`, `frontend/src/components/EPGProgramsTable.tsx:23`
- Severity: Medium
- Category: Accessibility
- Description: Many loading states render only `CircularProgress` or `LinearProgress` with no live region, no page-level status text, or inconsistent context.
- Impact: Screen reader users may not know what is loading, and all users get weak state clarity on slower connections.
- WCAG/Standard: WCAG 1.3.1 Info and Relationships, 4.1.3 Status Messages
- Recommendation: Pair loading indicators with concise status text and announce long-running state changes consistently.
- Suggested command: `/harden`

#### 6. Mobile and zoom behavior is fragile in dialogs
- Location: `frontend/src/components/BulkOperations.tsx:158`, `frontend/src/components/BatchAssignDialog.tsx:35`
- Severity: Medium
- Category: Responsive
- Description: `fullScreen={window.innerWidth < 600}` is computed directly during render instead of using responsive hooks.
- Impact: Dialog behavior can fail to adapt correctly to resize, split-screen, zoom, and accessibility text-scaling scenarios.
- WCAG/Standard: WCAG 1.4.10 Reflow
- Recommendation: Use breakpoint-aware responsive APIs and test dialogs under zoom and narrow-width conditions.
- Suggested command: `/adapt`

#### 7. Table-heavy pages are still desktop-first
- Location: `frontend/src/pages/EPG.tsx:539`, `frontend/src/pages/EPG.tsx:778`, `frontend/src/pages/TVChannelDetail.tsx:486`, `frontend/src/pages/EPGChannelDetail.tsx:404`, `frontend/src/pages/Search.tsx:228`, `frontend/src/components/EPGProgramsTable.tsx:45`
- Severity: Medium
- Category: Responsive
- Description: Several major pages rely on wide multi-column tables, centered tabs, and dense row action clusters with limited mobile adaptation.
- Impact: Small screens and large text settings risk horizontal scroll, clipped hierarchy, and difficult action targeting.
- WCAG/Standard: WCAG 1.4.10 Reflow, 1.4.4 Resize Text
- Recommendation: Redesign dense views for mobile context rather than simply shrinking desktop tables.
- Suggested command: `/adapt`

#### 8. Theme contract is split between tokens and ad hoc layout constants
- Location: `frontend/src/theme.ts:72`, `frontend/src/theme.ts:141`, `frontend/src/theme.ts:307`, `frontend/src/styles/layout.ts:1`, `frontend/src/components/layout/AppShell.tsx:17`
- Severity: Medium
- Category: Theming
- Description: Spacing, widths, and radii are defined partly in theme tokens and partly in standalone layout constants, and some component overrides ignore token values.
- Impact: Global refinements will not propagate cleanly, increasing visual drift and maintenance cost.
- WCAG/Standard: Internal theme contract in `docs/dev/frontend-theme-reference.md:35`
- Recommendation: Consolidate reusable layout values into semantic theme tokens and have shared primitives consume only those tokens.
- Suggested command: `/normalize`

#### 9. Hard-coded and non-semantic colors bypass the token system
- Location: `frontend/src/pages/Dashboard.tsx:377`, `frontend/src/pages/EPGChannelDetail.tsx:569`, `frontend/src/pages/EPGChannelDetail.tsx:574`
- Severity: Medium
- Category: Theming
- Description: Snackbar colors use fixed hex values and selection rows use raw greys instead of semantic surface/status tokens.
- Impact: Theme switching and contrast tuning become brittle, especially once dark mode is enabled for users.
- WCAG/Standard: Internal theme contract in `docs/dev/frontend-theme-reference.md:35`
- Recommendation: Replace raw colors with semantic action, surface, and status tokens.
- Suggested command: `/normalize`

#### 10. Dense icon-button rows create small touch targets
- Location: `frontend/src/components/ChannelTable.tsx:152`, `frontend/src/components/TVChannelsTable.tsx:85`, `frontend/src/pages/EPG.tsx:825`, `frontend/src/pages/Scraper.tsx:284`, `frontend/src/pages/TVChannelDetail.tsx:551`
- Severity: Medium
- Category: Responsive
- Description: Multiple `size="small"` icon actions are tightly packed into row-level controls.
- Impact: Touch users face higher mis-tap risk, especially around destructive actions and on smaller phones.
- WCAG/Standard: WCAG 2.5.5 Target Size (AAA), mobile usability best practice
- Recommendation: Increase hit areas, reduce concurrent row actions, or move secondary actions into progressive disclosure patterns.
- Suggested command: `/adapt`

### Low-Severity Issues

#### 11. Success dialogs auto-close on timers
- Location: `frontend/src/components/BulkOperations.tsx:94`, `frontend/src/components/BulkOperations.tsx:132`, `frontend/src/components/QuickEditDialog.tsx:59`, `frontend/src/components/BatchAssignDialog.tsx:26`, `frontend/src/components/BatchAcestreamAssignment.tsx:63`
- Severity: Low
- Category: Accessibility
- Description: Several dialogs dismiss themselves shortly after success.
- Impact: Focus can jump unexpectedly and users may miss confirmation details.
- WCAG/Standard: WCAG 2.2.1 Timing Adjustable, 3.2.1 On Focus
- Recommendation: Keep success state visible until the user dismisses it or provide a clearly announced persistent confirmation.
- Suggested command: `/harden`

#### 12. Legacy pages bypass the shared page header and section primitives
- Location: `frontend/src/pages/Health.tsx:92`, `frontend/src/pages/Settings.tsx:165`, `frontend/src/pages/Playlist.tsx:73`, `frontend/src/pages/Search.tsx:139`, `frontend/src/pages/WARP.tsx:106`, `frontend/src/pages/TVChannelDetail.tsx:203`
- Severity: Low
- Category: Theming
- Description: Many older pages still use bespoke `Box`/`Card` compositions instead of `PageHeader` and `ContentSection`.
- Impact: The app feels split between two design systems and shared improvements do not land evenly.
- WCAG/Standard: Internal shared-pattern expectations in `docs/dev/frontend-theme-reference.md:24`
- Recommendation: Migrate legacy pages to the shared primitives before doing page-level polish.
- Suggested command: `/normalize`

#### 13. Multiple pages use generic admin-style metric and card patterns
- Location: `frontend/src/pages/Dashboard.tsx:257`, `frontend/src/pages/Health.tsx:164`, `frontend/src/pages/Search.tsx:146`, `frontend/src/pages/Playlist.tsx:79`
- Severity: Low
- Category: Anti-Patterns
- Description: Repeated card blocks, hero stats, and uniform section containers flatten hierarchy and feel template-driven.
- Impact: The product loses the bold operational character defined in project guidance and gives users less guidance toward the next action.
- WCAG/Standard: Frontend-design anti-pattern guidance
- Recommendation: Remove decorative repetition, tighten hierarchy, and favor action-led information design over card accumulation.
- Suggested command: `/distill`

#### 14. Minor visual and performance drift remains in shared effects and controls
- Location: `frontend/src/theme.ts:287`, `frontend/src/theme.ts:339`, `frontend/src/components/QuickEditDialog.tsx:92`, `frontend/src/NotFound.tsx:14`
- Severity: Low
- Category: Performance
- Description: The app bar uses blur, contained buttons add hover shadow, one dialog uses native checkboxes inside MUI UI, and a few fixed heights remain.
- Impact: Small but recurring signs of inconsistency, extra paint cost, and text-scaling risk.
- WCAG/Standard: Frontend-design anti-pattern guidance, WCAG 1.4.4 Resize Text
- Recommendation: Remove unnecessary effects, standardize controls, and replace fixed-height layout shortcuts.
- Suggested command: `/polish`

## Patterns And Systemic Issues

- Shared primitives exist, but adoption is incomplete; new and old page patterns coexist across the app.
- Accessibility gaps cluster around custom or legacy interactions: icon-only actions, ad hoc selection rows, spinner-only states.
- Responsive debt concentrates in data-heavy pages where desktop tables were preserved instead of adapted.
- Semantic theming is partially implemented, but raw colors and parallel layout constants still leak into production pages.
- Touch-target compression is recurring anywhere row actions are packed into tables or lists.

## Positive Findings

- The semantic token foundation in `frontend/src/theme.ts:18` is solid and already defines `surface`, `text`, `status`, `action`, `layout`, and `motion` groups.
- Shared primitives in `frontend/src/components/layout/PageHeader.tsx:15` and `frontend/src/components/layout/ContentSection.tsx:18` are strong and align well with the project design docs.
- The app shell already uses meaningful landmarks in `frontend/src/components/layout/AppShell.tsx:18` and `frontend/src/components/NavBar.tsx:189`.
- Reduced-motion awareness exists in `frontend/src/theme.ts:160`, even though it is only partially applied.
- Some table action controls are already well-labeled in `frontend/src/components/ChannelTable.tsx:70` and `frontend/src/components/TVChannelsTable.tsx:87`.
- Logo images generally include alt text in `frontend/src/components/TVChannelsTable.tsx:50`, `frontend/src/pages/TVChannelDetail.tsx:251`, and `frontend/src/pages/EPG.tsx:812`.

## Recommendations By Priority

1. Immediate
- Wire real light/dark theme switching and verify both themes.
- Fix inaccessible selection rows and unlabeled icon-only controls in core dialogs and detail views.
- Establish a consistent accessible loading-state pattern for page loads and long-running operations.

2. Short-term
- Replace `window.innerWidth` responsive checks with proper breakpoint logic.
- Refactor table-heavy mobile flows, especially `EPG`, `TVChannelDetail`, `EPGChannelDetail`, and `Search`.
- Consolidate shared layout values and remove raw colors from reusable UI.

3. Medium-term
- Migrate legacy pages onto `PageHeader` and `ContentSection`.
- Rework row action density to improve touch targets and reduce destructive-action crowding.
- Remove timer-driven dialog dismissals and make confirmation handling more stable.

4. Long-term
- Reduce template-like metric/card repetition and strengthen action-led information hierarchy.
- Remove leftover blur/shadow drift and standardize any native controls still bypassing MUI.
- Expand reduced-motion coverage beyond button transitions.

## Suggested Commands For Fixes

- Use `/normalize` to align the app with the semantic theme and shared layout system; this addresses the dark-mode wiring gap, raw colors, token drift, and legacy primitive bypass.
- Use `/harden` to fix interaction accessibility; this addresses keyboard-inaccessible selection rows, missing accessible names, spinner-only states, and timer-based dialog dismissal.
- Use `/adapt` to improve responsive behavior; this addresses table-heavy mobile layouts, `window.innerWidth` dialog logic, and small touch targets.
- Use `/distill` to remove admin-template anti-patterns; this addresses nested surfaces, generic hero metrics, and redundant instructional copy.
- Use `/polish` for final consistency cleanup; this addresses minor effect drift, fixed-size leftovers, and mixed control treatments.
- Use `/critique` after the first remediation pass to reassess whether the app still reads like a generic template.
