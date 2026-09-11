# Testing Patterns

**Analysis date:** 2026-09-03
**Branch mapped:** `develop` (the release-candidate branch currently intended to merge into `main`)

## Test Stack at a Glance

| Layer | Frameworks | Primary location |
| --- | --- | --- |
| Backend unit/integration/contract | pytest, FastAPI `TestClient`, HTTPX, SQLAlchemy SQLite fixtures | `backend/tests/` |
| Frontend unit/component | Jest, ts-jest, jsdom, React Testing Library, jest-dom | `frontend/src/__tests__/` |
| Browser journeys | Playwright Test, Firefox by default, Zod scenario validation | `e2e/` |
| Migration/schema | pytest + real Alembic upgrade to temporary SQLite | `backend/tests/test_alembic_migrations.py`, `test_schema_parity.py`, Alembic fixtures |
| Packaging/runtime | pytest plus Docker buildx/Compose shell checks | `backend/tests/docker/`, `scripts/ci/`, Jenkins |

There is no configured coverage percentage gate. `backend/run_tests.py coverage` is an endpoint-presence report, not line/branch coverage, and should not be described as `pytest-cov` coverage.

## Backend Tests

### Commands

Run from the repository root so imports and paths match CI:

```bash
# Entire canonical backend suite
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests

# One file / one test
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py::test_name

# Domain-oriented convenience runner for the v2 backend
python backend/run_tests.py channels
python backend/run_tests.py tv
python backend/run_tests.py epg

# Full non-Docker suite (the canonical CI wrapper uses this for its full profile)
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests --ignore=backend/tests/docker
```

`backend/venv` is the repository convention. Bootstrap it with the command documented in `CLAUDE.md`; backend test dependencies are included in `backend/requirements.txt`.

### Two database fixture modes

`backend/tests/conftest.py` deliberately provides two runtimes:

- Fast fixtures: `backend_runtime`, `test_db`, `db_session`, `override_get_db`, `client`, and `async_client`. They bind a temporary SQLite database and create tables with `Base.metadata.create_all`. Use these for normal service and endpoint behavior.
- Migration-faithful fixtures: `alembic_test_db`, `alembic_backend_runtime`, `alembic_db_session`, `alembic_override_get_db`, `alembic_client`, and `alembic_async_client`. They run `alembic upgrade head` into a temporary SQLite file. Use them for schema defaults/nullability, migration behavior, startup/database compatibility, contract/regression behavior tied to production schema, and any model change.

The runtime is rebound through the lazy database engine and settings cache. Do not re-import/reload `main`, models, or SQLAlchemy `Base` inside fixtures: that splits the mapper registry and reintroduces relationship-resolution failures documented in `backend/tests/conftest.py`.

### Data and mocking patterns

- Shared sample dictionaries and seed fixtures in `backend/tests/conftest.py` cover Acestream channels, TV channels, EPG sources/channels/programs, and scraped URLs.
- Use FastAPI `app.dependency_overrides` when replacing injected services or sessions, and remove the override in `finally`/fixture teardown.
- Use pytest `monkeypatch` for environment variables and module attributes; use `unittest.mock.Mock`, `MagicMock`, `AsyncMock`, or `patch` for external processes/network collaborators.
- Mock service boundaries when testing endpoint translation; use real repositories/temp SQLite when testing persistence behavior. Do not mock the implementation under test.
- Network, AceStream/Acexy, WARP CLI, IPFS, ZeroNet, filesystem, and clock behavior should be isolated unless the test explicitly belongs to a live/runtime suite.
- Assert response status and shape, not only truthiness. Error-path tests should verify stable error code, message presence, correlation ID, and safe context as appropriate (`backend/tests/test_error_contracts.py`).

### Specialized suites

- `backend/tests/contracts/`: Pydantic/API payload contracts.
- `backend/tests/architecture/`: layer/import boundaries; update when dependencies between endpoints/services/repositories change.
- `backend/tests/parity/`: v1-to-v2 scraper/output baselines and checked-in JSON/YAML fixtures under `backend/tests/parity/`.
- `backend/tests/regression/`: legacy behavior that the cutover promises to preserve.
- `backend/tests/perf/`: hot-path benchmark/regression checks; supporting baseline is `phase6-db-baseline.json`.
- `backend/tests/docker/`: manifest, installer, vendored payload, and real engine/Acexy runtime smoke. These can build large images and need Docker/buildx; do not run them casually as a unit-test substitute.

## Frontend Tests

### Commands

```bash
cd frontend
npm test -- --watch=false --runInBand
npm test -- --watch=false --runInBand StatusLine.test.tsx
npm run lint -- --max-warnings=0
npm run typecheck
npm run build
```

Jest is configured by `frontend/jest.config.js` with `ts-jest`, `jsdom`, and `frontend/src/setupTests.ts` for jest-dom matchers. TypeScript strictness and ESLint are separate required checks; a passing Jest test alone is not sufficient verification.

### Component and hook patterns

- Test visible behavior and accessibility with `screen.getByRole`, accessible names, labels, and `within`. Prefer user-observable assertions over component internals or CSS structure.
- Use `@testing-library/user-event` for realistic interactions when practical; existing tests also use `fireEvent` for focused events.
- Async changes use `findBy*` or `waitFor`; await mutations and disappearance rather than using arbitrary sleeps.
- Mock service/hook modules with `jest.mock` and configure `mockResolvedValue`/`mockRejectedValue` per case. Reset mocks and module state between tests when a suite mutates shared implementations.
- For React Query consumers, create a fresh `QueryClient` per render with retries disabled and wrap in `QueryClientProvider`; this prevents cross-test cache leakage and delayed retries.
- Use `TestMemoryRouter` from `frontend/src/testUtils/router.tsx` for routed components; it centralizes the React Router future flags.
- Use `mockResponsiveShellQueries` from `frontend/src/testUtils/mockResponsiveShell.ts` for phone/desktop/wide behavior rather than hand-coding media-query strings.
- Cover loading, empty, success, validation, backend error, retry/recovery, keyboard/label behavior, and responsive variants relevant to the change.

### API contract generation

When backend schemas or routes change:

```bash
PYTHONPATH=backend backend/venv/bin/python backend/scripts/dump_openapi.py
cd frontend
npm run codegen
git diff -- ../backend/openapi.json src/types/api-generated.ts
```

The canonical CI suite regenerates `frontend/src/types/api-generated.ts` and fails if it differs from the committed output. Commit both schema and generated types when the API contract changes.

## Playwright End-to-End Journeys

The browser suite exists and is substantial, but it is not currently part of Jenkins `PR Validation`. Use it for manual/live-stack confidence, UI journey changes, and screenshots; do not report it as a required PR gate.

### Setup and execution

Prerequisites are Docker Desktop/buildx, Node 22, `backend/venv`, and frontend dependencies:

```bash
cd e2e
npm install
npm run browsers
npm run stack:up
npm run backend:start
npm test
npm run report
npm run backend:stop
npm run stack:down
```

Useful focused modes:

```bash
npx playwright test tests/03-scraper.spec.ts
E2E_STRICT=1 npm test
E2E_RESET_DB=1 npm run backend:start
E2E_SKIP_FRONTEND_BUILD=1 npm run backend:start
npm run test:docker
npm run test:docker-off
npm run test:headed
npm run test:ui
```

Later numbered specs assume earlier journeys have prepared the shared database; a single late spec may require an already-seeded `e2e/.stack/` database. Use a reset plus the full suite when isolation is uncertain.

### Configuration and artifacts

- `e2e/playwright.config.ts` uses Firefox by default; `E2E_BROWSERS=firefox,chromium` expands projects.
- The suite is serial (`fullyParallel: false`, `workers: 1`) because it shares SQLite and background scheduler state. Default test timeout is 180 seconds; expect timeout is 15 seconds.
- `E2E_BASE_URL` selects the app (`http://127.0.0.1:8000` by default). `E2E_TARGET=docker` switches scenario URLs for Compose-network hosts.
- Failure artifacts are retained: trace, video, screenshot, HTML report, JUnit XML in `e2e/results/junit.xml`, JSON in `e2e/results/results.json`, and raw output in `e2e/test-results/`.
- `e2e/src/global-setup.ts` fails fast unless the app health endpoint and (unless `E2E_REQUIRE_ENGINE=0`) the engine and Acexy are reachable.
- Scenario files in `e2e/scenarios/*.json` are selected by `E2E_SCENARIO` and validated by Zod in `e2e/src/scenario/schema.ts`. Keep secrets out of scenarios; they are source-controlled fixtures.
- Import `test` and `expect` from `e2e/src/fixtures.ts`, which supplies typed `scenario`, API helper, app-shell page object, and the automatic error monitor.
- Page objects query roles/labels rather than CSS selectors. Add reusable page behavior under `e2e/src/pages/`, API polling/seeding in `e2e/src/api.ts`, and readiness polling in `e2e/src/stack.ts`.
- The automatic `ErrorMonitor` records console errors, uncaught page errors, failed `/api` responses, and new backend error lines. `E2E_STRICT=1` turns unexpected observations into failures; intentional failures must be narrowly allowed in the spec or scenario policy.

## Canonical CI and PR Verification

GitHub Actions are not the authority on this branch; the workflows were removed during the cutover. Jenkins (`Jenkinsfile`) supplies the required `PR Validation` status.

The practical local entry points are:

```bash
# Backend contracts + key frontend tests + lint/typecheck/build
bash scripts/ci/run_v2_test_suite.sh --profile quick

# Adds legacy-path and Compose configuration checks
bash scripts/ci/run_cutover_required_checks.sh --profile quick

# Closest local wrapper to Jenkins validation; needs configured Docker buildx
bash scripts/ci/run_jenkins_validation.sh

# More exhaustive non-Docker backend/frontend checks
bash scripts/ci/run_cutover_required_checks.sh --profile full
```

Jenkins additionally performs:

- docs command-builder validation and dry-run wiki/Pages publishing;
- Phase 1 parity safety gates and Phase 3 cutover quick gate, with JSON reports archived;
- four-flavor multi-architecture build-plan/manifest checks;
- real AceStream/Acexy and ARM installer Docker smoke tests;
- Phase 5 architecture gate and artifact archiving;
- branch-policy enforcement for the `develop` to `main` release PR.

Validated `develop` builds may also publish channel images, wiki content, and the docs site using Jenkins-managed credentials. Tests and documentation must never embed or echo those credentials. Missing publication credentials can mark publication stages unstable; this is distinct from application test success.

## What to Run for a Change

- Backend service/repository: targeted pytest file; add Alembic fixture coverage if persistence/schema is involved.
- Endpoint/schema: targeted endpoint + contract/error tests, dump OpenAPI, regenerate frontend types.
- React component/hook: targeted Jest suite, ESLint, typecheck; build when imports/chunks/routes change.
- Navigation/responsive/user journey: relevant Jest suites plus focused Playwright journey; use the full ordered E2E suite if shared state is required.
- Migration/startup: Alembic, schema parity, startup DB initialization, and migration regression tests.
- Docker/flavor/runtime: targeted `backend/tests/docker/` and matching `scripts/ci` validator; expect a heavy build.
- Cross-layer or release-PR work: `run_cutover_required_checks.sh --profile quick` at minimum, then rely on Jenkins `PR Validation` for its Docker/architecture matrix.

## Agent Hygiene

- Preserve unrelated working-tree changes and generated artifacts owned by other agents.
- Do not point tests at production databases or private infrastructure. Use temp SQLite fixtures, the local E2E stack, or the configured Jenkins job.
- Do not weaken parity snapshots, error allowlists, assertions, or CI gates solely to make a failure disappear; explain and update the contract when behavior intentionally changes.
- Record the exact commands run and distinguish passed, skipped, not run, and environment-blocked checks.

---

*Update this map when fixture architecture, the Playwright journey order, generated API contract checks, or Jenkins required stages change.*
