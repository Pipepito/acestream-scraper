# Codebase Structure

**Analysis date:** 2026-09-03
**Branch snapshot:** `develop` (compared locally with `main`)

## Canonical Tracked Layout

```text
acestream-scraper/
|-- .github/                 # PR template, Copilot instructions/chat modes; no active workflows
|-- .planning/               # Project state, roadmap, research, phase records, codebase maps
|-- .tmp/jenkins/            # Sanitized/reference Jenkins job configuration artifacts
|-- .vscode/                 # Recommended editor configuration
|-- backend/                 # Canonical FastAPI application, migrations, scripts, and tests
|   |-- app/
|   |   |-- api/             # Router composition, auth, dependencies, errors, endpoints
|   |   |-- config/          # Settings, DB/session/schema bootstrap, version helpers
|   |   |-- models/          # SQLAlchemy models and URL-value abstractions
|   |   |-- repositories/    # Reusable persistence/query boundaries
|   |   |-- schemas/         # Pydantic API contracts
|   |   |-- scrapers/        # HTTP, ZeroNet, and IPFS scraper strategies
|   |   |-- services/        # Domain/application orchestration
|   |   |-- tasks/           # APScheduler job entry functions
|   |   `-- utils/           # Logging, activity, path, DB, outbound-URL helpers
|   |-- migrations/          # Canonical Alembic configuration and revisions
|   |-- scripts/             # Backend-local maintenance/codegen helpers
|   |-- tests/               # Backend feature, contract, parity, perf, Docker tests
|   |-- main.py              # FastAPI/Uvicorn entry point and SPA delivery
|   |-- migrate_database.py  # v1-to-v2 migration implementation
|   |-- openapi.json         # Checked-in API schema snapshot
|   `-- requirements.txt     # Dependency set used by the image
|-- docker/                  # Image manifests, installers, fixtures, vendored inputs
|-- docs/                    # Developer, architecture, migration, ops, release docs/site
|-- e2e/                     # Playwright live-stack journey suite and orchestration
|-- frontend/                # React/TypeScript/Vite SPA
|   |-- public/              # Static public assets
|   |-- scripts/             # Build-copy helper
|   `-- src/
|       |-- __tests__/       # Jest/Testing Library tests
|       |-- bootstrap/       # Root providers
|       |-- components/      # Reusable and domain UI
|       |-- config/          # Browser runtime configuration
|       |-- hooks/           # React Query/domain hooks
|       |-- pages/           # Route-level screens
|       |-- services/        # Axios API boundary and domain clients
|       |-- styles/          # Shared/screen styles
|       |-- testUtils/       # Frontend test helpers
|       |-- types/           # Generated API and handwritten UI types
|       `-- utils/           # Formatting, date, and error utilities
|-- jenkins/                 # Manual release pipeline
|-- samples/                 # Checked-in sample input data
|-- scripts/
|   |-- ci/                  # Jenkins/build/publish/runtime validation implementation
|   |-- dev/                 # Developer diagnostics and EPG scripts
|   |-- ops/                 # Deployment preflight
|   |-- perf/                # Performance profiling
|   `-- phase_gates/         # Repeatable milestone/gate runners and config
|-- wiki/                    # End-user/contributor wiki source
|-- CLAUDE.md                # Existing Claude-oriented repository guidance
|-- Dockerfile               # Canonical multi-stage, multi-flavor image build
|-- Jenkinsfile              # Canonical PR/develop validation pipeline
|-- README.md                # Primary project setup and verification index
|-- docker-compose.yml       # Local/unified runtime definition
|-- entrypoint.sh            # Container feature validation and process supervision
|-- healthcheck.sh           # Container health probe
|-- pyproject.toml           # Historical packaging metadata; not backend runtime authority
|-- requirements*.txt        # Root compatibility/development dependency lists
|-- version.txt              # Release version source
`-- warp-setup.sh            # WARP runtime preparation/control helper
```

The old tracked root `app/`, `tests/`, and `migrations/` directories shown by `main` do not exist in `develop`. Same-named directories seen locally are generated caches or untracked leftovers and are not canonical source.

## Source Areas

### `backend/`

Primary Python application. Work from this directory or set `PYTHONPATH=backend` because imports are written as `from app...`.

Important files:

- `backend/main.py`: app construction, lifespan/startup, canonical and compatibility routes, compiled-frontend serving.
- `backend/app/api/api.py`: complete `/api/v1` router registry.
- `backend/app/config/settings.py`: canonical environment settings and one-release legacy aliases.
- `backend/app/config/database.py`: lazy engine/session lifecycle and Alembic provisioning.
- `backend/app/models/models.py`: canonical ORM registry.
- `backend/app/services/task_service.py`: scheduler and task status.
- `backend/migrate_database.py`: foreground/deferred v1 data migration.
- `backend/openapi.json`: contract snapshot; update deliberately when API shapes change.

Backend test organization:

- `backend/tests/test_*.py`: feature and integration-style tests.
- `backend/tests/contracts/`: API contract assertions.
- `backend/tests/architecture/`: layer-boundary guards.
- `backend/tests/parity/` and `regression/`: v1 behavior baselines and compatibility checks.
- `backend/tests/docker/`: installer/image/runtime contracts.
- `backend/tests/perf/`: query-count and high-churn performance checks.

### `frontend/`

Production SPA source. Vite emits `frontend/dist/`; `npm run build:backend` then replaces the ignored `backend/frontend_build/` directory with that output. The root Docker build performs the equivalent copy between stages.

Important files:

- `frontend/src/index.tsx`: DOM mount.
- `frontend/src/bootstrap/AppBootstrap.tsx`: application providers and theme-mode state.
- `frontend/src/App.tsx`: route table and legacy browser redirects.
- `frontend/src/components/layout/AppShell.tsx`: persistent navigation/layout shell.
- `frontend/src/services/apiClient.ts`: shared API base URL, authentication header, and error normalization.
- `frontend/src/config/runtime.ts`: development/production API origin selection.
- `frontend/src/types/api-generated.ts`: generated OpenAPI types.
- `frontend/vite.config.ts`: dev proxy, output path, and chunking.
- `frontend/package.json`: canonical frontend scripts.

### `e2e/`

Stateful, ordered browser journeys. This suite intentionally uses one worker because tests share one SQLite-backed scenario and build on earlier operations.

- `e2e/tests/00-stack.spec.ts` through `09-system.spec.ts`: ordered cross-feature journeys.
- `e2e/src/pages/`: page objects.
- `e2e/src/scenario/` and `e2e/scenarios/default.json`: typed scenario data.
- `e2e/src/global-setup.ts`: app/AceStream/Acexy readiness gate.
- `e2e/stack/`: local backend and Docker stack lifecycle scripts.
- `e2e/stack/docker-compose.e2e.yml`: real service stack used by container-targeted runs.

Generated `node_modules/`, `.stack/`, `test-results/`, `playwright-report/`, and `results/` are ignored.

### `docker/`, `scripts/`, and Jenkins

- `docker/manifests/`: declarative supported-platform and optional-runtime metadata.
- `docker/scripts/`: installers and ARM AceStream launcher bridge.
- `docker/vendor/`: pinned archives/packages and checksum manifests used for reproducible/offline-tolerant builds.
- `docker/testdata/`: harmless installer/runtime fixtures.
- `scripts/ci/`: commands invoked by Jenkins for tests, builds, runtime checks, publication, and cleanup.
- `scripts/phase_gates/`: Python/shell validation gates retained as direct local and CI entry points.
- `Jenkinsfile`: validation plus guarded `develop` channel/docs/wiki publication.
- `jenkins/release.Jenkinsfile`: manual release wrapper.

Do not store private Jenkins URLs, credentials, tokens, or values from `infra-details.md` in any of these paths.

### Documentation and project memory

- `README.md`: supported quick start, environment, verification, and document index.
- `docs/dev/`: implementation standards and frontend/backend guidance.
- `docs/architecture/`: API and deployment architecture.
- `docs/ops/`: operational procedures, including Jenkins concepts without local secrets.
- `docs/migration/`: v2 cutover history and architecture smoke checklists.
- `docs/release/`: readiness/evidence/release notes.
- `docs/testing/test-ownership-matrix.md`: suite ownership and intent.
- `wiki/`: publishable operator/user documentation.
- `.planning/`: roadmap and execution history; `.planning/codebase/` is the concise agent map.

## Entry Points by Workflow

| Workflow | Entry point | Notes |
|---|---|---|
| Backend development | `backend/main.py` | Run Uvicorn with backend on import path; listens on 8000 by convention. |
| Frontend development | `frontend/package.json` `start` | Vite on 3000; proxies `/api` to 8000. |
| Production image | root `Dockerfile` | Builds SPA + backend; select a named flavor target. |
| Container startup | `entrypoint.sh` | Validates toggles, starts optional services, then Uvicorn. |
| Local Compose | `docker-compose.yml` | Unified `app`; optional `zeronet` profile. |
| Backend schema | `backend/migrations/alembic.ini` | Active revisions are under `backend/migrations/versions/`. |
| PR/develop CI | `Jenkinsfile` | Canonical checked-in validation pipeline. |
| Manual release | `jenkins/release.Jenkinsfile` | Delegates to `scripts/ci/run_jenkins_release.sh`. |
| Browser journeys | `e2e/playwright.config.ts` | Defaults to Firefox, one worker, app at `127.0.0.1:8000`. |
| API type generation | `frontend/package.json` `codegen` | Reads `backend/openapi.json`. |

## Where New Code Belongs

### Backend feature

1. Add/extend Pydantic contracts in `backend/app/schemas/`.
2. Put orchestration in `backend/app/services/`; put reusable persistence in `backend/app/repositories/`.
3. Add the endpoint in `backend/app/api/endpoints/` and register a new router in `backend/app/api/api.py`.
4. Add ORM entities to the canonical model registry and create an Alembic revision under `backend/migrations/versions/` when persistence changes.
5. Add focused tests to the matching `backend/tests/` category and refresh OpenAPI/types for contract changes.

### Frontend feature

1. Put route screens in `frontend/src/pages/` and register them in `App.tsx`.
2. Put reusable UI in the closest `components/` subdomain.
3. Keep HTTP calls in `services/`, server-state composition in `hooks/`, and types in `types/`.
4. Add Jest/Testing Library coverage in `frontend/src/__tests__/`; add an E2E journey only for cross-stack behavior.

### Build or infrastructure feature

- Image contents/flavors: root `Dockerfile`, then manifest/install/runtime tests in `backend/tests/docker/`.
- Container behavior: `entrypoint.sh`, `healthcheck.sh`, `warp-setup.sh`, and runtime-contract tests.
- CI behavior: thin stage in `Jenkinsfile` or release wrapper, with reusable implementation in `scripts/ci/`.
- Platform policy/data: `docker/manifests/`; avoid duplicating platform lists in pipelines.

## Generated, Local, and Sensitive Paths

These can exist in a checkout but are not tracked source:

- `backend/frontend_build/`, `frontend/dist/`, `frontend/build/`
- `backend/venv/`, root `venv/`, frontend/E2E `node_modules/`
- `backend/config/*.db`, root `config/`, `backend/logs/`, `*.log`
- `e2e/.stack/`, `e2e/test-results/`, `e2e/playwright-report/`, `e2e/results/`
- `.worktrees/`, `.planning/debug/`, caches, coverage, and phase-gate result JSON
- `infra-details.md` and `.claude/jenkins-api.sh` (local operations only; never quote or commit their contents)

When inspecting the repository, use `git ls-files` or `git status` to distinguish canonical files from these local artifacts.

## Branch Delta from `main`

| `main` path/role | `develop` replacement |
|---|---|
| `app/` Flask/Jinja backend and static UI | `backend/app/` FastAPI layers + `frontend/src/` React SPA |
| `wsgi.py`, `manage.py`, `run_dev.py` | `backend/main.py` and package/Docker scripts |
| root `migrations/` | `backend/migrations/` |
| root `tests/` | `backend/tests/`, `frontend/src/__tests__/`, `e2e/tests/` |
| root EPG diagnostic scripts | `scripts/dev/epg/` |
| GitHub Actions PR/release workflows | root `Jenkinsfile` + `jenkins/release.Jenkinsfile` + `scripts/ci/` |
| single legacy image shape | multi-stage root Dockerfile with named runtime flavors and manifests |

Do not create new work in removed root-era locations. Compatibility behavior belongs in the v2 backend and is verified by parity/regression tests.

---

*Update this map when canonical directories, generated-output policy, or workflow entry points change.*
