# Configuration Reference

This guide provides detailed information about configuring Acestream Scraper.

## Contents
- [Application Settings](#application-settings)
- [Environment Variables](#environment-variables)
- [Channel Status Checking](#channel-status-checking)
- [Port Mapping](#port-mapping)
- [Volumes](#volumes)
- [ZeroNet Configuration](#zeronet-configuration)
- [Running Behind a Reverse Proxy](#running-behind-a-reverse-proxy)
- [Security Considerations](#security-considerations)
- [Healthchecks](#healthchecks)

## Application Settings

Acestream Scraper is configured from the web interface (**Settings** and **Scraper** pages, stored in the database) and through the environment variables listed below. The v1 setup wizard and `config.json` file are kept in the next two sections for reference only.

### Setup Wizard

*Superseded (2026-08-28): the v1 first-run wizard no longer exists. In v2 these values are edited from the **Settings** page (base URL, Acestream Engine URL, rescrape interval) and the **Scraper** page (source URLs) and are stored in the database.* The original wizard steps were:

1. Configure Base URL format
2. Set Acestream Engine URL
3. Add source URLs to scrape
4. Set rescrape interval

### Manual Configuration

*Superseded (2026-08-28): v2 does not read `config/config.json`. Use the web interface or the `/api/v1/config/*` endpoints (`base_url`, `ace_engine_url`, `rescrape_interval`, ...); runtime options such as the database location are environment variables (see below).* The v1 file format, kept for reference:

```json
{
    "urls": [
        "https://example.com/url1",
        "https://example.com/url2"
    ],
    "base_url": "http://localhost:6878/ace/getstream?id=",
    "ace_engine_url": "http://localhost:6878",
    "rescrape_interval": 24
}
```

### Key Settings

- **urls**: Array of URLs to scrape for Acestream channels
- **base_url**: Base URL format for playlist generation. You can also store multiple *named* base URLs (Settings → Stream base URLs) with one marked as default; a pattern containing `{channel_id}` (and optionally `{pid}`) is filled in per entry, while a pattern without placeholders is used as a plain prefix. Playlist URLs accept `?base_url_id=<id>` to pick a named entry.
  - `acestream://` - For players with Acestream protocol support
  - `http://localhost:6878/ace/getstream?id=` - For local HTTP streaming
  - `http://server-ip:acexy_port/ace/getstream?id=` - For using built-in Acexy proxy
- **ace_engine_url**: URL of your Acestream Engine instance
- **rescrape_interval**: Hours between automatic rescans of URLs

## Environment Variables

### Core Application

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `FLASK_PORT` | Port the web app (uvicorn) listens on | `8000` | Name kept from v1 but still the real setting: `entrypoint.sh` passes it to `uvicorn --port` and `healthcheck.sh` probes `http://localhost:${FLASK_PORT}/api/v1/health`. Change it if port 8000 is in use |
| `FLASK_ENV` | *Superseded (2026-08-28)* — v1 Flask environment mode, not read by the v2 (FastAPI) runtime | – | For local debugging run `uvicorn main:app --reload` from `backend/` instead |
| `API_TOKEN` | Require a token on API and playlist routes | unset (open) | Sent as `Authorization: Bearer`, `X-Api-Token`, or `?token=` (for IPTV players); `/api/v1/health` stays public |
| `ALLOW_PRIVATE_SCRAPE_TARGETS` | Allow scrape/EPG URLs on private/LAN addresses | `true` | Set `false` to block loopback/private/link-local targets; the cloud metadata endpoint is always blocked |
| `ACESTREAM_STATUS_TIMEOUT` | Timeout (seconds) for the engine status probe | `10` | A timed-out probe retries once with a doubled timeout |
| `EPG_PROGRAM_RETENTION_HOURS` | How long finished EPG programs are kept | `24` | The hourly `epg_program_cleanup` job deletes programs that ended earlier than this, and a v1→v2 migration skips them (they are useless once aired — the EPG refresh keeps adding upcoming ones). `2` keeps only the last couple of hours; a negative value disables the purge. The XMLTV export's default `days_back=1` needs at least `24` |
| `SUPERVISED_RESTART_DELAY_SECONDS` | Delay before restarting a crashed engine/Acexy process | `5` | Supervision applies to in-container AceStream and Acexy |
| `SUPERVISED_FAST_EXIT_LIMIT` | Consecutive fast exits before giving up | `3` | With `SUPERVISED_FAST_EXIT_WINDOW` (default `10`s); a crash loop fails the container |

### Acestream Configuration

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENABLE_ACESTREAM_ENGINE` | Enable built-in Acestream Engine | Matches `ENABLE_ACEXY` | Set to `true` to run Acestream in the container |
| `ACESTREAM_HTTP_PORT` | Port for Acestream engine | `6878` | Internal Acestream Engine HTTP port |
| `ACESTREAM_HTTP_HOST` | Host for Acestream engine | Uses `ACEXY_HOST` | Address to access Acestream Engine |

### Acexy Configuration

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENABLE_ACEXY` | Enable Acexy proxy | `false` | Set to `true` to enable enhanced Acestream proxy |
| `ACEXY_LISTEN_ADDR` | Address for Acexy to listen on | `:8080` | Format is `[host]:port` or just `:port` |
| `ACEXY_HOST` | Hostname of Acestream Engine | `localhost` | Hostname or IP where Acestream Engine runs |
| `ACEXY_PORT` | Port of Acestream Engine | `6878` | Port where Acestream Engine is accessible |
| `ACEXY_NO_RESPONSE_TIMEOUT` | Timeout for Acestream responses | `15s` | Format: `15s`, `1m`, etc. |
| `ACEXY_BUFFER_SIZE` | Buffer size for data transfers | `5MiB` | Format: `5MiB`, `10MiB`, etc. |

### Why Both Acexy and Acestream Engine?

Acestream Scraper includes both Acexy and Acestream Engine for improved multi-client handling:

1. **Connection Management**: When multiple clients access the same stream, each needs a unique process ID (PID)
2. **Automatic PID Handling**: Acexy automatically adds the required `pid=id` parameter to stream requests
3. **Error Isolation**: With proper PID management, one client disconnecting won't affect others
4. **Simplified URLs**: End users don't need to worry about adding PID parameters manually
5. **Performance**: Acexy includes buffering mechanisms to improve streaming performance

Without Acexy, you'd need to manually append `&pid={unique_id}` to each stream URL to properly handle multiple connections. When a stream ends for one client, without this parameter, it might terminate the stream for all users. Acexy transparently manages these connections, making the system more robust for multi-user environments.

### ZeroNet and Other Settings

The amd64 images bundle a ZeroNet node (zeronet-conservancy v0.7.10) that is off by default; ARM images ship without it and use an external service instead. In both cases the scraper reaches the node over HTTP via `ZERONET_URL`. The v1 in-container `zeronet.conf` mechanism is gone — the node is configured through these variables:

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENABLE_ZERONET` | Start the bundled ZeroNet node | `false` | amd64 images only; fails with a clear error elsewhere |
| `ENABLE_TOR` | Run TOR for the bundled node | `false` | Only takes effect with `ENABLE_ZERONET=true`; the node auto-detects TOR over the control port |
| `ZERONET_URL` | Address the scraper fetches `zero://` sources through | `http://host.docker.internal:43110` in the checked-in compose example | With `ENABLE_ZERONET=true` and no explicit value it targets the embedded UI port automatically |
| `ZERONET_DATA_DIR` | Bundled node's state directory | `/data/zeronet` | Mount a volume there |
| `ZERONET_UI_PORT` | Bundled node's web UI port | `43110` | |
| `ZERONET_FILESERVER_PORT` | Bundled node's fileserver/peer port | `26552` | |
| `ZERONET_UI_HOST` | Extra Host headers the UI accepts | *(none)* | Space-separated hostnames; needed to browse the UI from another machine |
| `ZERONET_EXTRA_ARGS` | Extra zeronet-conservancy CLI flags | *(none)* | Passed through to the node verbatim |
| `TZ` | Timezone for the container | `Europe/Madrid` | Use any valid TZ identifier |

### IPFS Configuration

The image bundles the [Kubo](https://github.com/ipfs/kubo) IPFS daemon (amd64/arm64 — Kubo has no 32-bit ARM build) so `ipfs://` and `ipns://` sources can be scraped through its HTTP gateway:

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENABLE_IPFS` | Start the embedded Kubo daemon | `false` | Opt-in; fails with a clear error on `linux/arm/v7` images |
| `IPFS_GATEWAY_URL` | Gateway used to fetch `ipfs://`/`ipns://` sources | `http://127.0.0.1:8081` | Point at an external gateway to scrape IPFS without the embedded daemon |
| `IPFS_PATH` | IPFS repository location | `/data/ipfs` | Mount a volume there when the daemon is enabled |
| `IPFS_SWARM_PORT` | Swarm (P2P) port | `4001` | TCP and UDP (QUIC) |
| `IPFS_API_PORT` | RPC API / WebUI port | `5001` | Unauthenticated; binds to the container loopback by default |
| `IPFS_API_HOST` | RPC API bind address | `127.0.0.1` | Set `0.0.0.0` only if you need the WebUI, and publish it as `127.0.0.1:5001:5001` |
| `IPFS_GATEWAY_PORT` | HTTP gateway port | `8081` | `8080` is taken by Acexy in-container |
| `IPFS_PROFILE` | Kubo config profile applied at first init | *(none)* | e.g. `lowpower` for small devices, `server` for datacenter hosts |

### WARP Configuration

Cloudflare WARP provides enhanced privacy and secure connection options:

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `ENABLE_WARP` | Enable Cloudflare WARP | `false` | Requires `NET_ADMIN` and `SYS_ADMIN` capabilities |
| `WARP_ENABLE_NAT` | Enable NAT for WARP traffic | `true` | Allows routing traffic through WARP tunnel |
| `WARP_LICENSE_KEY` | WARP license key | - | Optional: For WARP+ or Team accounts |

### Docker Example with WARP Enabled

```bash
docker run -d \
  -p 8000:8000 \
  --cap-add NET_ADMIN \
  --cap-add SYS_ADMIN \
  -e ENABLE_WARP=true \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### Docker Compose Example with WARP Enabled

```yaml
version: '3.8'

services:
  acestream-scraper:
    image: pipepito/acestream-scraper:latest
    container_name: acestream-scraper
    cap_add:
      - NET_ADMIN
      - SYS_ADMIN
    environment:
      - TZ=Europe/Madrid
      - ENABLE_WARP=true
    ports:
      - "8000:8000"
    volumes:
      - ./data/config:/app/config
    restart: unless-stopped
```

## Channel Status Checking

The application verifies if channels are available:

1. Ensure you have Acestream Engine running (built-in if ENABLE_ACESTREAM_ENGINE=true)
2. Configure `ace_engine_url` to point to your Acestream Engine instance
3. Use the "Check Status" buttons in the UI to verify channel availability

### Status Tracking

- The application maintains history of status checks
- Status is color-coded in the interface (green = online, red = offline)
- Error messages are displayed when a channel cannot be accessed

## Port Mapping

When using Docker, map these ports as needed:

| Port | Service | Notes |
|------|---------|-------|
| 8000 | Main web interface | Configurable via `FLASK_PORT` |
| 8080 | Acexy web interface | Only if Acexy is enabled |
| 6878 | Acestream HTTP API | Configurable via `ACESTREAM_HTTP_PORT` |
| 8621 | Acestream P2P port | For Acestream peer connections |
| 43110 | ZeroNet web interface | Only if `ENABLE_ZERONET=true` (or published by the optional `zeronet` sidecar) |
| 26552 | ZeroNet fileserver/peer port | Only if `ENABLE_ZERONET=true`; publishing it improves peer connectivity |
| 4001 | IPFS swarm port (TCP and UDP) | Only if `ENABLE_IPFS=true`; improves peer connectivity |
| 8081 | IPFS HTTP gateway | Only if `ENABLE_IPFS=true` and you want to browse IPFS through the node |
| 5001 | IPFS RPC API / WebUI | Unauthenticated — publish only as `127.0.0.1:5001:5001` if needed |

## Volumes

When using Docker, mount these volumes:

| Container Path | Purpose | Notes |
|----------------|---------|-------|
| `/app/config` | Configuration and data | Contains the database (`scraper.db`; a v1 `acestream.db` found here is migrated on first start — channels and settings before the dashboard comes up, EPG programs in the background afterwards; see [Installation](Installation.md#migrating-from-v1)) |
| `/var/lib/acestream` | AceStream engine state and cache | Only used when `ENABLE_ACESTREAM_ENGINE=true` (ARM Android engine) |
| `/data/ipfs` | IPFS repository (identity, config, blockstore) | Only required if `ENABLE_IPFS=true` |
| `/data/zeronet` | Bundled ZeroNet node's state (sites, keys, content) | Only required if `ENABLE_ZERONET=true` |

The v1 `/app/ZeroNet/data` path is gone — the bundled node keeps its state under `/data/zeronet` now (and the compose sidecar example keeps its own data in `./zeronet_data`).

Example mount:
```bash
docker run -v "${PWD}/config:/app/config" -v "${PWD}/ipfs_data:/data/ipfs" -v "${PWD}/zeronet_app_data:/data/zeronet" ...
```

## ZeroNet Configuration

The v1 `zeronet.conf` file is gone; in v2 you either enable the bundled node or point at an external one:

**Bundled node (amd64 images):**

1. Set `ENABLE_ZERONET=true` (and optionally `ENABLE_TOR=true`), mount `/data/zeronet`, and publish `43110`/`26552` if you want the UI or better peer connectivity.
2. Leave `ZERONET_URL` unset — the scraper targets the embedded node automatically.
3. Tune the node with the `ZERONET_*` variables above (`ZERONET_UI_PORT`, `ZERONET_UI_HOST`, `ZERONET_EXTRA_ARGS`, ...).

**External service (any platform):**

1. Run a ZeroNet service somewhere the container can reach — the checked-in `docker-compose.yml` ships an optional amd64 sidecar (`docker compose --profile zeronet up -d`), or use any existing ZeroNet install.
2. Point `ZERONET_URL` at it (the compose default is `http://host.docker.internal:43110`). TOR and the node's own settings are configured on that external service.

Either way, add your ZeroNet sources in the Scraper page with the **ZeroNet** URL type (`zero://...` URLs are also auto-detected).

## Running Behind a Reverse Proxy

The application includes proper headers handling for running behind a reverse proxy:

- Automatic handling of SSL/TLS termination
- Correct handling of X-Forwarded-Proto and X-Forwarded-Host headers
- Works with nginx, Apache, Traefik or other reverse proxies

### Nginx Example

```nginx
server {
    listen 80;
    server_name acestream.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Security Considerations

- Don't publish the AceStream engine API (`6878`), the Acexy proxy (`8080`) or the IPFS RPC API (`5001`) beyond trusted networks — none of them authenticate callers
- If you expose the web interface beyond your LAN, do it through a reverse proxy with TLS and authentication (see [Reverse Proxy / HTTPS](https://github.com/Pipepito/acestream-scraper/blob/main/docs/ops/reverse-proxy.md))
- Consider using a reverse proxy with SSL/TLS for secure access
- Be aware of copyright and legal considerations when sharing playlists

## Healthchecks

The container includes comprehensive health checks:

- Main application health check at `/health` endpoint
- Acexy health check (if enabled)
- Acestream Engine health check (if enabled)
- Automatic monitoring of internal services
- Graceful handling of service dependencies

### Docker Health Check

The Docker container is configured with a health check that verifies all services are running correctly:

```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

You can check the health status with: `docker inspect --format='{{.State.Health.Status}}' acestream-scraper
