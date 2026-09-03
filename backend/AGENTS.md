# Backend agent guide

These instructions extend the repository root `AGENTS.md` for work in `backend/`.

## Commands

Run from the repository root unless a command says otherwise:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/test_channels.py::test_name
PYTHONPATH=backend alembic -c backend/migrations/alembic.ini history
PYTHONPATH=backend alembic -c backend/migrations/alembic.ini upgrade head
```

`python backend/run_tests.py <group>` supports `channels`, `tv`, `epg`,
`scrapers`, `search`, `playlists`, `config`, `health`, `warp`, and `coverage`.

## Architecture

- `main.py` owns the FastAPI lifespan, database initialization, router mount,
  scheduler registration, deferred migration scheduling, and SPA fallback.
- `app/api/api.py` is the router wiring point. Endpoint modules should validate and
  delegate, not accumulate domain or persistence logic.
- `app/services/` owns business behavior; `app/repositories/` owns DB-only access;
  `app/schemas/` owns request/response DTOs.
- `app/models/models.py` is the main SQLAlchemy model hub. Additional operational
  models live beside it. `Base` comes from `app/config/database.py`.
- `app/scrapers/` implements `BaseScraper`, HTTP, and ZeroNet strategies.
- `app/tasks/` contains work invoked by APScheduler tasks registered in `main.py`.
- Public API routes are under `/api/v1`; compatibility aliases are intentional.
  The public M3U route `/playlists/m3u` is not under `/api`.

## Database and startup invariants

- Production schema ownership belongs to Alembic. Add a revision for model changes,
  and test both a fresh upgrade and an upgrade from the relevant prior revision.
- `initialize_database()` migrates a legacy v1 SQLite database in two phases. Small
  tables move during startup; EPG programs are copied later in resumable batches.
  Never move the large copy back into the blocking startup path.
- Existing stamped databases are not automatically upgraded by
  `initialize_database()`. Deployment/preflight behavior must be considered when a
  new revision is added.
- Preserve migration checkpointing, keyset pagination, deduplication, retention
  filtering, and shutdown cancellation in deferred EPG migration work.
- Use timezone-aware UTC datetimes throughout models, schemas, services, and tests.

## Tests

- Most tests use `backend_runtime`, `client`, and `db_session`, which bind a temp
  SQLite database and create schema quickly.
- Migration-sensitive behavior uses `alembic_backend_runtime`, `alembic_client`,
  and `alembic_db_session`, which provision through `alembic upgrade head`.
- The fixture harness rebinds the lazy engine and invalidates cached settings; do
  not reintroduce module-reload-based runtime setup.
- Import config/models lazily inside fixtures when binding order matters.
- Add focused regression tests next to the affected domain, then run the relevant
  group plus migration/contract tests when schemas or startup change.

## API and security

- Type endpoint inputs/outputs with Pydantic DTOs and keep OpenAPI accurate.
- Preserve optional `API_TOKEN` behavior and frontend token compatibility.
- Outbound scrape and EPG URLs cross a trust boundary. Reuse the existing SSRF
  validation and redirect checks; do not bypass them for convenience.
- Avoid leaking upstream response bodies, credentials, tokens, local paths, or
  infrastructure details in API errors and logs.
- Move blocking network/filesystem/CPU work off the async event loop.
