# Static preview publication — review 06

The current verified repository setting serves **`gh-pages` at `/`**, using GitHub-managed legacy Pages builds with HTTPS. The earlier repository narrative saying `main` at `/docs` is stale for this preview setup; recheck before publication. Pages is not the application validation/deployment pipeline.

Public preview: [AceStream design review](https://pipepito.github.io/acestream-scraper/design/ux-review-314/). Only static design content is authorized. Do not merge application branches, replace installation tools with the design branch's older docs snapshot, trigger Jenkins or publish images/releases.

## Safe preparation and publication

1. Inspect clean/dirty worktrees and recheck `develop`, `main`, design and `gh-pages` tips. Re-fetch current issue bodies before updating them.
2. Read the current Pages configuration with `gh api repos/Pipepito/acestream-scraper/pages`. The GitHub connector has no Pages-administration read capability; the read-only CLI fallback is appropriate.
3. Commit the completed design package on its isolated task branch (currently `pepe/sportzz-brand-system`). Build from this immutable local SHA. A local design commit does not authorize or require pushing the application/source branch.
4. Stage the **current `gh-pages` snapshot** in an empty temporary output. Replace only its `design/ux-review-314/` subtree. Preserve every other site file byte for byte. `prepare_pages_preview.py` checks this invariant and pins both SHAs. The main/docs option is only for a separately reconciled baseline; do not overwrite independent current site changes.

```sh
workspace-test python docs/design/ux-review-314/prepare_pages_preview.py \
  --site-ref CURRENT_GH_PAGES_SHA --site-prefix . \
  --design-ref DESIGN_COMMIT_SHA --local-docs \
  --output /tmp/opencode/acestream-pages-brand-stage
```

5. Verify the candidate's links, images, selector, canonical workflows and local no-network constraints. Inspect landing/gallery phone and desktop compositions. The public prototype may store only its namespaced design preset.
6. Read `/opt/opencode-workspace-hooks/static-pages-route.md`. In an isolated worktree at the freshly checked remote `gh-pages` tip, copy only the prepared preview subtree and make one commit. Confirm the diff contains no other site paths and the publishing worktree is clean. Within the owner's publication authorization, push only `HEAD:refs/heads/gh-pages` to origin. The installed guard validates this narrow static route. If the remote advanced, regenerate over its new tip instead of force-pushing. Keep hooks intact; this route does not waive application validation.
7. Wait for the GitHub Pages build, then verify hosted index, all three launch presets, gallery, new CSS/JS/assets and manifest. Preserve existing installation tools and release-site content; hash comparisons and hosted probes belong in the current verification report.

Use `--local-docs` when the design source SHA is not publicly available. This option requires the checkout-local `Markdown==3.11.3` package (`workspace-test python -m pip install Markdown==3.11.3`); it is not an application dependency. It renders top-level Markdown as `*.md.html`, preserving heading fragments and relative navigation. Linked code becomes escaped, inert HTML snapshots with line anchors; no Python/TypeScript server scripts are deployed. Referenced JSON and historical screenshots are included from the same immutable source. The export fails on missing local assets or fragments and records document/link counts in its manifest. Without this option, the historical exporter mode points Markdown at the source SHA on GitHub and is suitable only when that SHA is already published.

Fonts retain their notices. The ZIP, supplier application, original media masters, live data, private screenshots, logs and caches are excluded. Deliberately synthetic design exports and explicitly linked historical design screenshots are public artifacts.

This procedure publishes design previews only. A page being built does not prove backend functionality, application CI, accessibility conformance, device behavior or owner approval of every visual decision. The current result and SHAs are recorded in [verification](verification-review-06.md).

## Published snapshot — 7 November 2026

Design source `530b366996265d351fe2ede9b29f462b1d3d6178`; Pages commit `c20548ab0dedaecdfec5a322595183c498091eaa`; previous site `ebea374d0e62da1ac7bf52c322ccad8daf1990fd`. GitHub Pages reported built at 21:19:33 UTC. All 102 non-preview files were preserved and all 1,290 hosted files matched the staged hashes. See the [public manifest](https://pipepito.github.io/acestream-scraper/design/ux-review-314/publication-manifest.json) and the verification report for hosted browser evidence and remaining manual acceptance. A later documentation-only commit records publication; rendered assets remain pinned to the design source above.
