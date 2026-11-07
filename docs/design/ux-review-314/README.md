# AceStream Scraper — whole-app design review 06

**Design-only continuation.** Earlier statements that design was closed or implementation would begin next are superseded. The owner approved executing the design plan, including static preview publication. Application implementation requires a separately authorized later session.

The package uses **one shared application structure and three presentation presets**: original lime, coral/navy and immersive cyan. It keeps AceStream identity and simplifies navigation to **Watch, Recordings, Events, Channels, Connections, Settings and System**. The immersive choice is the approved plan's first-visit/unknown-value default; final colors, fonts, assets and detailed compositions remain proposals for review.

## Explore and review

- [Preview home](index.html) and [published previews](https://pipepito.github.io/acestream-scraper/design/ux-review-314/).
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

Supplier Football/Tennis photos are reused with attribution. Existing selected Inter/Barlow fonts retain OFL notices. One original generic nature illustration fills the non-sports gap; it is visibly distinguished from actual programme artwork. Uncredited supplier generated art/icons and Sportzz marks are not published.

## Source and status

Application evidence is pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`; newer source was inspected as git objects separately from this design branch's older application base. See [current-source delta](current-source-delta.md). No application merge/rebase is needed to refresh design inventory.

Observed defects remain open in #315. F15 bulk metadata/repeated-batch behavior is a source finding awaiting isolated reproduction, not a verified performance regression. Now/next artwork and OpenAPI security/error documentation gaps require later work in #318–#320/#324. [Backend/source findings](source-findings-06.md) distinguish these from owner preferences and design hypotheses.

Composed and rendered does not mean owner-approved in every visual detail, participant-validated or implemented. Native AT, physical-device, fluent Spanish participant and application/media acceptance retain explicit owners. The design-only validation waiver applies here; the full application/Docker/E2E matrix was not run and is not reported as passed.

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
