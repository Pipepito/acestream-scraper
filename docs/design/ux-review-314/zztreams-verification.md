# ZZSTREAMS component expansion — verification

9 November 2026. Static design continuation on `pepe/sportzz-brand-system`, after
the published SPORTZZ source `c7f11fe9` and Pages snapshot `3340e195`.

## Scope

Material-informed reusable component styles and interactive reference catalogue;
new uppercase ZZSTREAMS identity applied to the current reference, mockup shell, index and
gallery. Earlier supplied assets remain intact. Production runtime code remains
unchanged. The three pre-existing E2E test corrections are preserved separately.

## Logo provenance

Two Magnific generations using **Google Nano Banana 2**, **75 credits each**;
total **150/200 credits**. The first lowercase 2K concept produced 2752×1536.
The corrected uppercase **ZZSTREAMS** generation requested **1K**, producing
1376×768; its display copy is 1024×572. Transparent PNG UI derivatives were
created locally without further charges. Both originals remain in shared assets.
The public
[provenance record](assets/zztreams/provenance.json) contains prompt, model,
dimensions, original hash, transformations and per-asset hashes, without signed
download tokens. Future image requests default to Nano Banana 2 at 1K.

## Current checks

Component checks passed in isolated Chromium, Firefox and WebKit: **70 explicit
checks**, **12 layouts**, **8 axe scans**, plus the interaction assertions for
selection, search, fields, sliders, tabs, menus, snackbar undo, pagination,
carousel and all five dialogs. Zero failed checks, accessibility violations,
console/script errors or unexpected requests. Chromium covered both themes at
320/390/820/1440 pixels; Firefox/WebKit covered both phone themes and the shared
keyboard/desktop interaction journey. Temporary server 18794 stopped and its
port was verified free.

Testing caught an inherited fixed-toast ID collision, unsupported tooltip focus
handler properties, and carousel tracks shrinking until no scrolling remained.
The section now has a unique ID, tooltip focus uses event listeners, and carousel
tracks have fixed responsive widths. The final run retains the interaction
assertions and the page's restrictive CSP. The corrected logo and desktop/phone
screenshots were visually inspected, including a white-background transparency
proof. The symbol specimen is bounded to its source width to avoid enlargement.

Logs and captures: `artifacts/visual-review/zztreams-components/` and
`artifacts/visual-review/zzstreams-final/`. Reproduce with a temporary local
server mounting `docs/` beneath `/acestream-scraper/`:

```sh
workspace-test python docs/design/ux-review-314/check_components.py \
  --base-url http://127.0.0.1:18794/acestream-scraper/design/ux-review-314/ \
  --output artifacts/visual-review/zztreams-components \
  --axe frontend/node_modules/axe-core/axe.min.js
```

The refreshed static suite passed: **146 workflows, 1,752 layouts, 877 axe scans,
105 functional assertions and 14 reflow cases**; all **876 gallery exports** were
refreshed. Connected journeys passed all **48 assertions**. Contrast checks passed
**24 contexts / 232 text rectangles**, minimum measured ratio **5.377:1**.
Artifact checks passed **4,076 local links, 674 fragments and ten generated files**
without drift. No browser errors, blocked requests or failed checks were reported.
The brand pass had **1,059 checks**, zero axe violations and no console errors.
Temporary server 18795 stopped and its port was verified free. Immutable Pages
packaging is verified separately before publishing; its manifest pins the source.
This record does not claim completion of application/image validation.

## Application validation boundary

The previous complete backend/frontend gate passed as recorded in
[brand verification](brand-verification.md). Its Docker/architecture and browser
jobs were stopped at the owner's request to retain only the newest static checks.
All five amd64 image variants passed build, HTTP startup and acceptance
(15 stages). The emulated arm64 scraper built, but its HTTP startup smoke timed
out with connection refused; this is an outstanding failure, not a pass. The
remaining matrix was cancelled during the arm64 AceStream image build; the two
queued native/Docker browser jobs were cancelled before starting. Their process
groups and emulated build children exited, no task containers remained running,
and ports 18839/18840/18849/18850 were verified free. Completed logs are retained.
These cancelled stages remain incomplete and are not automatically restarted. The
owner-selected local ARM scope is now QEMU emulation; actual native
ARM acceptance remains in CI. Static Pages uses its approved subtree-only route.
No application/source branch push or CI/CD mutation is part of this continuation.
