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

Every flavor is published for `linux/amd64`, `linux/arm64`, and `linux/arm/v7`. The AceStream-enabled flavors (`scraper-acestream`, `scraper-acestream-acexy`, and `latest`) install a different engine per platform:

| Platform | Engine | Support |
| --- | --- | --- |
| `linux/amd64` | Native Linux engine 3.2.11 (upstream tarball) | stable |
| `linux/arm64` | Official Android engine 3.1.80.0 (`AceStreamCore-3.1.80.0-armv8_64.apk`), run natively | stable |
| `linux/arm/v7` | Official Android engine 3.1.80.0 (`AceStreamCore-3.1.80.0-armv7.apk`), run natively | experimental |

Upstream only publishes native Linux engine builds for x86_64, so the ARM images unpack the engine payload from the official AceStream Android APK (the ones listed on https://docs.acestream.media/products/) and run it unmodified against a minimal Android 9 bionic userland shipped under `/system`. No chroot, `--privileged`, seccomp changes, or extra capabilities are needed. `linux/arm/v7` builds and installs but has not been runtime-tested on real ARMv7 hardware yet, so treat it as experimental.

WARP is installed in every flavor's `linux/amd64` image, but it only starts when `ENABLE_WARP=true`. The ARM images ship without the WARP client (`cloudflare-warp` is amd64-only), so `ENABLE_WARP` is unsupported there.

ZeroNet remains an external sidecar/service. The Docker image keeps the `ZERONET_URL` client contract, but it does not bundle a ZeroNet node into every flavor.

The checked-in compose stack keeps the `zeronet` service behind an optional `zeronet` profile and points the default app config at `http://host.docker.internal:43110`. It uses an amd64-focused sidecar image. On ARM hosts, point `ZERONET_URL` at an external ZeroNet service or swap in a compatible sidecar.

AceStream platform availability is manifest-driven via `docker/manifests/acestream.json`. Adding a new supported AceStream architecture means updating that manifest. The manifest pins the engine archive, checksum, and support level (`stable` or `experimental`) per platform; every pinned archive is also vendored under `docker/vendor/` and mirrored as GitHub Release assets, so image builds do not depend on reaching `download.acestream.media`.

If you run with `ENABLE_WARP=true`, the container must be started with the runtime capabilities `NET_ADMIN` and `SYS_ADMIN`.

### Pre-release channel (`develop`)

The tags above are release tags: `latest` and the immutable `vX.Y.Z` / `vX.Y.Z-<flavor>` tags are cut from the `main` branch. Next to them, every validated build of the `develop` branch publishes a pre-release channel:

- `develop` as the full `scraper-acestream-acexy` payload (the channel's equivalent of `latest`)
- `develop-scraper`, `develop-scraper-acestream`, `develop-scraper-acexy`, and `develop-scraper-acestream-acexy` for the individual flavors

Channel tags are moving tags: they are re-pushed for the same platforms as the release flavors each time `develop` passes CI, and there is no per-version or per-commit tag for them. Use them to test what the next release will contain, not for production. To run the pre-release, replace `latest` with `develop` (or `develop-<flavor>`) in the commands below, or set `image: pipepito/acestream-scraper:develop` in `docker-compose.yml`:

```bash
docker pull pipepito/acestream-scraper:develop
```

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

### Run the In-Container AceStream Engine (amd64 and ARM)

The engine is installed in `latest`, `scraper-acestream`, and `scraper-acestream-acexy`, but it only starts when `ENABLE_ACESTREAM_ENGINE=true`. The same command works on `linux/amd64`, `linux/arm64`, and `linux/arm/v7`; Docker picks the matching image and engine for the host:

```bash
docker run -d \
  -e ENABLE_ACESTREAM_ENGINE=true \
  -p 8000:8000 \
  -p 6878:6878 \
  -p 8621:8621 \
  -p 8621:8621/udp \
  -v "${PWD}/config:/app/config" \
  -v acestream-state:/var/lib/acestream \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

- `ENABLE_ACESTREAM_ENGINE=true` starts the engine; no extra capabilities are required (only WARP needs `NET_ADMIN`/`SYS_ADMIN`).
- On ARM, `/var/lib/acestream` (`ACESTREAM_HOME`) holds the Android engine's state: `acestream.conf`, `acestream.log`, `acestream_error.log`, and the `.ACEStream/` directory with the disk cache. Mount a named volume there so the cache and the per-install device id (`.device_id`) survive container replacement; the mount is harmless on amd64.
- Ports: `6878` is the engine HTTP API (the backend talks to it through `ACE_ENGINE_URL`, default `http://localhost:6878`); `8621` tcp/udp is the P2P port. Only publish `6878` if you want to reach the engine from outside the container, and only on trusted networks: the ARM engine is started with `--bind-all` so published-port clients are accepted, and the engine HTTP API has no authentication.
- Logs: the entrypoint supervises the engine, so its output shows up in `docker logs acestream-scraper` (on ARM the launcher passes `--log-stdout` for this). On ARM the engine also writes `acestream.log` / `acestream_error.log` under `/var/lib/acestream`.
- Health: the backend polls `/server/api?api_version=3&method=get_status` and `method=get_network_connection_status` on the engine. To confirm which engine is running: `curl "http://localhost:6878/webui/api/service?method=get_version"` returns `{"platform":"android","version":"3.1.80"}` on ARM.

ARM caveats:

- **Raspberry Pi 5 (and any 16 KB-page kernel):** the Android 9 bionic linker requires a 4 KB kernel page size. On Raspberry Pi OS 64-bit set `kernel=kernel8.img` in `config.txt` (the default `kernel_2712` kernel uses 16 KB pages). The engine checks `getconf PAGESIZE` at startup and exits with an explicit error instead of segfaulting.
- **`linux/arm/v7` is experimental:** the image builds and installs, but the 32-bit engine cannot be executed under QEMU user emulation, so it has not been runtime-tested on real ARMv7 hardware. Prefer `linux/arm64` wherever the device supports 64-bit containers.
- **Engine version skew:** ARM runs the Android engine 3.1.80.0 (reports `"platform":"android"`) while amd64 runs the native Linux engine 3.2.11.
- **No WebRTC transport on ARM:** the Android WebRTC module needs GPU/audio libraries that are not shipped; the engine logs a non-fatal error and keeps going. A few CPython accelerator modules also fall back to pure Python.
- **No WARP on ARM images:** `cloudflare-warp` is amd64-only.
- **Performance and streaming stability** on real ARM hardware are not yet validated; report results if you try it.
- Repackaging the official APK payload is a grey area under the AceStream user agreement, as with every community ARM image. Enable the engine at your own discretion.

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
- `/var/lib/acestream`: AceStream engine state, disk cache, and logs of the ARM Android engine (only used when `ENABLE_ACESTREAM_ENGINE=true` in an AceStream-enabled flavor)

These volumes should be mounted to local directories (or named volumes) to ensure your data persists when containers are updated or replaced.

Example:
```bash
docker run -d -p 8000:8000 -v "${PWD}/config:/app/config" pipepito/acestream-scraper:latest
```

This mounts your local `./config` directory to the container's `/app/config` directory.

With the engine enabled on ARM, add `-v acestream-state:/var/lib/acestream` (or a local directory) so the engine cache is not rebuilt on every container replacement.
