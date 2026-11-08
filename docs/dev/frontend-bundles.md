# Frontend bundle boundaries

`frontend/vite.config.mts` uses Rolldown code-splitting groups. React and scheduler
stay together; MUI's Emotion and transition helpers stay with the remaining
shared vendor modules. Explicit groups own their modules without recursively
claiming each other's dependencies. Splitting these shared helpers indiscriminately
can introduce initialization cycles that compile successfully but fail in browsers.

The data-grid groups have a 650,000-byte source-module target. The player keeps
controllers separate from their media primitives, preserving initialization order
for the demuxer/remuxer registry. Do not split that registry by size. These are
module grouping rules, not a raised warning threshold: Vite's default 500 KB
minified output warning remains enabled. The entry and route chunks remain
separate. Check both individual output sizes and total/gzip size when retuning.

Date utilities have their own group to keep the shared UI chunk below that limit
without separating MUI from Emotion or transition helpers. Vite configurations
use explicit ESM extensions; the shared TypeScript build helpers declare their
module format in `bundling/package.json`. Keep the script and Pages classifier
references aligned with `vite.recipes.config.mts`.

## HLS upgrades

The full HLS distribution is one indivisible module, too large to split. The
build instead aliases `hls.js` to the published TypeScript modules from the same
pinned package. `frontend/bundling/hls.ts` preserves every full-build feature,
including alternate audio, subtitles, DRM and advanced codecs. It excludes the
inline worker entry in the same way as upstream's ESM build; application worker
configuration is unchanged. No third-party CDN is needed at runtime.

When upgrading HLS:

1. Review upstream's `build-config.js` and the package's `src/define-plugin.d.ts`.
2. Update the exact HLS version and the source-build dependencies to the versions
   in upstream's package manifest. Keep the lockfile aligned.
3. Update feature definitions for any added or removed flags. The compatibility
   test checks the installed declarations and upstream dependency versions.
4. Run the production build, unit suite and the complete built-SPA browser suites,
   including real media playback, audio/subtitle selection and grid operations.
   A dev-server check alone does not exercise production chunk initialization.

From `frontend/`, run `npm run build:backend` to build and copy the SPA for backend
journeys. Follow `e2e/README.md` for isolated Firefox, mobile and monitor suites.

`StreamPlayerDialog` requests HLS through `loadHls()` only while open. Keep the
existing controller/media chunk boundary and one viewer lifecycle. A late module
load after close must not create an HLS instance; language, theme and presentation
changes must not reload the decoder or replace the video element. The loaded
constructor is cached by the module loader, while instances remain viewer-owned.

Catalogue browsing uses bounded `/tv-channels/browse` pages. All filters and sorts
run over the complete inventory before pagination; `/tv-channels/inventory`
supplies global facet choices and counts independently. Watch fetches 50 rows and
one bounded guide batch at a time. Stream names retain their server-provided TV
channel labels without fetching the complete TV catalogue. Keep the full snapshot
read for atomic reorder, whose expected order must contain every channel.

Pure EN/ES message modules and the router have separate groups. This keeps the
entry and MUI chunks within the unchanged 500 KB warning limit as localization
grows, without splitting MUI/Emotion/transitions or React/scheduler. Both language
catalogues are ready synchronously so a preference change never resets an editor
or delays a pending confirmation behind a second language fetch.

The complete-catalogue reorder editor is loaded only when requested. Above 100
channels it uses `@tanstack/react-virtual` 3.14.26, whose peer contract includes
React 18. The maintained [React adapter](https://tanstack.com/virtual/latest/docs/framework/react/react-virtual)
handles measured row heights and scroll ranges. The controller still retains every
ID and the original expected order. Visible rows include overscan plus the focused
or dragged row; stable channel keys retain those nodes. Home/End and Page Up/Down
move focus without changing order; Arrow Up/Down preview changes. Dynamic height
measurement preserves complete wrapped names rather than imposing truncation.

The measured 10,000-row pre-optimization view rendered 150,226 DOM elements and
about 793 MB of JavaScript heap. Use `e2e/scripts/measure-reorder.py` to compare
fixed before/after builds with identical owned fixture databases; this script never
saves the draft. The 48-case `mobile/large-reorder.spec.ts` matrix checks bounded
DOM, focus and exact complete save payloads. Native assistive-technology review
remains separate from these automated semantics checks.

At `5054e0a8`, five alternating desktop samples per build measured median reorder
open time 2,842 → 854 ms (including the fixed 500 ms idle window), keyboard movement
2,586 → 23 ms, and CDP open-state heap 751 → 31 MB. Post-cancel heap after explicit
GC was about 20 MB in both builds; this was a peak-rendering problem, not evidence
of a retained-memory leak. See `docs/design/ux-review-314/performance-reorder.json`.
These are controlled local comparisons with host scheduling and API latency still
included, not universal performance promises.

Evidence-based local regression targets are under 2 seconds to open this fixture
and under 100 ms for a keyboard move. Repeat on the same browser/device before
interpreting a timing regression. Browser tests enforce the structural budget of
fewer than 40 mounted reorder rows at the supported viewport sizes, complete save
arrays and retained focus. Fonts remain below 400,000 source bytes; the unchanged
500 KB per-chunk build warning threshold remains active. No budget permits dropping
catalogue entries, permissions, translations or media functionality.

Vite names the HTML entry `app-entry-[hash].js`. Its dynamic-preload dependency
resolver omits that already-executed entry from late preload hints while retaining
its native module imports and every other dependency/CSS preload. This removes a
redundant fetch hint that WebKit reported as unused during slower interactions.
The large-reorder browser regression observes beyond WebKit's delayed warning
window once per browser. This uses Vite's documented
[dependency resolver](https://vite.dev/config/build-options.html#build-modulepreload);
console warning checks remain enabled.

The production backend serves the root `manifest.json` and `favicon.ico` as
explicit static responses with revalidation. Missing root assets return 404,
never the SPA fallback HTML. Verify through FastAPI as well as Vite preview:
WebKit reports an invalid manifest if a static URL falls through to client routing.
