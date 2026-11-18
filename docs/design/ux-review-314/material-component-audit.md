# Material Design 3 → ZZSTREAMS component audit

Reviewed 9 November 2026 against Google's official Material Design 3 catalogue,
including its current Expressive button, menu and progress guidance. This is a
component-coverage reference for the static design system, not an adoption of
Google's brand or a production frontend implementation.

[Interactive component library](components.html) · [Brand foundations](brand-system.html)

## What was missing

The previous brand page demonstrated primary/secondary/destructive buttons,
basic fields, badges, a confirmation dialog, filter buttons, loading skeletons,
empty/error states and playback controls. Actual mockups already had navigation,
tables and forms, but many primitives lacked a reusable visual/interaction contract
or a live specimen. Selection controls, field variants, chips, menus, tabs, sheets,
snackbars, tooltips and progress were the largest gaps.

## Coverage map

| Material family | Before | ZZSTREAMS treatment / live location |
|---|---|---|
| Buttons | Primary, outline and destructive only | [Five emphasis levels](components.html#actions): filled, tonal, outlined, elevated and text; shared hover/focus/press/disabled rules |
| Toggle / icon / toggle icon buttons | Ad hoc favorite and player controls | Named 48px icon buttons, pressed semantics and visible toggle labels |
| Floating / extended FAB / FAB menu | No reference | Extended creation action; related Add actions use a modal bottom sheet rather than a floating radial menu |
| Button groups / segmented buttons | Filter buttons without a dedicated group style | Player toolbar with roving focus; connected native radio segments for single-view selection |
| Split buttons / menus | No reference | Split Schedule action with Arrow/Home/End navigation, disabled item, Escape and focus return |
| Checkbox | Browser defaults in mockups | [Native selection family](components.html#selection), visible labels, disabled and parent mixed state |
| Radio buttons | Browser defaults in mockups | Native, mutually exclusive vertical group and connected view selector |
| Switch | No shared contract | Immediate preview preference, labelled on/off state and visible thumb movement; saved forms retain checkboxes |
| Chips | Generic buttons | Assist, filter, input/removal and suggestion variants; named removal plus Delete/Backspace support |
| Sliders | No shared contract | Native stepped slider and two labelled endpoints with cross-field validation |
| Text fields | Basic outline and one error | [Outlined/filled fields](components.html#inputs), helper/error copy, read-only, disabled, textarea count, native select |
| Search | Basic catalogue search | Contained labelled search, explicit Clear, filtered example list, count and no-results recovery |
| Date / time pickers | Form fields but no specimen | Modal native date/time inputs, manual entry, explicit timezone and local display-only result; platform-owned calendar/clock interiors |
| App bars | Present in shell only | [Context app-bar specimen](components.html#navigation) with named drawer action |
| Navigation bar / rail / drawer | Existing responsive mockup navigation | Dedicated bar/rail/drawer specimens, current-state shape and underline, retained production-independent links |
| Tabs | No reference | Labelled tabs and panels, manual keyboard activation, roving focus, Home/End and ordinary Tab exit |
| Cards | Image-led cards only | [Outlined, filled, elevated](components.html#containment) surface variants; image dimensions and independent actions |
| Lists / dividers | Existing workflow rows | Leading identity, one/two-line text, trailing count/action and tokenized dividers |
| Carousel | No reference | Horizontal scroll-snap collection with named Previous/Next, ordinary keyboard links and no autoplay |
| Dialogs | One confirmation example | Destructive confirmation plus scheduling modal with initial focus, Escape, wrapping and return focus |
| Bottom / side sheets | No reference | Native modal sheet surfaces, explicit dismissal, supporting inline standard-sheet specimen |
| Badges | Semantic status pills | Retained text+color statuses and contextual count badge; no unexplained live dots |
| Progress / loading indicators | Static skeleton only | [Measured linear example](components.html#communication), unknown-duration circular indicator, skeleton and reduced-motion behavior |
| Snackbar | Generic status text | Undoable persistent snackbar, polite message, no focus stealing, Alt+G action access and focused Escape dismissal |
| Tooltips | No reference | Plain pointer/focus tooltip with Escape, hoverable target region and delayed pointer dismissal; rich help uses explicit native disclosure |
| Toolbars | No standalone specimen | Contextual action group with one Tab entry and arrow-key navigation |

Product-specific complements include breadcrumbs, pagination, accessible data
tables, empty/retry outcomes and disclosures. They use the same tokens without
claiming to be newly supplied Material 3 components.

## What stays ours

- **Color:** Signal Pitch cyan, ink/paper neutrals, original lime/coral composition
  accents and accessible semantic pairs. Light controls use dark teal for contrast.
- **Type:** supplied Inter for reading/controls, Barlow Condensed for display.
- **Shape:** existing 8px controls and 12px cards. Pills belong to search and switch
  tracks; a sheet gets a larger corner only where its layer needs distinction.
- **Density:** four-point spacing, 48px target goal, readable 16px phone inputs.
- **Identity:** new uppercase ZZSTREAMS PNG signature, retaining the supplied icon family,
  photographer attribution and the earlier SPORTZZ originals as provenance.
- **Motion:** short feedback, no decorative morphing in administration, no carousel
  autoplay and no animated rotation when reduced motion is requested.

## Behavioral decisions

1. **Switches act immediately.** Saved or restart-dependent settings must not adopt
   switch semantics merely for appearance. Existing mockup forms are not rewritten.
2. **Tabs and navigation differ.** Tabs reveal related local panels; destinations
   use links and `aria-current`. Selection never destroys unrelated drafts.
3. **Unknown work stays unknown.** No percentage on indeterminate progress. The
   catalogue's advance button is visibly labelled a simulation.
4. **Undo remains available.** The actionable snackbar does not time out. Errors
   persist beside the relevant field/action. No live region receives focus merely
   because its text changed.
5. **Native controls preserve access.** Date/time interiors, select popups and
   range interaction remain platform-native. A branded custom calendar, analog
   clock, multi-thumb slider and gesture-driven dismissals are not implemented.
6. **Styles are shared, examples are isolated.** Component CSS is in the shared
   system file, with no remote fonts, JavaScript framework or Material dependency.
   Existing mockup actions retain their own engine. No production application
   APIs, player ownership or saved settings are changed by this static extension.

## Official references

- [Component catalogue](https://m3.material.io/components)
- [Button types and hierarchy](https://m3.material.io/components/all-buttons)
- [Chips: variants and usage](https://m3.material.io/components/chips/guidelines)
- [Checkbox selection](https://m3.material.io/components/checkbox/guidelines)
- [Radio groups](https://m3.material.io/components/radio-button/guidelines)
- [Switches and immediate application](https://m3.material.io/components/switch/guidelines)
- [Sliders](https://m3.material.io/components/sliders/overview)
- [Search](https://m3.material.io/components/search/overview)
- [Menus](https://m3.material.io/components/menus/guidelines)
- [Tabs and keyboard access](https://m3.material.io/components/tabs/accessibility)
- [Cards](https://m3.material.io/components/cards/overview)
- [Bottom sheets](https://m3.material.io/components/bottom-sheets/overview)
- [Side sheets](https://m3.material.io/components/side-sheets/overview)
- [Date pickers](https://m3.material.io/components/date-pickers/overview)
- [Time pickers](https://m3.material.io/components/time-pickers/overview)
- [Progress guidance](https://m3.material.io/components/progress-indicators/guidelines)
- [Snackbar accessibility](https://m3.material.io/components/snackbar/accessibility)
- [Tooltip behavior](https://m3.material.io/components/tooltips/guidelines)
- [Keyboard traversal](https://m3.material.io/foundations/designing/flow)

Read these as interaction guidance. Native assistive-technology and physical-device
acceptance remain separate from automated browser/axe checks; see the current
[verification record](zztreams-verification.md).
