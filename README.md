# Acestream Scraper

Acestream Scraper now runs on a single canonical root stack:

- `backend/` (FastAPI + SQLAlchemy + scraper logic)
- `frontend/` (React + TypeScript)

Legacy root runtime entrypoints were retired during cutover. All deployment and development instructions below use only the root `backend/` and `frontend/` paths.

## Quick Start

### Docker Compose

```bash
docker compose up --build
```

Services:

- API + SPA: `http://localhost:8000`
- ZeroNet (if used): `http://localhost:43110`

### Local Development

Backend:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (optional dev server):

```bash
cd frontend
npm ci
npm start
```

## Project Structure

```text
.
├── backend/                  # FastAPI app, API, services, scrapers, tests
├── frontend/                 # React app
├── config/                   # SQLite DB + runtime config volume
├── scripts/                  # CI/release/ops scripts
├── docs/                     # Architecture, migration, development docs
├── docker-compose.yml
└── Dockerfile
```

## Environment Variables

### Canonical Backend Settings

- `DATABASE_URL` (default: `sqlite:///./config/scraper.db`)
- `LEGACY_DATABASE_URL` (default: `sqlite:///./config/acestream.db`)
- `ZERONET_URL` (default: `http://127.0.0.1:43110`)
- `CORS_ORIGINS` (default: `http://localhost:3000`)
- `FRONTEND_BUILD_PATH` (default: `frontend_build`)
- `ACE_ENGINE_URL` (default: `http://localhost:6878`)

### One-Release Env Compatibility Window

For the cutover release window (`v2-cutover-r1`), legacy env aliases are auto-mapped to canonical names. If both legacy and canonical vars are set with different values, canonical vars win and a warning is emitted at startup.

Legacy aliases currently mapped:

- `SCRAPER_DB_URL` -> `DATABASE_URL`
- `LEGACY_DB_URL` -> `LEGACY_DATABASE_URL`
- `ZERONET_BASE_URL` -> `ZERONET_URL`
- `CORS_ALLOW_ORIGINS` -> `CORS_ORIGINS`
- `FRONTEND_STATIC_DIR` -> `FRONTEND_BUILD_PATH`
- `ACESTREAM_ENGINE_URL` -> `ACE_ENGINE_URL`

Disable alias compatibility explicitly with:

- `ENABLE_LEGACY_ENV_ALIASES=false`

## Verification Commands

Quick cutover checks:

```bash
bash scripts/ci/run_cutover_required_checks.sh --profile quick
```

Strict legacy reference guard:

```bash
bash scripts/ci/assert_no_legacy_paths.sh --strict
```

## Documentation Index

- [Docs Home](docs/README.md)
- [Deployment](docs/architecture/deployment.md)
- [Migration Strategy](docs/migration/migration-strategy.md)
- [Development Phases](docs/migration/development-phases.md)
- [Development Progress](docs/migration/development-progress.md)
