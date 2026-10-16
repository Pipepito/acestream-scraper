# PR #207 local validation — 2026-10-09

This is a dated local test record, not a release approval or a Jenkins result.
Base: `develop` at `6ac3a8593de796e64de01b73175a2994ac0de833`.
Changes: `fix/pr207-live-validation`, intended for `develop` and subsequently
release PR #207. No release, image publication, or shared installation mutation
was performed. The supplied installation was read only to obtain source URLs.

## Guide matching reproduction (#204)

A fresh, disposable Docker database imported a public
[New Era M3U](https://github.com/yIsus-mEx/AF1CIONADOS/blob/main/Acestream.Lista.New.Era.26.02.25.m3u),
the supplied IPNS source through its configured gateway, and the supplied F1 HTTP
source. The combined catalogue contained **466 unique streams**, 144 with imported
`tvg_id` values. These are different data from the contributor's 589/1007-stream
catalogues; the results are not a repeat of their exact counts.

The [ES1 guide](https://epgshare01.online/epgshare01/epg_ripper_ES1.xml.gz) imported
373 guide channels and 33,222 programmes. With this guide alone, none of the 144
imported stream IDs resolved. Analysis through the running Docker API, before
any assignments:

| Threshold | Before: guide channels / streams | After: guide channels / streams |
| --- | ---: | ---: |
| Strict | 0 / 0 | 54 / 174 |
| Balanced | 2 / 6 | 60 / 191 |
| Loose | 18 / 47 | 73 / 229 |

These improvements combine unresolved-ID fallback and removal of publisher
suffixes after `-->`. A separate comparison on a cloned catalogue, with the same
373 guides and no TV assignments, isolated the two changes: original strict
matching found 0/0; ID fallback alone found 10/13; fallback plus suffix handling
found 54/174. The full change retains source-scope ambiguity, country/edition
checks, protected/inactive/assigned stream exclusion, and the comparison budget.
Resolvable IDs remain authoritative across **all** imported sources, including
ones disabled or outside the selected source filter.

Docker analysis took approximately 0.6 seconds after the change, compared with
2–4 seconds in the single-guide baseline. These are local observations under
varying build/test load, not a benchmark guarantee. The isolated same-process
comparison took 1.03 seconds originally, 0.48 seconds with fallback/indexing/bounds,
and 0.43 seconds with suffix handling too. Indexed resolvable IDs and safe
SequenceMatcher upper bounds keep the extra fallback work bounded.

The [dobleM guide](https://github.com/davidmuma/EPG_dobleM/blob/master/guiaiptv.xml)
also imported successfully: 639 guide channels and 83,109 programmes. With both
guides imported, 114 stream IDs resolved, so those IDs correctly constrain the
source choice. Unique accepted stream counts stay below catalogue size; candidate
ties do not count as accepted assignments.

## Manual workflow checks

- Chromium at 1440px and 390px, in light and dark themes: strict preview, no
  preselection, row selection, enabled Apply, threshold change clearing selection,
  and no page-level horizontal overflow. Five checks passed, including apply.
- Applied the reviewed Antena 3 row from the live catalogue: one TV channel and
  one stream linked; original `tvg_id="Antena 3 HD"` preserved. M3U and XMLTV both
  exported `Antena.3.es`, with programme records under that ID. Playlist coverage
  displayed 1 linked stream out of 466.
- Changed a proposed stream after preview: apply returned HTTP 409 with no
  assignment. Restored the test stream afterwards.
- Enabled automatic matching and refreshed ES1: 35 channels created, 91 streams
  assigned. A second refresh created/assigned zero. Existing Antena 3 name, guide,
  favorite and channel number remained unchanged. Disabled automation afterwards.
- In a separate token-protected container, all nine current/legacy M3U routes
  rejected unauthenticated requests. Each accepted query-token, Bearer and
  X-Api-Token requests, advertised a working authenticated XMLTV URL and returned
  `Cache-Control: private, no-store`. XMLTV alone rejected missing credentials.
  Diagnostics ZIP and storage endpoints also enforced authentication and worked
  with the test credential.
- The configured F1 HTTP source and IPNS gateway source imported successfully.
  The supplied `acestreamid.com` source timed out; the supplied Pages source
  returned no channels. These upstream outcomes are not claimed as passing imports.

- A live-source re-import exposed an ownership conflict in automatic M3U
  association. The fix preserves existing owners, protected and inactive streams.
  Re-importing the same 178-stream M3U twice succeeded and preserved all 109
  existing assignments in the previously failing disposable database.

## Docker, Kubo and engine access

- Built `scraper-acestream-acexy` for native `linux/arm64` through
  `scripts/ci/build_multiarch_images.sh`. Final local image ID:
  `sha256:20a11e16dfebf1b9b7c9815f92dbf2bf995885ccdcb80f6624863e5b1c1f1d14`.
  Both the bundled-services container and a services-disabled container using
  that engine became healthy.
- Updated Kubo from 0.43.0 to the official [0.43.1 release](https://github.com/ipfs/kubo/releases/tag/v0.43.1).
  Verified upstream SHA-512 pins for amd64 and arm64 through real installer
  downloads. ARM64 reported `ipfs version 0.43.1`; the amd64 binary reported the
  same version in a matching amd64 Debian userland under Docker emulation.
- Added content through bundled Kubo and fetched the identical bytes through its
  published HTTP gateway. ARMv7 still follows the explicit no-binary path; its
  installer contract test passed. No real ARMv7 hardware validation was done.
- AceStream 3.2.17 answered its version API from the Docker host and a different
  container with the existing default `ACESTREAM_BIND_ALL=true`. The process
  command included `--bind-all`. `ACESTREAM_HTTP_HOST=localhost` is an internal
  destination, not a remote-client restriction; changing it to `0.0.0.0` is not
  needed. The generator now explains this, the explicit all-IPv4 port mapping,
  and the opt-out address filter when the engine API is published. A Chromium
  browser check confirmed both default and opt-out guidance and generated values.
- Use the canonical build script for application images: a raw Dockerfile build
  without Acexy build arguments uses its test fixture. The initial exploratory
  raw build was replaced before the real browser journeys.

## Automated validation

- Full canonical gate: **1,526 backend tests passed, 3 skipped**; **79 frontend
  suites / 444 tests passed**; lint, typechecking, generated API drift, production
  build, and standalone Pages payload checks passed. The gate also ran its four
  selected Docker documentation/manifest contracts successfully.
- Focused matching, TV-channel and Kubo installer run: **103 passed**.
- After the re-import fix, scraper, TV-channel and guide setup regressions:
  **142 passed**, including two new ownership/opt-out cases.
- Focused engine, ARM DNS, cache and Kubo runtime contracts: **44 passed**.
- Command-builder contract, Docker manifest metadata and strict legacy-path
  checks passed.
- The final full gate includes both the re-import ownership fix and the Live TV
  breakpoint correction. A focused run of all **8 LiveTV unit tests** also passed.

## Browser journey results and limitations

The initial complete Firefox run against real Docker services passed 32 tests,
failed four, skipped one, and left 13 serial-dependent tests unrun. Investigation
found an intermittent EPG poll socket reset (the actual import succeeded), loose
selectors choosing similarly named streams, and a mobile resize scroll defect.
A subsequent run also exposed an old schedule expectation that included programmes
which had already ended. Exact selectors and the current/upcoming programme
expectation were corrected; no assertion was removed to hide a product failure.
The first rerun passed EPG import, stream assignment and all playlist checks.

The final fresh-database Firefox run passed **49**, skipped **1**, and failed
**0**. The skipped reorder journey required two TV channels; after adding two
explicit disposable samples, its focused rerun passed with strict error monitoring.
All **50 journey cases** were therefore exercised successfully across these runs.
The full run recorded no unexpected error-monitor annotations. The live-peer
case accepts a visible failure; its actual outcome is documented below.

The existing responsive UI suite passed **76/76** checks across 390px Chromium,
320px WebKit, 768px Firefox and 1440px Chromium, covering both themes, guide
review, opt-in automation, playback controls, routing, schedules and startup
recovery. These tests use mocked guide/media responses; they complement the real
Docker journeys rather than demonstrating live peer delivery.

Controlled-media HLS playback reached browser-ready video and stopped its engine
session when the viewer closed. The real-peer playback attempt ended with the
visible error “The stream stopped unexpectedly. Try again.” The suite deliberately
accepts either playback or a clear failure for peer-dependent streams, so a passing
journey is **not** evidence of successful live-peer media delivery. Acexy also
answered status requests; a live stream request could time out without media.
WARP was kept disabled. No claim is made for WARP routing, remote physical players,
ARMv7 hardware, or a complete amd64 application runtime.

Local screenshots, traces, JSON results, databases and logs are retained only in
ignored `e2e/.stack/`, `e2e/test-results/`, `e2e/results/` and task-specific `/tmp`
paths; none are committed. Re-run live sources to obtain fresh evidence.

To refresh GitHub release status separately:

```sh
gh pr view 207 --json state,mergeable,mergeStateStatus,statusCheckRollup,updatedAt,url
```
