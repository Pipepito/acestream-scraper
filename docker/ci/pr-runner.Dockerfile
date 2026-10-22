# syntax=docker/dockerfile:1.7

# This image is built from a trusted validation ref (develop or release main).
# Pull-request code
# runs inside it without network access, Jenkins credentials, or the Docker
# socket. Keep both upstream images digest-pinned so rebuilding the sandbox is
# deliberate and reviewable.
FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5 AS node

# Exercise media integration with the application's exact minimal FFmpeg build.
# The distro binary remains available only to generate synthetic test fixtures.
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254 AS ffmpeg-builder
ARG TARGETARCH
RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential nasm pkg-config curl xz-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY docker/manifests/ffmpeg.json /tmp/ffmpeg.json
COPY docker/scripts/build-ffmpeg.sh /tmp/build-ffmpeg.sh
RUN python - <<'PYTHON'
import json
import os
import subprocess
from pathlib import Path
manifest = json.loads(Path('/tmp/ffmpeg.json').read_text())
settings = {
    'FFMPEG_VENDORED_FILE': manifest['vendored_file'],
    'FFMPEG_SHA256': manifest['sha256'],
    'FFMPEG_SOURCE_URL': manifest['source_url'],
    'FFMPEG_MIRROR_URLS': ' '.join(manifest['mirror_urls']),
}
subprocess.run(['bash', '/tmp/build-ffmpeg.sh'], env=dict(os.environ, **settings), check=True)
PYTHON

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

LABEL org.acestream-scraper.ci.kind="dependency-runner"

COPY --from=node /usr/local/ /usr/local/

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        bash \
        ca-certificates \
        git \
        ffmpeg \
        jq \
        rsync \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN python -m venv /opt/backend-venv \
    && /opt/backend-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/backend-venv/bin/pip install --no-cache-dir -r /tmp/backend-requirements.txt

WORKDIR /tmp/frontend-install
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci \
    && npm cache clean --force \
    && mv node_modules /opt/frontend-node_modules \
    && rm -rf /tmp/frontend-install

COPY --from=ffmpeg-builder /out/ffmpeg /out/ffprobe /usr/local/bin/

ENV CI=true \
    FFMPEG_TEST_TOOL_PATH=/usr/bin/ffmpeg \
    HOME=/tmp/ci-home \
    PATH=/opt/backend-venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /workspace /tmp/ci-home

WORKDIR /workspace
