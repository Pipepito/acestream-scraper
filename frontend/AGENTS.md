# Frontend agent guide

These instructions extend the repository root `AGENTS.md` for work in `frontend/`.

## Commands

Run inside `frontend/`:

```bash
npm ci
npm start
npm test -- --runInBand
npm test -- --runInBand src/__tests__/SystemDashboard.test.tsx
npm run typecheck
npm run lint -- --max-warnings=0
npm run build
npm run build:backend
npm run codegen
```

The Vite dev server runs on port 3000 and proxies `/api` to port 8000.
`build:backend` copies a fresh bundle into `backend/frontend_build/`; use it when
testing the SPA through FastAPI rather than the Vite server.

## Structure and data flow

- `src/App.tsx` owns routes and compatibility redirects.
- `StartupGate` in `AppBootstrap` blocks normal views until boot is ready, serves
  `/startup` diagnostics, accepts the optional API token, and shows deferred import
  progress. Preserve confirmation and backup consequences for recovery actions;
  see `docs/ops/startup-recovery.md`.
- `src/components/layout/AppShell.tsx` owns the application shell.
- `src/pages/` contains route-level views; reusable UI belongs in `src/components/`.
- API calls belong in `src/services/`, built on `apiClient.ts`.
- Server state uses `@tanstack/react-query` v5. Prefer query invalidation and
  existing hooks over parallel local caches.
- Generated OpenAPI types live at `src/types/api-generated.ts`; do not hand-edit.
- Shared formatters, errors, state surfaces, and test helpers should be reused
  before adding a page-local variant.

## UI contract

- Navigation includes TV dashboard, Live TV, Recordings, Catalogues and Events under Watch; other destinations are System status, Scraper, Search,
  Acestream Channels, TV Channels, EPG, Playlist, Public address, Web player, Remote players, Media servers, Telegram, WARP, Settings and Changelog, grouped by Watch, Manage, Integrations and System.
- Live TV (`/live-tv`) is the viewing catalog; TV Channels remains the management
  inventory. Use `ChannelPlayerDialog` to retain or resolve TV context and
  `StreamPlayerDialog` for the underlying HLS lifecycle.
- A primary page follows `PageHeader` -> `StatusLine` -> `ContentSection`.
- Keep headings and nav labels aligned. Prefer measured status facts and clear next
  actions over hero copy or explanatory filler.
- Use `ConfirmDialog`/`useConfirm()` instead of `window.confirm`, and
  `RowActionsMenu` for compact row action sets.
- Preserve established theme tokens in `src/theme.ts` and layout tokens in
  `src/styles/layout.ts`; verify light and dark modes.
- Design for phone widths, touch targets, long/localized text, keyboard operation,
  visible focus, reduced motion, and status communication beyond color alone.
- Use the guidance in `docs/dev/frontend-design-checklist.md`,
  `docs/dev/frontend-theme-reference.md`, and `docs/dev/typescript-standards.md`.

## Type and test rules

- Application source is TypeScript/TSX only. Use named interfaces/types and avoid
  new `any` unless an integration boundary genuinely requires it.
- Keep service response types aligned with generated API types; normalize only at
  a deliberate adapter boundary.
- Test behavior through accessible roles, names, and user-visible state. Prefer
  React Testing Library user interactions over implementation details.
- Cover loading, empty, error, success, long-content, and responsive behavior for
  meaningful UI changes.
- For navigation, API integration, or cross-page workflows, add/update Playwright
  journeys as appropriate after focused Jest coverage.
- Preserve Vite `manualChunks` behavior unless bundle tuning is the task; a casual
  import change can move large MUI/data-grid/page chunks back into the entry bundle.

## Player audio

- Audio selection restarts only the current viewer and must release stale starts.
  Show discovered language/codec/layout without assuming every source has metadata.
- Browser audio selection does not change copied source links or remote-player
  actions; those players receive the source with its original audio tracks.

## Live TV and settings navigation

Live TV embeds the existing HLS player alongside a scrollable catalogue. Filtering
does not release playback; changing the channel or Stop watching releases the
current viewer. Other pages retain the player dialog. Navigation groups Watch,
Manage, Integrations and System, with WARP always discoverable. Settings uses deep-linkable
`?tab=playback|automation|links|access` sections; public address belongs to
Integrations. PID/AppID belong to Stream links, not Automation.


## TV channel inventory and playlist formats

TV Channels combines catalogue-wide filters before sorting and pagination. Number
and Favorite have dedicated controls in the table and phone cards; number changes
save on Enter/blur and blank clears the number. Keep remaining row actions intact.
Playlist shows the selected stream format and expands the shared
`StreamLinkFormatsSection` inline, preserving playlist options. Settings retains
its Stream links entry because formats also affect copied links and supported
remote-player actions. Do not fork the format editor or duplicate its API logic.

TV Channels keeps Search, Category, Status and Favorite filters visible; other
filters live under Advanced filters with an active count. Reorder channels shows
the complete catalogue, supports drag handles and keyboard/arrow controls, and
previews consecutive numbers. Save order uses `POST /api/v1/tv-channels/reorder`
with the complete desired IDs and original order; the backend commits all numbers
atomically and rejects stale/incomplete inventories. Cancel leaves stored numbers
unchanged. Number edits remain available outside reorder mode.


Engines are optional. Settings → Automation stores external checker selection via
`/api/v1/config/check-engine`; disabled dedicated checks use the saved playback
URL, and with neither URL probes are skipped without changing channel results.
A configured dedicated checker never falls back on failure. Bundled checker
configuration remains supervisor-owned and read-only in Settings. New scraper-only
installs default to an empty playback URL; existing saved endpoints are preserved.

## TV and system dashboards

The default `/` route is TV dashboard under Watch: app-owned playback, channel/stream
inventory, upcoming/followed events and time until the next content updates. System status at `/system` owns services, storage,
diagnostics and full job history. `/health` redirects to `/system`; `/dashboard` and
`/stats` redirect to `/`. Keep section failures independent and missing data unknown.
Playback summaries only read the shared streams query; never touch session heartbeats
or ownership. Event summaries use server-side `selection=dashboard` before pagination,
with six results over seven local calendar days. Display interests/timezone are
browser preferences; Following remains installation-wide. Reuse agenda rows and
`/events?event=<id>&zone=<timezone>` details; never import or play during dashboard
reads. See `docs/dev/dashboard-split.md`.

## Integration navigation

Integrations is a sidebar category with independent pages at
`/integrations/public-address`, `/integrations/web-player`,
`/integrations/remote-players`, `/integrations/media-servers` and
`/integrations/telegram`. The old `/integrations` URL redirects to Public address.
Keep tuner settings with Media servers, WARP under System, and contextual links
pointing directly to the relevant setup. Each page mounts only its own section;
shared query keys and page-scoped feedback preserve existing operations.


## Built-in recordings

Recordings are opt-in with an explicit persistent `RECORDINGS_DIR`. Keep DVR
capture on its dedicated coordinator, outside the maintenance FIFO; prioritize
scheduled capture over local MP4/AAC preparation. Preserve direct-engine source
leases, guarded HTTP input, control-pipe/process-group cleanup, journal recovery,
stop intent and immutable guide snapshots. Never replace originals during
conversion or delete protected/active/reader-held media. File routes retain the
optional API-token policy and descriptor-relative no-follow access. Recordings
is under Watch; scheduling is TV-channel-only. See `wiki/Recordings.md` and
`docs/ops/recordings.md` for limits, qualification and rollback.
