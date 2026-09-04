# Coding Conventions

**Analysis date:** 2026-09-03
**Branch mapped:** `develop` (the release-candidate branch currently intended to merge into `main`)

## Authority and Scope

- `backend/` and `frontend/` are the canonical application trees on this branch. Do not recreate the removed root `app/`, `tests/`, Flask entrypoints, or server-rendered frontend; `scripts/ci/assert_no_legacy_paths.sh --strict` guards this cutover.
- `CLAUDE.md` is the most current repository-specific operating guide. The older `.github/instructions/*.instructions.md` files describe intent but contain stale paths and tooling assumptions; verify them against the live tree before following them.
- Keep infrastructure credentials and private connection values out of code, tests, generated maps, and logs. `infra-details.md` is operator-only context; agent documentation should refer to Jenkins jobs and credential IDs symbolically.

## Naming and File Layout

### Python backend

- Modules, functions, local variables, and fixtures use `snake_case`: `backend/app/services/channel_status_service.py`, `get_tv_channels_with_total`, `alembic_backend_runtime`.
- Classes, SQLAlchemy models, Pydantic schemas, and exceptions use `PascalCase`: `ChannelRepository`, `TVChannel`, `ErrorResponse`, `APIError`.
- Constants and stable module-level maps use `UPPER_SNAKE_CASE`; environment variables are also uppercase (`DATABASE_URL`, `ACE_ENGINE_URL`).
- Tests are `backend/tests/test_*.py`. Specialized suites live in `backend/tests/contracts/`, `architecture/`, `parity/`, `regression/`, `perf/`, and `docker/`.
- Alembic revisions live in `backend/migrations/versions/`. Existing names mix timestamp and generated-slug styles; new migrations must have a unique revision/down-revision chain and should be exercised through Alembic, not only `Base.metadata.create_all`.

### React/TypeScript frontend

- Route pages and components use `PascalCase.tsx`: `frontend/src/pages/TVChannels.tsx`, `frontend/src/components/StatusLine.tsx`.
- Hooks use `useX.ts` and export `useX` functions: `frontend/src/hooks/useSystemServices.ts`.
- Services, utilities, callbacks, and variables use `camelCase`: `apiClient.ts`, `normalizeApiError`, `handleSubmit`.
- Interfaces, type aliases, and props types use `PascalCase`; constants shared across modules use `UPPER_SNAKE_CASE` when truly constant.
- Jest files are `*.test.ts` or `*.test.tsx` under `frontend/src/__tests__/`. Shared render/router/responsive helpers belong in `frontend/src/testUtils/`.
- E2E specs use numeric journey prefixes (`e2e/tests/00-stack.spec.ts` through `09-system.spec.ts`) because the suite is deliberately serial and stateful. Page objects use lowercase hyphenated filenames under `e2e/src/pages/`.

## Backend Design and Style

- Keep endpoint modules in `backend/app/api/endpoints/` thin: validate request/query data, obtain dependencies, call a service, and translate known failures.
- Put business rules in `backend/app/services/`; isolate database-only operations in `backend/app/repositories/`; define request/response DTOs in `backend/app/schemas/`.
- Register routers only in `backend/app/api/api.py`. Public API routes are under `/api/v1`; preserve intentional compatibility aliases such as `/channels` and `/acestream-channels` unless parity tests and migration policy change together.
- Dependency injection uses FastAPI `Depends`, normally with the SQLAlchemy `Session` from `get_db`. Avoid importing or constructing alternate application singletons.
- Add type hints to new/changed functions. The existing code is not uniformly typed, so improve touched code without turning a focused change into a repository-wide formatting rewrite.
- Use descriptive docstrings for public classes/functions and comments for non-obvious compatibility, lifecycle, migration, or platform behavior. Comments should explain why, not restate the code.
- Imports generally follow standard library, third-party, then `app.*` groups separated by blank lines. Imports are absolute within the backend because commands set `PYTHONPATH=backend`.
- The backend has no enforced Black/Ruff/isort/mypy configuration. Match the surrounding file (four-space indentation, conventional PEP 8 layout) and do not claim an unconfigured formatter is authoritative.

## Frontend Design and Style

- TypeScript runs with `strict: true`; new props, state, service payloads, and hook results should be explicitly typed. ESLint permits strategic `any`, but prefer generated or local domain types.
- Use React function components and hooks. Data fetching/mutations belong in `frontend/src/hooks/` using TanStack Query; HTTP calls belong in `frontend/src/services/` and share `apiClient`.
- API access should ultimately use types generated from `backend/openapi.json` in `frontend/src/types/api-generated.ts`. When a schema changes, regenerate both artifacts and commit them together.
- Use MUI and the tokens/extensions in `frontend/src/theme.ts` / `theme.d.ts`. Prefer shared layout and state primitives (`PageHeader`, `ContentSection`, `StatusLine`, `EmptyState`, `InlineStatusNotice`) to one-off page styling.
- Use accessible roles, names, labels, and semantic headings. Navigation labels are expected to match page `<h1>` values; tests and Playwright page objects intentionally query by roles and labels rather than CSS selectors.
- Pages are route-level composition; reusable UI goes in `frontend/src/components/`; API state goes through hooks/services rather than ad-hoc `fetch` calls in components.
- Formatting observed in current TypeScript is two-space indentation, single quotes, semicolons, trailing commas in multiline literals, and relative imports (no path aliases are configured).
- ESLint is configured in `frontend/.eslintrc.cjs`: React, hooks, JSX accessibility, TypeScript, and Testing Library rules. Unused variables prefixed `_` are permitted. There is no Prettier configuration; preserve local formatting.

## Error Handling

### Backend API

- Use Pydantic validation for request shape and FastAPI status semantics for expected invalid input or missing resources.
- Prefer `APIError` from `backend/app/api/error_handlers.py` for application failures that need a stable machine code, HTTP status, safe message, and optional context.
- The canonical error envelope is `{"error": {"code", "message", "correlation_id", "context"}}`, modeled in `backend/app/schemas/errors.py`. Global handlers add `X-Correlation-ID`; tests assert this contract.
- Let unexpected exceptions reach the registered global handler when possible. It logs the traceback and returns `INTERNAL_ERROR`. Do not leak secrets, tokens, or sensitive infrastructure details in messages/context.
- If a service intentionally degrades (for example a health/status probe), log the failure and return an explicit availability state. Broad `except Exception` is acceptable only at a deliberate resilience boundary; document why and retain enough structured logging to diagnose it.
- Use the standard `logging` module (`logger = logging.getLogger(__name__)`) and parameterized messages for new code. Reserve `logger.exception` for caught failures where a traceback is useful.
- Database write ownership must be clear. Existing repositories may commit or flush; when changing transactional code, inspect the caller and tests so nested transactions and rollback behavior remain correct.

### Frontend

- All Axios responses pass through `frontend/src/services/apiClient.ts`. Its interceptor converts backend/network failures with `normalizeApiError` and signals 401 token requirements.
- Preserve `ApiError` metadata (`kind`, `status`, `canRetry`, backend `code`, `correlationId`, and `context`) instead of reducing errors to strings too early.
- UI error states should be actionable, accessible, and specific enough for recovery. Test loading, empty, validation, unavailable, and retry states for changed surfaces.
- React Query mutations must invalidate the affected query keys after success. Avoid optimistic updates unless rollback and failure behavior are covered.

## Branch-Specific Contracts

- `develop` is the permanent pre-release branch; feature PRs target `develop`. A PR into `main` must have `develop` as its head, enforced by the Jenkins `Branch Policy` stage.
- The branch is a full v2 cutover: FastAPI + React/Vite are canonical, GitHub Actions workflows were removed, and Jenkins is the authoritative validator/publisher.
- Preserve startup/lifespan behavior in `backend/main.py`: database initialization/migration precedes scheduler registration, and scheduler intervals are read from settings at startup.
- Existing databases require Alembic-aware thinking. A model edit alone is insufficient; add a migration, run migration/schema tests, and verify startup compatibility paths.
- Preserve frontend Vite chunk rules in `frontend/vite.config.ts` unless bundle partitioning is the explicit task.

## Practical Agent Checklist

1. Read `CLAUDE.md`, the touched modules, and their nearest tests before editing.
2. Search for both canonical and compatibility routes/names before renaming anything.
3. Add or update the narrowest relevant backend/frontend test; use Alembic fixtures for real-schema behavior.
4. If API schemas change, run the OpenAPI dump and frontend code generation, then inspect the generated diff.
5. Run lint/typecheck/build for frontend changes and the relevant phase/cutover gate for cross-layer changes.
6. Do not modify generated build output (`frontend/dist/`, `frontend/build/`, `backend/frontend_build/`) by hand.
7. Never copy values from `infra-details.md` into docs or command output. Jenkins access/publishing should use configured jobs and credential IDs, not embedded secrets.

---

*Update this map when the canonical application layout, CI authority, API error contract, or branch policy changes.*
