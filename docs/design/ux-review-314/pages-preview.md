# GitHub Pages preview

The owner requested public interactive mockups on 7 November 2026. The static package is prepared by [prepare_pages_preview.py](prepare_pages_preview.py). This is separate from application deployment and the implementation work in epic #314.

## Published preview · 7 November 2026

The owner explicitly approved switching GitHub Pages from `main:/docs` to `gh-pages:/`. The existing `github-pages` environment already permitted this branch; its policy, HTTPS enforcement and custom-domain setting were unchanged. Neither protected branch was changed. This approval is for publication, not approval or implementation of the proposed designs.

The [public preview home](https://pipepito.github.io/acestream-scraper/design/ux-review-314/), [interactive workflows](https://pipepito.github.io/acestream-scraper/design/ux-review-314/workflow-prototype.html?screen=dashboard) and [expanded gallery](https://pipepito.github.io/acestream-scraper/design/ux-review-314/workflow-gallery.html) are live and verified. The snapshot preserves every existing `main/docs` file byte for byte and adds `design/ux-review-314/`.

- Published branch/commit: `gh-pages` at `ebea374d0e62da1ac7bf52c322ccad8daf1990fd`.
- Preserved release site: `main/docs` at `7fe2a4c54f5fdd96660eb316df17f49f63710617`.
- Design source: `bdc88af0aeacae55e395e138d30d7b1f328bf765`.
- [GitHub Pages build and deployment](https://github.com/Pipepito/acestream-scraper/actions/runs/42405519082): completed successfully at the published commit. The Pages source update needed a separate Pages build request; no Jenkins job or application CI workflow was added or triggered.
- [Published manifest](https://pipepito.github.io/acestream-scraper/design/ux-review-314/publication-manifest.json) records immutable sources and file hashes.

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

The approved change from `main:/docs` to `gh-pages:/` is a hosting-source change, not a protected-branch merge. The owner confirmed its effect on the release-site update path. It did not change the environment branch policy or introduce a workflow/Jenkins publisher.

Future `main/docs` changes will not automatically appear while this source is selected: refresh the snapshot from freshly checked `main` and the selected design commit, revalidate, and push it explicitly. Publish only the prepared static content and verify the resulting build, URL, assets and unchanged install tools. Never overwrite the install tools from the design branch's older application base. Returning Pages to `main:/docs` restores the release-site source but removes this preview unless it has reached `main` through the normal reviewed branch flow. Do not delete either branch or bypass branch protection. Recheck the source with `gh api repos/Pipepito/acestream-scraper/pages` before a future publication or rollback.

The [implementation prompt](implementation-prompt.md) is ready for the next Plan mode session. It does not authorize application changes in this publishing session.

## Preparation evidence

The candidate retains 102 existing site files byte for byte and copies 300 explicit design assets. Isolated Chromium checks exercise 288 workflow deep links (144 workflows in EN/light/desktop and ES/dark/phone), 318 layout cases including all three prototype generations, all 288 gallery images at two widths, language/theme/proposal switching with a dirty draft, safe confirmation focus/Escape/discard, and phone drawer opening/closing. The landing page has zero axe violations or incomplete results at 320, 390, 768 and 1440 CSS pixels. Desktop/phone landing and recording views were visually inspected. These are publishing checks, not a repeat of the whole application or review-04 acceptance matrix.

The existing installation-tools homepage requests external Google Fonts and `release-status.json`. The latter returned HTTP 404 on the existing live Pages site before publication; it is also absent from the pinned `main/docs` snapshot. Intercepted testing blocks the former deliberately. These existing-site observations are separate from preview errors; preserving the existing bytes does not claim to fix or fully validate the installation tools. No app/runtime/dependency changes or live installation requests are part of this work.

## Verification of the published site

System HTTPS checks compared **402 public files** with the approved manifest: **101 preserved site files and 301 preview files**, all HTTP 200 and SHA-256 identical. The published manifest also matched exactly. The remaining preserved file is `.nojekyll`, a deployment marker checked in the package rather than requested as public content. No existing site file changed.

Live Chromium checks passed **32 page/layout cases and 37 assertions**, with zero script/console errors, failed resource responses or unexpected requests. They covered ten representative workflow deep links in EN/light/desktop and ES/dark/phone, both historical prototypes, all 288 gallery images at phone and desktop widths, dirty-draft retention across language/theme/proposal changes, confirmation focus/Escape/discard and phone drawer focus return. The hosted landing page passed four axe scans at 320/390/768/1440 with zero violations or incomplete results. Hosted desktop/phone renders were also visually inspected. All requests in the browser checks were restricted to this static public preview directory.

These results verify static publication, not application functionality, a completed cyan interface, production selector, screen-reader conformance or new real-device testing. The earlier review's acceptance limits remain in force. Application code, runtime, dependencies, protected branches and Jenkins were unchanged. The pre-existing release-status 404 remains a separate website maintenance finding.
