# Documentation Home

This repository now uses a single root deployment model:

- `backend/` is the API/runtime source of truth.
- `frontend/` is the web UI source of truth.

## Key Docs

- `docs/architecture/deployment.md`: production and local deployment model for `backend/` + `frontend/`.
- `docs/ops/jenkins-ci.md`: primary Jenkins CI/CD operator guide, cutover steps, and rollback guidance.
- `docs/ops/reverse-proxy.md`: reverse-proxy/HTTPS deployment — TLS, proxy-level auth, `base_url`, and port-exposure guidance.
- `docs/ops/acestream-arm-engine.md`: operator guide for the in-container AceStream engine on `linux/arm64` / `linux/arm/v7` (what is shipped, runtime settings, known gaps, testing on a Raspberry Pi, pin updates).
- `docs/ops/multiarch-manifest-updates.md`: schema of `docker/manifests/acestream.json` and the procedure for updating engine/platform pins.
- `docs/migration/migration-strategy.md`: cutover rules and migration direction.
- `docs/migration/development-phases.md`: planned phase breakdown.
- `docs/migration/development-progress.md`: current execution progress and completed work.

## Release Docs

- `docs/release/v2-release-notes.md`: user-facing v2 release notes (source for the GitHub release).
- `docs/release/v2-release-readiness.md`: gap audit, closure record, open items before the `v2.0.0` tag, and the two-phase `:latest` publish flow.
- `docs/release/phase5-multiarch-evidence.md`: how multi-arch evidence is produced on Jenkins and the per-release record.

## Testing

- `docs/testing/test-ownership-matrix.md`: canonical test locations and the required-check ownership policy.

## Developer Entry Points

- Backend local run: `cd backend && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Frontend local run: `cd frontend && npm install && npm start`
- Container stack: `docker compose up --build`

## Backend Alembic

Run Alembic from the repo root with the backend virtualenv active:

- `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini history`
- `PYTHONPATH=backend alembic -c backend/migrations/alembic.ini upgrade head`
