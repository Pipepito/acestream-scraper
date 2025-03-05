# Use the official Python image from the Docker Hub
FROM python:3.9-slim

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
    build-essential 

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

# Set environment variable to indicate Docker environment
ENV DOCKER_ENV=true
ENV TZ=UTC

# Expose the ports
EXPOSE 8000
EXPOSE 43110
EXPOSE 43111

# Clean up APT
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Make sure WORKDIR is set correctly
WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
