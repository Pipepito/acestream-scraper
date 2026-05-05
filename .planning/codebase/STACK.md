# Technology Stack

**Analysis Date:** 2026-02-27

## Languages

**Primary:**
- Python 3.10/3.11 - backend services and scheduled tasks in `backend/` plus legacy runtime remnants (`wsgi.py`, `run_dev.py`)
- TypeScript 4.9 - React frontend in `frontend/src/`

**Secondary:**
- JavaScript - React build tooling and Jest config in `frontend/package.json` and `frontend/jest.config.js`
- Shell - container/process orchestration in `entrypoint.sh`, `healthcheck.sh`, `warp-setup.sh`
- SQL (via ORM/migrations) - SQLite schema/migrations in `migrations/` and `backend/migrations/`

## Runtime

**Environment:**
- FastAPI + Uvicorn runtime in `backend/main.py`
- Legacy Flask/WSGI-to-ASGI runtime still present in `wsgi.py`
- SQLite default DB paths in `backend/app/config/settings.py` (`sqlite:///./config/scraper.db`) and legacy path `config/acestream.db`

**Package Manager:**
- Python: `pip` with `requirements.txt`, `requirements-dev.txt`, `requirements-prod.txt`, and `backend/requirements.txt`
- Node: `npm` with lockfile `frontend/package-lock.json`
- Lockfile: present for frontend (`frontend/package-lock.json`), missing for Python dependencies

## Frameworks

**Core:**
- FastAPI (`backend/main.py`)
- SQLAlchemy ORM (`backend/app/models/models.py`, `backend/app/config/database.py`)
- APScheduler for periodic jobs (`backend/app/services/task_service.py`)
- Flask + Flask-Migrate + Flask-SQLAlchemy in legacy root stack (`pyproject.toml`, `manage.py`, `migrations_app.py`)

**Testing:**
- Pytest for Python tests (`tests/`, `backend/tests/`)
- Jest + React Testing Library for frontend tests (`frontend/src/__tests__/`, `frontend/jest.config.js`)

**Build/Dev:**
- `react-scripts` (CRA) in `frontend/package.json`
- `ts-node` for frontend build copy script in `frontend/scripts/copy-build.ts`
- Docker for the canonical stack (`Dockerfile`, `docker-compose.yml`, `backend/Dockerfile`)

## Key Dependencies

**Critical:**
- `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings` - API and settings (`backend/requirements.txt`)
- `sqlalchemy`, `alembic` - persistence and migrations (`backend/requirements.txt`, `backend/migrations/`)
- `aiohttp`, `beautifulsoup4`, `lxml` - scraping/parsing stack (`backend/app/scrapers/`)
- `react`, `react-dom`, `@mui/material`, `react-query`, `axios` - frontend app stack (`frontend/package.json`)

**Infrastructure:**
- `requests`/`httpx` for outbound integrations in backend services (`backend/app/services/acestream_status_service.py`, `backend/app/services/warp_service.py`)
- `gunicorn` + `uvicorn.workers.UvicornWorker` in legacy runtime (`wsgi.py`, `requirements-prod.txt`)

## Configuration

**Environment:**
- Main backend settings are `BaseSettings`-driven via `.env` in `backend/app/config/settings.py`
- Runtime/docker toggles rely heavily on env vars (examples: `ENABLE_WARP`, `ENABLE_ACEXY`, `ENABLE_ACESTREAM_ENGINE`, `ACEXY_HOST`, `ACESTREAM_HTTP_PORT`) in `Dockerfile`, `docker-compose.yml`, and `entrypoint.sh`
- Frontend API base depends on `NODE_ENV` in `frontend/src/services/apiClient.ts`

**Build:**
- Frontend TS config in `frontend/tsconfig.json`
- Frontend Jest config in `frontend/jest.config.js`
- CI workflows in `.github/workflows/pull_request.yml` and `.github/workflows/release.yml`

## Platform Requirements

**Development:**
- Python virtualenv for root and canonical Python code (`venv/` and `backend/venv/` present)
- Node/npm for frontend (`frontend/`)
- Optional Docker-based dev path for integrated services (ZeroNet, Acexy, WARP, engine)

**Production:**
- Container-first deployment model via Docker images in the root `Dockerfile` and `backend/Dockerfile`
- Current CI/release logic uses canonical root paths for release inputs and validation

---

*Stack analysis: 2026-02-27*
*Update after major dependency changes*
