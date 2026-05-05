# Documentation Home

This repository now uses a single root deployment model:

- `backend/` is the API/runtime source of truth.
- `frontend/` is the web UI source of truth.

## Key Docs

- `docs/architecture/deployment.md`: production and local deployment model for `backend/` + `frontend/`.
- `docs/ops/jenkins-ci.md`: primary Jenkins CI/CD operator guide, cutover steps, and rollback guidance.
- `docs/migration/migration-strategy.md`: cutover rules and migration direction.
- `docs/migration/development-phases.md`: planned phase breakdown.
- `docs/migration/development-progress.md`: current execution progress and completed work.

## Developer Entry Points

- Backend local run: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Frontend local run: `cd frontend && npm install && npm start`
- Container stack: `docker compose up --build`

## Backend Alembic

Run Alembic from the repo root with the backend virtualenv active:

- `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini history`
- `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini upgrade head`
