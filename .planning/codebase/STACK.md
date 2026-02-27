# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- Python 3.10/3.11 - backend services and scheduled tasks in `v2/backend/` and legacy root runtime (`wsgi.py`, `run_dev.py`)
- TypeScript 4.9 - React frontend in `v2/frontend/src/`

**Secondary:**
- JavaScript - React build tooling and Jest config in `v2/frontend/package.json` and `v2/frontend/jest.config.js`
- Shell - container/process orchestration in `entrypoint.sh`, `healthcheck.sh`, `warp-setup.sh`
- SQL (via ORM/migrations) - SQLite schema/migrations in `migrations/` and `v2/backend/migrations/`

## Runtime

**Environment:**
- FastAPI + Uvicorn runtime in `v2/backend/main.py`
- Legacy Flask/WSGI-to-ASGI runtime still present in `wsgi.py`
- SQLite default DB paths in `v2/backend/app/config/settings.py` (`sqlite:///./config/scraper.db`) and legacy path `config/acestream.db`

**Package Manager:**
- Python: `pip` with `requirements.txt`, `requirements-dev.txt`, `requirements-prod.txt`, and `v2/backend/requirements.txt`
- Node: `npm` with lockfile `v2/frontend/package-lock.json`
- Lockfile: present for frontend (`v2/frontend/package-lock.json`), missing for Python dependencies

## Frameworks

**Core:**
- FastAPI (`v2/backend/main.py`)
- SQLAlchemy ORM (`v2/backend/app/models/models.py`, `v2/backend/app/config/database.py`)
- APScheduler for periodic jobs (`v2/backend/app/services/task_service.py`)
- Flask + Flask-Migrate + Flask-SQLAlchemy in legacy root stack (`pyproject.toml`, `manage.py`, `migrations_app.py`)

**Testing:**
- Pytest for Python tests (`tests/`, `v2/backend/tests/`)
- Jest + React Testing Library for frontend tests (`v2/frontend/src/__tests__/`, `v2/frontend/jest.config.js`)

**Build/Dev:**
- `react-scripts` (CRA) in `v2/frontend/package.json`
- `ts-node` for frontend build copy script in `v2/frontend/scripts/copy-build.ts`
- Docker for both legacy root and v2 stack (`Dockerfile`, `docker-compose.yml`, `v2/backend/Dockerfile`, `v2/docker-compose.yml`)

## Key Dependencies

**Critical:**
- `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings` - API and settings (`v2/backend/requirements.txt`)
- `sqlalchemy`, `alembic` - persistence and migrations (`v2/backend/requirements.txt`, `v2/backend/migrations/`)
- `aiohttp`, `beautifulsoup4`, `lxml` - scraping/parsing stack (`v2/backend/app/scrapers/`)
- `react`, `react-dom`, `@mui/material`, `react-query`, `axios` - frontend app stack (`v2/frontend/package.json`)

**Infrastructure:**
- `requests`/`httpx` for outbound integrations in backend services (`v2/backend/app/services/acestream_status_service.py`, `v2/backend/app/services/warp_service.py`)
- `gunicorn` + `uvicorn.workers.UvicornWorker` in legacy runtime (`wsgi.py`, `requirements-prod.txt`)

## Configuration

**Environment:**
- Main backend settings are `BaseSettings`-driven via `.env` in `v2/backend/app/config/settings.py`
- Runtime/docker toggles rely heavily on env vars (examples: `ENABLE_WARP`, `ENABLE_ACEXY`, `ENABLE_ACESTREAM_ENGINE`, `ACEXY_HOST`, `ACESTREAM_HTTP_PORT`) in `Dockerfile`, `docker-compose.yml`, and `entrypoint.sh`
- Frontend API base depends on `NODE_ENV` in `v2/frontend/src/services/apiClient.ts`

**Build:**
- Frontend TS config in `v2/frontend/tsconfig.json`
- Frontend Jest config in `v2/frontend/jest.config.js`
- CI workflows in `.github/workflows/pull_request.yml` and `.github/workflows/release.yml`

## Platform Requirements

**Development:**
- Python virtualenv for root and v2 Python code (`venv/` and `v2/backend/venv/` present)
- Node/npm for frontend (`v2/frontend/`)
- Optional Docker-based dev path for integrated services (ZeroNet, Acexy, WARP, engine)

**Production:**
- Container-first deployment model via Docker images in `Dockerfile` (legacy) and `v2/backend/Dockerfile` (v2)
- Current CI release path is still tied to legacy root stack (`.github/workflows/release.yml` watches `app/**` and root runtime files)

---

*Stack analysis: 2026-02-27*
*Update after major dependency changes*
