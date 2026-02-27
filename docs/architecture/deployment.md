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

### Supported Image Targets

The canonical image build now targets:

- `linux/amd64`
- `linux/arm/v7`
- `linux/arm64`

Required minimum compatibility claims for release signoff:

- ARM v7 image build succeeds and is included in architecture validation outputs.
- ARM64 image build succeeds and is included in architecture validation outputs.
- Runtime smoke checks pass for required ARM targets (`/api/v1/health`, frontend root path).

### Build and Validation Path

Use the canonical scripts:

```bash
# Build matrix (local dry-run check)
bash scripts/ci/build_multiarch_images.sh --dry-run --platforms linux/arm/v7,linux/arm64

# Verify required architecture variants
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result.json --required linux/arm/v7,linux/arm64

# Runtime smoke flow
bash scripts/ci/phase5_arch_smoke.sh --platforms linux/arm/v7,linux/arm64
```

CI orchestration:

- `.github/workflows/multiarch-validation.yml`
- `scripts/phase_gates/phase5_gate_runner.py` (`quick` and `full` profiles)

### Android TV Notes

Android TV deployments should prefer `linux/arm64` when device firmware supports 64-bit containers.  
`linux/arm/v7` remains supported for older ARM32 devices but may need conservative runtime settings.

Recommended operator caveats:

- Prefer reduced background concurrency on lower-memory ARMv7 devices.
- Validate storage I/O performance for SQLite-backed deployments on removable media.
- Run the Phase 5 smoke checklist before production rollouts on new device classes.

See: `docs/migration/phase5-architecture-smoke-checklist.md`
