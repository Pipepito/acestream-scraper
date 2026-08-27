# Acestream Scraper

Acestream Scraper now runs on a single canonical root stack:

- `backend/` (FastAPI + SQLAlchemy + scraper logic)
- `frontend/` (React + TypeScript)

Legacy root runtime entrypoints were retired during cutover. All deployment and development instructions below use only the root `backend/` and `frontend/` paths.

## Quick Start

### Docker Compose

```bash
docker compose up -d
```

To start the example ZeroNet sidecar from `docker-compose.yml`, enable its optional profile:

```bash
docker compose --profile zeronet up -d
```

Services:

- API + SPA: `http://localhost:8000`
- ZeroNet example sidecar (optional profile, reachable from the host): `http://localhost:43110`

The checked-in `docker-compose.yml` uses `pipepito/acestream-scraper:latest`. `latest` is the full `scraper-acestream-acexy` image, while the explicit flavor tags are `scraper`, `scraper-acestream`, `scraper-acexy`, and `scraper-acestream-acexy`.

WARP is installed in every flavor's `linux/amd64` image (ARM images ship without it), but it only starts when `ENABLE_WARP=true`. WARP-enabled containers need the runtime capabilities `NET_ADMIN` and `SYS_ADMIN`.

ZeroNet remains an external sidecar/service. It is not bundled into every image, and the app talks to it through `ZERONET_URL`.

The default compose file points `ZERONET_URL` at `http://host.docker.internal:43110`, so the app can start cleanly even when the optional `zeronet` profile is disabled. The checked-in `zeronet` compose service is an amd64-focused sidecar example. On ARM hosts, prefer an external ZeroNet endpoint or a compatible replacement sidecar and keep `ZERONET_URL` pointed at it.

Runtime behavior is env-driven even when binaries are installed in the selected image. `ENABLE_ACESTREAM_ENGINE` controls the in-container AceStream engine, `ENABLE_ACEXY` controls Acexy, `ACESTREAM_HTTP_HOST` and `ACESTREAM_HTTP_PORT` define the engine endpoint, and `ACEXY_HOST` and `ACEXY_PORT` define where Acexy connects.

AceStream platform availability is manifest-driven via `docker/manifests/acestream.json`. `latest` and `scraper-acestream-acexy` are only published for platforms listed there.

The manifest currently covers `linux/amd64` (native Linux engine 3.2.11), `linux/arm64` (stable: the official AceStream Android engine 3.1.80.0 running natively on a minimal Android bionic userland inside the image) and `linux/arm/v7` (experimental: builds and installs, but has not been runtime-tested on real ARMv7 hardware yet). `latest`, `scraper-acestream`, and `scraper-acestream-acexy` are therefore published for all three platforms. The engine stays opt-in (`ENABLE_ACESTREAM_ENGINE=false` by default), and no extra privileges, capabilities, or seccomp changes are needed to run it on ARM.

When you enable the engine on ARM, it keeps its config, cache, and logs under `/var/lib/acestream` (`ACESTREAM_HOME`); mount a volume there (for example `-v acestream-state:/var/lib/acestream`) so they survive container replacement, and publish `6878` (engine HTTP API — unauthenticated, so only on trusted networks) plus `8621` tcp/udp (P2P) if they must be reachable from outside the container. Raspberry Pi 5: the Android engine needs a 4 KB kernel page size, so set `kernel=kernel8.img` in `config.txt` (the default `kernel_2712` kernel uses 16 KB pages and the engine refuses to start). ARM images ship without WARP. See [wiki/Docker.md](wiki/Docker.md) for the full ARM engine notes and caveats.

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
- `ZERONET_URL` (default: `http://host.docker.internal:43110` in the checked-in compose example)
- `CORS_ORIGINS` (default: `http://localhost:3000`)
- `FRONTEND_BUILD_PATH` (default: `frontend_build`)
- `ACE_ENGINE_URL` (default: `http://localhost:6878`)

### Docker Runtime Toggles

- `ENABLE_WARP` (default: `false`)
- `ENABLE_ACESTREAM_ENGINE` (default: `false`)
- `ENABLE_ACEXY` (default: `false`)
- `ACESTREAM_HTTP_HOST` (default: `localhost`)
- `ACESTREAM_HTTP_PORT` (default: `6878`)
- `ACEXY_HOST` (default: `localhost`)
- `ACEXY_PORT` (default: `6878`)
- `ACESTREAM_HOME` (default: `/var/lib/acestream`; state, cache, and logs of the ARM Android engine — mount a volume there)

Docker flavor choice controls which optional binaries are installed. Runtime env vars control whether those installed services actually start.

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

Safe pre-deploy check for existing user databases:

```bash
bash scripts/ops/preflight_v2_deploy.sh
```

This script creates timestamped DB backups under `config/backups/` and prints a clear SAFE/UNSAFE result before v2 rollout.
If result is UNSAFE, it also exports detected scraper sources into a rescue DB file (`scraper_sources_rescue.db`) inside the same backup run folder.

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
- [Reverse Proxy / HTTPS](docs/ops/reverse-proxy.md) — TLS, proxy-level auth, and safe port exposure for access beyond a trusted network
- [Migration Strategy](docs/migration/migration-strategy.md)
- [Development Phases](docs/migration/development-phases.md)
- [Development Progress](docs/migration/development-progress.md)
