# Installation Guide

This guide covers different methods for installing and setting up Acestream Scraper.

For the quickest v2 setup, open the [Docker command builder](https://pipepito.github.io/acestream-scraper/). It generates the correct `docker run` command or `docker-compose.yml` for your CPU, image flavor, optional services, ports, and volumes. The [project README](https://github.com/Pipepito/acestream-scraper#readme) provides the short release overview; this page explains each installation path in detail.

## Contents
- [Docker Compose Method (Recommended)](#docker-compose-method-recommended)
- [Docker Method](#docker-method)
- [Manual Installation](#manual-installation)

## Docker Compose Method (Recommended)

Docker Compose provides the easiest way to get started with Acestream Scraper.

### Prerequisites
- Docker and Docker Compose installed on your system
- Basic understanding of Docker (see [Docker Guide](Docker.md))

### Steps

1. **Create a docker-compose.yml file:**

   ```yaml
   services:
     acestream-scraper:
       image: pipepito/acestream-scraper:latest
       container_name: acestream-scraper
       environment:
         - TZ=Europe/Madrid
         - ENABLE_ACEXY=true
         - ENABLE_ACESTREAM_ENGINE=true
         - ENABLE_IPFS=false
         - ACESTREAM_HTTP_HOST=localhost
         - ACESTREAM_HTTP_PORT=6878
         - FLASK_PORT=8000
         - ZERONET_URL=http://host.docker.internal:43110
       ports:
         - "0.0.0.0:8000:8000"  # Web app (FastAPI/uvicorn; port set by FLASK_PORT)
         - "8080:8080"          # Acexy proxy
         - "8621:8621"          # Acestream P2P port
         - "8621:8621/udp"      # Acestream P2P port (UDP)
       volumes:
         - ./config:/app/config
       extra_hosts:
         - "host.docker.internal:host-gateway"
       restart: unless-stopped
   ```

   ZeroNet moved to opt-in in v2: the amd64 images bundle a node you enable with `ENABLE_ZERONET=true` (state under `/data/zeronet` — the v1 `/app/ZeroNet/data` volume is gone), or you point `ZERONET_URL` at an external service such as the optional `zeronet` sidecar profile in the repository's `docker-compose.yml` (the only mode available on ARM). IPFS scraping is built in as well: flip `ENABLE_IPFS=true` to run the embedded Kubo daemon (see [With the Embedded IPFS Daemon](#with-the-embedded-ipfs-daemon)).

2. **Start the service:**

   ```bash
   docker compose up -d
   ```

3. **Access the application:**
   
   Open your browser and navigate to `http://localhost:8000`
   
   Open **Settings** in the left navigation to set the stream base URL, Acestream Engine URL and rescrape interval, and **Scraper** to add the source URLs to scrape. (The v1 first-run wizard no longer exists — superseded 2026-08-28.)

## Docker Method

If you prefer using Docker without Docker Compose, follow these steps:

### Basic Installation

```bash
docker pull pipepito/acestream-scraper:latest
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

`latest` is the current release. To test the upcoming release instead, use the moving pre-release tag `pipepito/acestream-scraper:develop` (not for production); see the [Docker guide](Docker.md#pre-release-channel-develop) for the channel and flavor tags.

### With Acexy and Internal Acestream Engine

```bash
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=true \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With External Acestream Engine

```bash
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=false \
  -e ACEXY_HOST=192.168.1.100 \
  -e ACEXY_PORT=6878 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With the Embedded IPFS Daemon

Enables scraping of `ipfs://` / `ipns://` sources through the bundled Kubo node (amd64/arm64 images; on 32-bit ARM point `IPFS_GATEWAY_URL` at an external gateway instead):

```bash
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -p 4001:4001 \
  -p 4001:4001/udp \
  -e ENABLE_IPFS=true \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/ipfs_data:/data/ipfs" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With the Bundled ZeroNet Node (amd64)

The amd64 images ship a ZeroNet node that only starts when `ENABLE_ZERONET=true`; add `ENABLE_TOR=true` to run TOR alongside it (like v1):

```bash
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -p 43110:43110 \
  -p 26552:26552 \
  -e ENABLE_ZERONET=true \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_app_data:/data/zeronet" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

The scraper finds the embedded node automatically when `ZERONET_URL` is not set. Publishing `43110` is only needed to browse the ZeroNet UI yourself (set `ZERONET_UI_HOST` for access from other machines — the UI is unauthenticated, keep it on trusted networks).

### With an External ZeroNet Service

On ARM images (which ship without the bundled node), or whenever you prefer it, run ZeroNet as its own service — for example the optional `zeronet` profile in the repository's `docker-compose.yml` — and point the scraper at it:

```bash
docker run -d \
  -p 0.0.0.0:8000:8000 \
  -e ZERONET_URL=http://host.docker.internal:43110 \
  --add-host host.docker.internal:host-gateway \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

TOR and the rest of the ZeroNet node's settings are configured on that external service, not on the scraper container.

## Manual Installation

For advanced users who want to run the application directly on their system.

> **Superseded (2026-08-28):** the v1 steps that used to live here — a `venv` at the repository root, `pip install -r requirements.txt`, a `config/config.json` file and `python run_dev.py` / `python wsgi.py` — no longer apply. v2 is a FastAPI backend under `backend/` plus a React web interface under `frontend/`.

### Prerequisites
- Python 3.11 or higher
- Node.js 20 or higher with npm (only needed to build the web interface)
- Git

### Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/Pipepito/acestream-scraper.git
   cd acestream-scraper
   ```

2. **Set up the backend virtual environment:**

   ```bash
   python3 -m venv backend/venv
   source backend/venv/bin/activate  # On Windows use: backend\venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```

3. **Build the web interface** (the backend serves it from `backend/frontend_build/`):

   ```bash
   cd frontend
   npm ci
   npm run build:backend
   cd ..
   ```

4. **Configure (optional):**

   Runtime options are environment variables, not a `config.json` file. The defaults work out of the box; the most common overrides are:

   ```bash
   export DATABASE_URL="sqlite:///./config/scraper.db"   # v2 database, relative to the directory uvicorn runs from (backend/)
   export ACE_ENGINE_URL="http://localhost:6878"          # your Acestream Engine
   ```

   The stream base URL, rescrape interval and source URLs are edited in the web interface (**Settings** and **Scraper** pages) and stored in the database. An existing v1 database is migrated on first start when it is at `backend/config/acestream.db` (paths resolve relative to the `backend/` working directory) or when `LEGACY_DATABASE_URL` points at it, e.g. `export LEGACY_DATABASE_URL=sqlite:////absolute/path/to/config/acestream.db`. See [Migrating from v1](#migrating-from-v1) for what happens during that first start.

5. **Run the application:**

   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   For development add `--reload`. For a hot-reloading UI run `npm start` in `frontend/` (Vite on port 3000, proxying `/api` to port 8000) instead of rebuilding after every change.

6. **Access the application:**

   Open your browser and navigate to `http://localhost:8000`

## Migrating from v1

When the container (or `uvicorn`) starts and finds a v1 `acestream.db` in the config directory that is not yet archived, it migrates it automatically — no manual step is needed:

1. **Before the first request (seconds):** the v2 schema is created, and your scraped URLs, EPG sources, TV/EPG/AceStream channels, EPG string mappings and settings are copied. `acestream.db` is then renamed to `acestream.db.migrated` and a small `acestream.db.migration.json` file records what is still pending.
2. **In the background:** the EPG programs — usually by far the largest table — are copied by the `v1_epg_programs_migration` task while the dashboard is already reachable and the container reports healthy. Programs that already ended more than `EPG_PROGRAM_RETENTION_HOURS` (default 24) hours ago are not copied at all — a v1 database that accumulated months of listings shrinks to the current day plus upcoming programs. Watch its progress on the dashboard's **Background Tasks** card (`Progress: 12,000 / 300,000 · 4%`) or in the container log (`v1 EPG programs migration progress …`). The regular hourly EPG refresh keeps running; already-present programs are never duplicated.
3. **Restarts are safe:** the copy checkpoints after every batch and resumes where it stopped. Once it reports `done`, `acestream.db.migrated` is only kept as a backup and can be deleted together with `acestream.db.migration.json`.

If the archived `acestream.db.migrated` is removed before the copy finishes, the task logs an error and stops; the EPG refresh will re-download current programs from your EPG sources on its next run.

## Updating to a newer image

Pull the new image and recreate the container (`docker compose pull && docker compose up -d`). The app brings its own database up to date on the first start:

1. **The schema is upgraded in place.** If `config/scraper.db` was written by an older version, the new one applies the missing migrations while starting. Nothing to run by hand.
2. **A copy is taken first.** Before applying anything, the app copies the database to `config/backups/<date>-<time>-pre-upgrade-<from>-<to>/scraper.db` and logs `Upgrading v2 database schema … (backup: …)`. One copy is kept per upgrade step; if the container fails and restarts, the existing copy is reused instead of writing another one. **Nothing here is ever deleted automatically** — remove old folders yourself when the disk gets tight.
3. **A failed upgrade stops the container** rather than starting with a half-migrated database. The log line naming the failing migration is what to include in a bug report.

### Going back to an older image

An older image refuses a database that a newer one has already upgraded (`Can't locate revision identified by …` in the log). Restore the copy taken before the upgrade:

```bash
docker compose down
mv config/scraper.db config/scraper.db.new
cp config/backups/<stamp>-pre-upgrade-<from>-<to>/scraper.db config/scraper.db
# pin the older tag in docker-compose.yml, then:
docker compose up -d
```

Anything added after the upgrade lives in `scraper.db.new`, not in the restored copy, so only do this when you actually mean to go back.
