# Coding Conventions

**Analysis Date:** 2026-02-27

## Naming Patterns

**Files:**
- Python backend files use `snake_case.py` in `backend/app/`.
- React pages/components use `PascalCase.tsx` in `frontend/src/pages/` and `frontend/src/components/`.
- Frontend hooks use `useX.ts` naming (examples: `useChannels.ts`, `useEPG.ts`).
- Python tests use `test_*.py`; frontend tests use `*.test.tsx`.

**Functions:**
- Python functions/methods use `snake_case` (examples: `get_acestream_channels`, `run_epg_refresh_task`).
- TS/React functions use `camelCase`, with handler prefix `handle*` in UI components.
- Async operations in Python and TS typically use `async`/`await`; no special naming prefix.

**Variables:**
- Python local variables are predominantly `snake_case`.
- TypeScript variables are predominantly `camelCase`.
- Constants use mixed style; some uppercase constants exist, but many config values remain inline.

**Types:**
- Pydantic schema classes use `PascalCase` in backend (`AcestreamChannelResponse`).
- TS interfaces/types use `PascalCase` in frontend service/type files.

## Code Style

**Formatting:**
- Root CI enforces `flake8` checks via `.github/workflows/pull_request.yml` and `release.yml`.
- No repository-level `ruff.toml`, `mypy.ini`, `pytest.ini`, or root `.eslintrc` detected.
- Frontend inherits CRA ESLint config from `frontend/package.json`.
- Semicolon usage in TypeScript is consistent.

**Linting:**
- Python linting is CI-driven (`flake8`) instead of local config files.
- Frontend linting is via `react-scripts` defaults.
- Debug `console.log` and `print` statements still exist in production paths (example: `frontend/src/pages/AcestreamChannels.tsx`, `backend/app/api/endpoints/playlists.py`).

## Import Organization

**Order (observed):**
1. Standard library imports
2. Third-party imports
3. Local app imports

**Grouping:**
- Python files generally separate groups with blank lines.
- TS imports are grouped but not always strictly sorted.

**Path Aliases:**
- No TS path aliases configured in `frontend/tsconfig.json`.
- Relative imports are standard in frontend source.

## Error Handling

**Patterns:**
- Endpoints raise `HTTPException` for expected request failures.
- Services and tasks often wrap execution in broad `try/except` and return fallback message payloads.
- Integration status services prefer returning structured availability dictionaries over throwing.

**Error Types:**
- Validation errors are delegated to FastAPI/Pydantic.
- Internal operational errors are often logged and converted to generic error responses.
- Some modules still rely on ad-hoc error string construction.

## Logging

**Framework:**
- Python `logging` is the primary backend logging mechanism.
- Setup helper in `backend/app/utils/logging.py` configures root logger, stdout, and file logs.

**Patterns:**
- Scheduler/task services log start/finish/error status.
- Third-party noisy loggers are downgraded to `WARNING`.
- Mixed logging quality: some `print()`/debug logging remains.

## Comments

**When to Comment:**
- Docstrings are common on backend classes/functions.
- Inline comments are used to explain compatibility or temporary behavior.

**JSDoc/TSDoc:**
- Frontend service modules include lightweight doc comments.
- Full TSDoc coverage is inconsistent.

**TODO Comments:**
- TODOs exist in frontend pages (example: `frontend/src/pages/EPG.tsx`, `TVChannels.tsx`).
- TODOs are not linked to issue IDs consistently.

## Function Design

**Size:**
- Some functions are large and multi-responsibility (examples: `backend/app/services/epg_service.py`, large page components in `frontend/src/pages/`).

**Parameters:**
- FastAPI endpoints commonly use explicit query/body params.
- Service methods often accept many optional parameters for filtering/update flexibility.

**Return Values:**
- Backend API returns Pydantic-compatible dict/object responses.
- Some frontend service type annotations do not perfectly reflect backend payload shape (example: paginated channel responses).

## Module Design

**Exports:**
- Backend is class/module oriented by domain.
- Frontend uses default exports for many components and named exports for hooks/services.

**Barrel Files:**
- Limited frontend barrel usage (example: `frontend/src/services/index.ts`, `frontend/src/hooks/index.ts`).
- Most modules are imported directly from source files.

---

*Convention analysis: 2026-02-27*
*Update when patterns change*
