# Frontend Theme Reference

This reference defines the phase-1 semantic theme contract for shared frontend work.

## Token Groups

- `surface`: semantic backgrounds and structure for canvas, panels, muted surfaces, raised surfaces, and borders.
- `text`: semantic text roles for primary, secondary, muted, and inverse content.
- `status`: semantic state families for success, warning, error, and info; each family must expose `bg`, `border`, `text`, and `icon` roles.
- `action`: semantic interactive roles for primary, secondary, destructive, disabled, and focus-visible treatments.
- `layout`: semantic spacing, radius, divider, and shadow roles that preserve a compact operational dashboard rhythm.
- `motion`: semantic timing roles for standard transitions, reduced-motion behavior, and no-motion fallbacks.

## Typography Contract

- Page title: highest-emphasis page heading for fast orientation and primary page context.
- Section title: compact section heading for dense operational grouping.
- Body text: default readable copy for explanatory and instructional content.
- Helper text: supporting guidance for forms, secondary labels, and inline assistance.
- Status/meta text: compact status/meta text for health, timestamps, summaries, and supporting signals.
- Dense data text: compact typography for tables, dense lists, and data-heavy surfaces.
- IBM Plex Sans remains the default family across themes.

## Shared Pattern Expectations

- Page header: presents title, supporting description, and primary actions in a consistent top-of-page pattern.
- Content section: groups related controls or information with a clear title, optional description, and bounded surface treatment.
- Status treatment: pairs semantic status tokens with text or icon cues so meaning never depends on color alone.
- Form section and form actions: keep guidance near inputs and group primary versus secondary actions predictably.
- Table or dense list container: preserve scanability, clear row grouping, and overflow behavior at smaller widths.
- Empty, loading, and error states: explain what is happening, what is missing, and what to do next.

## Theme Usage Rules

- Prefer semantic tokens over raw hex values in reusable UI and shared layout code.
- Keep the teal/blue identity as the base and use warm accents only for emphasis.
- Preserve equivalent semantic keys across light and dark themes.
- Use semantic status roles consistently: `bg` for surface fill, `border` for structure, `text` for readable copy, and `icon` for supporting emphasis.
- Keep spacing and shadows compact, operational, and aligned with shared layout patterns.
- Reduced motion must keep the interface usable: no essential state change can depend on animation timing, and touched transitions should honor reduced-motion expectations through shorter or removed motion.

## Review Evidence

- Each PR that touches frontend UI should include lightweight review evidence covering light theme, dark theme, one mobile width, one desktop width, keyboard access for the primary flow, and any loading, empty, error, or success-feedback states that exist.
- Evidence can be concise notes, screenshots, or short recordings, but it must be specific enough for a reviewer to confirm what was checked.
- Record the verification method, result, and notes in `docs/dev/frontend-design-review-evidence.md` when the work is part of this foundation or updates shared frontend primitives.
