# Design-only verification — review 06

Observed 2026-11-07. This report covers documentation, selected assets and disposable prototypes in `docs/design/ux-review-314/`. The owner explicitly waived the full application/Docker/E2E matrix for this design-only session. Those suites were **not run**, and no application, API, media, device or participant pass is implied.

## Revision, environment and isolation

Tested worktree: `/tmp/acestream-ux-review-314`, branch `design/ux-review-314`, based on `7b2d8e204d3a58f8013f826621dc137e867abc38`. Current application evidence is pinned to `cf952afc6b4489c02b7a675ff3d634cc13d98e0b`. At the final source recheck, `main` advanced to merge commit `180f544c140f2f0361c386ebd395dcf366ae343d`; its `backend/` and `frontend/` trees have no difference from that reviewed develop source. No application merge or rebase was performed in the design branch.

Cached Python Playwright 1.61.0, Chromium 149 and axe-core 4.14.0 were used, without installing dependencies. Browser requests were intercepted at `design.invalid`: GETs could load only local files below this design directory; all other requests were rejected. Service workers were blocked, reduced motion enabled, and fixtures were synthetic. There was no installation connection, playback, recording, source import, device discovery/control, notification or recovery. The only browser persistence is the namespaced design-preset preference.

Raw reports and diagnostic screenshots remain outside Git under `/tmp/ux314-review06/`. [Verification summary](verification-summary-06.json) records report hashes, observed counts and final prototype hashes; it contains no installation data. The 876 current gallery exports are intentionally public synthetic artifacts, separate from 288 historical exports.

## Observed checks

Rows overlap; do not add them as unique test totals. The full matrix is broader than the later focused reruns. A failing earlier run is retained as evidence, not relabelled as passing.

| Run / report directory | Scope | Observed result |
|---|---|---|
| `full` | All 146 contexts; three presets; EN/ES; light/dark; 320/820/1440; open advanced controls; base and workflow-specific states | 10,077 layout cases; **4 failures**, all the coral Documentary category label at 320 px. 877 axe cases with 0 violations, 105 functional assertions passing, 14 reflow/text-stress cases passing. 876 exports |
| `final-affected` | Eight affected viewing, detail and source compositions after layout/current-section/advanced indicator fixes | 675 layouts, 48 axe cases; 0 failures/violations |
| `final-exports` | All 146 contexts after those corrections, EN/light desktop and ES/dark phone, all presets and advanced controls | 1,752 layouts, 105 functional assertions and 14 reflow/text-stress cases passing; 876 regenerated exports |
| `final-source-copy` | Five source variants and account permissions after primary-action and plain-language refinements | 414 layouts, 36 axe cases; 0 failures/violations; 36 refreshed exports |
| `final-recovery` | Both consequential recovery choices after plain-language refinements | 126 layouts, 12 axe cases; 0 failures/violations; 12 refreshed exports |
| `final-hero` | Watch hero after image-overlay and illustration-label fixes | 105 layouts, 6 axe cases; 0 failures/violations; 6 refreshed exports |
| `final-interactions` | Final shared renderer: drafts, locale/theme/preset, query context, selection, pending work, synthetic player ownership, validation, dialogs, independent saves and consequences | **105 passing, 0 failing**; 14 reflow/text-stress cases passing; 1 dialog axe case with 0 violations |
| `journeys-final` | Six connected task paths through the shared navigation in all three presets, including invalid source submission and canonical setup aliases | **48 passing, 0 failing** |
| `gallery-final` | Gallery at 320/390/768/1440, plus 23 critical states × three presets × two locale/theme/viewport combinations | 146 images decoded at each width; 0 overflow/broken images. 138 axe cases, 0 violations |
| `gallery-final` | Computed semantic color pairs in all presets/themes | **78 pairs pass**; minimum normal-text ratio **4.988:1**, minimum focus/control ratio **3.510:1** |
| `image-contrast-final` | Actual selected hero art and overlays, three presets × EN/light and ES/dark × 320/390/820/1440 | **215 text rectangles across 24 contexts pass**; minimum measured ratio **4.886:1** |
| `pages` | Current preview home/gallery, four widths each, plus long original title and expanded action text in six preset/locale combinations | 8 static cases and 6 long-content cases pass; 0 axe violations, broken images or overflow |
| `artifacts` | Generated-file reproducibility, links/fragments, asset hashes/notices, exports, field inventory and script syntax | Final counts are in the linked machine-readable summary; 0 drift or failures |
| OpenAPI reference checker | 333 operations, 130 design/resource bindings, 473 field occurrences, 24 explicit model-property references | Pass; three negative tests reject a fabricated path, wrong method and nonexistent field. The remaining 449 field occurrences are **not claimed runtime payload-validated** |

All final browser runs above recorded zero JavaScript errors, warning/error console entries and attempted blocked external requests. The first image-check iteration emitted a Pillow deprecation warning; the checker now uses the supported API and the final run was warning-free. No warning suppression was added. `node --check` and `git diff --check` pass.

The first rendered-image measurement found three small-text contrast failures in the lime 320 px hero (minimum 3.097:1). The phone overlay was strengthened. Visual review then found that the illustration label itself was underneath the overlay; it now sits above it. The final measurement and exports cover both corrections. This demonstrates why overflow and axe alone were insufficient.

## Accessibility and visual interpretation

The initial full axe run had 25 cases marked incomplete for color contrast, involving image/pseudo-element backgrounds or non-text player glyphs. In the 138 critical-state run, 12 incomplete cases were the decorative, `aria-hidden` player glyph. These are not silently counted as automatic passes. The hero cases received the separate rendered-image measurement: glyphs were hidden without changing layout, actual background pixels were sampled over each text rectangle, and computed foreground colors were compared. Large text was assessed at 3:1 and ordinary text at 4.5:1. The label was moved above the overlay before the final measurement. Other illustrated labels use the same dark backing and were visually inspected. This is bounded evidence, not a general WCAG conformance certificate.

Author visual inspection covered the three viewing compositions on desktop and phone, the landing page, and representative source, guide matching, account permissions, recording/DST, WARP partial application and recovery compositions. Controls, original content names, long EN/ES copy, image identity/fallbacks and destructive consequences were checked. Every context was rendered automatically; this does **not** claim a separate full-resolution human review of all 876 exports.

The built-in browser was also used on the Spanish recording editor: the Adjust programme times draft survived a switch to Coral; Escape closed the interface dialog and returned focus to its opener. The native accessibility tree exposed the controls and state. This was keyboard/AX observation, **not VoiceOver listening**. The built-in browser's zoom shortcut produced no change to viewport or scale, so it was not recorded as a zoom pass. The owner declined access to personal Firefox; no further access was attempted. Playwright 320 CSS-pixel reflow and 200% text enlargement are explicitly different from actual browser zoom.

## Reproducible commands

Run from the design worktree. Set `AXE` to the already cached `axe-core/axe.min.js`; no application dependency installation is required. Output directories below are disposable and excluded from Git.

```sh
python3 docs/design/ux-review-314/compose_workflows.py
python3 docs/design/ux-review-314/openapi_contracts.py --check --self-test
python3 docs/design/ux-review-314/check_workflows.py --output /tmp/ux314-review06/full --exports --axe "$AXE"
python3 docs/design/ux-review-314/check_workflows.py --output /tmp/ux314-review06/final-exports --smoke --exports
python3 docs/design/ux-review-314/check_workflows.py --output /tmp/ux314-review06/final-interactions --interactions-only --axe "$AXE"
python3 docs/design/ux-review-314/check_journeys06.py --output /tmp/ux314-review06/journeys-final
python3 docs/design/ux-review-314/check_gallery.py --output /tmp/ux314-review06/gallery-final --axe "$AXE"
python3 docs/design/ux-review-314/check_image_contrast06.py --output /tmp/ux314-review06/image-contrast-final
python3 docs/design/ux-review-314/check_pages06.py --output /tmp/ux314-review06/pages --axe "$AXE"
python3 docs/design/ux-review-314/check_artifacts.py --output /tmp/ux314-review06/artifacts
node --check docs/design/ux-review-314/workflow-engine.js
git diff --check
```

Focused workflow reruns use the same command with `--only` and these exact lists: `dashboard,channel-detail,recording-parts,source-web,source-auto,source-provider,source-zeronet,source-ipfs`; `source-web,source-auto,source-zeronet,source-ipfs,source-provider,access-account`; `recovery-readable,recovery-fresh`; and `dashboard`. The latter three use `--exports --axe "$AXE"`; the first uses `--axe "$AXE"` only. Reports record the exercised cases rather than extrapolating to unexecuted combinations.

## Remaining acceptance and publication

All requested capability families have composed contexts and a linked field/state/source specification. Detailed visual approval remains with the owner under #316. Native VoiceOver/NVDA/TalkBack listening, actual 200/400% browser zoom, native input popups and physical phone/keyboard checks remain under #317/#324. Fluent Spanish review and nontechnical participant sessions remain under #317 and #316/#324. [Exact protocols and recording requirements](acceptance-protocols.md) are provided. Equipment/participants were not available through the authorized tools; no results were invented.

Observed application defects remain open in #315. F15 is a source finding requiring isolated reproduction in #315/#320; general slowdown is unproven in #323. OpenAPI security/error descriptions and programme-image adapter decisions remain future work in #318–#320/#324. Actual consumer/provider contract tests, media ownership, access/transport and independent-transaction behavior require separately authorized application work. See [source findings](source-findings-06.md) and [OpenAPI acceptance](openapi-contracts-06.md).

Static publication is authorized and follows [the verified Pages procedure](pages-preview.md). The preview is built from an immutable committed design revision over the current `gh-pages` snapshot, with every non-preview file preserved. Publication SHA, hosted checks and existing-issue readback are appended after publication; until then, a local pass is not a hosted-site pass.
