# Combined design deliverables

Integration: 10 November 2026, on top of application commit `f31d7a7f` for PR #325.
These collections preserve three distinct identities: **ZZTREAM**, **SPORTZZ**
and the existing **ZZSTREAMS** design work. Filenames and artwork retain the
spelling/case supplied by their authors; importing a kit does not select a new
application identity.

## Collections

| Collection | Entry point | Contents |
| --- | --- | --- |
| ZZTREAM identity v1 | [Manual PDF](zztream/manual-v1/zztream-manual-identidad-v1.pdf), [kit guide](zztream/manual-v1/LEEME.md) | 20-page manual, vector/PNG signatures, tokens, image originals and derivatives, licensed fonts, previews and construction scripts; 57 files |
| SPORTZZ visual library v1 | [Catalogue](sportzz/visual-library-v1/index.html), [asset guide](sportzz/visual-library-v1/ASSET-README.md) | Eight photos, eight mockups, five primary graphics, masters/optimized variants, 70 individual SVG icons and sprite, brand/font assets, manifests and sources; 205 files |
| SPORTZZ 10-second promo | [Player](sportzz/brand-promo-10s/index.html), [production guide](sportzz/brand-promo-10s/README.md) | Four MP4 exports, silent WebM, poster/storyboard, retouched source plate, Spanish voice/audio stems, tracking, vectors/fonts and construction scripts; 60 files |
| Existing ZZSTREAMS design and application work | [Design reference](../docs/design/ux-review-314/README.md), [integration snapshot](../docs/design/ux-review-314/pr325-integration.md), [category implementation](../docs/dev/tv-categories.md) | Existing application/category artwork, brand/component reference, mockups and gallery remain at their established paths |

The **322 copied files (206,966,052 bytes)** are byte-identical to their source
deliverables. [integration-manifest.json](integration-manifest.json) records every
included file's source-relative path, SHA-256, size and role, plus every excluded
file and reason. It records 16 copies identical to already-versioned design
assets. Those copies preserve self-contained collections and relative links;
different logo/icon variants have not overwritten existing work. No shared
original has been moved or modified.

## Final assets, sources and rejected material

- `assets/`, `logos/` and the promo's root exports are the supplied delivery
  assets. Use their individual provenance and usage records when selecting them.
- `source/`, `sources/` and `previews/` contain construction, reference and review
  material, not runtime assets. The visual library's two rejected original images
  remain explicitly under `sources/rejected/`. Its generated motion study is a
  reference master; the reconstructed SVG/WebP is the final graphic.
- The unretouched video `sportzz-generated-source-preview.mp4` contains the
  unwanted third-party shoe mark. It and editing/calibration frame dumps remain
  in the original local directory and are **excluded from Git and packages**.
  The promo follows the supplied 59-entry final-delivery manifest, plus that
  manifest itself. Repeating raw-source retouching requires the local original;
  the corrected picture, mask, tracking and audio stems are included.
- The promo is **1280 × 720, 24 fps, 240 frames, exactly 10 seconds**. Master and
  web MP4 have Spanish voiceover/sound; silent MP4, clean MP4 and WebM have no
  audio. `clean` is the corrected plate for alternate composition, not the
  finished commercial. No resolution change or new generation was performed.
- Font OFL files, attribution, prompts, source manifests and historical validation
  reports remain intact. Historical reports describe the original sessions, not
  this integration. Some archived construction/review scripts retain workstation
  paths and temporary-transfer assumptions: review/configure those before running
  them in a scratch copy. They are not invoked by integration verification or
  packaging. See [VALIDATION.md](VALIDATION.md) for fresh checks.

This is a repository archive for review and reuse. `design-assets/` is excluded
from the Docker context, is outside `frontend/` and Pages' `docs/` tree, and is
not added to the existing Pages exporter. Importing these files does not deploy
them. The supplied brand/rights/creative-review limitations remain in each kit.

## Storage and reproducible packaging

There is no existing Git LFS convention. All canonical files fit ordinary Git;
the largest is the 13.78 MiB manual PDF. Four duplicate ZIPs remain local:

- `zztream-kit-identidad-v1.zip`
- `sportzz-visual-assets-collection-1.0-complete.zip` (**144.49 MiB**, above the
  ordinary GitHub per-file limit)
- `sportzz-visual-assets-collection-1.0-web.zip`
- `sportzz-brand-promo-10s-delivery.zip`

Caches and `work/` media are also excluded. The complete per-file omission list
is in the integration manifest; there are no omitted canonical large assets.

Create deterministic complete archives from the recorded files, without generation,
network access, source-directory dependencies or modification of the collections:

```sh
python3 design-assets/tools/package.py --output /tmp/opencode/design-deliveries
```

Each ZIP uses a collection-specific top-level directory, sorted entries and fixed
timestamps/permissions. Running the command with the same Python/zlib versions
produces identical ZIP bytes. It recreates the canonical contents, not necessarily
the byte layout of the historical ZIPs. The full visual-library archive includes
clearly separated `sources/rejected/` references; never deploy the entire archive.
Retain the complete library and select optimized paths from its manifest for web
use rather than making a second duplicate ZIP in Git.

## Verify or review locally

For technical verification, install Pillow and PyMuPDF in a disposable environment
(the integration used Pillow 13.0.0 and PyMuPDF 2.1), and provide FFprobe:

```sh
python3 design-assets/tools/verify.py
```

This verifies copied hashes, both supplied checksum manifests, complete inventory,
file-size limits, image/PDF decoding, local HTML/CSS references, SVG IDs and icon
geometry, documented image dimensions and the five final media specifications.
It reads files only and prints a new report; it does not rewrite historical reports.

The catalogues work under a temporary HTTP server rooted here (external SVG
sprites require HTTP). Stop the server after review:

```sh
python3 -m http.server 18863 --bind 0.0.0.0 --directory design-assets
```

Open `/sportzz/visual-library-v1/` or `/sportzz/brand-promo-10s/` on that server.
Current desktop/mobile captures and the integration check results are described
in [VALIDATION.md](VALIDATION.md).
