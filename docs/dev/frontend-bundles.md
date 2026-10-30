# Frontend bundle boundaries

`frontend/vite.config.ts` uses Rolldown code-splitting groups. React and scheduler
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
