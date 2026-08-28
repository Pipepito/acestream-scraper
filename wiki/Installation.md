# Installation Guide

This guide covers different methods for installing and setting up Acestream Scraper.

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
   version: '3.8'

   services:
     acestream-scraper:
       image: pipepito/acestream-scraper:latest
       container_name: acestream-scraper
       environment:
         - TZ=Europe/Madrid
         - ENABLE_TOR=false
         - ENABLE_ACEXY=true
         - ENABLE_ACESTREAM_ENGINE=true
         - ACESTREAM_HTTP_PORT=6878
         - FLASK_PORT=8000
         - ACEXY_LISTEN_ADDR=:8080
         - ACEXY_HOST=localhost
         - ACEXY_PORT=6878
         - ALLOW_REMOTE_ACCESS=no
         - ACEXY_NO_RESPONSE_TIMEOUT=15s
         - ACEXY_BUFFER_SIZE=5MiB
         - ACESTREAM_HTTP_HOST=localhost
       ports:
         - "8000:8000"  # Web app (FastAPI/uvicorn; port set by FLASK_PORT)
         - "8080:8080"  # Acexy proxy
         - "8621:8621"  # Acestream P2P Port
         - "43110:43110"  # ZeroNet UI
         - "43111:43111"  # ZeroNet peer
         - "26552:26552"  # ZeroNet peer
       volumes:
         - ./data/zeronet:/app/ZeroNet/data
         - ./data/config:/app/config
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "/app/healthcheck.sh"]
         interval: 30s
         timeout: 10s
         retries: 3
         start_period: 60s
   ```

2. **Start the service:**

   ```bash
   docker-compose up -d
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
  -p 8000:8000 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With Acexy and Internal Acestream Engine

```bash
docker run -d \
  -p 8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=true \
  -e ALLOW_REMOTE_ACCESS=yes \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With External Acestream Engine

```bash
docker run -d \
  -p 8000:8000 \
  -p 8080:8080 \
  -e ENABLE_ACEXY=true \
  -e ENABLE_ACESTREAM_ENGINE=false \
  -e ACEXY_HOST=192.168.1.100 \
  -e ACEXY_PORT=6878 \
  -v "${PWD}/config:/app/config" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With ZeroNet (TOR disabled)

```bash
docker run -d \
  -p 8000:8000 \
  -p 43110:43110 \
  -p 43111:43111 \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_data:/app/ZeroNet/data" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### With ZeroNet (TOR enabled)

```bash
docker run -d \
  -p 8000:8000 \
  -p 43110:43110 \
  -p 43111:43111 \
  -e ENABLE_TOR=true \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_data:/app/ZeroNet/data" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

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

   The stream base URL, rescrape interval and source URLs are edited in the web interface (**Settings** and **Scraper** pages) and stored in the database. An existing v1 database is migrated on first start when it is at `backend/config/acestream.db` (paths resolve relative to the `backend/` working directory) or when `LEGACY_DATABASE_URL` points at it, e.g. `export LEGACY_DATABASE_URL=sqlite:////absolute/path/to/config/acestream.db`.

5. **Run the application:**

   ```bash
   cd backend
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   For development add `--reload`. For a hot-reloading UI run `npm start` in `frontend/` (Vite on port 3000, proxying `/api` to port 8000) instead of rebuilding after every change.

6. **Access the application:**

   Open your browser and navigate to `http://localhost:8000`
