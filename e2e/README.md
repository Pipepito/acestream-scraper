# End-to-end suite (Playwright, Firefox)

Drives the real product the way a user does: the built SPA served by the backend, a
live AceStream engine and Acexy proxy in Docker, a local IPFS (kubo) gateway for
IPNS-hosted channel lists, the public EPG feed, and the engine's search API.
Every test records browser console errors, page errors, failed `/api` responses and
new `ERROR`/`Traceback` lines from the backend log, and attaches them to the report.

## Layout

```
e2e/
  playwright.config.ts   Firefox by default (E2E_BROWSERS=firefox,chromium), 1 worker, serial journeys
  scenarios/*.json       data-driven scenario files (see below)
  src/
    scenario/            zod schema + loader (E2E_SCENARIO=<name|path>, E2E_TARGET=local|docker)
    api.ts               typed helper over /api/v1 for seeding, polling background jobs, cross-checks
    error-monitor.ts     per-test console/network/backend-log watchdog (E2E_STRICT=1 fails on any error)
    fixtures.ts          `test`/`expect` with scenario, api, app and errors fixtures
    pages/               page objects (roles/labels, no CSS selectors)
  tests/                 journeys, run in file order: stack → navigation → settings → scraper →
                         search → channels → EPG → TV channels → playlist → dashboard/health/stats/WARP
  stack/                 docker compose for engine+Acexy+kubo, backend start/stop scripts
  .stack/                (git-ignored) e2e database, backend log, container config
```

## Running it

Prerequisites: Docker Desktop, Node 22, the backend venv (`backend/venv`) and `frontend/node_modules`.

```bash
cd e2e
npm install && npm run browsers          # once: @playwright/test + Firefox
npm run stack:up                         # engine + Acexy (arm64 image, built if missing) + kubo gateway on :8080
npm run backend:start                    # builds the SPA, starts uvicorn on :8000 with e2e/.stack/config/scraper.db
npm test                                 # the whole journey (the EPG import of the 33 MB feed takes ~10 s)
npm run report                           # HTML report with traces/videos for failures
npm run backend:stop && npm run stack:down [-- --volumes]
```

Useful variants:

- `npx playwright test tests/03-scraper.spec.ts` — one journey (later journeys assume the earlier ones ran once against the same database).
- `E2E_RESET_DB=1 npm run backend:start` — start from an empty database.
- `E2E_SKIP_FRONTEND_BUILD=1 npm run backend:start` — reuse `backend/frontend_build`.
- `npm run test:docker` — run the same suite against the containerised app on :8001 (uses `dockerUrl` from the scenario for in-network hosts).
- `E2E_STRICT=1 npm test` — fail a test on any unexpected console error, failed API call or backend error line (patterns in `scenario.errors` are ignored).
- `npm run test:headed` / `npm run test:ui` — watch it in Firefox.

## Scenarios

`scenarios/default.json` describes what the journey uses; add another file and select it with
`E2E_SCENARIO=<name>`. Validated by `src/scenario/schema.ts`:

| Section | Purpose |
| --- | --- |
| `stack` | engine / Acexy / IPFS gateway URLs the suite probes before running |
| `scrape.sources[]` | URLs to add through the Scraper page (`url`, optional `dockerUrl` for the container target, `fallbackUrl` if the primary cannot be fetched, `urlType`, `expectMinChannels`, `scrapeTimeoutMs`) |
| `search.queries[]` | engine search terms, how many rows to add (`addFirst`) |
| `epg.sources[]` + `epg.targetChannel` | EPG feeds to add and refresh, and the guide channel used for mapping/schedule checks |
| `tv.channels[]` | TV channels to create, the search query that finds a stream to attach, the EPG xml id to map |
| `playlist` | named stream base URL (Acexy) used when generating playlists |
| `errors` | regexes for console/API errors that are acceptable |

## Stack notes

- `stack/docker-compose.e2e.yml` runs `acestream-scraper:e2e-arm64` (target `scraper-acestream-acexy`,
  engine + Acexy enabled) publishing engine `:6878`, Acexy `:8081`, the containerised app `:8001`, P2P `8621`,
  and `ipfs/kubo` with its gateway on `:8080` so `http://127.0.0.1:8080/ipns/<key>/` works verbatim.
- `stack/stack-up.sh` builds the image through `scripts/ci/build_multiarch_images.sh` when missing and waits
  for every service. Set `E2E_IMAGE`/`E2E_PLATFORM` to test another flavor/platform.
- The backend runs from source (`stack/backend-start.sh`) so bugs found by the suite can be debugged and
  fixed locally; its database and logs live under `e2e/.stack/`.
