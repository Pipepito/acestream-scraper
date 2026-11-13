# syntax=docker/dockerfile:1.7

# Component image: the API with the built web interface, and nothing else. It has
# no engines, FFmpeg, WARP or supervisor; the published images come from the
# root Dockerfile. Build from the repository root:
#
#   docker build -f backend/Dockerfile -t acestream-scraper-backend .
#
# The database is created under /app/config; mount a volume there to keep it.
ARG APP_PYTHON_VERSION=3.13

FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
COPY version.txt /build/version.txt
RUN npm run build


FROM python:${APP_PYTHON_VERSION}-slim AS python-deps

WORKDIR /build/backend

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# --ignore-installed: a package the build stage already has would otherwise be
# left out of /install, the only thing the final stage copies.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --prefix=/install --ignore-installed -r requirements.txt


FROM python:${APP_PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_BUILD_PATH=frontend_build

COPY --from=python-deps /install /usr/local

WORKDIR /app
COPY backend/ /app/
COPY version.txt /app/version.txt
COPY --from=frontend-builder /build/frontend/dist/ /app/frontend_build/

# The application only writes its database, logs and player scratch files.
RUN useradd --system --uid 10001 --home-dir /app --no-create-home scraper \
    && mkdir -p /app/config /app/logs \
    && chown scraper:scraper /app/config /app/logs

USER scraper

EXPOSE 8000

# /api/v1/health needs no token and answers 503 until startup has finished.
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4)"]

# --no-proxy-headers: ForwardedHeadersMiddleware owns X-Forwarded-* trust
# (FORWARDED_ALLOW_IPS). --timeout-graceful-shutdown: live streams must not
# hold the shutdown open.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers", "--timeout-graceful-shutdown", "3"]
