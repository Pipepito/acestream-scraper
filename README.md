# Acestream Scraper v2

> Current release line: **v2.0.0** — FastAPI backend, React web interface, multi-flavor Docker images, and amd64/ARM deployment.

Acestream Scraper now runs on a single canonical root stack:

- `backend/` (FastAPI + SQLAlchemy + scraper logic)
- `frontend/` (React + TypeScript)

Legacy Flask runtime entrypoints were retired during the v2 cutover. All deployment and development instructions below use only `backend/` and `frontend/`.

## Choose Your Starting Point

- **Installing with Docker:** use the [interactive Docker command builder](https://pipepito.github.io/acestream-scraper/) to generate the correct image tag, ports, volumes, and environment options for your machine.
- **Using the application:** follow the [illustrated v2 walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage), from checking services through importing the generated playlist.
- **Upgrading from v1:** read the [migration guide](wiki/Installation.md#migrating-from-v1) and run the preflight backup before starting v2.
- **Developing or operating the service:** use the local-development section below and the [documentation index](#documentation-index).

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

Not sure which tag, ports, folders or options you need? The [Docker command builder](https://pipepito.github.io/acestream-scraper/) asks three questions and produces a ready-to-copy `docker run` command or `docker-compose.yml` for your flavor, platform and features. It lives in this repository as `docs/index.html` + `docs/builder/`; Jenkins publishes it to the `gh-pages` branch (served by GitHub Pages) and mirrors the wiki pages under `wiki/` to the [GitHub wiki](https://github.com/Pipepito/acestream-scraper/wiki) on every validated `develop` build.

`latest` and the immutable `vX.Y.Z` tags (plus `vX.Y.Z-<flavor>`) are the releases, cut from `main`. A pre-release channel is published from the `develop` branch as well: `pipepito/acestream-scraper:develop` (the full `scraper-acestream-acexy` payload, mirroring what `latest` means for releases) plus `develop-scraper`, `develop-scraper-acestream`, `develop-scraper-acexy`, and `develop-scraper-acestream-acexy`. The channel tags are moving tags, re-pushed on every validated build of `develop` (the full CI validation runs first, on the same platforms as the release flavors), so they are meant for testing the next release and not for production. To try one, set `image: pipepito/acestream-scraper:develop` in your compose file or `docker pull pipepito/acestream-scraper:develop`.

WARP is installed in every flavor's `linux/amd64` image (ARM images ship without it), but it only starts when `ENABLE_WARP=true`. WARP-enabled containers need the runtime capabilities `NET_ADMIN` and `SYS_ADMIN`.

ZeroNet works in two modes. The `linux/amd64` images bundle a ZeroNet node ([zeronet-conservancy](https://github.com/zeronet-conservancy/zeronet-conservancy) v0.7.10 on its own Python 3.11, like the v1 image) that is opt-in via `ENABLE_ZERONET=true` (plus optional `ENABLE_TOR=true`); its state lives in `/data/zeronet` and its UI/fileserver ports are `43110`/`26552`. Alternatively — and on ARM images, which ship without the bundled node — ZeroNet runs as an external sidecar/service and the app talks to it through `ZERONET_URL`.

The default compose file points `ZERONET_URL` at `http://host.docker.internal:43110`, so the app can start cleanly even when the optional `zeronet` profile is disabled. The checked-in `zeronet` compose service is an amd64-focused sidecar example. On ARM hosts, prefer an external ZeroNet endpoint or a compatible replacement sidecar and keep `ZERONET_URL` pointed at it. When you enable the embedded node instead, leave `ZERONET_URL` unset (it then targets the embedded UI port automatically) or set it to `http://127.0.0.1:43110`.

IPFS is bundled: every flavor ships the [Kubo](https://github.com/ipfs/kubo) daemon on `linux/amd64` and `linux/arm64` (Kubo publishes no 32-bit ARM build, so `linux/arm/v7` images ship without it and refuse `ENABLE_IPFS=true`). The daemon is opt-in — `ENABLE_IPFS=false` by default — and `ipfs://` / `ipns://` sources are fetched through `IPFS_GATEWAY_URL`, which defaults to the embedded gateway at `http://127.0.0.1:8081`. The gateway sits on `8081` in-container because Acexy already owns `8080`. To scrape IPFS without the embedded daemon, keep `ENABLE_IPFS=false` and point `IPFS_GATEWAY_URL` at an external node instead (for example `http://host.docker.internal:8080` for a Kubo or IPFS Desktop install on the Docker host).

When the embedded daemon is enabled, persist its repository by mounting a volume at `/data/ipfs` (`-v ./ipfs_data:/data/ipfs`), and publish `4001` tcp/udp (swarm — improves peer connectivity), `8081` (HTTP gateway) as needed. The RPC API on `5001` is unauthenticated and binds to the container loopback by default; only expose it as `127.0.0.1:5001:5001` (set `IPFS_API_HOST=0.0.0.0` in-container first) if you need the WebUI.

Runtime behavior is env-driven even when binaries are installed in the selected image. `ENABLE_ACESTREAM_ENGINE` controls the in-container AceStream engine, `ENABLE_ACEXY` controls Acexy, `ACESTREAM_HTTP_HOST` and `ACESTREAM_HTTP_PORT` define the engine endpoint, and `ACEXY_HOST` and `ACEXY_PORT` define where Acexy connects.

AceStream platform availability is manifest-driven via `docker/manifests/acestream.json`. `latest` and `scraper-acestream-acexy` are only published for platforms listed there.

The manifest currently covers `linux/amd64` (native Linux engine 3.2.11), `linux/arm64` (stable: non-premium-gated Android engine 3.2.17 from [`jopsis/acestream:v3.2.17-fix`](https://hub.docker.com/r/jopsis/acestream), digest-pinned and grafted into this image), and `linux/arm/v7` (experimental: official Android engine 3.1.80.0; builds and installs, but has not been runtime-tested on real ARMv7 hardware yet). The jopsis build sources are [public on GitHub](https://github.com/jopsis/docker-acestream-aceserve); the dashboard reports and links the exact engine package at runtime. `latest`, `scraper-acestream`, and `scraper-acestream-acexy` are published for all three platforms. The engine stays opt-in (`ENABLE_ACESTREAM_ENGINE=false` by default), and no extra privileges, capabilities, or seccomp changes are needed to run it on ARM.

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
- `EPG_PROGRAM_RETENTION_HOURS` (default: `24`) — EPG programs that ended more than this many hours ago are deleted by the hourly `epg_program_cleanup` job and skipped by the v1→v2 migration; negative keeps everything
- `ZERONET_URL` (default: `http://host.docker.internal:43110` in the checked-in compose example)
- `IPFS_GATEWAY_URL` (default: the embedded gateway `http://127.0.0.1:8081`; point it at an external IPFS gateway when `ENABLE_IPFS=false`)
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
- `ENABLE_IPFS` (default: `false`; starts the embedded Kubo daemon — amd64/arm64 images only)
- `IPFS_PATH` (default: `/data/ipfs`; the embedded daemon's repository — mount a volume there)
- `IPFS_SWARM_PORT` (default: `4001`), `IPFS_API_PORT` (default: `5001`, loopback-bound), `IPFS_GATEWAY_PORT` (default: `8081` — `8080` belongs to Acexy)
- `ENABLE_ZERONET` (default: `false`; starts the bundled ZeroNet node — amd64 images only)
- `ENABLE_TOR` (default: `false`; runs TOR for the bundled ZeroNet node — only with `ENABLE_ZERONET=true`)
- `ZERONET_DATA_DIR` (default: `/data/zeronet`; the bundled node's state — mount a volume there)
- `ZERONET_UI_PORT` (default: `43110`), `ZERONET_FILESERVER_PORT` (default: `26552`), `ZERONET_UI_HOST` (extra Host headers the UI should accept)

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
