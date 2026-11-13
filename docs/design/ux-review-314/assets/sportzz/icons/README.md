# SPORTZZ icon set (Signal Pitch) — construction

- **Grid:** 24×24 viewBox; live area 20×20 (2px padding).
- **Stroke:** 1.5px at 24px; scale stroke with `vector-effect` avoided — export optical sizes 16/24/32.
- **Caps / joins:** `round` / `round`.
- **Corner language:** soft 2px optical radii on rectangular forms; sharp notches reserved for brand mark only (do not copy ZZ into icons).
- **Color:** `currentColor`; states via parent token (`--color-text-*`, `--color-action-*`).
- **Filled vs outline:** outline default for nav; filled for selected/toggle (favorites, live pulse uses filled + label).
- **Naming:** `ic-{domain}-{name}.svg` (e.g. `ic-media-play.svg`).
- **Not derived from** Material / Font Awesome paths; drawn for this proposal.

Pending: optical QA at 16px on device screens; Figma component library not created in this pass.
