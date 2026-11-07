# v2.1 working triage

Updated 2026-09-15 after the maintainer closed completed and superseded issues.
Source: `gh issue list --state open --limit 100 --json number,title,body,labels,url`.
There are 13 remaining issues: #13, #41, #55, #93, #99, #102, #122,
#149, #153, #155, #158, #159 and #160. Recheck GitHub before reporting closure.

## Current work

- #155: retirement deferred by maintainer decision. v2.1 retains all six legacy
  names with deprecation warnings in logs and Overview; canonical values win.
  This issue is not a v2.1 closure candidate.
- #149: implemented locally. Shared pinned HTTP clients cover HTTP/IPFS, ZeroNet
  pages and iframe redirects, nested M3U, recipes and EPG; Host/TLS identity is preserved.
- #153: implemented locally. EPGService is a stable 12-line facade over source,
  XMLTV processing, channel/matching and export modules (all below 300 lines).
  Existing frontend pages are 400 and 374 lines. The recorded XML export is unchanged.
- Extraction builder: guide expanded with HTML, JSON and raw-regex walkthroughs,
  limits, troubleshooting, save/run instructions and an in-builder guide link.
- #122: selected and implemented locally. Manual/bulk/scheduled checks persist the
  latest peers and P2P download/upload rates with their observation time; desktop
  and phone channel lists show them alongside separately measured media bitrate.
  The issue's statistics-collection request is covered; history, automatic playlist
  thresholds and looping-content detection remain follow-ups, not closure claims.
- #41: notifications remain a separate optional feature.
- #93 and #102: need current network / multi-viewer reproduction, not closure claims.
- #13, #55, #99: defer native packages, sports aggregation and VOD catalogue.
- #158–#160: close only when their remaining child scope is complete; do not count
  them as independent implementation tasks.

Core implementation is not a release or an issue closure. #149/#153 become
closure candidates after review and merge; #159 and #160 must be reconciled against their child lists, including deferred #155. #158 remains a community roadmap.

## Core-pass verification (2026-09-15, uncommitted working tree)

- Backend: `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker` — 1,371 passed, 3 skipped.
- Frontend: `npm test -- --runInBand` — 76 suites, 431 tests passed.
- Typecheck, zero-warning lint, app/helper builds, documentation links, command-builder
  runtime contract and strict legacy-path check passed.
- OpenAPI and generated TypeScript hashes unchanged by this maintenance pass.
- 30 EPG method bodies are unchanged; the source-fetch method alone switches to
  the pinned client. Recorded XML output matches the existing fixture.
- New connection tests cover real HTTP pinning and Host preservation, blocked
  rebinding and literal-address redirects, TLS pool SNI/hostname settings, and
  disabled environment proxies.
- No GitHub issue was closed or edited by this pass. No release, image publication
  or Jenkins job was triggered. The existing local test containers were left running.

The selected #122 statistics feature is implemented locally. Notifications #41
remain the next separate feature candidate.
Do not close #93/#102 without a current network/multi-client reproduction.

## #122 verification (2026-09-15, uncommitted working tree)

- Full backend run: 1,376 passed, 3 skipped; eight checks were blocked by sandbox
  socket/process/file-descriptor access. Rerunning the affected tests with access
  passed (11 tests, including three already-passing outbound-client checks).
  Combined result: 1,384 backend tests passed, 3 skipped.
- Frontend: 77 suites / 433 tests passed, plus typecheck, zero-warning lint and
  both app/helper builds. Documentation, command-builder and legacy-path checks passed.
- Fresh and prior-head migrations, downgrade/re-upgrade, preserved channel data,
  numeric validation, atomic samples, zero/unknown handling, API serialization,
  engine-unavailable preservation and media-signal independence are covered.
- Local ARM64 all-services image rebuilt and test container restarted with its
  existing settings/volumes. Healthy; desktop light and phone dark browser checks
  passed using response fixtures without changing the user's channel data.
- Installed extraction builder and public hub browser checks passed after restart.
- #122's core statistics request is a closure candidate after review/merge;
  historical trends, playlist thresholds and loop detection remain separate scope.
  No GitHub issue mutations, publication, release or Jenkins runs were performed.

## Pre-merge mitigations and storage (2026-09-15)

- Maintainer decision: retain legacy environment names with name-only warnings;
  canonical settings win. #155 retirement is deferred and is not closed by v2.1.
- Overview reports container mount destinations, allocated directory sizes and
  filesystem free space through a bounded, cached, isolated scan. No Docker socket
  or host mount-source disclosure. Partial and unavailable results are explicit.
- Preview request admission, authentication, wire-byte limits and temporary spooling
  precede JSON parsing. Uploads have a 30-second deadline; 32 MiB source support stays.
  Browser rendering has a separate budget and raw/manual-field fallbacks.
- Pinned synchronous HTTP retries validated addresses; real HTTPS tests verify SNI,
  trust and hostname rejection. Startup upgrade/backup/restore preserves prior data.
- Full backend run: 1,393 passed, 3 skipped, one middleware-order assertion failed.
  After restoring forwarded-header middleware as outermost, all 19 middleware/upload
  checks passed. Combined final coverage: 1,394 passed, 3 skipped.
- Frontend: 78 suites / 437 tests passed; typecheck, zero-warning lint, app/helper
  builds, documentation, command-builder, Dockerfile/manifest and legacy guards passed.
- ARM64 all-services image rebuilt, current test container healthy with existing
  settings/volumes. Live report detected all six data mounts with sizes/free space.
  Desktop light and phone dark checks passed. Initial browser check used an invalid
  /overview URL; the corrected / route passed. Installed builder and an 8 MiB source
  fetch/extraction passed without writing source/channel data.

## Original assessment (historical)

The following 2026-09-14 assessment predates the closures and builder implementation.
Its issue states and proposed details are historical. The implementation contract is
in `docs/dev/extraction-recipes.md` and `wiki/Extraction-Recipes.md`.

# v2.1.0 issue triage and scraper-builder proposal

Snapshot: 2026-09-14. Reviewed all 27 open issues and their comments in Pipepito/acestream-scraper, plus the titles of all 68 closed issues. Baseline: `main` at `d6047f12b68e36e99f268ea1d5cb4f20b5ce40d1`. Local main was fast-forwarded from `81cc4fa`; the untracked `.claude/` directory was preserved. No application changes, releases, issue comments, milestone changes, or issue closures are part of this work.

## Disposition of every open issue

“Resolved” means the requested behavior is implemented in the reviewed main tree, supported by the evidence below; it does not imply every original deployment was reproduced. “Superseded” means the v2 workflow or architecture replaces the original request. Partial issues remain work.

| Issue | Disposition | Evidence and remaining scope |
|---|---|---|
| [#13 Release packages](https://github.com/Pipepito/acestream-scraper/issues/13) | Open; defer | Docker images and source installation exist, but downloadable native application packages remain separate packaging, updating, and platform-support work. |
| [#41 Notifications](https://github.com/Pipepito/acestream-scraper/issues/41) | Open; feasible stretch | Background task results and persisted job history provide hooks. Start with completion/failure webhooks; Telegram/Gotify adapters can follow. |
| [#45 Acexy custom-port health](https://github.com/Pipepito/acestream-scraper/issues/45) | Resolved in v2 | `healthcheck.sh` derives the probe port from `ACEXY_LISTEN_ADDR`; Overview does too. Parameterized `test_acexy_probe_follows_listen_addr` passes. The runtime contract includes `:8084`, although the full local runtime validator did not complete in this review. |
| [#55 Sporting events](https://github.com/Pipepito/acestream-scraper/issues/55) | Open; defer | Event ingestion, timezones, deduplication, channel mapping and an events interface form a separate feature. Generic extraction could help later, but does not deliver event aggregation. |
| [#61 Browser playback/base URL](https://github.com/Pipepito/acestream-scraper/issues/61) | Superseded by v2 | Built-in HLS playback, Live TV, and configurable named stream-link formats cover the original goal of watching without a hardcoded `acestream://` link. This is not a claim that every row now has the exact requested right-click anchor behavior. |
| [#93 WARP remote access](https://github.com/Pipepito/acestream-scraper/issues/93) | Open; needs reproduction | The reverse-proxy guide explains the full-tunnel interaction and workarounds. Documentation is not evidence that simultaneous WARP egress and inbound remote streaming are fixed. |
| [#97 Regex EPG search patterns](https://github.com/Pipepito/acestream-scraper/issues/97) | Resolved in v2 | `EPGService.auto_map_channels` and match analysis recognize slash-delimited regex; `test_auto_map_channels_regex` passes. This issue concerns EPG mapping, not custom source extraction. |
| [#99 Movie/VOD scraping](https://github.com/Pipepito/acestream-scraper/issues/99) | Open; defer | M3U ingestion already exists. A movie catalogue with metadata, library UI and integration remains separate product scope. |
| [#101 Swagger Base64 URL docs](https://github.com/Pipepito/acestream-scraper/issues/101) | Superseded by v2 | The old Flask `/api/doc` URL contract has been replaced by typed FastAPI routes; source CRUD uses integer `url_id`, not Base64-encoded source URLs. |
| [#102 Acexy multiple channels](https://github.com/Pipepito/acestream-scraper/issues/102) | Open; reproduce first | Supervision, playback ownership and Acexy routing improve the surrounding behavior. They do not prove the reported two-channel failure or three-viewer 15–20 minute failure is gone; comments also report it in standalone Acexy. |
| [#109 Last update says never](https://github.com/Pipepito/acestream-scraper/issues/109) | Resolved in v2 | Channel repository persists `last_checked`, the API exposes it, and the stream table renders that field. Channel/backend and table/frontend tests pass. |
| [#114 Missing group-title](https://github.com/Pipepito/acestream-scraper/issues/114) | Resolved in v2 | Extraction/persistence tests cover `group-title`, EXTGRP, logo and EPG IDs; playlist tests cover export metadata. |
| [#121 Refresh removes mappings](https://github.com/Pipepito/acestream-scraper/issues/121) | Resolved in v2 | Scraper upserts surviving IDs instead of deleting them, and updates preserve existing TV associations. An isolated same-ID scrape verified that the mapping, favorite and channel number survive. IDs actually removed from a nonempty source remain eligible for removal. |
| [#122 Advanced stream stats](https://github.com/Pipepito/acestream-scraper/issues/122) | Partial; feasible follow-up | v2 stores encoded media bitrate, verifies A/V delivery and supports a separate checker. `EngineClient` parses peers and P2P speeds, but persisted per-stream statistics, history and quality-threshold filtering are not delivered. Media bitrate is not P2P download speed. |
| [#123 Blank EPG ID on creation](https://github.com/Pipepito/acestream-scraper/issues/123) | Resolved in v2 | EPG-to-TV creation populates `epg_id`; creation and link-repair tests pass, including matching streams to newly created TV channels. |
| [#127 EPG two-hour offset](https://github.com/Pipepito/acestream-scraper/issues/127) | Resolved in v2 | XMLTV parsing normalizes offsets to aware UTC, and exports label UTC. Existing EPG tests pass; isolated checks verify summer `+0200` and winter `+0100` timestamps. This does not certify inaccurate source feeds or already corrupted historical data. |
| [#130 Cannot delete EPG source](https://github.com/Pipepito/acestream-scraper/issues/130) | Resolved in v2 | Source deletion with channels/programs and TV-channel relinking have passing regression tests. |
| [#148 Optional API token](https://github.com/Pipepito/acestream-scraper/issues/148) | Resolved in v2 | Optional token enforcement, player-facing token URLs and health exemptions are implemented; backend authentication and frontend token tests pass. |
| [#149 SSRF guards](https://github.com/Pipepito/acestream-scraper/issues/149) | Partial; prioritize in 2.1 | Destination and redirect validation exist, with tests. `url_guard.py` explicitly states that DNS results are not pinned to connections, leaving an acceptance criterion unmet. Finish connection pinning and review every outbound fetch path, including nested playlists, without breaking configured local gateways. |
| [#150 Reverse-proxy guide](https://github.com/Pipepito/acestream-scraper/issues/150) | Resolved in v2 | `docs/ops/reverse-proxy.md` supplies nginx/Caddy/Traefik, authentication, forwarded headers, tuner routing, exposure and WARP guidance. This review verified the document, not a live deployment of all three examples or a resolution comment on #93. |
| [#153 Oversized modules](https://github.com/Pipepito/acestream-scraper/issues/153) | Partial; bounded cleanup | `EPG.tsx` is 400 lines and `TVChannels.tsx` 374 after extraction. `epg_service.py` remains 868 lines; split its backend responsibilities while preserving its service/API surface. |
| [#155 Retire environment aliases](https://github.com/Pipepito/acestream-scraper/issues/155) | Open; mandatory for 2.1.0 | The alias map and startup application remain. `test_settings_env_compat.py` enforces expiry at final 2.1.0. Remove the shim, revise tests, and document canonical names for users upgrading directly from v1. |
| [#156 Compatibility epic](https://github.com/Pipepito/acestream-scraper/issues/156) | Resolved in v2 | Children #142–#147 are closed; legacy M3U/XML routes, curated/all-streams playlists, refresh and TV endpoint compatibility are implemented with passing tests. Epic checkboxes are stale. |
| [#157 Reliability epic](https://github.com/Pipepito/acestream-scraper/issues/157) | Resolved in v2 | Children #128, #129, #119, #81 and #125 are closed. Current code contains WARP syntax updates, configurable probe behavior, Acexy supervision, opt-in bare-ID extraction and curated numbering. This does not subsume #102's independent long-duration playback report. |
| [#158 Community epic](https://github.com/Pipepito/acestream-scraper/issues/158) | Partial; roadmap stale | #140 ARM engines and #62 named URLs are already closed. #122 remains partial, #41 open, #55/#99 unscoped. Preserve ARMv7 hardware-verification limitations. |
| [#159 Security epic](https://github.com/Pipepito/acestream-scraper/issues/159) | Partial | #148 and #150 are delivered, but #149 still lacks DNS pinning. Do not mark the entire exposure-hardening epic complete. |
| [#160 Maintenance epic](https://github.com/Pipepito/acestream-scraper/issues/160) | Partial | Dependency/earlier cleanup tasks shipped; #153 backend extraction and #155 alias retirement remain. |

Labels: `resolved-in-v2` on 12 issues; `superseded-by-v2` on 2; `partially-implemented` on 6. Replace stale `resolved-awaiting-merge` on #148/#149/#150/#157 with their verified disposition. Leave all issues open for maintainer closure. Existing milestones and issue bodies are unchanged.

## Recommended v2.1 scope

1. **Required release maintenance:** #155 alias removal and its migration notes.
2. **Complete the fetch boundary:** remaining #149 work; this is especially relevant when introducing user-configured extraction from arbitrary source URLs.
3. **Main feature: user-defined extraction recipes.** Two authoring modes, HTML/text and JSON, sharing validation, preview, storage, import/export and the same channel result model.
4. **Optional bounded additions:** the backend portion of #153, or a first slice of #122 showing the latest peers/P2P speed and observation time. Decide capacity after the builder runtime is proven.
5. **Stretch:** #41 completion/failure webhooks with retries and duplicate suppression. Avoid bundling several provider integrations into the initial slice.

#102 and #93 deserve reproduction plans, but are poor fixed-scope release promises without current evidence. Defer native packaging, VOD and sports-event aggregation. The three epics #158–#160 are trackers, not three additional features.

## Builder requirements proposal

The purpose is to let users support sites the maintainer has never seen. No known-site catalogue or site-specific patch should be required for a user to create a working recipe. No matching open issue currently tracks this; the closed-issue title review also found no obvious custom-regex/JSON-builder request. #97 is specifically EPG mapping.

### Shared guided flow

1. **Provide a sample.** Paste HTML/text/JSON or open a saved file. Explain “Elements → Copy outerHTML” and “Network → response body” as optional paths. A console command is not required. Samples stay local to the helper by default.
2. **Choose the repeated record.** For HTML, select a channel row/card and confirm the inferred repetition against at least a second row. For JSON, choose the array containing channel objects.
3. **Choose fields within that record.** Required channel ID/link; channel name with an explicit missing-name policy. Optional group, logo and EPG ID. Support multiple IDs belonging to the same record with an explicit one-to-many rule.
4. **Review every match in the supplied sample.** Show extracted rows, original positions, duplicates, invalid IDs, missing fields, ambiguous mappings, ignored records and counts. A preview can prove coverage of the sample, not completeness of an unseen website, unloaded rows or future pages.
5. **Export and test in the scraper.** Copy the generated rules or download a versioned recipe. Separately open the installed scraper, add or edit a source URL, paste/import its rules, and test against the actual fetched URL there. The public helper never connects to the installation. Its preview verifies only the supplied sample; the scraper's own test reports what its fetch and extraction produce.

### HTML and regex

- Prefer record selectors and relative field selectors for the visual picker. Let advanced users edit a record regex with named captures or separate field regexes applied inside the same record. Two unrelated whole-page match lists must never be zipped together by position.
- Regex can extract a 40-hex ID from a link/attribute, select text, or perform bounded cleanup. Let users inspect what was generated. Do not promise that one click synthesizes a robust regex for arbitrary markup.
- Render a sanitized, isolated preview with scripts, form submission, navigation and network-loading resources disabled. Provide a source/text view when stripped styling makes the preview less recognizable. Preserve a separate original sample for extraction; the displayed sanitized DOM is not the authoritative input.
- Account for browser/backend parsing and regex differences. Python named groups use `(?P<name>...)`, JavaScript uses `(?<name>...)`. Choose a supported subset or a shared runtime and keep a conformance corpus. A JavaScript preview alone cannot certify a Python recipe.
- Enforce limits on input size, patterns, matches, recursion and execution time. A UI timeout or an async wrapper alone does not stop pathological CPU-bound matching; execution must be cancellable in an isolated worker/process or use an appropriately bounded engine.

### JSON mode

- Parse JSON rather than matching its serialized text with regex.
- Select the record-array path, then field paths relative to each object. Example: records `data.channels`, name `title`, ID `stream.acestream_id`, group `category.name`.
- Handle direct arrays and wrapped objects, nested fields, nullable/missing values, duplicate IDs, and IDs supplied as bare hashes or AceStream links. Use the same output validation as HTML extraction.
- Initial runtime scope: public GET endpoints, static responses and one page per run. Request headers, authentication, POST bodies, pagination/cursors and multi-request joins are explicit later scope unless required for the first release. Do not include secrets in shareable recipe exports.

### GitHub Pages and runtime responsibilities

The existing project Pages helper can host the authoring UI beside the Docker command builder. Static Pages processes pasted/uploaded samples locally. The agreed architecture has no connection from Pages to a user's scraper, no public scraper exposure, and no fetch proxy. A source URL may be entered as optional recipe metadata or to resolve relative links; entering it does not fetch the website. Copy/paste and recipe-file export/import are the integration paths. Fetching and real-source testing take place separately inside the installed scraper's own UI.

The backend needs a versioned per-source extraction configuration, Alembic migration, typed API contracts/generated frontend types, source-settings editor and a preview endpoint. Preserve `auto` behavior for existing sources. Run custom extraction in an explicit configured mode; surface zero matches or recipe errors without silently substituting heuristic matches or destructively reconciling a broken result.

The current code already has M3U parsing, link/copy-field detection, bare-ID opt-in and two hardcoded embedded-script formats. It does not have saved custom extraction rules or general JSON field mapping. `url_type` currently identifies transport/source type; add extraction mode separately so HTTP/ZeroNet/IPFS transport decisions are not confused with HTML/JSON/regex parsing.

The HTTP scraper does not run a browser. A recipe derived from JavaScript-rendered HTML may work on the pasted snapshot while failing on the HTTP response. The helper must explain this distinction and guide the user to the site's JSON response where available. Browser automation, login flows and anti-bot handling are outside the proposed first release.

### Implementation order and acceptance

1. Define the recipe schema and representative synthetic fixtures: tables, cards, attributes, missing names, multiple IDs, text lists, nested JSON, malformed records, and changed layouts.
2. Implement bounded extraction and backend preview, with migration and preservation tests for existing source behavior and channel associations.
3. Deliver JSON field mapping and a manual regex editor as the first working authoring path.
4. Add HTML selection, repeated-record inference, generated-rule editing and full-sample review.
5. Add recipe export/import, backend comparison, documentation and Pages publication through the existing Jenkins flow.

Release acceptance: a user can configure an unfamiliar supported source without a code change; all valid sample records are accounted for; no name/ID cross-pairing occurs; saved recipes reproduce preview results on a fresh backend fetch; failures explain whether fetching or extraction failed; upgrades preserve existing behavior; pasted HTML cannot execute source scripts; malformed patterns cannot stall the app; shared exports contain no credentials or source sample data by default.

Useful primary references: [MDN iframe srcdoc isolation](https://developer.mozilla.org/en-US/docs/Web/API/HTMLIFrameElement/srcdoc), [Python regex named groups](https://docs.python.org/3/howto/regex.html), [JavaScript named capture groups](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Regular_expressions/Named_capturing_group).

## Follow-up requirements: catalogue and visual/source authoring

The user wants a community catalogue included in the product direction. Users must be able to author recipes for unfamiliar sites; supplying known target sites is not a prerequisite.

The requested authoring experience prioritizes a faithful visual preview, falls back gracefully when rendering is incomplete, and always offers raw HTML/text selection. Visual and source selections should refer to the same sample and feed the same extraction recipe. Source selections mark a record, name, ID or optional field; selecting examples should infer a reusable rule and highlight all matches rather than save literal offsets.

A live third-party URL iframe cannot be the general element picker: sites may prohibit embedding, and same-origin restrictions prevent the helper from inspecting cross-origin content even when it renders. CORS permission for fetching does not grant access to a cross-origin iframe DOM. Use an iframe to display an imported snapshot whose DOM the picker can inspect under a deliberately restricted sandbox. Disable source scripts, handlers, forms and navigation; preserve safe layout/styles and optionally acquire permitted assets through bounded, validated fetches. Do not offer unrestricted execution of imported site code as a fidelity option.

User decision: the public helper must not connect to the installed scraper. Users provide HTML/text/JSON samples, build and export rules, then separately add or update the URL and rules in their own scraper and test there. There is no URL-fetch dependency in the helper and no requirement to expose an installation. Rendering a JavaScript-produced snapshot still does not make the scheduled HTTP scraper capable of reproducing it; distinguish sample-preview results from real-source test results.

Catalogue proposal: repository-backed versioned recipe files, sanitized example fixtures, author credit, supported source patterns, minimum runtime version, and test/verification date. The builder exports a contribution bundle; GitHub review and automated fixture validation precede catalogue publication. Installed sources pin a recipe version and offer an update preview rather than silently switching extraction rules. Private recipes remain possible, and credentials and full user HTML snapshots are excluded from catalogue submissions by default. This is a proposal, not a published catalogue or an authorization to submit content on anyone's behalf.

## Agreed direction: two helpers sharing one builder

The user wants both the standalone Pages helper and an integrated helper in the scraper app. Neither requires exposing the installed scraper or connecting the public Pages site to it.

- **GitHub Pages:** paste/upload HTML, text or JSON; use visual/source selection and sample-result preview; browse the catalogue; copy/export recipes and prepare optional catalogue contributions.
- **Installed app:** the same authoring controls, plus fetching a new or existing source URL through the local backend, previewing the actual response, testing extraction with the production extraction engine, importing catalogue recipes and saving the configuration directly to the source. Pasted/uploaded samples remain available as a fallback.
- **Shared implementation:** reuse the builder UI, recipe schema and sample fixtures through environment adapters. Keep source fetching, persistence and catalogue submission separate from the authoring components. Backend extraction is authoritative for installed-app tests; do not maintain independent subtly different recipe formats or present browser preview as production verification.
- **Local flow:** Scraper → Add/Edit source → Configure extraction → Load source or provide sample → Select fields → Test → Review results → Save. Tests must not import/delete channels or change saved source settings; normal scraping runs after the user saves and launches it. Explain fetch errors, unsupported rendering needs, invalid rules and zero matches separately.
- **Catalogue access:** allow outbound catalogue retrieval from the installed app, with recipe-file import as an offline fallback. No inbound access or Pages-to-app bridge is required. Keep contributions explicit and exclude credentials and full private samples.

This supersedes the earlier implication that the standalone helper would be the only authoring interface. The manual transfer workflow remains supported, while local users can complete authoring and real-source validation without leaving the app.

## Validation performed

- Backend group 1: 254 passed, 12 warnings (`test_epg`, `test_epg_link_repair`, `test_scrapers`, `test_playlists`, `test_curated_playlists`, `test_legacy_playlist_routes`, `test_playlist_refresh`, `test_api_token_auth`, `test_url_guard`, `test_system_services`, `test_acestream_status`, `test_bare_id_scraping`).
- Backend group 2: 91 passed, 13 warnings (`test_tv_channels`, `test_channels`, `test_warp_status`, `test_settings_env_compat`, `test_channel_cleanup`).
- Frontend: 11 tests passed across ChannelTable and ChannelCardList; 4 API-token tests passed separately. The first command also named a nonexistent `apiClientAuth.test.ts`; Jest selected the two existing suites. API-token coverage was then run using the actual `apiToken.test.ts` file.
- Two isolated assertions passed: summer/winter XMLTV timezone normalization and same-ID scrape preservation of a manually assigned TV channel.
- `bash scripts/ci/validate_runtime_contract.sh` was attempted locally and failed at the first AceStream-missing flavor assertion because the expected guard text was absent. This is recorded as an incomplete runtime validation, not a pass; its root cause was not established during this triage.
- No full application gate, Docker runtime matrix, live multi-viewer soak, or three-proxy deployment smoke was run. Test logs remain under `/tmp/acestream-v210-*`.
