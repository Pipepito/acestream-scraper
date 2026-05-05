# Docker Guide

## What is Docker?

Docker is a platform that uses containerization technology to package applications and their dependencies together in isolated containers. These containers are lightweight, portable units that can run consistently across different environments.

### Key Docker Concepts

- **Container**: A lightweight, standalone executable package that includes everything needed to run an application
- **Image**: A read-only template used to create containers
- **Dockerfile**: A script with instructions for building a Docker image
- **Docker Compose**: A tool for defining and running multi-container applications
- **Volume**: Persistent data storage that exists outside the container lifecycle

### Benefits of Using Docker with Acestream Scraper

1. **Simplified Installation**: No need to worry about dependencies or system compatibility
2. **Consistent Environment**: Works the same way on any system that supports Docker
3. **Flavor-Based Packaging**: Pick the image that includes only the optional binaries you need
4. **Isolation**: Keeps the application and its dependencies contained
5. **Easy Updates**: Simple command to update to the latest version
6. **Resource Management**: Controls how much system resources the application can use

## Docker vs. Docker Compose

### Docker
- Manages individual containers
- Best for simple deployments
- Uses CLI commands to configure containers
- Example: `docker run -p 8000:8000 pipepito/acestream-scraper:latest`

### Docker Compose
- Manages multi-container applications
- Configuration in a YAML file
- Easier to maintain complex setups
- Example: `docker compose up -d`

For Acestream Scraper, Docker Compose is recommended as it makes managing all configuration parameters easier.

## Image Tags and Flavors

Docker images are published under `pipepito/acestream-scraper`.

- `latest` as the full `scraper-acestream-acexy` image
- `scraper` for the base app runtime plus WARP tooling
- `scraper-acestream` for the base app plus AceStream
- `scraper-acexy` for the base app plus Acexy
- `scraper-acestream-acexy` for the full app plus AceStream and Acexy

WARP is installed in every flavor, but it only starts when `ENABLE_WARP=true`.

ZeroNet remains an external sidecar/service. The Docker image keeps the `ZERONET_URL` client contract, but it does not bundle a ZeroNet node into every flavor.

The checked-in compose stack keeps the `zeronet` service behind an optional `zeronet` profile and points the default app config at `http://host.docker.internal:43110`. It uses an amd64-focused sidecar image. On ARM hosts, point `ZERONET_URL` at an external ZeroNet service or swap in a compatible sidecar.

AceStream platform availability is manifest-driven via `docker/manifests/acestream.json`. Adding a new supported AceStream architecture means updating that manifest.

If you run with `ENABLE_WARP=true`, the container must be started with the runtime capabilities `NET_ADMIN` and `SYS_ADMIN`.

## Basic Docker Commands

### Pull the Image
```bash
docker pull pipepito/acestream-scraper:latest
```

### Run the Container
```bash
docker run -d -p 8000:8000 --name acestream-scraper pipepito/acestream-scraper:latest
```

`latest` is the full `scraper-acestream-acexy` image. If you want to pin behavior explicitly, pull one of the flavor tags instead.

Important runtime env expectations:

- `ENABLE_WARP` enables WARP only when set to `true`
- `ENABLE_ACESTREAM_ENGINE` starts the installed AceStream engine only when set to `true`
- `ENABLE_ACEXY` starts the installed Acexy binary only when set to `true`
- `ACESTREAM_HTTP_HOST` and `ACESTREAM_HTTP_PORT` define the in-container AceStream endpoint
- `ACEXY_HOST` and `ACEXY_PORT` define the engine endpoint Acexy connects to
- `ZERONET_URL` points the scraper to an external ZeroNet sidecar/service

The default compose example uses `http://host.docker.internal:43110` so the app can still boot when the optional `zeronet` profile is not enabled.

Example with WARP enabled:

```bash
docker run -d \
  --cap-add NET_ADMIN \
  --cap-add SYS_ADMIN \
  -e ENABLE_WARP=true \
  -p 8000:8000 \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

### View Running Containers
```bash
docker ps
```

### View Container Logs
```bash
docker logs acestream-scraper
```

### Stop the Container
```bash
docker stop acestream-scraper
```

### Remove the Container
```bash
docker rm acestream-scraper
```

### Update to Latest Version
```bash
docker pull pipepito/acestream-scraper:latest
docker stop acestream-scraper
docker rm acestream-scraper
# Run the container again with your preferred configuration
```

## Docker Compose Commands

### Start Services
```bash
docker compose up -d
```

### Start Services With The Example ZeroNet Sidecar
```bash
docker compose --profile zeronet up -d
```

### View Logs
```bash
docker compose logs
```

### Stop Services
```bash
docker compose down
```

### Update to Latest Version
```bash
docker compose pull
docker compose up -d
```

## Docker Data Persistence

Acestream Scraper uses Docker volumes to persist data:

- `/app/config`: Configuration files including database

These volumes should be mounted to local directories to ensure your data persists when containers are updated or replaced.

Example:
```bash
docker run -d -p 8000:8000 -v "${PWD}/config:/app/config" pipepito/acestream-scraper:latest
```

This mounts your local `./config` directory to the container's `/app/config` directory.
