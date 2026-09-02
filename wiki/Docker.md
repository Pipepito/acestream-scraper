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

WARP is installed in every flavor's `linux/amd64` and `linux/arm64` images, but it only starts when `ENABLE_WARP=true` (it needs `--cap-add NET_ADMIN --cap-add SYS_ADMIN` and `--device /dev/net/tun`). The `linux/arm/v7` images ship without the WARP client (Cloudflare publishes no 32-bit ARM build), so `ENABLE_WARP` is unsupported there.

ZeroNet works in two modes. The `linux/amd64` images bundle a [zeronet-conservancy](https://github.com/zeronet-conservancy/zeronet-conservancy) v0.7.10 node — opt-in, nothing runs until `ENABLE_ZERONET=true` (add `ENABLE_TOR=true` for TOR, like the v1 image). The node runs on its own Python 3.11 under `/opt/zeronet` because its dependency set (gevent 23.9.x) predates the app's Python; that dependency set is also why ARM images ship without it — there, and whenever you prefer it, ZeroNet runs as an external sidecar/service and the app reaches it through `ZERONET_URL`.

The checked-in compose stack keeps the `zeronet` service behind an optional `zeronet` profile and points the default app config at `http://host.docker.internal:43110`. It uses an amd64-focused sidecar image. On ARM hosts, point `ZERONET_URL` at an external ZeroNet service or swap in a compatible sidecar. With the embedded node enabled, leave `ZERONET_URL` unset — the entrypoint targets the embedded UI port automatically.

IPFS is bundled, unlike ZeroNet: every flavor ships the [Kubo](https://github.com/ipfs/kubo) IPFS daemon on `linux/amd64` and `linux/arm64`. Kubo publishes no 32-bit ARM build, so `linux/arm/v7` images ship without it (the container exits with a clear error if `ENABLE_IPFS=true` is requested there — same situation as WARP). The daemon is opt-in: nothing IPFS-related runs until `ENABLE_IPFS=true`. `ipfs://` and `ipns://` sources are fetched through `IPFS_GATEWAY_URL`, which defaults to the embedded gateway at `http://127.0.0.1:8081` — the gateway uses `8081` in-container because Acexy already listens on `8080`. You can also scrape IPFS without the embedded daemon: keep `ENABLE_IPFS=false` and point `IPFS_GATEWAY_URL` at an external node, e.g. `http://host.docker.internal:8080` for a Kubo/IPFS Desktop install on the Docker host (this works on every platform, `linux/arm/v7` included).

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

> **Tip:** the [Docker command builder](https://pipepito.github.io/acestream-scraper/) generates the full `docker run` command or `docker-compose.yml` for your flavor, platform and features — ports, folders and capabilities included.

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
- `ZERONET_URL` points the scraper at a ZeroNet node — the embedded one or an external sidecar/service
- `ENABLE_ZERONET` starts the bundled ZeroNet node only when set to `true` (amd64 images); `ENABLE_TOR` adds TOR for it
- `ENABLE_IPFS` starts the embedded Kubo IPFS daemon only when set to `true` (amd64/arm64 images)
- `IPFS_GATEWAY_URL` points the scraper to the IPFS HTTP gateway used for `ipfs://`/`ipns://` sources (defaults to the embedded gateway `http://127.0.0.1:8081`)

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
- **No WARP on linux/arm/v7 images:** `cloudflare-warp` ships for amd64 and arm64 only.
- **Performance and streaming stability** on real ARM hardware are not yet validated; report results if you try it.
- Repackaging the official APK payload is a grey area under the AceStream user agreement, as with every community ARM image. Enable the engine at your own discretion.

### Run the Bundled ZeroNet Node (amd64)

ZeroNet is installed in every amd64 flavor but only starts when `ENABLE_ZERONET=true`:

```bash
docker run -d \
  -e ENABLE_ZERONET=true \
  -p 8000:8000 \
  -p 43110:43110 \
  -p 26552:26552 \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/zeronet_app_data:/data/zeronet" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

- `/data/zeronet` (`ZERONET_DATA_DIR`) holds the node's sites, keys and content; mount it so they survive container replacement.
- The scraper reaches the node automatically (`ZERONET_URL` falls back to the embedded UI port when you don't set it), so `zero://` sources work with no further setup.
- Ports: `43110` is the ZeroNet web UI, `26552` the fileserver/peer port (`ZERONET_UI_PORT` / `ZERONET_FILESERVER_PORT` to change them). Publishing `43110` is only needed to browse the ZeroNet UI yourself — and ZeroNet only answers Host headers it knows, so add `-e ZERONET_UI_HOST="myserver.lan 192.168.1.10"` to reach it from another machine. The UI has no authentication: publish it on trusted networks only.
- Add `-e ENABLE_TOR=true` to run TOR alongside; the node auto-detects it over the control port (same contract as v1). `ZERONET_EXTRA_ARGS` passes any extra zeronet-conservancy flags through.
- ARM images ship without the bundled node (its gevent-era dependency set is amd64-focused); use the external `ZERONET_URL` mode there.

### Run the Embedded IPFS Daemon (amd64 and arm64)

Kubo is installed in every flavor but only starts when `ENABLE_IPFS=true`:

```bash
docker run -d \
  -e ENABLE_IPFS=true \
  -p 8000:8000 \
  -p 4001:4001 \
  -p 4001:4001/udp \
  -p 8081:8081 \
  -v "${PWD}/config:/app/config" \
  -v "${PWD}/ipfs_data:/data/ipfs" \
  --name acestream-scraper \
  pipepito/acestream-scraper:latest
```

- `/data/ipfs` (`IPFS_PATH`) holds the IPFS repository (keys, blockstore, config); mount it so the node identity and cache survive container replacement.
- Ports: `4001` tcp/udp is the swarm port (publishing it improves peer connectivity), `8081` is the HTTP gateway (only needed outside the container if you want to browse IPFS content through the node). The RPC API on `5001` has **no authentication** and full control of the node; it binds to the container loopback by default. If you need the WebUI, set `-e IPFS_API_HOST=0.0.0.0` and publish it only on the host loopback: `-p 127.0.0.1:5001:5001`.
- Port overrides: `IPFS_SWARM_PORT` (default `4001`), `IPFS_API_PORT` (default `5001`), `IPFS_GATEWAY_PORT` (default `8081`; `8080` is taken by Acexy in-container). The entrypoint re-applies these to the IPFS config on every boot.
- Once running, add sources as `ipfs://<cid>/path/list.m3u` (or `ipns://<name>/...`) in the Scraper page — they are fetched through the embedded gateway. A bare `ipfs://<cid>` whose content is an M3U playlist also works; the scraper detects the playlist by content.

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
- `/data/ipfs`: The embedded IPFS daemon's repository — node identity, config, and blockstore (only used when `ENABLE_IPFS=true`)
- `/data/zeronet`: The bundled ZeroNet node's state — sites, keys, and content (only used when `ENABLE_ZERONET=true`)

These volumes should be mounted to local directories (or named volumes) to ensure your data persists when containers are updated or replaced.

Example:
```bash
docker run -d -p 8000:8000 -v "${PWD}/config:/app/config" pipepito/acestream-scraper:latest
```

This mounts your local `./config` directory to the container's `/app/config` directory.

With the engine enabled on ARM, add `-v acestream-state:/var/lib/acestream` (or a local directory) so the engine cache is not rebuilt on every container replacement.
