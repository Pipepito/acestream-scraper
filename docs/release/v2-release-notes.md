# Acestream Scraper v2.0.0

Acestream Scraper v2 replaces the legacy Flask application with one supported FastAPI backend and React web interface. It brings Live TV and browser playback, remote-player and media-server integrations, safer database migration and recovery, configurable Docker flavors, ARM support, verified stream checks, and persistent scheduled-job results.

This is a major release. Read **Upgrade from v1** and **Breaking changes** before replacing an existing container.

## User-facing highlights

- A responsive interface with light/dark themes, keyboard access, reduced-motion support, and navigation grouped into Watch, Manage, and System. Live TV, Integrations, and WARP have dedicated entries; phone layouts keep source, channel, player, and job controls reachable.
- A single Overview for engine/service health, inventory totals, scheduled jobs, recent outcomes, and next-run times.
- Clear source management for regular HTTP, ZeroNet, IPFS/IPNS, and pages containing bare 40-character AceStream IDs.
- Stream filters, status checks, CSV export, playlist visibility, and assignment to user-facing TV channels.
- TV channels can group primary/backup streams, carry guide metadata, show now/next schedules, and be marked as favorites.
- A five-part EPG workflow for XMLTV sources, guide channels, automatic matching, matching rules, and filtered XMLTV export.
- Playlist filtering by name, online state, favorites, groups, and named stream-link formats, with copy, download, and QR-code actions.
- Search and bulk-add flows backed by the configured AceStream engine.
- Optional API-token protection for API, playlist, and EPG endpoints.

## Watch, play, and integrate

- **Live TV:** browse TV channels and online unassigned streams alongside an embedded player, search by name/category/number, filter favorites, and open a channel by URL. Filtering, resizing the player, and collapsing navigation preserve playback. The schedule shows current/upcoming programmes and day tabs in the viewing device's timezone.
- **Browser playback:** bundled FFmpeg packages engine output as HLS, copies the video, and converts audio to AAC. hls.js and native browser HLS support power playback without an AceStream plugin on the viewing device. Viewers of the same channel/audio selection share a session; leaving releases their viewer and unused sessions are cleaned up.
- **Playback controls and recovery:** choose a channel's alternative stream or audio track, inspect startup/peer/download status, and retry failed sessions. Fixes release engine/FFmpeg resources after failed launches, handle temporary status-request failures, recover from HLS errors, and distinguish buffering, paused, playing, and failed states.
- **Direct or Acexy routing:** Settings → Playback selects direct engine access or Acexy MPEG-TS delivery. Browser, tuner, and remote-player relay paths follow the selection. Existing sessions retain their route and ownership until teardown; changing settings cannot stop another proxy client's stream.
- **Remote players:** save, discover, test, and control VLC and Kodi players from Integrations. VLC Android supports its remote-access pairing flow. Send a stream directly to a saved player without starting browser playback, with supported transport/volume controls and clear connection/authentication errors. IPv6 hosts and bounded LAN discovery are supported; credentials stay tied to their saved target.
- **Media servers:** connect Jellyfin and Plex, test access, refresh/synchronize configuration, and inspect status. A software HDHomeRun-compatible tuner exposes discovery, lineup, guide, playlists, and MPEG-TS relay routes. Stable device IDs, channel numbering, tuner-slot limits, startup fallback streams, and Plex DVR matching keep integrations consistent.
- **Relay reliability:** preferred/backup stream ordering is shared across playlists and tuner output. Playback-time checks refresh fallback choices, startup failures can try another source, and transport errors/timeouts clean up resources. Stream changes after delivery are conservative; automatic midstream failover remains an explicit experimental option.

See [Web Player](https://github.com/Pipepito/acestream-scraper/wiki/Web-Player), [Remote Players](https://github.com/Pipepito/acestream-scraper/wiki/Remote-Players), and [Media Servers](https://github.com/Pipepito/acestream-scraper/wiki/Media-Servers).

## Catalogue, scraping, EPG, and playlists

- **TV inventory:** catalogue-wide filters apply before sorting/pagination. Search, category, status, and favorites stay visible; advanced filters show an active count. Dedicated favorite/number controls work on tables and phone cards. Reorder the complete catalogue with drag handles or keyboard controls, preview consecutive numbers, and save atomically; stale inventories are rejected and Cancel preserves saved numbers.
- **Stream assignment:** reviewed automatic matching suggests TV-channel assignments; primary/backup ordering, unassigned filters, and detail views make relationships easier to manage. Copied links and remote-player actions follow the selected stream.
- **Source handling:** HTTP, ZeroNet, IPFS/IPNS, relative gateway links, browser-style IPNS URLs, and optional bare AceStream IDs are supported. Fixes preserve hidden/disabled state, tolerate old NULL bare-ID settings and newly discovered streams, and prevent numeric engine channel names from failing an entire search.
- **EPG:** source refresh, channel mapping, matching rules, bulk matching, now/next information, and filtered XMLTV exports share one workflow. Broken guide links are repaired, deletion cleans up dependent data, and retention removes expired programmes. Imports avoid unnecessary SQLite write locks and normalize times to UTC.
- **Playlists and exports:** named link formats support custom base URLs, masks, PID, and AppID. The shared format editor opens inline on Playlist while retaining playlist choices. Absolute public URLs, API-token propagation, favorites/groups/online filters, curated playlists, QR codes, and complete catalogue CSV exports are supported. Established v1 playlist/XMLTV URLs remain compatible.
- **Settings organization:** Playback, Automation, Stream links, and Access have deep links. Public address and player/media-server connections live in Integrations. Saved intervals take effect at startup and when changed.

## Stream verification and scheduled work

- **Verified signal:** engine catalogue lookup is separate from actual media delivery. A stream is reported online only after identified audio/video packets; importing an ID does not establish signal. Timeouts and engine errors remain distinct from an explicit missing ID or offline result.
- **Optional engines:** scraper-only installations can start without an engine URL. Configure an external playback engine when needed, or a separate external checker under Settings → Automation. With no usable engine, checks skip without overwriting previous results.
- **Dedicated checker:** engine-bearing images can run a second, independently supervised engine with `ENABLE_ACESTREAM_CHECK_ENGINE=true`; `ACE_CHECK_ENGINE_URL` selects an external checker. A configured checker never falls back to the playback engine when unavailable, and checker outage does not fail whole-container health.
- **Playback ownership:** direct clients coordinate starts and final stops through shared source ownership. Checks are serialized and playback probes take priority; active app-owned streams are protected from destructive engine stop calls. Acexy owns its sessions independently.
- **Persistent job results:** Overview retains each scheduled job's latest start/outcome across restarts and labels interrupted runs. Manual actions have separate summaries. Stream checks report checked, online, offline, skipped, and errors without counting exceptions as offline.
- **Scheduling and contention:** optional start times and timezone complement existing intervals. Recurring maintenance and scheduler “run now” requests share a FIFO queue; due jobs show Waiting and repeated requests do not duplicate running/waiting jobs. SQLite writes retry lock failures, failed sessions roll back before reuse, and blocking work runs off the async event loop.

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
| `linux/arm64` | Android 3.2.17, stable | Bundled, opt-in | Bundled, opt-in | Bundled, opt-in |
| `linux/arm/v7` | Android 3.2.17, experimental | External | External | Not available |

Both ARM engine entries use their matching platform variant from the same
digest-pinned [`jopsis/acestream:v3.2.17-fix`](https://hub.docker.com/r/jopsis/acestream)
multi-platform image. ARMv7 is build/layout-verified but remains experimental
until the engine is exercised on real 32-bit ARM hardware.

Acexy-bearing flavors now build and run the real upstream Acexy 0.2.2 proxy. Every flavor includes a static FFmpeg 8.1.2 build for its platform. The full and engine flavors persist engine state under `/var/lib/acestream`; mount a volume there when enabling the engine.

Additional deployment changes:

- Bundled ZeroNet on amd64/arm64 uses a pinned zeronet-conservancy node with DHT discovery, seeded trackers, and an isolated Python runtime. Startup preserves downloaded sites and `.node/` private state; legacy configuration is copied only when absent. A narrow manifest-path fix restores root downloads without bypassing signature verification.
- Kubo provides an opt-in local IPFS gateway on amd64/arm64; external gateways remain supported on all platforms. ZeroNet and Tor are also opt-in.
- WARP is supervised and controllable from its own page, with registration, tunnel, exit-location, and status details. ARM64 support and legacy CLI compatibility are repaired.
- The command builder understands platform/flavor capabilities, optional engine/checker services, persistent engine/player storage, and external services. An optional, off-by-default [xdp.es DNS](https://xdp.es/about) choice configures its Standard resolver.
- First publication supplies `v2.0.0`, four `v2.0.0-<flavor>` tags, and four floating flavor tags. `latest` moves only in a separate promotion after canary validation; pin a version or digest for a controlled upgrade. Validated `develop` builds publish only the development channel.

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
- Application and per-service logs rotate with bounded retention. Overview downloads a diagnostics ZIP even when database startup fails, with normal API-token enforcement and credential masking. Docker console output carries service tags; low-level WARP noise stays in its own log while issues remain visible.
- Container health checks cover the API and any enabled in-container engine/Acexy services.
- AceStream remains supervised in the foreground and retries every exit until explicitly stopped from the UI. Start/Restart resumes recovery; intentional Stop is accepted by health checks. The dedicated checker has independent controls/logs. Other sidecars retain their bounded fast-exit recovery behavior.
- `API_TOKEN` can protect `/api/v1`, playlist, and EPG routes. `/api/v1/health` remains public for health probes.
- Outbound scrape and EPG URLs reject the cloud metadata endpoint. Set `ALLOW_PRIVATE_SCRAPE_TARGETS=false` to also reject private, loopback, and link-local targets except the configured ZeroNet service.
- LAN-only target validation protects remote-player/media-server connections. Public URL validation, proxy-header trust, bounded scans, and token masking in access logs strengthen integration boundaries.
- Tuner routes use a network allowlist rather than API-token authentication because media-server clients cannot send the application's token. Configure allowed networks and proxy trust before exposing them.
- Reverse-proxy examples for TLS and external authentication are documented in [the proxy guide](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/reverse-proxy.md).

## Upgrade from v1

1. Stop the v1 container and keep its config volume intact.
2. From a v2 checkout, run `bash scripts/ops/preflight_v2_deploy.sh`. It creates a timestamped backup under `config/backups/` and reports whether migration is safe.
3. Generate the new Docker configuration with the [command builder](https://pipepito.github.io/acestream-scraper/) or update your existing Compose file for the selected v2 flavor.
4. Prefer the canonical environment names listed below. The legacy names are accepted for this release only.
5. Start v2 with the same `/app/config` data volume.
6. Open the Overview and verify `/api/v1/health`, service status, inventory totals, and background migration progress.
7. Open Settings and confirm the engine URL and default stream-link format, then test the generated playlist from a player.

On first boot, v2 provisions its schema and migrates URLs, EPG sources, TV/EPG/AceStream channels, matching rules, and settings before enabling normal application APIs; a startup/progress screen is already available. Large EPG programme history is copied in resumable background batches so the UI becomes available promptly. The original v1 database is archived as `acestream.db.migrated`; migration progress is checkpointed in `acestream.db.migration.json`.

### Database upgrades on every boot

Every start brings `config/scraper.db` to the Alembic head, not just fresh databases: an existing installation receives new revisions, and a database with tables but no recorded revision (what the pre-2026-08-29 migrator left behind) is stamped first.

- **Backup.** When the recorded revision differs from the head, startup first copies the SQLite file to `config/backups/<UTC stamp>-pre-upgrade-<from>-<to>/scraper.db` and logs one `Upgrading v2 database schema` line.
- **How many.** One copy per `<from>-<to>` pair. A boot that finds an existing copy for the same pair reuses it, so a container Docker keeps restarting against a failing upgrade does not fill the config volume.
- **Pruning.** None. Delete the folders you no longer want.
- **Failure stops normal startup.** The startup screen and diagnostics remain available; there is no automatic empty-database or `create_all` fallback. Fix disk/permission problems and retry, or explicitly choose a recovery action.
- **Rolling back needs the backup.** An older image started against a database stamped with a revision it does not ship aborts with an Alembic "Can't locate revision" error. Restore the matching folder from `config/backups/` before running the older image.

### Startup diagnostics and recovery

Startup reports milestones and resumable programme-import counts. Interrupted background imports retain checkpoints; duplicates, orphaned rows, and expired programmes are accounted for separately.

If database startup fails, **Recover readable data** builds a replacement schema and prioritizes scraper/EPG sources, then other readable settings and inventory. Programme listings can be refreshed afterward. **Start fresh** is a separate confirmed choice. Both preserve original databases, SQLite sidecars, and checkpoints before replacement; a recovery marker prevents old imports from writing into rebuilt channel IDs. Recovery is best effort, not SQLite page repair. See [startup recovery](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/startup-recovery.md).

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
- New scraper-only installs no longer assume a local playback engine; existing saved endpoints are retained.
- Run catalogue-wide checks through `/api/v1/background-tasks/channel_status/run`; the former `/channels/check_status_all` and `/acestream-channels/check_status_all` management routes are removed.
- Tuner access and reverse-proxy authentication require separate configuration from the main API. Remote-player credentials are stored in the application database; protect its volume and backups.

## Known limitations

- `linux/arm/v7` AceStream support is experimental and still requires validation on real ARMv7/AArch32 hardware.
- ARM AceStream has no WebRTC transport and may use pure-Python fallbacks for some accelerators.
- The Android engine requires a 4 KB kernel page size. On Raspberry Pi 5, use the 4 KB-page `kernel8.img`; the default 16 KB-page kernel cannot start it.
- WARP is unavailable on `linux/arm/v7` because Cloudflare does not publish a 32-bit ARM package; amd64 and arm64 are supported.
- Browser playback copies video rather than transcoding it. Unsupported video codecs need an external player; HLS introduces a delay behind live broadcast.
- ARM64 engine startup has smoke evidence, but this does not establish successful playback on every device. Real-hardware playback validation remains necessary; ARMv7 stays experimental.
- The ZeroNet root-manifest fix does not repair every upstream included/user-manifest or publishing issue. See [the compatibility notes](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/zeronet-verification.md).
- Direct engine clients outside the app's ownership registry cannot receive the same playback/check isolation guarantees.
- The app remains open on trusted networks unless `API_TOKEN` or reverse-proxy authentication is configured.

## Documentation

- [Illustrated usage walkthrough](https://github.com/Pipepito/acestream-scraper/wiki/Usage)
- [Installation guide](https://github.com/Pipepito/acestream-scraper/wiki/Installation)
- [Docker guide](https://github.com/Pipepito/acestream-scraper/wiki/Docker)
- [Configuration reference](https://github.com/Pipepito/acestream-scraper/wiki/Configuration)
- [Release readiness and remaining operator checks](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/release/v2-release-readiness.md)

## Validation

The release PR is gated by Jenkins `PR Validation`: full non-Docker backend/frontend suites, contracts, generated-client drift, lint/typecheck/build, legacy-path checks, and architecture/runtime contracts. Fork code runs in isolated credential-free, network-disabled containers. Trusted `develop` validation additionally builds images and exercises the engine/Acexy runtime and ARM installer layouts before channel publication. Playwright desktop/mobile and live-stack journeys provide additional coverage.

Release publishing remains a separate manual Jenkins action on `main`. It reruns preflight and publish-time smokes; promotion retags the canaried manifest without rebuilding it. Successful promotion updates the production label on the documentation site. Merging alone does not publish images, create a Git tag/GitHub release, or publish these notes. Build/layout checks do not replace ARM hardware validation; consult the release-readiness checklist for outstanding operator evidence.

## Acknowledgements and upstream projects

Thank you to the maintainers, contributors, testers, and issue reporters whose work makes this release possible. The following projects provide bundled components, application dependencies, or integration interfaces; the historical proxy credit is retained explicitly.

### Contributors to the v2 integration branch

A special thank-you to everyone who submitted pull requests that are now merged into `develop`, including its former `ai-coding-documentation` name:

- **[@scarcraft1](https://github.com/scarcraft1)** — fixed scraping of newly discovered channels ([#165](https://github.com/Pipepito/acestream-scraper/pull/165)), ZeroNet startup arguments ([#166](https://github.com/Pipepito/acestream-scraper/pull/166)) and bootstrap trackers ([#167](https://github.com/Pipepito/acestream-scraper/pull/167)), and numeric channel names breaking search ([#168](https://github.com/Pipepito/acestream-scraper/pull/168)). Also brought bundled ZeroNet to ARM64 with a DHT-capable pin ([#191](https://github.com/Pipepito/acestream-scraper/pull/191)) and repaired root-manifest path verification ([#193](https://github.com/Pipepito/acestream-scraper/pull/193)). Thank you for making discovery and scraping more reliable across platforms.
- **[@Meikkun](https://github.com/Meikkun)** — updated the AceStream engine version from 3.2.3 to 3.2.11 in [#131](https://github.com/Pipepito/acestream-scraper/pull/131), merged into the integration branch before its rename to `develop`. Thank you for helping bring the engine forward.
- **[@Pipepito](https://github.com/Pipepito)** — project maintenance and integration, including the Docker command builder ([#163](https://github.com/Pipepito/acestream-scraper/pull/163)), IPFS/ZeroNet integration ([#164](https://github.com/Pipepito/acestream-scraper/pull/164)), web player and media integrations ([#171](https://github.com/Pipepito/acestream-scraper/pull/171)), and the subsequent merged Live TV, playback, diagnostics, scheduler, and CI improvements.

Thanks also to everyone who tested development images, reported bugs, and shared reproduction details.

### Streaming, networking, and bundled components

| Project | Contribution to this release |
|---|---|
| [AceStream](https://acestream.org/) | Engine and middleware APIs underlying catalogue lookup and stream delivery; native Linux engine 3.2.11. |
| [jopsis/docker-acestream-aceserve](https://github.com/jopsis/docker-acestream-aceserve) | Community ARM engine distribution: matching ARM64/ARMv7 variants from digest-pinned `jopsis/acestream:v3.2.17-fix`. |
| [Javinator9889/acexy](https://github.com/Javinator9889/acexy) | AceStream multiplexing proxy; version 0.2.2 source is vendored and built for Acexy-bearing flavors. |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | Media inspection and HLS processing; pinned 8.1.2 source is built into static per-platform binaries. |
| [video-dev/hls.js](https://github.com/video-dev/hls.js) | HLS playback in supported browsers. |
| [ipfs/kubo](https://github.com/ipfs/kubo) | Bundled IPFS daemon/gateway on amd64 and arm64; pinned v0.43.0. |
| [zeronet-conservancy/zeronet-conservancy](https://github.com/zeronet-conservancy/zeronet-conservancy) | Bundled ZeroNet node pinned at `81d3ffc6bdfb600e9a1d4a091f1ceb131d92c4f1`, with the local manifest-path compatibility patch described above. |
| [Cloudflare WARP](https://developers.cloudflare.com/warp-client/) and [Tor](https://www.torproject.org/) | Optional networking services. |
| [xdp.es](https://xdp.es/about) | Optional Standard DNS service exposed by the Docker command builder. |
| [martinbjeldbak/acestream-http-proxy](https://github.com/martinbjeldbak/acestream-http-proxy) | Historical AceStream HTTP-proxy credit carried forward from this project's wiki; the v2 bundled proxy is Acexy. |

### Application libraries

- **API and persistence:** [FastAPI](https://github.com/fastapi/fastapi), [Starlette](https://github.com/Kludex/starlette), [Uvicorn](https://github.com/encode/uvicorn), [Pydantic](https://github.com/pydantic/pydantic), [pydantic-settings](https://github.com/pydantic/pydantic-settings), [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy), [Alembic](https://github.com/sqlalchemy/alembic), and [APScheduler](https://github.com/agronholm/apscheduler).
- **Fetching and parsing:** [aiohttp](https://github.com/aio-libs/aiohttp), [HTTPX](https://github.com/encode/httpx), [Requests](https://github.com/psf/requests), [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/), [lxml](https://github.com/lxml/lxml), [python-multipart](https://github.com/Kludex/python-multipart), and [python-dotenv](https://github.com/theskumar/python-dotenv).
- **Web interface:** [React](https://github.com/facebook/react), [Material UI](https://github.com/mui/material-ui) and [MUI X](https://github.com/mui/mui-x), [Emotion](https://github.com/emotion-js/emotion), [TanStack Query](https://github.com/TanStack/query), [React Router](https://github.com/remix-run/react-router), [Axios](https://github.com/axios/axios), [date-fns](https://github.com/date-fns/date-fns), and [qrcode.react](https://github.com/zpao/qrcode.react).
- **Build and verification:** [TypeScript](https://github.com/microsoft/TypeScript), [Vite](https://github.com/vitejs/vite), [openapi-typescript](https://github.com/openapi-ts/openapi-typescript), [ESLint](https://github.com/eslint/eslint), [Jest](https://github.com/jestjs/jest), [Testing Library](https://github.com/testing-library/react-testing-library), [pytest](https://github.com/pytest-dev/pytest), [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio), [Playwright](https://github.com/microsoft/playwright), [Jenkins](https://github.com/jenkinsci/jenkins), [Docker Buildx](https://github.com/docker/buildx), [BuildKit](https://github.com/moby/buildkit), and [tonistiigi/binfmt](https://github.com/tonistiigi/binfmt).

### Integration ecosystems

Thanks also to [VideoLAN VLC](https://code.videolan.org/videolan/vlc), [VLC Android](https://github.com/videolan/vlc-android), [Kodi](https://github.com/xbmc/xbmc), [Jellyfin](https://github.com/jellyfin/jellyfin), [Plex](https://www.plex.tv/), and [SiliconDust HDHomeRun](https://www.silicondust.com/) for the players, media servers, and interfaces this application works with. These are external integrations, not bundled media-server applications.

Component pins and source locations are recorded in `docker/manifests/`, installer scripts, and `docker/vendor/*/README.md`; application dependencies are listed in `backend/requirements.txt` and `frontend/package.json`/`package-lock.json`. Upstream projects retain their own licenses and notices. These acknowledgements are a project credit list, not a replacement for dependency license files or a complete transitive dependency inventory.
