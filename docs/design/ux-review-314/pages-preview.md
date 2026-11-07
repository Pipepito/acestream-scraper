# GitHub Pages preview

The owner requested public interactive mockups on 7 November 2026. The static package is prepared by [prepare_pages_preview.py](prepare_pages_preview.py). This is separate from application deployment and the implementation work in epic #314.

## Publication candidate

At inspection, GitHub Pages is built from `main:/docs`, at `7fe2a4c54f5fdd96660eb316df17f49f63710617`. The existing `github-pages` environment permits `main`, `develop` and `gh-pages`. Neither protected branch is changed by the preview preparation.

The proposed `gh-pages:/` snapshot preserves every existing `main/docs` file byte for byte and adds `design/ux-review-314/`. Its intended entry point is `https://pipepito.github.io/acestream-scraper/design/ux-review-314/`. The initial preparation alone does **not** establish that this URL is published.

The package contains the current 144-workflow prototype and 288 synthetic exports, plus the two clearly labelled historical interactive studies, local fonts and licence notices. Specifications and evidence link to an immutable design commit on GitHub. Supplier reference screenshots, original media masters/archive, current-installation captures, runtime data and private test reports are excluded. The prototype scripts do not connect to an installation. The older concept gains the same no-network boundary in the published copy.

The published choices are the existing coral/lime comparisons. The three-interface implementation prompt explicitly includes completing cyan and the production selector; publication does not claim that this work is already done.

## Prepare and verify

From a clean design worktree, pin both source commits and use an empty temporary destination:

```bash
python3 docs/design/ux-review-314/prepare_pages_preview.py \
  --site-ref origin/main --design-ref HEAD \
  --output /tmp/acestream-pages-preview
```

The script runs no application or supplier build, makes no network requests and publishes nothing. It rejects non-regular archive entries and an existing preview directory in the site source. `publication-manifest.json` records both source commits and file hashes; every existing site file is checked unchanged. Review the root install tools and extraction helper as well as preview links, assets, deep links, themes/languages, mobile bounds and interactions before publication. Keep raw reports outside Git.

## Publishing contract and future maintenance

Changing Pages from `main:/docs` to `gh-pages:/` is a hosting-source change, not a protected-branch merge. It requires the owner's publishing-route decision because it changes the documented release-site update path. It does not require changing the environment branch policy or introducing a workflow/Jenkins publisher.

If selected, publish only the prepared static snapshot to `gh-pages`, then update the Pages source and verify the resulting build, URL, assets and unchanged install tools. Future `main/docs` changes will not automatically appear while this source is selected: refresh the snapshot from freshly checked `main` and the selected design commit, revalidate, and push it explicitly. Never overwrite the install tools from the design branch's older application base. Returning Pages to `main:/docs` restores the release-site source but removes this preview unless it has reached `main` through the normal reviewed branch flow. Do not delete either branch or bypass branch protection.

The [implementation prompt](implementation-prompt.md) is ready for the next Plan mode session. It does not authorize application changes in this publishing session.

## Preparation evidence

The candidate retains 102 existing site files byte for byte and copies 300 explicit design assets. Isolated Chromium checks exercise 288 workflow deep links (144 workflows in EN/light/desktop and ES/dark/phone), 318 layout cases including all three prototype generations, all 288 gallery images at two widths, language/theme/proposal switching with a dirty draft, safe confirmation focus/Escape/discard, and phone drawer opening/closing. The landing page has zero axe violations or incomplete results at 320, 390, 768 and 1440 CSS pixels. Desktop/phone landing and recording views were visually inspected. These are publishing checks, not a repeat of the whole application or review-04 acceptance matrix.

The existing installation-tools homepage requests external Google Fonts and `release-status.json`. The latter returned HTTP 404 on the existing live Pages site before publication; it is also absent from the pinned `main/docs` snapshot. Intercepted testing blocks the former deliberately. These existing-site observations are separate from preview errors; preserving the existing bytes does not claim to fix or fully validate the installation tools. No app/runtime/dependency changes or live installation requests are part of this work.
