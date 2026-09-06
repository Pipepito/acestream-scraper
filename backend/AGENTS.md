# Backend agent guide

These instructions extend the repository root `AGENTS.md` for work in `backend/`.

## Commands

Run from the repository root unless a command says otherwise:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 --no-proxy-headers
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
- Existing stamped databases are backed up and upgraded to Alembic head by
  `initialize_database()`. Keep deployment/preflight and upgrade-path tests aligned.
- Startup runs in a background boot task, with blocking DB work in a thread. The
  SPA and authenticated startup diagnostics stay available on failure; other APIs
  and public health return 503 until ready. Preserve the per-database process lock,
  confirmed backup-first staged recovery, and interrupted-recovery marker. See
  `docs/ops/startup-recovery.md`. Never expose raw exceptions or DB values in
  downloadable diagnostics.
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

## Tuner and player media selection

- Stable tuner channel URLs resolve online, active sources by measured bitrate
  (unknown last). Startup retries retain one tuner slot and close every failed
  engine session. Never splice unrelated feeds after sending MPEG-TS bytes.
- Bitrate/audio probes must stay bounded and restrict every HTTP redirect to the
  engine host before issuing it. ffprobe consumes a byte sample through stdin,
  never an upstream URL. Missing metadata is unknown, not zero bitrate.
- Browser session sharing includes the selected audio track. An audio change must
  not change another viewer's session, evade capacity limits, or leak an engine
  session. Parse input audio tracks only, excluding ffmpeg output declarations.

- Status probes use unique PIDs, but native AceStream 3.2.11 stop affects viewers
  of the same source despite distinct PIDs. Preserve the active-playback guard
  before probing and before cleanup, the shared two-probe limit, and per-source
  serialization. Stable tuner GETs refresh alternatives in the background; HEAD
  must not start probes. See `docs/ops/stream-check-pid.md` for live evidence.

## Playback routing

`GET/PUT /api/v1/config/playback-routing` persists `use_acexy` and `acexy_url`
as one JSON setting. Direct mode is the default. Web-player and tuner factories
use `playback_client_from_settings`; engine health/probes remain direct.
Acexy mode reads MPEG-TS from `/ace/getstream?id=…` with no PID or engine JSON
start/stat/stop calls. The session retains its Acexy ownership flag across
configuration changes so cleanup never stops another proxy client. Remote
players use the server relay in Acexy mode, bypassing saved custom link formats;
direct mode honors their formats and adds a unique PID to direct engine links.
Existing shared browser sessions retain their route until teardown. See
`wiki/Remote-Players.md#playback-routing` for operator behavior.
