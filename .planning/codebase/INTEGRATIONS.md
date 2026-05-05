# External Integrations

**Analysis Date:** 2026-02-27

## APIs & External Services

**Streaming/Network Services:**
- Acestream Engine - channel status and streaming backend integration
- Client: HTTP requests via `requests` in `backend/app/services/acestream_status_service.py`
  - Auth: none detected; network reachability and runtime env vars drive access
  - Endpoints used: `/server/api?api_version=3&method=get_status`, `/server/api?api_version=3&method=get_network_connection_status`
- Acexy Proxy - proxy/status integration for Acestream bridge
  - Client: health checks and operational scripts in `healthcheck.sh` and `entrypoint.sh`
  - Auth: none detected
  - Endpoint used: `http://localhost:8080/ace/status`
- Cloudflare WARP - connectivity/privacy routing integration
- Client: CLI invocation (`warp-cli`) in `backend/app/services/warp_service.py`
  - Additional verification: Cloudflare trace endpoint `https://www.cloudflare.com/cdn-cgi/trace/` via `httpx`
  - Auth: optional license registration endpoint in app (`/api/v1/warp/license`)
- ZeroNet - scraping source host/service
- Client: HTTP scraping via `aiohttp` in `backend/app/scrapers/zeronet.py`
- Default URL source: `ZERONET_URL` in `backend/app/config/settings.py`

**External Content Sources:**
- Arbitrary user-configured playlist/scrape URLs are fetched by scrapers
- Regular HTTP scraper: `backend/app/scrapers/http.py`
- ZeroNet scraper: `backend/app/scrapers/zeronet.py`
- URL inventory stored in DB (`scraped_urls` table via `backend/app/models/models.py`)

## Data Storage

**Databases:**
- SQLite (primary canonical runtime)
  - Connection: `DATABASE_URL` in `backend/app/config/settings.py`
  - Client: SQLAlchemy in `backend/app/config/database.py`
  - Migrations: Alembic-style migration files in `backend/migrations/`
- SQLite (legacy root stack)
  - Connection path implied by root config/scripts (`config/acestream.db`)
  - Migration tooling in root `migrations/` and `manage.py`

**File Storage:**
- Local filesystem config/log/state
  - Config paths in `config/` and Docker-mounted volumes in `docker-compose.yml`
  - Generated files: `generated_epg.xml`, `list.m3u`, logs in `/app/logs` via `entrypoint.sh`

**Caching:**
- No dedicated cache service (Redis/Memcached not detected)

## Authentication & Identity

**Auth Provider:**
- Not detected for end-user API auth (no OAuth/JWT middleware in active routes)

**OAuth Integrations:**
- Not detected

## Monitoring & Observability

**Error Tracking:**
- No third-party error tracking service detected (no Sentry/NewRelic SDK usage)

**Analytics:**
- Not detected

**Logs:**
- Python logging configured in `backend/app/utils/logging.py`
- Container/runtime logs managed by shell scripts in `entrypoint.sh`
- CI logs from GitHub Actions workflows in `.github/workflows/`

## CI/CD & Deployment

**Hosting/Packaging:**
- Docker Hub push configured in `.github/workflows/release.yml`
  - Image tags: `pipepito/acestream-scraper:latest` and version tags from `version.txt`

**CI Pipeline:**
- GitHub Actions pipelines for PR checks and release in `.github/workflows/pull_request.yml` and `.github/workflows/release.yml`
- Lint/test steps use Python 3.9 and run `flake8` + `pytest tests/` on root test suite

## Environment Configuration

**Development:**
- Critical vars include DB path and integration toggles (`DATABASE_URL`, `ZERONET_URL`, `ENABLE_WARP`, `ENABLE_ACEXY`, `ENABLE_ACESTREAM_ENGINE`)
- Secrets strategy is env var based; no dedicated secret manager config detected in repo

**Staging:**
- No explicit staging environment config found in repository workflows

**Production:**
- Production deployment assumed via Docker runtime with env vars and mounted config volumes
- Privileged capabilities required when WARP enabled (`NET_ADMIN`, `SYS_ADMIN`) in `docker-compose.yml`

## Webhooks & Callbacks

**Incoming:**
- Not detected

**Outgoing:**
- Not implemented as webhook callbacks; outbound interactions are pull/command based (HTTP scrape calls, engine status checks, warp-cli)

---

*Integration audit: 2026-02-27*
*Update when adding/removing external services*
