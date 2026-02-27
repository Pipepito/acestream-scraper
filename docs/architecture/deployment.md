# Deployment Architecture

## Canonical Runtime Model

Acestream Scraper runs with root-owned application paths:

- `backend/` provides API, background tasks, scraper logic, and serves the built SPA.
- `frontend/` builds static assets consumed by backend runtime image.

## Containers

### Unified Image Build

Root `Dockerfile` performs a two-stage build:

1. Build `frontend/` with Node.
2. Build `backend/` runtime with Python and copy frontend build output to `frontend_build/`.

Runtime command:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Compose Stack

`docker-compose.yml` runs:

- `app`: backend runtime at port `8000`
- `zeronet`: optional ZeroNet dependency at port `43110`

Bring up stack:

```bash
docker compose up --build
```

## Environment Configuration

Primary backend settings:

- `DATABASE_URL`
- `LEGACY_DATABASE_URL`
- `ZERONET_URL`
- `CORS_ORIGINS`
- `FRONTEND_BUILD_PATH`
- `ACE_ENGINE_URL`

Legacy env aliases remain supported for one release window (`v2-cutover-r1`) with canonical-variable precedence and conflict warnings.

## Multi-Architecture Direction

Current deployment docs define one canonical runtime path. Multi-arch release hardening (including `linux/arm/v7` and `linux/arm64`) is tracked in roadmap Phase 5 and will extend this document with buildx and runtime validation details.
