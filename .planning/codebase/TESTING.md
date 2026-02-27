# Testing Patterns

**Analysis Date:** 2026-02-27

## Test Framework

**Runner:**
- Python: `pytest` for root and v2 backend tests.
- Frontend: Jest + React Testing Library + `ts-jest` (`v2/frontend/jest.config.js`).

**Assertion Library:**
- Python: pytest assert introspection.
- Frontend: Jest `expect` with `@testing-library/jest-dom` matchers.

**Run Commands:**
```bash
pytest tests/                                # Root/legacy suite
pytest v2/backend/tests/                     # V2 backend suite
python v2/backend/run_tests.py               # V2 backend grouped test runner
cd v2/frontend && npm test                   # Frontend tests
```

## Test File Organization

**Location:**
- Root tests in `tests/` with split `tests/unit/` and `tests/integration/`.
- V2 backend tests in `v2/backend/tests/`.
- Frontend tests in `v2/frontend/src/__tests__/` and near setup helpers.

**Naming:**
- Python: `test_*.py`.
- Frontend: `*.test.tsx`.

**Structure:**
```
tests/
  unit/
  integration/
v2/backend/tests/
v2/frontend/src/__tests__/
```

## Test Structure

**Suite Organization:**
- Python often uses `class TestX:` grouping with method-level test cases.
- Extensive pytest fixtures in `tests/conftest.py` and `v2/backend/tests/conftest.py`.
- Frontend test files use Jest `describe`/`it` blocks.

**Patterns:**
- Fixture-driven setup for DB sessions and dependency overrides.
- Route-level integration tests validate status codes and response payloads.
- Frontend tests mock hooks/services for deterministic rendering behavior.

## Mocking

**Framework:**
- Python: `unittest.mock.patch`, `MagicMock`, `AsyncMock`, pytest monkeypatch.
- Frontend: Jest `jest.mock(...)` and mocked hook return values.

**Patterns:**
- Backend integration tests patch service methods in endpoint modules (example WARP tests).
- Legacy tests heavily patch module paths that assume root `app.*` package availability.
- Frontend tests stub API clients and mutate hook responses per scenario.

**What to Mock:**
- External APIs/CLIs (`requests`, `warp-cli`, Acestream endpoints).
- Time/network dependent paths.
- Out-of-process integrations.

**What NOT to Mock (preferred):**
- Internal business logic inside services/repositories when testing unit behavior.

## Fixtures and Factories

**Test Data:**
- Rich fixture sets for seeded channels/EPG URLs/programs in `v2/backend/tests/conftest.py`.
- Root test fixtures also establish temp SQLite DBs and monkeypatch singleton config state.

**Location:**
- Shared fixtures primarily in `conftest.py` files.
- No dedicated `tests/factories/` directory detected.

## Coverage

**Requirements:**
- No explicit coverage threshold configuration detected.
- CI gates on lint + test pass/fail, not coverage percent.

**Configuration:**
- No repository coverage config file detected (`.coveragerc` not present).

**View Coverage:**
```bash
pytest --cov=v2/backend/app v2/backend/tests
cd v2/frontend && npm test -- --coverage
```

## Test Types

**Unit Tests:**
- Present in root `tests/unit/` and in mixed backend service tests.
- Emphasize service/repository behavior and helper logic.

**Integration Tests:**
- Heavy emphasis in `v2/backend/tests/` for endpoint workflows and DB interactions.
- Root `tests/integration/` validates older API/UI paths.

**E2E Tests:**
- Browser-level E2E framework (Playwright/Cypress) not detected.

## Common Patterns

**Async Testing:**
- Async FastAPI paths are tested via `TestClient` + patched async services.
- Some async fixtures are declared for HTTPX usage.

**Error Testing:**
- Tests explicitly assert 4xx/5xx behavior and error payload fields.
- Endpoint failure paths are simulated using patched side effects.

**Snapshot Testing:**
- Snapshot testing not detected in frontend suite.

---

*Testing analysis: 2026-02-27*
*Update when test patterns change*
