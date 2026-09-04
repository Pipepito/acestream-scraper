# syntax=docker/dockerfile:1.7

# This image is built only from the trusted develop branch. Pull-request code
# runs inside it without network access, Jenkins credentials, or the Docker
# socket. Keep both upstream images digest-pinned so rebuilding the sandbox is
# deliberate and reviewable.
FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5 AS node

FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

LABEL org.acestream-scraper.ci.keep="true"

COPY --from=node /usr/local/ /usr/local/

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        bash \
        ca-certificates \
        git \
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

ENV CI=true \
    HOME=/tmp/ci-home \
    PATH=/opt/backend-venv/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /workspace /tmp/ci-home

WORKDIR /workspace
