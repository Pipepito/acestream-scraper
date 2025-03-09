# Use a multi-stage build for Acexy
FROM golang:1.22 AS acexy-builder
WORKDIR /app
RUN git clone https://github.com/Javinator9889/acexy.git . && \
    cd acexy && \
    CGO_ENABLED=0 GOOS=linux go build -o /acexy

# Continue with your main image
FROM python:3.10-slim

# Add metadata labels
LABEL maintainer="pipepito" \
      description="Acestream channel scraper with ZeroNet support" \
      version="1.2.7"

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

# Copy application files
COPY --chmod=0755 entrypoint.sh /app/entrypoint.sh
COPY requirements.txt requirements-prod.txt ./
COPY migrations/ ./migrations/
COPY migrations_app.py manage.py ./
COPY wsgi.py ./
COPY app/ ./app/

# Install the required dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-prod.txt

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



# Set environment variable to indicate Docker environment
ENV DOCKER_ENV=true
ENV TZ=UTC
ENV ENABLE_TOR=false
ENV ENABLE_ACEXY=false
ENV ACESTREAM_HTTP_PORT=6878
ENV ACEXY_LISTEN_ADDR=":8080"
ENV EXTRA_FLAGS=''
ENV ALLOW_REMOTE_ACCESS=false

# Acexy and Acestream environment variables
ENV ENABLE_ACEXY=false \
    ACEXY_LISTEN_ADDR=":8080" \
    EXTRA_FLAGS="--cache-dir /tmp --cache-limit 2 --cache-auto 1 --log-stderr --log-stderr-level error"

# Expose the ports
EXPOSE 8000
EXPOSE 43110
EXPOSE 43111
EXPOSE 26552
EXPOSE 8080
EXPOSE 6878
# Set the volume
VOLUME ["/app/ZeroNet/data"]

# Clean up APT
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Make sure WORKDIR is set correctly
WORKDIR /app

HEALTHCHECK --interval=10s --timeout=10s --start-period=1s \
    CMD curl -qf http://localhost${ACEXY_LISTEN_ADDR}/ace/status || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
