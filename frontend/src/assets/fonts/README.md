# Self-hosted fonts

Inter and Barlow Condensed are the approved review-06 fonts. The complete original
glyph sets and variable weight range are retained; WOFF2 changes compression only.
Original TTFs are in the design package at `de69e644428abe5d0e4149b4e437d37996c4b769`,
`docs/design/ux-review-314/assets/{inter,barlow-condensed}.ttf`. The manifest records
source/output hashes, sizes and conversion versions. Licences remain distributed
under `frontend/public/static/fonts/`.

Reproduce with fonttools 4.68.0 and brotli 1.2.1 in an isolated tooling environment:
load each source with `fontTools.ttLib.TTFont`, set `font.flavor = 'woff2'`, then
`font.save(destination)`. No subsetting, style changes or runtime dependency.

Theme imports let Vite resolve the asset for both the installed SPA and the
relative-base standalone recipe helper. Do not restore absolute `/static/fonts`
URLs: those bypass the standalone helper's deployment base and leave it without
its selected fonts. Both faces use font-display swap and system fallbacks.
