# TV Channels Design System Normalization Design

## Goal

Bring the responsive `TVChannels` workflow and its shared shell/layout surfaces into closer alignment with the frontend design system so the page feels fully native to the product's operational dashboard patterns in both phone and desktop contexts.

This pass keeps the existing information architecture and route structure, but normalizes the experience around shared semantic tokens, shared layout hooks, guided low-friction management, and stronger progressive disclosure for low-technical users.

## Design-System Context

- `docs/dev/frontend-design-checklist.md` requires clear next actions, scanable hierarchy, visible state treatment, reusable shared patterns, mobile and desktop support, WCAG AA behavior, restrained motion, and theme integrity.
- `docs/dev/frontend-theme-reference.md` defines semantic token usage for `surface`, `text`, `status`, `action`, `layout`, and `motion`, plus shared expectations for page header, content section, table/dense list containers, and empty/loading/error/success states.
- `frontend/src/theme.ts` and `frontend/src/theme.d.ts` already define the semantic contract, IBM Plex Sans typography roles, and the responsive shell threshold model.
- The existing responsive shell work already established `PageHeader`, `ContentSection`, `AppShell`, `NavBar`, and a mobile/desktop split in `TVChannelsTable`, so this phase should normalize and strengthen those patterns rather than replacing them.

## Users And Workflow

The primary users are single operators with limited technical knowledge who need to manage TV-channel inventory without decoding dense tooling conventions.

For this page, the primary jobs are:

1. confirm the page purpose quickly
2. run one obvious primary action (`Refresh` or `Add TV Channel`)
3. narrow the list with filters only when needed
4. scan inventory status and metadata
5. edit, delete, or open playback checks without hunting for controls

## Current Problems

### What Already Works

- `frontend/src/pages/TVChannels.tsx` already uses `PageHeader` and `ContentSection`, which keeps the page structurally consistent with the rest of the app.
- `frontend/src/components/TVChannelsTable.tsx` already switches to a stacked mobile summary below `md`, which matches the responsive-shell spec.
- `frontend/src/components/layout/AppShell.tsx` and `frontend/src/components/NavBar.tsx` already follow the semantic shell tokens and grouped route structure.

### Normalization Gaps

- `frontend/src/pages/TVChannels.tsx` still contains page-local wide-layout grid rules instead of using a shared layout helper, which duplicates responsive composition knowledge.
- `frontend/src/theme.ts`, `frontend/src/theme.d.ts`, and `frontend/src/styles/layout.ts` are slightly inconsistent around wide-content naming (`contentMaxWidth` vs shared contract terminology), which makes the shell API less clear than the design-system docs intend.
- `frontend/src/components/AdvancedSearch.tsx` is functional but still behaves like a generic filter form rather than a normalized operational filter section: compact inputs everywhere, limited guidance, and no explicit section-level layout hooks.
- `frontend/src/components/TVChannelsTable.tsx` uses semantic surfaces, but its mobile summaries and desktop data container still rely on some page-local styling choices instead of a clearer shared operational rhythm.
- `frontend/src/pages/TVChannels.tsx` uses `window.confirm(...)` for delete, which breaks the product's visual/system consistency and is weaker for guided low-technical workflows, especially on mobile.
- create/edit dialogs are responsive, but they still feel like raw field stacks instead of a guided form section with clearer grouping and better spacing consistency.

## Chosen Direction

Normalize the page around three improvements:

1. strengthen the shared responsive layout contract so pages do not carry their own wide-layout math
2. turn filters, inventory, and dialogs into clearer operational surfaces using existing page header/content section/form patterns
3. replace the remaining browser-native interaction outliers with theme-consistent MUI flows

## Rejected Alternatives

### Rejected: cosmetic token sweep only

- would be fast
- would leave the guided-flow and progressive-disclosure problems mostly unchanged
- would not remove page-local layout knowledge

### Rejected: full TV-channels redesign with new information architecture

- would create unnecessary churn
- would diverge from the already-established shell/page conventions
- is larger than the normalization problem the codebase currently has

### Selected: normalize the existing responsive pattern

- preserves the product's current mental model
- reduces one-off layout and interaction code
- improves usability for low-technical users without expanding scope into unrelated pages

## Design Deliverable 1: Clearer Shared Shell Composition Contract

The shell/layout layer should expose a clearer wide-layout API so route pages do not re-encode grid behavior.

### Required Changes

- rename the wide content-width token contract so the theme and helpers clearly distinguish `standard` and `wide` content maxima
- keep breakpoint thresholds unchanged
- add a shared page-composition helper in `frontend/src/styles/layout.ts` for optional `primary`/`supporting` wide layouts

### Acceptance Criteria

- `TVChannels` can opt into wide split composition without local hard-coded grid values
- the same helper remains reusable for future page-level supporting rails
- desktop and wide-desktop behavior remain deterministic in tests

## Design Deliverable 2: Stronger Filter Section Pattern

Filters should feel like a guided operational control surface rather than an exposed generic query builder.

### Required Behavior

- keep filters in a dedicated `ContentSection`
- on phone, preserve the explicit show/hide affordance
- add concise guidance explaining when users should open filters and what they affect
- make filter controls wrap and size responsively without feeling cramped or overly tiny on phone
- keep `Apply` as the stronger action and `Reset` secondary
- preserve compatibility with the current `AdvancedSearch` consumers in `TVChannels` and `AcestreamChannels`

### Acceptance Criteria

- the filters section shows plain-language helper copy that explains the purpose of filtering
- on phone, `Show Filters` / `Hide Filters` continues to control the filter region explicitly
- after opening filters on phone, `Apply` and `Reset` are both visible without horizontal overflow
- `AdvancedSearch` remains API-compatible with `filters`, `onChange`, `categories`, and `groups`

### Shared-Pattern Note

`frontend/src/components/AdvancedSearch.tsx` should be normalized rather than replaced, because it is already reused by `AcestreamChannels`.

The result should remain generic enough for current consumers, but it should adopt semantic spacing, safer responsive layout, and a clearer action row.

## Design Deliverable 3: More Native Inventory Surface

The TV inventory should read as one cohesive operational surface in both desktop and phone contexts.

### Mobile

- keep the existing stacked summary pattern
- surface channel identity, number, status, category, and stream count without expansion
- add supporting metadata such as language/country as secondary text when present
- keep explicit `Edit`, `Delete`, and `Play` actions with touch-friendly sizing
- use semantic chips/status treatment consistently instead of default-looking fallback styling

### Desktop

- keep the dense data grid
- wrap it in a more clearly normalized panel treatment using semantic surface, border, and spacing rules
- preserve keyboard reachability and visible row actions
- keep empty and loading states aligned with the shared state patterns

### Acceptance Criteria

- below `md`, each row still shows name, number when present, status text, category when present, stream count, and explicit `Edit`, `Delete`, and `Play` actions
- below `md`, language and country render as supporting metadata when present
- at `md` and above, the data grid remains the primary desktop presentation
- loading, empty, and no-results-on-this-page states remain text-explicit and theme-consistent

## Design Deliverable 4: Guided CRUD Interactions

The page should replace browser-native confirmation with in-system interaction patterns.

### Delete Flow

- replace `window.confirm(...)` with a MUI `Dialog`
- title and body copy should clearly explain the consequence in plain language
- keep the destructive action explicit and visually secondary to cancellation until the user confirms
- keep the mutation side effects unchanged until the user confirms

### Create/Edit Dialogs

- keep responsive full-screen behavior on phone
- improve content structure so the form reads as grouped operational input rather than one long undifferentiated list
- keep primary and secondary actions predictable at the bottom
- preserve current field coverage; no workflow redesign beyond clearer grouping and spacing

### Acceptance Criteria

- the delete action does nothing until the explicit confirm button is pressed in the dialog
- the delete dialog uses product-consistent title/body/actions instead of browser-native confirmation UI
- create and edit dialogs remain full-screen on phone
- create and edit dialogs separate identity/basic metadata from optional supporting fields with visible grouping or sectioning
- existing create, update, and notice flows still work after the dialog/form normalization

## Accessibility And Theme Expectations

- preserve semantic headings and section landmarks
- keep focus-visible behavior fully theme-driven
- keep status meaning readable in text, not color alone
- preserve light/dark semantic token usage across all touched surfaces
- keep responsive controls comfortably tappable on phone and keyboard-usable on desktop

## Testing Strategy

Implementation should continue using TDD.

### Required Coverage

- shared layout helper coverage for wide split composition
- responsive filter-section behavior and guidance visibility
- mobile inventory summaries including secondary metadata and explicit actions
- desktop inventory container behavior and action accessibility
- delete confirmation dialog behavior
- create/edit dialog grouping and responsive sizing regressions

## Review Evidence

Record concise verification evidence in `docs/dev/frontend-design-review-evidence.md` for:

- light theme on touched surfaces
- dark theme on touched surfaces
- phone width around `375px`
- desktop width around `1024px`
- wide desktop width around `1440px`
- one keyboard path through desktop navigation or inventory actions
- one guided CRUD path covering delete confirmation plus create or edit dialog behavior

## Completion Criteria

This normalization pass is complete when:

- the shell/layout API expresses wide page composition without page-local grid duplication
- the filters area exposes helper guidance, explicit phone disclosure, and visible `Apply` / `Reset` actions without overflow
- the TV inventory preserves the required mobile summary fields, supporting metadata, and desktop data-grid path with semantic container treatment
- browser-native confirmation has been replaced by a theme-consistent guided dialog
- create and edit dialogs keep mobile-safe sizing and clearer grouped structure
- review evidence has been recorded in `docs/dev/frontend-design-review-evidence.md`
- tests, typecheck, and build all pass
