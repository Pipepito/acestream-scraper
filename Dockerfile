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
# The bundled ZeroNet node (zeronet-conservancy v0.7.10) needs gevent 23.9.x
# (newer gevent deadlocks its import-time ThreadPool), which tops out at
# CPython 3.12 — so ZeroNet, like the AceStream engine, runs on its own
# interpreter, carried inside /opt/zeronet.
ARG ZERONET_PYTHON_VERSION=3.11

# ARM64 and ARMv7 use the maintained, non-premium-gated Android payloads packaged
# by jopsis. Pin the multi-arch manifest digest as well as the human-readable tag:
# upstream tag changes can never silently alter a release build.
ARG ACESTREAM_COMMUNITY_IMAGE=jopsis/acestream:v3.2.17-fix@sha256:506c4215115d8b0ac1e24f4c67c954f0dbf86e4b4ea508582e497d8c920e9933

FROM ${ACESTREAM_COMMUNITY_IMAGE} AS acestream-community-source

# Static assets are platform-independent: build them once on the build host
# (no QEMU) and COPY the output into every target platform.
FROM --platform=$BUILDPLATFORM node:20-slim AS frontend-builder

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
# upstream x86_64 tarball and both ARM platforms -> their matching variant from
# the pinned jopsis OCI image) and prefers the vendored archives under
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
# The source is copied into this throwaway installer stage for every platform;
# install-acestream.sh selects it only for manifest entries with kind=oci-image.
COPY --from=acestream-community-source /acestream/ /tmp/acestream-community/acestream/
COPY --from=acestream-community-source /system/ /tmp/acestream-community/system/
# The vendored archives (~250 MB) are bind-mounted, not copied, so they never
# land in a layer.
RUN --mount=type=bind,source=docker/vendor,target=/tmp/acestream-vendor,readonly \
    chmod +x /usr/local/lib/acestream-install/install-acestream.sh \
    && /usr/local/lib/acestream-install/install-acestream.sh


FROM python:${ACESTREAM_ENGINE_PYTHON_VERSION}-slim AS engine-python


# Kubo (go-ipfs) is a static Go binary: download it once on the build host for
# the target platform instead of running under QEMU. Upstream ships
# linux-amd64 and linux-arm64 only — on linux/arm/v7 the stage produces an
# empty /opt/ipfs/bin and the image ships without IPFS.
FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS ipfs-installer

ARG TARGETPLATFORM
ARG KUBO_VERSION=v0.43.0

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl tar \
    && rm -rf /var/lib/apt/lists/*

COPY docker/scripts/install-ipfs.sh /usr/local/lib/ipfs-install/install-ipfs.sh
RUN chmod +x /usr/local/lib/ipfs-install/install-ipfs.sh \
    && TARGETPLATFORM=${TARGETPLATFORM} KUBO_VERSION=${KUBO_VERSION} \
       /usr/local/lib/ipfs-install/install-ipfs.sh


# Self-contained ZeroNet node (zeronet-conservancy), bundled for linux/amd64
# only like the v1 image. The stage runs on $BUILDPLATFORM so ARM image
# builds skip it natively (empty /opt/zeronet + metadata); install-zeronet.sh
# refuses cross-builds of the amd64 payload. The whole CPython prefix is
# staged into /opt/zeronet/python because the runtime image runs the app on a
# different interpreter version.
FROM --platform=$BUILDPLATFORM python:${ZERONET_PYTHON_VERSION}-slim AS zeronet-installer

ARG TARGETPLATFORM
ARG ZERONET_REF=v0.7.10
ARG ZERONET_COMMIT=18d35d3bed4f0683e99f8af5a86a8d76ed866e1e

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/zeronet/requirements.txt /tmp/zeronet-requirements.txt
COPY docker/scripts/install-zeronet.sh /usr/local/lib/zeronet-install/install-zeronet.sh
RUN chmod +x /usr/local/lib/zeronet-install/install-zeronet.sh \
    && TARGETPLATFORM=${TARGETPLATFORM} ZERONET_REF=${ZERONET_REF} ZERONET_COMMIT=${ZERONET_COMMIT} \
       /usr/local/lib/zeronet-install/install-zeronet.sh


# Go cross-compiles: build on the build host for the target platform instead
# of running the toolchain under QEMU (and pulling golang for every arch).
FROM --platform=$BUILDPLATFORM golang:1.22 AS acexy-builder

ARG ACEXY_REPO
ARG ACEXY_REF
# Vendored source archive under docker/vendor/acexy (see its README): used when
# present so builds need no GitHub egress; ACEXY_SHA256 must match it.
ARG ACEXY_VENDORED_FILE
ARG ACEXY_SHA256
ARG ACEXY_BINARY_NAME=acexy
ARG TARGETOS
ARG TARGETARCH
ARG TARGETVARIANT

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/testdata/acexy/ /tmp/acexy-fixture/

# Source precedence: explicit fixture -> vendored archive -> git clone -> fixture.
RUN --mount=type=bind,source=docker/vendor,target=/tmp/acexy-vendor,readonly \
    mkdir -p /src /out \
    && if [ "${ACEXY_REPO:-}" = "fixture" ]; then \
        cp -R /tmp/acexy-fixture/. /src/; \
      elif [ -n "${ACEXY_VENDORED_FILE:-}" ] && [ -f "/tmp/acexy-vendor/acexy/${ACEXY_VENDORED_FILE}" ]; then \
        echo "acexy: using vendored ${ACEXY_VENDORED_FILE}"; \
        echo "${ACEXY_SHA256}  /tmp/acexy-vendor/acexy/${ACEXY_VENDORED_FILE}" | sha256sum -c -; \
        tar -xzf "/tmp/acexy-vendor/acexy/${ACEXY_VENDORED_FILE}" -C /src --strip-components=1; \
      elif [ -n "${ACEXY_REPO:-}" ]; then \
        echo "acexy: cloning ${ACEXY_REPO} at ${ACEXY_REF}"; \
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
    && CGO_ENABLED=0 GOOS="${TARGETOS:-linux}" GOARCH="${TARGETARCH:-amd64}" GOARM="${TARGETVARIANT#v}" \
       go build -ldflags "-s -w" -o "/out/$ACEXY_BINARY_NAME" .


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
    ZERONET_URL=http://127.0.0.1:43110 \
    ENABLE_ZERONET=false \
    ENABLE_TOR=false \
    ZERONET_BINARY_PATH=/opt/zeronet/bin/zeronet \
    ZERONET_DATA_DIR=/data/zeronet \
    ZERONET_UI_PORT=43110 \
    ZERONET_FILESERVER_PORT=26552 \
    ENABLE_IPFS=false \
    IPFS_PATH=/data/ipfs \
    IPFS_BINARY_PATH=/opt/ipfs/bin/ipfs \
    IPFS_START_COMMAND="/opt/ipfs/bin/ipfs daemon --migrate=true" \
    IPFS_SWARM_PORT=4001 \
    IPFS_API_PORT=5001 \
    IPFS_GATEWAY_PORT=8081

WORKDIR /app

# Cloudflare publishes cloudflare-warp for amd64 and arm64 (no 32-bit ARM), so
# those images ship warp-cli; linux/arm/v7 stays without it (ENABLE_WARP is
# unsupported there). The apt suite follows the base image's Debian codename.
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
    && case "$TARGETARCH" in amd64|arm64) \
        . /etc/os-release \
        && wget -q https://pkg.cloudflareclient.com/pubkey.gpg -O /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
        && printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ %s main\n' "${VERSION_CODENAME:-bookworm}" > /etc/apt/sources.list.d/cloudflare-client.list \
        && apt-get update \
        && apt-get install -y --no-install-recommends cloudflare-warp ;; \
    esac \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-deps /install /usr/local
COPY backend/ /app/
RUN mkdir -p /app/frontend_build /app/logs /opt/acestream/bin /opt/acexy/bin
COPY --from=frontend-builder /build/frontend/dist/ /app/frontend_build/

# Kubo IPFS daemon (all flavors; /opt/ipfs/bin is empty on linux/arm/v7 where
# upstream ships no 32-bit ARM build — the entrypoint detects the missing
# binary and refuses ENABLE_IPFS=true there). The daemon is opt-in at runtime:
# ENABLE_IPFS=false by default. Its gateway defaults to 8081 in-container
# because Acexy already owns 8080.
COPY --from=ipfs-installer /opt/ipfs/ /opt/ipfs/
RUN mkdir -p /data/ipfs \
    && if [ -x /opt/ipfs/bin/ipfs ]; then ln -sf /opt/ipfs/bin/ipfs /usr/local/bin/ipfs; fi

# Bundled ZeroNet node (linux/amd64 only; /opt/zeronet holds just metadata on
# ARM — the entrypoint detects the missing launcher and refuses
# ENABLE_ZERONET=true there). Opt-in at runtime: ENABLE_ZERONET=false by
# default; the scraper reaches whichever node ZERONET_URL points at either
# way. tor rides along for the v1 ENABLE_TOR toggle (amd64 only, matching
# where the bundled node exists).
COPY --from=zeronet-installer /opt/zeronet/ /opt/zeronet/
RUN mkdir -p /data/zeronet \
    && if [ "$TARGETARCH" = "amd64" ]; then \
        apt-get update \
        && apt-get install -y --no-install-recommends tor \
        && rm -rf /var/lib/apt/lists/*; \
    fi
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY warp-setup.sh /usr/local/bin/warp-setup.sh
COPY healthcheck.sh /usr/local/bin/healthcheck.sh

RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/warp-setup.sh /usr/local/bin/healthcheck.sh

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-proxy-headers", "--timeout-graceful-shutdown", "3"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 CMD ["/usr/local/bin/healthcheck.sh"]


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
    ACESTREAM_BIND_ALL=true \
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
