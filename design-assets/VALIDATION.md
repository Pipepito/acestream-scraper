# Asset integration verification — 10 November 2026

Scope: the combined deliverables added to PR #325 on top of application revision
`f31d7a7fd3c7beb935aa25e701322853160f9d78`, in the `pr325-zzstreams-sync`
worktree. The integration manifest pins the exact copied bytes. This record
describes fresh integration checks; supplied reports dated 9 November are retained
unchanged as historical provenance.

## Passed

| Check | Fresh result |
| --- | --- |
| Source/copy inventory | 322 files, 206,966,052 bytes; SHA-256 and byte lengths match; 52 exclusions explicitly inventoried; sources preserved |
| Supplied checksum manifests | All 204 visual-library entries and 59 promo entries match |
| Storage | No canonical file reaches 100 MiB; largest is the 13.78 MiB PDF; four duplicate ZIPs excluded |
| Decoding and references | 162 images decoded, 97 SVGs parsed with unique per-document IDs, 11 JSON documents parsed, 162 local HTML/CSS/fetch references resolve |
| Visual library | Eight photos, eight mockups and five primary graphics; manifest dimensions match; seamless texture edges match |
| Icons | 70 unique individual SVGs, 70 unique sprite symbols, exact geometry/style correspondence; every external symbol renders `currentColor` pixels |
| Manual | 20 pages rendered, 960 × 600 points, selectable text; both actually used fonts embedded; contact sheet and cover inspected |
| Media | All five final exports decode to 240 frames at 24 fps, exactly 10.000 seconds, 1280 × 720; four H.264 MP4s and one VP9 WebM |
| Audio presence | Master/web MP4 have audio; clean/silent MP4 and WebM have none; voice/mix stems preserved by checksum |
| Browser | Isolated VM Chromium at 1440 × 900 and 390 × 844; catalogues load, icon search/theme/16–32 px sizing work, all five videos advance in playback, seeking works; no console/page/request failures or horizontal overflow |
| Packaging | Three independently rebuilt ZIPs match byte-for-byte across two runs; ZIP CRC checks pass; no excluded source, ZIP, cache or `work/` file in packages |
| Existing design regression | 4,077 links, 674 fragments, 146 screens, 876 current exports and 288 historical exports checked; no drift/failures |
| Repository checks | Four documentation contract tests pass; strict legacy-path assertion and Docker metadata validation pass; new integration tools pass Ruff |
| Prerequisites | `workspace-prepare` passes package consistency, Docker/Compose/Buildx, native media provenance and isolated Chromium/Firefox/WebKit readiness |
| Secret scan | Gitleaks directory scan reports no leaks |
| Staged contents | All 330 staged paths are scoped to this import; the 322 staged asset hashes still match the originals |

The full `git diff --cached --check` reports seven inherited trailing-space lines:
one in the supplied FFmpeg loudness measurement and one in each of the six OFL
licence copies. These source bytes and their supplied manifest checksums were
preserved deliberately. Integration-authored documentation/scripts and the two
root configuration edits pass the whitespace check. No other staged whitespace
issue was reported.

The initial verifier assumed four PDF fonts, but this document actually uses and
embeds two. The check now validates the fonts used by text spans rather than
unused font registrations. A mistyped test path ran no tests; the corrected
documentation-test invocation above passed. Initial tool lint issues and a Pillow
pixel-helper deprecation were corrected; final tool and pixel checks passed with
warnings treated as errors where applicable.

## Commands and evidence

```sh
python -W error design-assets/tools/verify.py
python3 design-assets/tools/package.py --output /tmp/opencode/pr325-assets-pack-a
python3 design-assets/tools/package.py --output /tmp/opencode/pr325-assets-pack-b
workspace-test ruff check design-assets/tools
workspace-test pytest -q backend/tests/docker/test_docs_contract.py
workspace-test bash scripts/ci/assert_no_legacy_paths.sh --strict
workspace-test python scripts/ci/validate_docker_manifest_metadata.py
workspace-test python docs/design/ux-review-314/check_artifacts.py --output /tmp/opencode/pr325-assets-design-check
gitleaks dir design-assets --redact --no-banner
```

`python` for the media/PDF verifier was the disposable
`/tmp/opencode/pr325-assets-venv/bin/python` (Pillow 13.0.0, PyMuPDF 2.1); FFprobe
was the system decoder. Browser verification used this checkout's installed
Playwright, with requests confined to the temporary local catalogue server.
New screenshots are local evidence, excluded from Git:

```text
artifacts/visual-review/pr325-deliverables/
  library-desktop.png  library-mobile.png
  icons-desktop.png    icons-mobile.png    icons-contact.png
  promo-desktop.png    promo-mobile.png
  promo-shoe.png       promo-sports.png    promo-experience.png  promo-brand.png
  manual-cover.png     manual-contact.png
```

Machine reports are under `/tmp/opencode/pr325-assets-*`; they are not substituted
for the original manifests or committed as runtime logs. The temporary HTTP server
and isolated browser were stopped, and port 18863 was verified free.

## Scope remaining

The full application/Docker/native-architecture/E2E matrix was not rerun locally
for this archival import. The owner previously selected Jenkins for remaining
full validation; a successful focused asset check is not a full CI pass for the
new commit. No release, Pages publication, application deployment or paid
generation is part of this import. The existing creative/rights limitations are
retained in the supplied documentation. Technical playback checks were muted;
Spanish voiceover identity follows the supplied production record and preserved
audio hashes, not a new listening/creative approval.
