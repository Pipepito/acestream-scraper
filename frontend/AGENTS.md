# Frontend agent guide

These instructions extend the repository root `AGENTS.md` for work in `frontend/`.

## Commands

Run inside `frontend/`:

```bash
npm ci
npm start
npm test -- --runInBand
npm test -- --runInBand src/__tests__/Overview.test.tsx
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
- `src/components/layout/AppShell.tsx` owns the application shell.
- `src/pages/` contains route-level views; reusable UI belongs in `src/components/`.
- API calls belong in `src/services/`, built on `apiClient.ts`.
- Server state uses `@tanstack/react-query` v5. Prefer query invalidation and
  existing hooks over parallel local caches.
- Generated OpenAPI types live at `src/types/api-generated.ts`; do not hand-edit.
- Shared formatters, errors, state surfaces, and test helpers should be reused
  before adding a page-local variant.

## UI contract

- Navigation has eight primary destinations: Overview, Scraper, Search, Acestream
  Channels, TV Channels, EPG, Playlist, and Settings. WARP remains a hidden route
  reached from the Overview services panel.
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
