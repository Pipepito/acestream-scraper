# Acestream Scraper v2.0.0

Acestream Scraper v2 replaces the legacy Flask application with one supported FastAPI backend and React web interface. It adds a redesigned operational UI, safer v1 data migration, configurable Docker flavors, ARM support, stronger API and runtime safeguards, and a Jenkins-validated release process.

This is a major release. Read **Upgrade from v1** and **Breaking changes** before replacing an existing container.

## User-facing highlights

- A new responsive interface with light/dark themes and eight focused destinations: Overview, Scraper, Search, Acestream Channels, TV Channels, EPG, Playlist, and Settings.
- A single Overview for engine/service health, inventory totals, scheduled jobs, recent outcomes, and next-run times.
- Clear source management for regular HTTP, ZeroNet, IPFS/IPNS, and pages containing bare 40-character AceStream IDs.
- Stream filters, status checks, CSV export, playlist visibility, and assignment to user-facing TV channels.
- TV channels can group primary/backup streams, carry guide metadata, show now/next schedules, and be marked as favorites.
- A five-part EPG workflow for XMLTV sources, guide channels, automatic matching, matching rules, and filtered XMLTV export.
- Playlist filtering by name, online state, favorites, groups, and named stream-link formats, with copy, download, and QR-code actions.
- Search and bulk-add flows backed by the configured AceStream engine.
- Optional API-token protection for API, playlist, and EPG endpoints.

## Deployment and Docker

The image is published in four flavors. The image flavor controls what is installed; runtime flags control what starts.

| Flavor | Release tag | Contents |
|---|---|---|
| Full | `latest` or `v2.0.0` | Scraper, web app, AceStream engine, Acexy |
| Scraper + engine | `scraper-acestream` | Scraper, web app, AceStream engine |
| Scraper + Acexy | `scraper-acexy` | Scraper, web app, Acexy; use an external engine |
| Scraper only | `scraper` | Scraper and web app; optional services are external |

Use the [interactive Docker command builder](https://pipepito.github.io/acestream-scraper/) to select the platform, flavor, ports, volumes, and optional services and generate a ready-to-copy command or Compose file.

Platform support:

| Platform | AceStream engine | IPFS | ZeroNet | WARP |
|---|---|---|---|---|
| `linux/amd64` | Native 3.2.11, stable | Bundled, opt-in | Bundled, opt-in | Bundled, opt-in |
| `linux/arm64` | Android 3.2.17, stable | Bundled, opt-in | External | Bundled, opt-in |
| `linux/arm/v7` | Android 3.1.80, experimental | External | External | Not available |

Acexy-bearing flavors now build and run the real upstream Acexy 0.2.2 proxy. The full and engine flavors persist ARM engine state under `/var/lib/acestream`; mount a volume there when enabling the engine.

## Architecture and API

- `backend/` is the canonical FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, and APScheduler application.
- `frontend/` is the canonical React 18, TypeScript, Vite, Material UI, and React Query application.
- Current APIs live under `/api/v1`; interactive OpenAPI documentation is served at `/docs`.
- The player-friendly M3U endpoint is `/playlists/m3u`. Compatibility aliases remain for the established v1 playlist and XMLTV URLs so configured players do not silently receive the SPA.
- Requests receive an `X-Correlation-ID`, and API failures use a consistent error envelope.
- The frontend OpenAPI types are generated and checked for drift in CI.

## Reliability and security

- APScheduler owns scraping, EPG refresh/retention, channel status, stale-channel cleanup, and activity-log cleanup. The UI reports real scheduler state.
- SQLite hot paths have dedicated indexes and set-based bulk updates.
- Application logs rotate instead of growing without bound.
- Container health checks cover the API and any enabled in-container engine/Acexy services.
- The container entrypoint supervises AceStream and Acexy and fails on persistent crash loops so the container runtime can restart it.
- `API_TOKEN` can protect `/api/v1`, playlist, and EPG routes. `/api/v1/health` remains public for health probes.
- Outbound scrape and EPG URLs reject the cloud metadata endpoint. Set `ALLOW_PRIVATE_SCRAPE_TARGETS=false` to also reject private, loopback, and link-local targets except the configured ZeroNet service.
- Reverse-proxy examples for TLS and external authentication are documented in `docs/ops/reverse-proxy.md`.

## Upgrade from v1

1. Stop the v1 container and keep its config volume intact.
2. From a v2 checkout, run `bash scripts/ops/preflight_v2_deploy.sh`. It creates a timestamped backup under `config/backups/` and reports whether migration is safe.
3. Generate the new Docker configuration with the [command builder](https://pipepito.github.io/acestream-scraper/) or update your existing Compose file for the selected v2 flavor.
4. Prefer the canonical environment names listed below. The legacy names are accepted for this release only.
5. Start v2 with the same `/app/config` data volume.
6. Open the Overview and verify `/api/v1/health`, service status, inventory totals, and background migration progress.
7. Open Settings and confirm the engine URL and default stream-link format, then test the generated playlist from a player.

On first boot, v2 provisions its schema and migrates URLs, EPG sources, TV/EPG/AceStream channels, matching rules, and settings before serving requests. Large EPG programme history is copied in resumable background batches so the UI becomes available promptly. The original v1 database is archived as `acestream.db.migrated`; migration progress is checkpointed in `acestream.db.migration.json`.

Legacy environment aliases available during the v2.0.0 transition:

| Legacy | Canonical |
|---|---|
| `SCRAPER_DB_URL` | `DATABASE_URL` |
| `LEGACY_DB_URL` | `LEGACY_DATABASE_URL` |
| `ZERONET_BASE_URL` | `ZERONET_URL` |
| `CORS_ALLOW_ORIGINS` | `CORS_ORIGINS` |
| `FRONTEND_STATIC_DIR` | `FRONTEND_BUILD_PATH` |
| `ACESTREAM_ENGINE_URL` | `ACE_ENGINE_URL` |

## Breaking changes

- The root Flask runtime and its entrypoints (`app/`, `wsgi.py`, `run_dev.py`, `manage.py`, and root migrations) have been removed. Run `backend/main.py` with Uvicorn.
- The API contract is versioned under `/api/v1` and is not a 1:1 copy of the v1 management API. Integrations should use `/docs` as the contract.
- The frontend build system is Vite. Use `npm start` for development and `npm run build:backend` to build the SPA served by FastAPI.
- The v1 setup wizard and `config/config.json` workflow are gone. Application settings live in the database and are managed from Settings/Scraper; container behavior uses environment variables.
- Optional services do not start merely because their binaries exist in the selected image. Set the corresponding `ENABLE_*` flags.
- The bundled ZeroNet data path is `/data/zeronet`, not `/app/ZeroNet/data`.

## Known limitations

- `linux/arm/v7` AceStream support is experimental and still requires validation on real ARMv7/AArch32 hardware.
- ARM AceStream has no WebRTC transport and may use pure-Python fallbacks for some accelerators.
- The Android engine requires a 4 KB kernel page size. On Raspberry Pi 5, use the 4 KB-page `kernel8.img`; the default 16 KB-page kernel cannot start it.
- WARP is unavailable on `linux/arm/v7` because Cloudflare does not publish a 32-bit ARM package; amd64 and arm64 are supported.
- The app remains open on trusted networks unless `API_TOKEN` or reverse-proxy authentication is configured.

## Documentation

- [Illustrated usage walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage)
- [Installation guide](https://github.com/Pipepito/acestream-scraper/wiki/Installation)
- [Docker guide](https://github.com/Pipepito/acestream-scraper/wiki/Docker)
- [Configuration reference](https://github.com/Pipepito/acestream-scraper/wiki/Configuration)
- [Release readiness and remaining operator checks](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/release/v2-release-readiness.md)

## Validation

The release PR is gated by Jenkins `PR Validation`, including backend contracts/parity/regression checks, frontend lint/typecheck/tests/build, legacy-path guards, Docker manifest and command-builder checks, and AceStream/Acexy runtime smoke. Release publishing remains a separate manual Jenkins action on `main`; merging this PR does not publish version tags or promote `latest` by itself.

## Acknowledgements

Thank you to the AceStream, Acexy, FastAPI, React, Material UI, SQLAlchemy, Kubo/IPFS, ZeroNet, and broader open-source communities that make this project possible.
