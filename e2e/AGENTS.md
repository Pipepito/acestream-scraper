# End-to-end agent guide

These instructions extend the repository root `AGENTS.md` for work in `e2e/`.

## Purpose and prerequisites

The Playwright suite drives the built SPA served by FastAPI and exercises real
AceStream, Acexy, and IPFS services. It is slower and more stateful than unit tests.
It requires Docker Desktop, Node 22, `backend/venv`, `frontend/node_modules`, and
Firefox installed through Playwright.

## Safe run sequence

From `e2e/`:

```bash
npm install
npm run browsers
npm run stack:up
E2E_RESET_DB=1 npm run backend:start
npm test
npm run report
npm run backend:stop
npm run stack:down
```

Use `npm run stack:down -- --volumes` only when intentionally discarding E2E
volumes. State and logs under `e2e/.stack/` are local runtime artifacts.

Useful focused commands:

```bash
npm run typecheck
npx playwright test tests/03-scraper.spec.ts
E2E_STRICT=1 npm test
npm run test:docker
npm run test:docker-off
```

Later numbered journeys can depend on state created by earlier journeys. For a
reproducible isolated run, reset the DB and confirm the selected spec seeds all
state it needs.

## Test conventions

- Reuse `src/fixtures.ts`, API helpers, and page objects under `src/pages/`.
- Locate UI through roles and accessible labels, not CSS selectors.
- Scenarios belong in `scenarios/*.json` and must pass the Zod schema in
  `src/scenario/schema.ts`.
- Keep console, page-error, failed-API, and backend-log monitoring active. Add an
  allowed error pattern only for a known, documented condition.
- Capture traces/screenshots/video as failure evidence; do not commit generated
  reports or media unless a documentation task explicitly requires curated proof.
- Do not aim tests at production or shared infrastructure. The suite may create,
  edit, scrape, and delete application data.
