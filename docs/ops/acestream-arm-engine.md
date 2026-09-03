# AceStream Engine On ARM (Operator Guide)

This guide covers the in-container AceStream engine shipped for `linux/arm64`
and `linux/arm/v7` in the `scraper-acestream`, `scraper-acestream-acexy`,
`latest`, and version tags: what the ARM images actually run, what is bundled
and under which terms, how to operate the engine on real hardware, what is
known not to work, how to test it, and how to update the pinned binaries.

Related documents:

- `docs/ops/multiarch-manifest-updates.md`: manifest schema and the pin update procedure.
- `docs/ops/jenkins-ci.md`: what Jenkins verifies per platform ("AceStream Engine Smoke Coverage").
- `docs/migration/phase5-architecture-smoke-checklist.md`: architecture smoke checklist, including the ARM engine steps.
- `docs/release/phase5-multiarch-evidence.md`: recorded smoke evidence per release.
- `docker/vendor/acestream/README.md`: the vendored engine archives.
- `wiki/Docker.md`: user-facing Docker notes and caveats.

## Support Matrix

| Platform | Engine | `install.kind` | `support` | Notes |
|---|---|---|---|---|
| `linux/amd64` | Native Linux engine 3.2.11 (`acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz`) | `executable` | `stable` | Unchanged: upstream tarball on a grafted `python3.10`. |
| `linux/arm64` | Android engine 3.2.17 from [`jopsis/acestream:v3.2.17-fix`](https://hub.docker.com/r/jopsis/acestream) | `oci-image` | `stable` | Non-premium-gated distribution; immutable OCI digest; API/startup verified on ARM64. |
| `linux/arm/v7` | Android engine 3.2.17 from [`jopsis/acestream:v3.2.17-fix`](https://hub.docker.com/r/jopsis/acestream) | `oci-image` | `experimental` | Matching ARMv7 OCI variant; builds and installs; cannot execute under qemu-user; not runtime-tested on hardware yet. |

`support` is the value from `docker/manifests/acestream.json`; the resolved
kind, version, support level and source for every platform are printed by
`bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream`.

Upstream publishes native Linux engine tarballs only for x86_64. Both ARM
platforms use their matching variant of the maintained
[`jopsis/acestream`](https://github.com/jopsis/docker-acestream-aceserve) 3.2.17
multi-platform distribution. The engine is opt-in on every platform
(`ENABLE_ACESTREAM_ENGINE=false` by default), so the app itself is unaffected
on hosts where the engine cannot start.

## How It Works

Both ARM distributions carry a python-for-Android engine: a bionic-linked
CPython 3.8 plus compiled engine modules. Rather than chroot-ing into Android,
the image runs the payload against the accompanying bionic userland:

1. At build time, each ARM target's `oci-image` path copies `/acestream` and
   `/system` from the matching platform variant of the digest-pinned jopsis stage.
2. The Linux bootstrap files from `docker/scripts/acestream-android/` replace
   the source bootstrap while the originals remain as `*.oci-orig` or
   `*.android-orig`. This avoids inheriting a fixed device identity and keeps
   state under `ACESTREAM_HOME`. `/opt/acestream/bin/acestreamengine` links to
   `/opt/acestream/start-engine`.
3. The bionic tree supplies `bin/linker64` (arm64) or `bin/linker` (armv7), plus `libc.so`,
   `libdl.so`, `libm.so`, `libz.so`, `liblog.so`, `libc++.so`, and
   `ld-android.so` under `lib64` or `lib`, a `libstdc++.so -> libc++.so`
   symlink, `tzdata`, and `etc/hosts -> /etc/hosts`. The runtime stage copies
   that tree to `/system`: the payload's ELF interpreter path is hard-coded to
   `/system/bin/linker*`, so no other location works.
4. Runtime (`/opt/acestream/start-engine`, source
   `docker/scripts/acestream-android/start-engine`): sets `ANDROID_ROOT=/system`,
   `PYTHONHOME`, `PYTHONPATH`, and `LD_LIBRARY_PATH`, checks the kernel page
   size, seeds `ACESTREAM_HOME/acestream.conf`, and execs the bionic `python`
   with `main_linux.py`. `main_linux.py` is a Linux copy of the APK bootstrap
   that keeps `--log-stdout` output on stdout so it reaches `docker logs`.
   `app_bridge.py` replaces the Android RPC client: it answers the engine's
   device questions locally (persistent per-install device id in
   `ACESTREAM_HOME/.device_id`, disk answers from `statvfs`, memory from
   `/proc/meminfo`).

`ACESTREAM_START_COMMAND` is identical on every platform
(`env PYTHONPATH=/opt/acestream/python-deps /opt/acestream/start-engine --client-console --http-port 6878`):
on amd64 `start-engine` is upstream's wrapper, on ARM it is the script above.
No chroot, `--privileged`, seccomp profile, or extra capabilities are required
(verified on arm64).

## What Is Shipped

Inside the ARM `scraper-acestream*` images:

| Path | Content |
|---|---|
| `/opt/acestream/` | Engine payload from the APK (`python/`, `lib/`, `modules.zip`, `acestreamengine/`, `eggs/`, `main.py`) plus `start-engine`, `main_linux.py`, `app_bridge.py`, `acestream.conf`, and `install-metadata.txt`. |
| `/system/` | Minimal Android 9 bionic userland (see above). Empty on amd64. |
| `/system/etc/NOTICE-aosp-libs/` | License notices for the bionic libraries. |
| `/var/lib/acestream/` | `ACESTREAM_HOME`: engine config, state, cache, and logs. Created empty; mount a volume here. |

The amd64 archive and legacy ARM APKs are vendored in the repository and mirrored
on a GitHub Release. The legacy APKs are retained for reproducibility but are no
longer selected by the current ARM manifest entries:

- `docker/vendor/acestream/`: `acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz`,
  `AceStreamCore-3.1.80.0-armv7.apk`,
  `SHA256SUMS`, `README.md`.
- `docker/vendor/bionic/`: `aosp-libs_9.0.0-r76-4_aarch64.deb`,
  `aosp-libs_9.0.0-r76-4_arm.deb`, `SHA256SUMS`.
- Mirror: https://github.com/Pipepito/acestream-scraper/releases/tag/acestream-binaries-3.2.11-3.1.80.0

ARM64 and ARMv7 instead copy `/acestream` and `/system` from their matching
platform variants of
`jopsis/acestream:v3.2.17-fix@sha256:506c4215115d8b0ac1e24f4c67c954f0dbf86e4b4ea508582e497d8c920e9933`
as a Docker build stage. The tag documents the selected release and the digest
prevents drift. The installer resolves each conventional archive as vendored copy -> upstream `url` ->
`mirror_urls` and verifies the pinned sha256 whichever source wins, so builds
no longer need network access to `download.acestream.media`. The vendored
directory is bind-mounted into the installer stage, not copied into a layer.

To see what a given image installed:

```bash
docker run --rm --entrypoint cat pipepito/acestream-scraper:scraper-acestream /opt/acestream/install-metadata.txt
```

Expected on ARM: the matching `platform`, `kind=oci-image`,
`engine_version=3.2.17`, the platform's support level,
`distribution=jopsis/acestream v3.2.17-fix`, and an `engine_source=oci:...`
value containing the pinned digest.

## Licensing And Notices

- AceStream engine: proprietary, distributed under AceStream's terms. Both ARM
  payloads and bionic runtimes come from `jopsis/acestream`; its Docker Hub page
  and public GitHub build source are linked above, but the repository has no
  explicit packaging-code license. Release
  owners must review redistribution terms; operators enable the engine at their
  own discretion.
- Bionic userland: `aosp-libs 9.0.0-r76-4` from Termux, built from AOSP source.
  The AOSP components are under BSD, Apache-2.0, and similar permissive
  licenses; their NOTICE files ship under `/system/etc/NOTICE-aosp-libs/`.
- `docker/scripts/acestream-android/app_bridge.py` is derived from the SL4A RPC
  client (Copyright 2009 Google Inc., Apache License 2.0), as noted in its
  header.
- WARP is installed on linux/arm64 images (Cloudflare ships an arm64 `cloudflare-warp`); linux/arm/v7 has no build, so `ENABLE_WARP` is unsupported there.

## Running The Engine On ARM

### Image tags

`pipepito/acestream-scraper:latest`, `:scraper-acestream`,
`:scraper-acestream-acexy`, and their version-prefixed variants are
multi-platform manifests covering `linux/amd64`, `linux/arm64`, and
`linux/arm/v7`; Docker selects the platform automatically. `:scraper` and
`:scraper-acexy` do not contain an engine.

### Runtime environment variables

| Variable | Default | Meaning |
|---|---|---|
| `ENABLE_ACESTREAM_ENGINE` | `false` | Start the in-container engine. `entrypoint.sh` refuses `true` on flavors without the engine (`IMAGE_HAS_ACESTREAM=false`). |
| `ACESTREAM_HTTP_HOST` / `ACESTREAM_HTTP_PORT` | `localhost` / `6878` | Engine endpoint used by the app, the Acexy defaults, and `healthcheck.sh`. `ACE_ENGINE_URL` is derived from them unless set explicitly. |
| `ACESTREAM_HOME` | `/var/lib/acestream` | Engine state directory (config, cache, logs, `.device_id`). |
| `ACESTREAM_START_COMMAND` | see above | The command `entrypoint.sh` supervises. Same on every platform; extra flags appended after `--http-port 6878` win. |
| `ACESTREAM_INSTALL_DIR` | `/opt/acestream` | Read by the ARM `start-engine` only; leave as is. |
| `TEMP` | `/tmp` | Scratch directory used by the Android engine. |
| `ENABLE_ACEXY` | `false` | Optional Acexy proxy in front of the engine (`scraper-acestream-acexy`, `latest`). |

These are the same variables as on amd64; there is no ARM-specific switch.

### Volume

Engine state lives under `ACESTREAM_HOME=/var/lib/acestream`:
`acestream.conf` (seeded from `/opt/acestream/acestream.conf` on first start),
`acestream.log`, `acestream_error.log`, `.device_id`, and `.ACEStream/`
(engine state including the disk cache). Mount a named volume there so the
cache and the engine identity survive container replacement:

```text
-v acestream-state:/var/lib/acestream
```

### Ports

- `6878/tcp`: engine HTTP API. The app reaches it in-container; publish it only if something outside the container needs it.
- `8621/tcp` and `8621/udp`: P2P port. Publish it for better peer connectivity.
- The engine is started with `--bind-all` (env `ACESTREAM_BIND_ALL`, default `true`, on every platform) so clients arriving through a published `6878` port are accepted whatever their address; without it the engine only admits loopback and RFC1918 sources and answers `Internal server error` to VPN/CGNAT (Tailscale) or Docker Desktop host clients. The engine API is unauthenticated: publish `6878` only on trusted networks, or set `ACESTREAM_BIND_ALL=false` to keep the engine's own address filter.
- `8000/tcp`: the app.

### Examples

```bash
docker run -d --name acestream-scraper \
  -p 8000:8000 -p 6878:6878 -p 8621:8621 -p 8621:8621/udp \
  -e ENABLE_ACESTREAM_ENGINE=true \
  -v "$PWD/config:/app/config" \
  -v acestream-state:/var/lib/acestream \
  pipepito/acestream-scraper:latest
```

Compose (the checked-in `docker-compose.yml` already sets the toggles to
`false`; flip the engine on and add the volume):

```yaml
services:
  app:
    image: pipepito/acestream-scraper:latest
    ports:
      - "8000:8000"
      - "6878:6878"
      - "8621:8621"
      - "8621:8621/udp"
    environment:
      - ENABLE_ACESTREAM_ENGINE=true
    volumes:
      - ./config:/app/config
      - acestream-state:/var/lib/acestream
volumes:
  acestream-state:
```

### Kernel page-size guard (Raspberry Pi 5)

The Android 9 bionic linker segfaults on kernels with 16 KB pages.
`start-engine` checks `getconf PAGESIZE` before launching and exits with

```text
start-engine: kernel page size is 16384, but the Android 9 bionic linker requires 4096 (Raspberry Pi 5: set kernel=kernel8.img in config.txt)
```

instead of crashing. Raspberry Pi OS 64-bit on the Pi 5 boots `kernel_2712`
(16 KB pages) by default: add `kernel=kernel8.img` to `/boot/firmware/config.txt`
and reboot. Check on the host with `getconf PAGESIZE` (must print `4096`). Pi 4
and earlier already use 4 KB pages.

### Health and status

- Container healthcheck (`healthcheck.sh`): with `ENABLE_ACESTREAM_ENGINE=true`
  it curls `http://${ACESTREAM_HTTP_HOST}:${ACESTREAM_HTTP_PORT}` in addition to
  `/api/v1/health`.
- Backend engine probe (`backend/app/services/acestream_status_service.py`):
  `/server/api?api_version=3&method=get_status` and
  `method=get_network_connection_status`. Both return 200 on the Android engine.
- Identify the running engine:

```bash
docker exec acestream-scraper curl -fsS "http://localhost:6878/webui/api/service?method=get_version"
# ARM:   {"result":{"platform":"android","version":"3.2.17"},"error":null}
# amd64: version 3.2.11 (Linux engine)
```

### Logs

- `docker logs <container>`: `entrypoint.sh` supervision messages plus the
  engine's `--log-stdout` output (the Linux bootstrap does not redirect it into
  a file, unlike the APK's `main.py`).
- `${ACESTREAM_HOME}/acestream.log`: bootstrap and engine log, rotated by the
  engine (`--log-max-size 15000000`, `--log-backup-count 1` from `acestream.conf`).
- `${ACESTREAM_HOME}/acestream_error.log`: tracebacks when the engine fails to
  start.
- `/opt/acestream/install-metadata.txt`: what the image installed (platform,
  kind, version, support level, engine and bionic sources).

## Known Gaps And Limitations

- Engine version skew: ARM64 and ARMv7 run 3.2.17, while amd64 runs 3.2.11;
  `get_version` reports `"platform":"android"` on ARM.
- No WebRTC transport on ARM: `pywebrtc` needs Android GPU/audio libraries that
  are not shipped. The engine logs a non-fatal error at startup and keeps
  working over the classic transports.
- A few CPython accelerator modules fall back to pure Python (slower,
  functionally equivalent).
- No WARP on linux/arm/v7 images (`cloudflare-warp` ships amd64 and arm64 only).
- `linux/arm/v7` is experimental: it builds and installs, but the 32-bit bionic
  engine calls `personality(PER_LINUX32)`, which qemu-user cannot honour, so it
  has never been executed in CI. It needs real ARMv7 (or AArch32-capable)
  hardware.
- 4 KB kernel pages are required (see the guard above).
- Performance and streaming stability on real ARM hardware are not validated.
  Expect the engine to be slower than on amd64.
- Licensing grey area (see above).
- Fork PRs are not built by Jenkins at all (see the fork PR policy in
  `docs/ops/jenkins-ci.md`), so they get no engine smoke.

## Testing On A Raspberry Pi

### arm64 (Raspberry Pi 4 / Pi 5 with a 64-bit OS, or any aarch64 Docker host)

Prerequisites: 64-bit OS, Docker with buildx, `getconf PAGESIZE` printing
`4096`, and for the automated smoke a checkout of the repository (the vendored
archives are in git) plus the backend virtualenv.

1. Automated smoke: the same test Jenkins runs; on an arm64 host it
   parametrizes `linux/arm64` as well as `linux/amd64` (the latter under QEMU):

   ```bash
   python3 -m venv backend/venv && backend/venv/bin/pip install -r backend/requirements.txt
   PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
   ```

   It builds `scraper-acestream` for the platform through
   `scripts/ci/build_multiarch_images.sh`, starts the container with
   `ENABLE_ACESTREAM_ENGINE=true`, waits for the app port, and asserts that
   `get_version` matches the manifest's `engine_version` and that `get_status`
   answers. Apple Silicon Docker Desktop counts as an arm64 host for this test.

2. Manual probe with a published image:

   ```bash
   docker run -d --name ace-test -p 8000:8000 -e ENABLE_ACESTREAM_ENGINE=true \
     -v acestream-state:/var/lib/acestream pipepito/acestream-scraper:scraper-acestream
   docker logs -f ace-test            # Ctrl-C once the engine has bound :6878 (a few seconds)
   docker exec ace-test uname -m      # aarch64
   docker exec ace-test curl -fsS "http://localhost:6878/webui/api/service?method=get_version"
   docker exec ace-test curl -fsS "http://localhost:6878/server/api?api_version=3&method=get_status"
   curl -fsS http://127.0.0.1:8000/api/v1/health
   docker rm -f ace-test
   ```

3. Streaming check (what CI cannot do): add a known-working channel in the UI,
   play it for at least 30 minutes, and watch `docker stats` and `docker logs`
   for stalls, engine restarts, or memory growth. Record the outcome in
   `docs/release/phase5-multiarch-evidence.md`.

### armv7 (32-bit hardware only)

Experimental. Same steps, but pull or build for `linux/arm/v7` explicitly:

```bash
docker run -d --name ace-test --platform linux/arm/v7 -p 8000:8000 \
  -e ENABLE_ACESTREAM_ENGINE=true -v acestream-state:/var/lib/acestream \
  pipepito/acestream-scraper:scraper-acestream
docker exec ace-test uname -m      # armv7l (or armv8l on an AArch32-capable 64-bit CPU)
```

Use real ARMv7 hardware or an AArch32-capable AArch64 board running a 32-bit
userland (Raspberry Pi 3/4 with 32-bit Raspberry Pi OS). It will not work under
QEMU. Please record the outcome (engine version reported, memory footprint,
playback stability) in an issue so the support level can be promoted from
`experimental`.

### Building locally on the Pi

```bash
PLATFORM=linux/arm/v7
TAG=armv7-local
bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms "$PLATFORM" --load --tag "acestream-scraper:$TAG"
```

Set `PLATFORM=linux/arm64` and `TAG=arm64-local` for a 64-bit build. `--load`
requires a single platform. ARM builds pull the pinned jopsis source image, so
a cold builder needs Docker Hub access.

## Updating The Pins

The full procedure lives in `docs/ops/multiarch-manifest-updates.md` and
`docker/vendor/acestream/README.md`. In short:

1. For amd64 archives, download and vendor the new tarball and regenerate
   `SHA256SUMS`. For ARM, verify that the selected jopsis tag publishes both
   `linux/arm64` and `linux/arm/v7`, then record its multi-platform digest.
2. Update `docker/manifests/acestream.json`: archive fields for amd64, or
   `image_ref`, `image_digest`, attribution, and `engine_version` for each ARM entry.
3. Publish conventional archive files as a GitHub Release when their mirrors change.
4. Validate: `python3 scripts/ci/validate_docker_manifest_metadata.py` and
   `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker`.
5. Runtime-test on arm64 hardware (section above) before promoting a new ARM
   engine to `support: stable`; keep `linux/arm/v7` at `experimental` until it
   has run on real hardware.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `AceStream is enabled but not installed in this image flavor` | The container runs `scraper` or `scraper-acexy`; switch to an engine flavor. |
| `start-engine: bionic runtime missing at /system` | The image was built without an ARM engine payload (for example with `ACESTREAM_SOURCE=fixture`); rebuild in the default auto mode. |
| `start-engine: kernel page size is 16384 ...` | 16 KB-page kernel; set `kernel=kernel8.img` in `config.txt` (Pi 5) and reboot. |
| Engine never answers on `:6878` | Check `docker logs` and `${ACESTREAM_HOME}/acestream_error.log`; confirm the container architecture with `docker exec <name> uname -m`; on armv7 hardware expect experimental results. |
| WebRTC error in the engine log | Expected on ARM; non-fatal. |
| Acexy refuses to start | `ENABLE_ACEXY=true` needs `ENABLE_ACESTREAM_ENGINE=true`, or an external `ACEXY_HOST:ACEXY_PORT` other than `localhost:6878`. |
