# Two Python interpreters live in the engine-bearing images and they are
# pinned independently:
#   APP_PYTHON_VERSION             the FastAPI app's runtime (scraper flavors can
#                                  track the latest CPython; 3.13 is the newest
#                                  release with full wheel coverage on arm/v7).
#   ACESTREAM_ENGINE_PYTHON_VERSION the interpreter the upstream x86_64 engine
#                                  links against (docker/manifests/acestream.json
#                                  install.python_version; 3.2.x -> 3.10). The
#                                  Android engine on ARM ships its own CPython 3.8.
ARG APP_PYTHON_VERSION=3.13
ARG ACESTREAM_ENGINE_PYTHON_VERSION=3.10

FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


FROM python:${APP_PYTHON_VERSION}-slim AS python-deps

WORKDIR /build/backend

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


FROM python:${ACESTREAM_ENGINE_PYTHON_VERSION}-slim AS acestream-installer

# Engine selection is manifest-driven per target platform: install-acestream.sh
# reads docker/manifests/acestream.json for $TARGETPLATFORM (linux/amd64 ->
# upstream x86_64 tarball, linux/arm64 + linux/arm/v7 -> official Android
# engine APK on a bionic runtime) and prefers the vendored archives under
# docker/vendor/ over network downloads. Explicit build-args override the
# manifest; ACESTREAM_SOURCE=fixture installs the contract-test fixture.
ARG TARGETPLATFORM
ARG ACESTREAM_SOURCE=auto
ARG ACESTREAM_DOWNLOAD_URL=
ARG ACESTREAM_DOWNLOAD_SHA256=
ARG ACESTREAM_ARCHIVE_TYPE=
ARG ACESTREAM_STRIP_COMPONENTS=
ARG ACESTREAM_INSTALL_KIND=
ARG ACESTREAM_BINARY_PATH=
ARG ACESTREAM_VENDORED_FILE=
ARG ACESTREAM_MIRROR_URLS=
ARG ACESTREAM_ANDROID_ABI=
ARG ACESTREAM_BIONIC_URL=
ARG ACESTREAM_BIONIC_SHA256=
ARG ACESTREAM_BIONIC_VENDORED_FILE=
ARG ACESTREAM_BIONIC_MIRROR_URLS=
ARG ACESTREAM_BIONIC_LIBDIR=
ARG ACESTREAM_BIONIC_LINKER=
ARG ACESTREAM_ENGINE_PYTHON_VERSION
ARG ACESTREAM_PYTHON_VERSION=${ACESTREAM_ENGINE_PYTHON_VERSION}

ENV TARGETPLATFORM=${TARGETPLATFORM} \
    ACESTREAM_SOURCE=${ACESTREAM_SOURCE} \
    ACESTREAM_DOWNLOAD_URL=${ACESTREAM_DOWNLOAD_URL} \
    ACESTREAM_DOWNLOAD_SHA256=${ACESTREAM_DOWNLOAD_SHA256} \
    ACESTREAM_ARCHIVE_TYPE=${ACESTREAM_ARCHIVE_TYPE} \
    ACESTREAM_STRIP_COMPONENTS=${ACESTREAM_STRIP_COMPONENTS} \
    ACESTREAM_INSTALL_KIND=${ACESTREAM_INSTALL_KIND} \
    ACESTREAM_BINARY_PATH=${ACESTREAM_BINARY_PATH} \
    ACESTREAM_VENDORED_FILE=${ACESTREAM_VENDORED_FILE} \
    ACESTREAM_MIRROR_URLS=${ACESTREAM_MIRROR_URLS} \
    ACESTREAM_ANDROID_ABI=${ACESTREAM_ANDROID_ABI} \
    ACESTREAM_BIONIC_URL=${ACESTREAM_BIONIC_URL} \
    ACESTREAM_BIONIC_SHA256=${ACESTREAM_BIONIC_SHA256} \
    ACESTREAM_BIONIC_VENDORED_FILE=${ACESTREAM_BIONIC_VENDORED_FILE} \
    ACESTREAM_BIONIC_MIRROR_URLS=${ACESTREAM_BIONIC_MIRROR_URLS} \
    ACESTREAM_BIONIC_LIBDIR=${ACESTREAM_BIONIC_LIBDIR} \
    ACESTREAM_BIONIC_LINKER=${ACESTREAM_BIONIC_LINKER} \
    ACESTREAM_PYTHON_VERSION=${ACESTREAM_PYTHON_VERSION} \
    ACESTREAM_MANIFEST=/tmp/acestream-manifest.json \
    ACESTREAM_VENDOR_ROOT=/tmp/acestream-vendor \
    ACESTREAM_SCRIPTS_DIR=/usr/local/lib/acestream-install

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        tar \
        unzip \
    && rm -rf /var/lib/apt/lists/*

COPY docker/testdata/acestream/ /tmp/acestream-fixture/
COPY docker/manifests/acestream.json /tmp/acestream-manifest.json
COPY docker/scripts/install-acestream.sh docker/scripts/acestream_manifest.py /usr/local/lib/acestream-install/
COPY docker/scripts/acestream-android/ /usr/local/lib/acestream-install/acestream-android/
# The vendored archives (~250 MB) are bind-mounted, not copied, so they never
# land in a layer.
RUN --mount=type=bind,source=docker/vendor,target=/tmp/acestream-vendor,readonly \
    chmod +x /usr/local/lib/acestream-install/install-acestream.sh \
    && /usr/local/lib/acestream-install/install-acestream.sh


FROM python:${ACESTREAM_ENGINE_PYTHON_VERSION}-slim AS engine-python


FROM golang:1.22 AS acexy-builder

ARG ACEXY_REPO
ARG ACEXY_REF
ARG ACEXY_BINARY_NAME=acexy

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/testdata/acexy/ /tmp/acexy-fixture/

RUN mkdir -p /src /out \
    && if [ -n "${ACEXY_REPO:-}" ] && [ "$ACEXY_REPO" != "fixture" ]; then \
        git clone --depth 1 "$ACEXY_REPO" /src; \
        cd /src; \
        git fetch --depth 1 origin "$ACEXY_REF"; \
        git checkout FETCH_HEAD; \
      else \
        cp -R /tmp/acexy-fixture/. /src/; \
      fi \
    && cd /src \
    # Upstream acexy keeps its Go module in the acexy/ subdirectory; the
    # build fixture (and any flat fork) keeps go.mod at the root.
    && if [ ! -f go.mod ] && [ -f acexy/go.mod ]; then cd acexy; fi \
    && CGO_ENABLED=0 GOOS=linux go build -ldflags "-s -w" -o "/out/$ACEXY_BINARY_NAME" .


FROM python:${APP_PYTHON_VERSION}-slim AS runtime-base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FRONTEND_BUILD_PATH=frontend_build \
    LOG_DIR=/app/logs \
    ENABLE_WARP=false \
    ENABLE_ACESTREAM_ENGINE=false \
    ENABLE_ACEXY=false \
    IMAGE_HAS_ACESTREAM=false \
    IMAGE_HAS_ACEXY=false \
    FLASK_PORT=8000 \
    ACESTREAM_HTTP_HOST=localhost \
    ACESTREAM_HTTP_PORT=6878 \
    ACEXY_HOST=localhost \
    ACEXY_PORT=6878 \
    ACEXY_STATUS_PORT=8080 \
    ZERONET_URL=http://127.0.0.1:43110

WORKDIR /app

# cloudflare-warp is only published for amd64 in Cloudflare's apt repo;
# installing it unconditionally breaks the arm/v7 and arm64 baseline images.
# ARM images ship without warp-cli (ENABLE_WARP is unsupported there).
ARG TARGETARCH
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        dbus \
        iproute2 \
        iptables \
        logrotate \
        nftables \
        procps \
        tini \
        wget \
    && if [ "$TARGETARCH" = "amd64" ]; then \
        wget -q https://pkg.cloudflareclient.com/pubkey.gpg -O /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
        && printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ bookworm main\n' > /etc/apt/sources.list.d/cloudflare-client.list \
        && apt-get update \
        && apt-get install -y --no-install-recommends cloudflare-warp; \
    fi \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-deps /install /usr/local
COPY backend/ /app/
RUN mkdir -p /app/frontend_build /app/logs /opt/acestream/bin /opt/acexy/bin
COPY --from=frontend-builder /build/frontend/dist/ /app/frontend_build/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY warp-setup.sh /usr/local/bin/warp-setup.sh
COPY healthcheck.sh /usr/local/bin/healthcheck.sh

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/warp-setup.sh /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 CMD ["/usr/local/bin/healthcheck.sh"]


FROM runtime-base AS scraper


FROM scraper AS scraper-acestream

# Graft the engine's interpreter from the official slim image. Two Pythons
# coexist: APP_PYTHON_VERSION for the FastAPI app and
# ACESTREAM_ENGINE_PYTHON_VERSION for the x86_64 AceStream engine (its binary
# links libpython<version>.so.1.0 directly). Harmless on ARM, where the
# Android engine brings its own CPython.
ARG ACESTREAM_ENGINE_PYTHON_VERSION
COPY --from=engine-python /usr/local/bin/python${ACESTREAM_ENGINE_PYTHON_VERSION} /usr/local/bin/python${ACESTREAM_ENGINE_PYTHON_VERSION}
COPY --from=engine-python /usr/local/lib/python${ACESTREAM_ENGINE_PYTHON_VERSION} /usr/local/lib/python${ACESTREAM_ENGINE_PYTHON_VERSION}
COPY --from=engine-python /usr/local/lib/libpython${ACESTREAM_ENGINE_PYTHON_VERSION}.so.1.0 /usr/local/lib/libpython${ACESTREAM_ENGINE_PYTHON_VERSION}.so.1.0
RUN ldconfig

COPY --from=acestream-installer /opt/acestream/ /opt/acestream/
# ARM flavors run the official Android engine payload against a minimal Android 9
# bionic userland; its ELF interpreter path is hard-coded to /system/bin/linker*.
# The directory is empty for the native x86_64 engine.
COPY --from=acestream-installer /opt/acestream-system/ /system/
RUN mkdir -p /var/lib/acestream /data

# The same start command works for every platform: on x86_64 start-engine is
# upstream's wrapper; on ARM it is docker/scripts/acestream-android/start-engine
# (which sets its own PYTHONPATH and keeps state under ACESTREAM_HOME).
ENV IMAGE_HAS_ACESTREAM=true \
    ACESTREAM_BINARY_PATH=/opt/acestream/bin/acestreamengine \
    ACESTREAM_HOME=/var/lib/acestream \
    ACESTREAM_START_COMMAND="env PYTHONPATH=/opt/acestream/python-deps /opt/acestream/start-engine --client-console --http-port 6878"


FROM scraper AS scraper-acexy

ARG ACEXY_BINARY_NAME=acexy

COPY --from=acexy-builder /out/${ACEXY_BINARY_NAME} /opt/acexy/bin/${ACEXY_BINARY_NAME}

ENV IMAGE_HAS_ACEXY=true \
    ACEXY_BINARY_PATH=/opt/acexy/bin/${ACEXY_BINARY_NAME} \
    ACEXY_START_COMMAND=/opt/acexy/bin/${ACEXY_BINARY_NAME}


FROM scraper-acestream AS scraper-acestream-acexy

ARG ACEXY_BINARY_NAME=acexy

COPY --from=acexy-builder /out/${ACEXY_BINARY_NAME} /opt/acexy/bin/${ACEXY_BINARY_NAME}

ENV IMAGE_HAS_ACEXY=true \
    ACEXY_BINARY_PATH=/opt/acexy/bin/${ACEXY_BINARY_NAME} \
    ACEXY_START_COMMAND=/opt/acexy/bin/${ACEXY_BINARY_NAME}
