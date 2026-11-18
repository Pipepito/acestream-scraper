# One application, three presentations

Review 06 · design-only architecture and future acceptance. The owner confirmed keeping three styles while maintaining one product. The prototype demonstrates the separation; it is not application code to transplant.

The SPORTZZ continuation is documented in [Brand system](brand-system.html).
Current mockups share `sportzz-tokens.css` and `sportzz-system.css`; presentation
recipes retain composition and accent differences, with common neutral surfaces,
type and controls. The reference consumes those same files. Original marks and
icons are reused as supplied; see the README for the asset map and maintenance.

## Shared by construction

One router and deep-link resolver; one application bootstrap; one query client/cache; one auth and permission layer; one domain model; one API adapter per resource; one validation/save transaction; one field and EN/ES message catalogue; one playback/session owner. Presets must not create another tree that mounts these providers again.

Feature controllers own drafts, baseline revisions, selections, pending requests and results. Canonical editors receive typed values/actions and semantic slots. A feature is added once to the capability registry and is immediately reachable in all presets. Shared editor markup covers routine administration. Existing `StreamLinkFormatsSection`, access, source, guide and recording editors retain ownership regardless of contextual entry point. A second entry point is a link to that editor, not another implementation.

| Layer | Responsibility | Permitted preset variation |
|---|---|---|
| Existing generated API types and shared services | Methods, parameters, payloads, normalization, errors | None |
| Feature controller / query hooks | Permissions, request timing, draft revisions, media leases | None |
| Canonical editor and task model | Labels, help, validation, save/cancel, consequential states | None |
| Semantic design tokens | Background, surface, text, action, focus, status, spacing, radius, type | Preset values; theme overrides |
| Shared layout recipes | App shell, field group, list, summary, contextual editor, dialog | Density, columns, media/text balance and order when meaningful reading order is retained |
| Stateless composition slots | Featured Watch area, programme tiles, category tiles | Image prominence and arrangement; same view model and actions |

Do not duplicate routers, request functions, translation dictionaries, permission checks or business conditionals for a style. Avoid an all-purpose component with dozens of style flags: use a small recipe vocabulary and semantic slots. CSS custom properties and container/media queries handle most differences. A real composition exception must name its reason, owner, shared controller, common interaction tests and evidence that CSS alone was insufficient.

## Composition exception register

| Surface | Design exception | Shared contract | Owner |
|---|---|---|---|
| Watch featured item | Lime compact band; coral image/text split; cyan immersive image area and stacked phone actions | Same programme identity, exact times, Watch action and recording opener | #316/#319 |
| Programme list | Lime dense rows, coral editorial rows, cyan image cards | Same query/filter/selection and action names; stable item keys | #316/#319 |
| Category links | Lime compact chips, coral horizontal tiles, cyan image tiles | Actual catalogue/event taxonomy; no translated machine names or sport substitution | #316/#319 |
| Administration | Token/density/type differences only | Identical canonical editors and transaction groups | #318–#322 |

No exception owns API logic. This register is deliberately small. Additions need evidence, not a new third implementation.

## Interface selector contract

**Interface / Interfaz** opens three previews with descriptions, selected indication and keyboard-operable buttons. Names in the review are Lime, Coral / navy and Immersive. Final naming is still a proposal. The first-visit and unknown-value fallback is immersive cyan, per the approved execution plan. Theme defaults remain system-derived where available; saved theme and locale are independent.

Changing style applies immediately. It is not a settings API transaction. Remember a small versioned identifier in the existing preference facility in future application work; catch read/write exceptions. Keep the visible choice in the current tab after storage failure and offer Retry saving preference. Do not discard other saved preferences or treat an unknown value as malformed user content. The disposable prototype writes only `ace-design-314:preset`; it never writes app preference keys, credentials, drafts or playback state.

| State to retain | Behavior on interface change | Prototype demonstration / future acceptance |
|---|---|---|
| Draft and validation | Keep exact values, errors, dirty status and expanded advanced fields | Shared Maps, stable field IDs; test unsaved source and account forms |
| Focus and selection | Keep focus on initiating selector/control; preserve selected rows and text input value | Modal traps Tab, Escape closes, focus returns; row selection survives |
| Scroll | Restore same offset after reflow; future app anchors the same logical content if geometry changes substantially | Prototype restores scrollY; native zoom/manual review remains required |
| Route and query | Keep path meaning, selected channel, filters, return context and unrelated query keys | Prototype clones URLSearchParams rather than replacing known keys only |
| Pending work | Do not resubmit, cancel or lose pending state; late result updates original editor | Pending timer model survives switch and returns the result; no network requests |
| Playback | Same viewer/session owner, channel and playback position; no player remount, stop or start | Same synthetic player DOM node during style/locale/theme change; real lease/media tests are future work |
| Open dialog | Keep purpose, draft and focus containment; avoid reopening as a different transaction | Selector remains open during choice; dirty guard is independent |
| Permissions | Same visibility, eligibility and denial behavior | Shared state gates; server enforcement remains authoritative |

The disposable renderer replaces ordinary DOM when a preference changes and restores state. The implementation should use stable keyed components, not copy this string renderer. Recreating the query client/provider tree or player is prohibited.

## Adding a future capability once

Add its contract-backed service operation and shared controller; add the canonical editor/action and one EN/ES message set; register its destination/context and permission; use existing semantic recipes; run the same behavioral scenarios with all three preset identifiers; inspect presentation and focus/reflow per preset. Only add a stateless layout exception when necessary. A small visual regression suite per preset complements the shared behavioral suite; it cannot replace it.

The [OpenAPI strategy](openapi-contracts-06.md) checks the shared network boundary. Endpoint correctness is never tested only in one style-specific service because such services must not exist.
