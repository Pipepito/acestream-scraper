# ZZSTREAMS — whole-app design review and brand reference

## Current revision — component expansion

The working name is **ZZSTREAMS**, always uppercase with the S after ZZ. The current
[brand reference](brand-system.html) and [component library](components.html) keep
the Signal Pitch palette, typography and supplied icons, with a new generated
double-z symbol and wordmark. [Material Design 3 comparison](material-component-audit.md)
records the missing families, adopted interactions and deliberate web adaptations.
The earlier SPORTZZ assets and decisions below are provenance; the current identity
section supersedes their use as the active signature. CSS filenames and selectors
retain their existing names for continuity.

The shared tokens and `sportzz-system.css` now own button emphasis, selection,
chips, tabs, cards/lists, menus, sheets, search, fields, progress, navigation and
feedback primitives. `components.css` owns catalogue layout; `components.js` only
demonstrates local interactions. No Material runtime dependency is introduced.
The Pages exporter includes the catalogue and renders its linked documents locally.

Two logo generations through Magnific used Nano Banana 2: the first lowercase
concept at 2K and the corrected **ZZSTREAMS** logo at **1K**. Each cost 75 credits,
for **150 of the authorized 200 credits**. Both originals are retained. Transparent
UI variants were derived locally without further charges. Legacy asset filenames
remain stable; their contents are the corrected uppercase identity.
[Provenance](assets/zztreams/provenance.json) records
the prompt, model, dimensions, original hash and transformations. These are PNG
assets, not claimed vector masters. New image requests default to Nano Banana 2
at 1K unless explicitly overridden. Current evidence: [verification](zztreams-verification.md).

**Design-only continuation.** Earlier statements that design was closed or implementation would begin next are superseded. The owner approved executing the design plan, including static preview publication. Application implementation requires a separately authorized later session.

The package uses **one shared application structure and three presentation presets**: lime, coral and immersive cyan. The current ZZSTREAMS identity uses the corrected uppercase wordmark, shared Signal Pitch foundations and the existing **Watch, Recordings, Events, Channels, Connections, Settings and System** navigation. Immersive remains the first-visit/unknown-value default. The static mockup identity does not change the production application's name or code.

## Explore and review

- [Preview home](index.html) and [published previews](https://pipepito.github.io/acestream-scraper/design/ux-review-314/).
- [Brand system](brand-system.html) — current identity, preserved supplied marks, theme-aware colors, type and imagery. [Components](components.html) — expanded interactive catalogue. Local changes are not automatically published.
- [Interactive prototype](workflow-prototype.html?screen=dashboard) — use Interface to change presets; review controls select workflows/states. Synthetic local outcomes only.
- [Whole-app gallery](workflow-gallery.html) — 146 contextual compositions across all three presets. This is not a target page count.
- [Simplification and six task paths](simplification-06.md), [exhaustive before/after ownership and saves](before-after-map.md).
- [One shared implementation architecture](shared-foundations-06.md), [OpenAPI contract strategy](openapi-contracts-06.md) and [checked operation/field references](openapi-contract-map.json).
- [Field and state specification](workflow-specification.md), [traceability](traceability-matrix.md), [source-control map](source-control-map.md), [source contracts](source-contracts.md), [coverage and state catalogue](coverage-review-06.md).
- [Selected graphics, provenance and genuine gaps](asset-selection-06.md), [current validation and limitations](verification-review-06.md), [acceptance protocols](acceptance-protocols.md).
- [Existing task ownership](task-refinements-06.md), [future implementation brief](implementation-prompt.md), [Pages publication procedure](pages-preview.md).

## What changed

Watch joins the home overview and Live TV while preserving both existing routes. Channels owns source setup, guide matching and advanced streams. Recordings owns its settings. Connections groups browser playback, TVs/players, media servers, playlists and notifications by purpose. Telegram ingestion stays with sources. Settings is a concise index to canonical editors. System includes WARP, services, job history, storage, diagnostics and advanced setup/recovery.

The prototype has one field catalogue, state/interaction engine and semantic component set. Lime uses compact broadcast rows and condensed headings; coral uses editorial image/text balance; cyan uses a featured illustrated viewing area and richer cards, with separate phone composition. Administration remains calm in each. The selector preserves draft, query, focus, selection, pending action and synthetic player ownership, with namespaced preference storage and a usable failure state.

Supplier Football/Tennis photos are reused with attribution, joined by Basketball and Formula 1 examples in the reference. Existing selected Inter/Barlow fonts retain OFL notices. The earlier generic nature illustration remains visibly distinguished from programme artwork. The first identity pass copied SPORTZZ marks and the supplied icon family; the current logo generation is recorded above. Sports concept masters remain outside the deployed payload.

## Brand maintenance

- Authoritative values: `sportzz-tokens.css`. Shared component treatment: `sportzz-system.css`, loaded after existing structural styles. `presentation-presets.css` owns composition differences, not a competing palette. `brand-reference.css` owns only the reference/index editorial layouts.
- Current reference: `brand-system.html`; specimen interactions: `brand-reference.js`. Mockup interactions remain in `workflow-engine.js`; do not fork the field catalogue or workflow contracts to change appearance.
- Designer originals: `/srv/opencode-workspace/assets/designer-reference/sportzz-frontend/`. Read its parent README, inspect actual graphics, then select optimized runtime files. Keep originals unchanged. VM paths are maintenance context only, never runtime URLs.
- Preserve the current ZZSTREAMS geometry and capitalization; use its ink/paper wordmarks or cyan lockups. Earlier SPORTZZ black/white/lime SVGs remain historical reference. The supplied lime SVGs are #B6FF00, not cyan. Digital wordmark sizes and accessible light-theme ramps are documented refinements.
- Every selected asset is mapped in [assets/sportzz/asset-map.json](assets/sportzz/asset-map.json), with source, purpose and SHA256. Keep category attribution JSON and font OFL notices; the earlier [image manifest](assets/selected/asset-manifest.json) remains authoritative for existing imagery. Do not infer rights or factual event identity from a filename.
- Use the existing `.button`, `.field`, `.badge`, `.notice`, native dialog and supplied `.icon` patterns. New variants belong in the shared stylesheet; add a live specimen here and inspect the corresponding workflow in both themes. Avoid unlabelled icon controls and unrelated decorative photos.
- Update tokens, affected mockups and reference together. Inspect and reuse existing assets before proposing generation; generation needs explicit user authorization. Preserve the static no-backend boundary and relative URLs.
- Refresh landing/gallery HTML with `python3 docs/design/ux-review-314/compose_review06.py --pages-only`. Full workflow generation also calls this renderer. Regenerate current synthetic gallery exports after visual changes; historical exports remain historical.
- `prepare_pages_preview.py` includes the reference, shared CSS/JS and all selected assets in its existing immutable-commit publication allowlist. Follow [Pages preparation](pages-preview.md); no new build system or deployment job is required.
- The inherited review-06 validation report and waiver are historical evidence, not a validation receipt for this pass. See [brand verification](brand-verification.md) for current commands and gaps.

## Source and status

Application evidence is pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`; newer source was inspected as git objects separately from this design branch's older application base. See [current-source delta](current-source-delta.md). No application merge/rebase is needed to refresh design inventory.

Observed defects remain open in #315. F15 bulk metadata/repeated-batch behavior is a source finding awaiting isolated reproduction, not a verified performance regression. Now/next artwork and OpenAPI security/error documentation gaps require later work in #318–#320/#324. [Backend/source findings](source-findings-06.md) distinguish these from owner preferences and design hypotheses.

Composed and rendered does not mean owner-approved in every visual detail, participant-validated or implemented. Native AT, physical-device, fluent Spanish participant and application/media acceptance retain explicit owners. Review 06 used a design-only validation waiver; that historical waiver is not assumed for the SPORTZZ continuation. Current checks and outstanding application/Docker/E2E acceptance are recorded in `brand-verification.md`.

## Reproduce design checks

```sh
python3 docs/design/ux-review-314/compose_workflows.py
python3 docs/design/ux-review-314/openapi_contracts.py --check --self-test
python3 docs/design/ux-review-314/check_workflows.py --output /tmp/ux-review-06 --exports --axe /path/to/cached/axe.min.js
python3 docs/design/ux-review-314/check_journeys06.py --output /tmp/ux-journeys-06
python3 docs/design/ux-review-314/check_image_contrast06.py --output /tmp/ux-image-contrast-06
python3 docs/design/ux-review-314/check_artifacts.py --output /tmp/ux-artifacts-06
```

Playwright uses cached tooling and an intercepted `design.invalid` origin: only local files below this design directory can load. There are no application imports, network APIs, media playback or live mutations. Reports/private captures stay outside Git; deliberately synthetic gallery exports are public design artifacts. See the verification report for exact commands and observed counts.

The earlier [administration prototype](admin-prototype.html), [illustrative viewing concept](prototype.html), reviews 03–05 and their verification logs are historical context. They neither override review 06 nor establish new passes. The supplied frontend and translation helper remain references, never canonical application roots.
