# Static preview publication — review 06

The current verified repository setting serves **`gh-pages` at `/`**, using GitHub-managed legacy Pages builds with HTTPS. The earlier repository narrative saying `main` at `/docs` is stale for this preview setup; recheck before publication. Pages is not the application validation/deployment pipeline.

Public preview: [AceStream design review](https://pipepito.github.io/acestream-scraper/design/ux-review-314/). Only static design content is authorized. Do not merge application branches, replace installation tools with the design branch's older docs snapshot, trigger Jenkins or publish images/releases.

## Safe preparation and publication

1. Inspect clean/dirty worktrees and recheck `develop`, `main`, design and `gh-pages` tips. Re-fetch current issue bodies before updating them.
2. Read the current Pages configuration with `gh api repos/Pipepito/acestream-scraper/pages`. The GitHub connector has no Pages-administration read capability; the read-only CLI fallback is appropriate.
3. Commit the completed design package on `design/ux-review-314`. Build from this immutable SHA.
4. Stage the **current `gh-pages` snapshot** in an empty temporary output. Replace only its `design/ux-review-314/` subtree. Preserve every other site file byte for byte. `prepare_pages_preview.py` checks this invariant and pins both SHAs. The main/docs option is only for a separately reconciled baseline; do not overwrite independent current site changes.

```sh
python3 docs/design/ux-review-314/prepare_pages_preview.py \
  --site-ref CURRENT_GH_PAGES_SHA --site-prefix . \
  --design-ref DESIGN_COMMIT_SHA --output /tmp/acestream-pages-review06-stage
```

5. Verify the candidate's links, images, selector, canonical workflows and local no-network constraints. Inspect landing/gallery phone and desktop compositions. The public prototype may store only its namespaced design preset.
6. In an isolated worktree at the freshly checked `gh-pages` tip, copy only the prepared preview subtree and commit. Confirm the diff contains no other site paths. Push a normal fast-forward to `gh-pages`; if the remote advanced, reconcile and regenerate instead of force-pushing.
7. Wait for the GitHub Pages build, then verify hosted index, all three launch presets, gallery, new CSS/JS/assets and manifest. Preserve existing installation tools and release-site content; hash comparisons and hosted probes belong in the current verification report.

Markdown specification links in published HTML/engine resolve to the immutable design commit on GitHub. Fonts retain their notices. The ZIP, supplier code, original media masters, live data, private screenshots, logs and caches are excluded. Deliberately synthetic design exports are public artifacts.

This procedure publishes design previews only. A page being built does not prove backend functionality, application CI, accessibility conformance, device behavior or owner approval of every visual decision. The current result and SHAs are recorded in [verification](verification-review-06.md).
