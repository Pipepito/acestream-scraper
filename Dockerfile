FROM node:20-slim AS frontend-builder

WORKDIR /build/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS python-deps

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


FROM python:3.10-slim AS acestream-installer

ARG ACESTREAM_DOWNLOAD_URL
ARG ACESTREAM_DOWNLOAD_SHA256=
ARG ACESTREAM_ARCHIVE_TYPE=tar.gz
ARG ACESTREAM_STRIP_COMPONENTS=1
ARG ACESTREAM_INSTALL_KIND=executable
ARG ACESTREAM_BINARY_PATH=acestreamengine
ARG ACESTREAM_PYTHON_MODULE=acestreamengine
ARG ACESTREAM_PYTHON_VERSION=3.10

ENV ACESTREAM_DOWNLOAD_URL=${ACESTREAM_DOWNLOAD_URL} \
    ACESTREAM_DOWNLOAD_SHA256=${ACESTREAM_DOWNLOAD_SHA256} \
    ACESTREAM_ARCHIVE_TYPE=${ACESTREAM_ARCHIVE_TYPE} \
    ACESTREAM_STRIP_COMPONENTS=${ACESTREAM_STRIP_COMPONENTS} \
    ACESTREAM_INSTALL_KIND=${ACESTREAM_INSTALL_KIND} \
    ACESTREAM_BINARY_PATH=${ACESTREAM_BINARY_PATH} \
    ACESTREAM_PYTHON_MODULE=${ACESTREAM_PYTHON_MODULE} \
    ACESTREAM_PYTHON_VERSION=${ACESTREAM_PYTHON_VERSION}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        tar \
    && rm -rf /var/lib/apt/lists/*

COPY docker/testdata/acestream/ /tmp/acestream-fixture/
COPY docker/scripts/acestream-engine-wrapper.sh.tpl /usr/local/share/acestream/wrapper.sh.tpl
COPY docker/scripts/install-acestream.sh /usr/local/bin/install-acestream.sh
RUN chmod +x /usr/local/bin/install-acestream.sh \
    && /usr/local/bin/install-acestream.sh


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
    && CGO_ENABLED=0 GOOS=linux go build -o "/out/$ACEXY_BINARY_NAME" .


FROM python:3.11-slim AS runtime-base

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
    && wget -q https://pkg.cloudflareclient.com/pubkey.gpg -O /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
    && printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ bookworm main\n' > /etc/apt/sources.list.d/cloudflare-client.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends cloudflare-warp \
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

# Pull a working python3.10 interpreter from the official slim image. Two
# Pythons coexist: 3.11 for the FastAPI app, 3.10 for the AceStream engine
# (its bundled .so extensions are compiled against CPython 3.10).
COPY --from=python:3.10-slim /usr/local/bin/python3.10 /usr/local/bin/python3.10
COPY --from=python:3.10-slim /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=python:3.10-slim /usr/local/lib/libpython3.10.so.1.0 /usr/local/lib/libpython3.10.so.1.0
RUN ldconfig

COPY --from=acestream-installer /opt/acestream/ /opt/acestream/

ENV IMAGE_HAS_ACESTREAM=true \
    ACESTREAM_BINARY_PATH=/opt/acestream/bin/acestreamengine \
    ACESTREAM_START_COMMAND=/opt/acestream/bin/acestreamengine


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
