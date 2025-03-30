# Use a multi-stage build for Acexy
FROM golang:1.22 AS acexy-builder
WORKDIR /app
RUN git clone https://github.com/Javinator9889/acexy.git . && \
    cd acexy && \
    CGO_ENABLED=0 GOOS=linux go build -o /acexy

# Create base image with all dependencies
FROM python:3.10-slim AS base

# Add metadata labels
LABEL maintainer="pipepito" \
      description="Base image for Acestream channel scraper" \
      version="1.2.14"

# Set the working directory
WORKDIR /app

# Create the config directory
RUN mkdir -p /app/config

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    gcc \
    python3-dev \
    build-essential \
    tor

# Add TOR configuration
RUN echo "ControlPort 9051" >> /etc/tor/torrc && \
    echo "CookieAuthentication 1" >> /etc/tor/torrc

# Install ZeroNet dependencies with specific versions
RUN pip install --no-cache-dir \
    "msgpack-python" \
    "gevent==22.10.2" \
    "PySocks" \
    "gevent-websocket" \
    "python-bitcoinlib" \
    "bencode.py" \
    "merkletools" \
    "pysha3" \
    "cgi-tools" \
    "urllib3<2.0.0" \
    "rich" \
    "requests" \
    "pyaes" \
    "coincurve" \
    "base58" \
    "defusedxml" \
    "rsa"

# Download and install ZeroNet
RUN mkdir -p ZeroNet && \
    wget https://github.com/zeronet-conservancy/zeronet-conservancy/archive/refs/heads/master.tar.gz -O ZeroNet.tar.gz && \
    tar xvf ZeroNet.tar.gz && \
    mv zeronet-conservancy-master/* ZeroNet/ && \
    rm -rf ZeroNet.tar.gz zeronet-conservancy-master

ENV ACESTREAM_VERSION="3.2.3_ubuntu_22.04_x86_64_py3.10"
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install acestream dependencies
RUN apt-get update \
  && apt-get install --no-install-recommends -y \
      python3.10 ca-certificates wget sudo \
  && rm -rf /var/lib/apt/lists/* \
  #
  # Download acestream
  && wget --progress=dot:giga "https://download.acestream.media/linux/acestream_${ACESTREAM_VERSION}.tar.gz" \
  && mkdir acestream \
  && tar zxf "acestream_${ACESTREAM_VERSION}.tar.gz" -C acestream \
  && rm "acestream_${ACESTREAM_VERSION}.tar.gz" \
  && mv acestream /opt/acestream \
  && pushd /opt/acestream || exit \
  && bash ./install_dependencies.sh \
  && popd || exit

# Copy the acexy binary from the builder stage
COPY --from=acexy-builder /acexy /usr/local/bin/acexy
RUN chmod +x /usr/local/bin/acexy

# Install Cloudflare WARP dependencies
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    gnupg \
    curl \
    lsb-release \
    dirmngr \
    ca-certificates \
    --no-install-recommends

# Add Cloudflare GPG key and repository
RUN curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/cloudflare-client.list

# Install Cloudflare WARP
RUN apt-get update && apt-get install -y cloudflare-warp \
    && rm -rf /var/lib/apt/lists/*

# Clean up APT in base image
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set default environment variables for base image
ENV DOCKER_ENV=true
ENV TZ='Europe/Madrid'
ENV ENABLE_TOR=false
ENV ENABLE_ACEXY=false
ENV ENABLE_ACESTREAM_ENGINE=false
ENV ENABLE_WARP=false
ENV WARP_ENABLE_NAT=true
ENV WARP_ENABLE_IPV6=false
ENV ACESTREAM_HTTP_PORT=6878
ENV IPV6_DISABLED=true
ENV FLASK_PORT=8000
ENV ACEXY_LISTEN_ADDR=":8080"
ENV ACEXY_HOST="localhost"
ENV ACEXY_PORT=6878
ENV ALLOW_REMOTE_ACCESS="no"
ENV ACEXY_NO_RESPONSE_TIMEOUT=15s
ENV ACEXY_BUFFER_SIZE=5MiB
ENV ACESTREAM_HTTP_HOST=ACEXY_HOST
ENV EXTRA_FLAGS="--cache-dir /tmp --cache-limit 2 --cache-auto 1 --log-stderr --log-stderr-level error"

# Final image with application code
FROM base

# Update metadata labels for the final image
LABEL description="Acestream channel scraper with ZeroNet support" \
      version="1.2.14"

# Copy application files
COPY --chmod=0755 entrypoint.sh /app/entrypoint.sh
COPY --chmod=0755 healthcheck.sh /app/healthcheck.sh
COPY --chmod=0755 warp-setup.sh /app/warp-setup.sh
COPY requirements.txt requirements-prod.txt ./
COPY migrations/ ./migrations/
COPY migrations_app.py manage.py ./
COPY wsgi.py ./
COPY app/ ./app/

# Install the application dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-prod.txt

# Expose the ports
EXPOSE 8000
EXPOSE 43110
EXPOSE 43111
EXPOSE 26552
EXPOSE 8080
EXPOSE 8621

# Set the volume
VOLUME ["/app/ZeroNet/data"]

# Make sure WORKDIR is set correctly
WORKDIR /app

# Define the healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD /app/healthcheck.sh

# IMPORTANT: The following capabilities must be added when running the container with WARP enabled:
# --cap-add NET_ADMIN
# --cap-add SYS_ADMIN
# Example: docker run --cap-add NET_ADMIN --cap-add SYS_ADMIN -e ENABLE_WARP=true ...
# Note: Container runs with IPv6 disabled to avoid DNS lookup issues

ENTRYPOINT ["/app/entrypoint.sh"]
