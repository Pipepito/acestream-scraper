# Deployment Architecture

## Canonical Runtime Model

Acestream Scraper runs with root-owned application paths:

- `backend/` provides API, background tasks, scraper logic, and serves the built SPA.
- `frontend/` builds static assets consumed by backend runtime image.

## Containers

### Unified Image Build

Root `Dockerfile` is a multi-stage build with named flavor targets.

It assembles shared frontend and backend runtime layers once, then publishes these final targets:

- `scraper`
- `scraper-acestream`
- `scraper-acexy`
- `scraper-acestream-acexy`

`latest` is the same payload as `scraper-acestream-acexy`.

Runtime command:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Compose Stack

`docker-compose.yml` runs:

- `app`: includes both `build` and `image` for `pipepito/acestream-scraper:latest`, so Compose can either build from the local repository `Dockerfile` or tag the resulting image with the published name
- `zeronet`: optional ZeroNet sidecar at port `43110` when the `zeronet` profile is enabled

Bring up stack:

```bash
docker compose up -d
```

With the checked-in compose file, `docker compose up -d` uses the configured `build` plus `image` definition and will build locally when the app image is missing. If you want to force a fresh local rebuild from the current checkout, use:

```bash
docker compose up --build
```

If you want a prebuilt-image workflow instead of the checked-in local-build default, adjust the compose configuration to remove or override the `build` section and point at the published tag you want to run.

To include the example ZeroNet sidecar:

```bash
docker compose --profile zeronet up -d
```

When you use published images, `latest` is the same payload as `scraper-acestream-acexy`. Operators can also pin `scraper`, `scraper-acestream`, `scraper-acexy`, or `scraper-acestream-acexy` directly.

ZeroNet remains an external sidecar/service. The container image keeps the `ZERONET_URL` contract but does not bundle ZeroNet into every flavor.

The checked-in compose file points `ZERONET_URL` at `http://host.docker.internal:43110` by default so the app can run without the optional `zeronet` profile. The example `zeronet` service is pinned for amd64. ARM deployments should use an external ZeroNet endpoint or replace that sidecar while keeping `ZERONET_URL` unchanged.

## Environment Configuration

Primary backend settings:

- `DATABASE_URL`
- `LEGACY_DATABASE_URL`
- `ZERONET_URL`
- `CORS_ORIGINS`
- `FRONTEND_BUILD_PATH`
- `ACE_ENGINE_URL`

Docker runtime toggles:

- `ENABLE_WARP`
- `ENABLE_ACESTREAM_ENGINE`
- `ENABLE_ACEXY`
- `ACESTREAM_HTTP_HOST`
- `ACESTREAM_HTTP_PORT`
- `ACEXY_HOST`
- `ACEXY_PORT`

The selected image flavor controls which optional binaries are installed. Runtime env flags control whether those installed services start.

WARP is installed in every flavor, but it only starts when `ENABLE_WARP=true`. For the documented containerized runtime path in this repository, WARP-enabled containers require the runtime capabilities `NET_ADMIN` and `SYS_ADMIN`.

Legacy env aliases remain supported for one release window (`v2-cutover-r1`) with canonical-variable precedence and conflict warnings.

## Multi-Architecture Direction

### Supported Image Targets

Baseline flavors without AceStream use the manifest-defined baseline matrix:

- `scraper`
- `scraper-acexy`

AceStream-enabled flavors are manifest-gated and only publish for platforms listed in `docker/manifests/acestream.json`:

- `scraper-acestream`
- `scraper-acestream-acexy`
- `latest`

That means `latest` is not a universal multi-arch alias. Its availability follows the AceStream manifest because it is the same payload as `scraper-acestream-acexy`. (Superseded on 2026-08-27: the manifest now lists every baseline platform, so `latest` currently resolves to `linux/amd64,linux/arm/v7,linux/arm64` — but the gating rule stands, and dropping a platform from the manifest drops it from `latest` again.)

The manifest currently pins, per platform (`platforms.<platform>` entries with `engine_version`, `support`, `url`, `sha256`, `archive_type`, `vendored_file`, `mirror_urls[]`, and `install{kind, ...}`):

- `linux/amd64` — `support: stable`; install kind `executable`; upstream native Linux engine 3.2.11 tarball (unchanged).
- `linux/arm64` — `support: stable`; install kind `android-apk` (`abi: arm64-v8a`); the official Android engine `AceStreamCore-3.1.80.0-armv8_64.apk` unpacked to `/opt/acestream` and run unmodified against a minimal Android 9 bionic userland copied to `/system` (`linker64` + `libc/libdl/libm/libz/liblog/libc++`, from the Termux `aosp-libs 9.0.0-r76-4` package; NOTICE files under `/system/etc/NOTICE-aosp-libs`). Verified: the HTTP API answers within ~5 s, RSS ~95 MB idle.
- `linux/arm/v7` — `support: experimental`; install kind `android-apk` (`abi: armeabi-v7a`); same layout with the `armv7` APK and 32-bit bionic (`linker`, `lib`). Builds and installs, but the 32-bit bionic engine cannot run under qemu-user (it calls `personality(PER_LINUX32)`), so it has not been runtime-tested on real ARMv7 hardware.

Every pinned engine archive and bionic `.deb` is vendored in-repo (`docker/vendor/acestream/`, `docker/vendor/bionic/`, each with a `SHA256SUMS`) and mirrored as GitHub Release assets (`mirror_urls`, currently the `acestream-binaries-3.2.11-3.1.80.0` release). `docker/scripts/install-acestream.sh` resolves vendored copy -> upstream `url` -> `mirror_urls`, sha256-verified, so builds no longer need WARP/egress to `download.acestream.media`. `docker/scripts/acestream_manifest.py` is the shared resolver (also used by `scripts/ci/derive_acestream_build_args.py`); `scripts/ci/build_multiarch_images.sh` validates each resolved platform and prints an `AceStream engine for <platform>: kind=... version=... support=... source=vendored ...` line instead of injecting global `ACESTREAM_*` build-args (which would apply one engine to every platform of a multi-platform build). `ACESTREAM_SOURCE=fixture` builds the contract-test fixture. Pin updates follow `docker/vendor/acestream/README.md`.

Required minimum compatibility claims for release signoff:

- Baseline flavors (`scraper`, `scraper-acexy`) succeed for ARM v7 and ARM64 and are included in architecture validation outputs.
- AceStream-enabled flavors (`scraper-acestream`, `scraper-acestream-acexy`, `latest`) only need to succeed for the platforms allowed by `docker/manifests/acestream.json`.
- Runtime smoke checks pass for the ARM targets required by the flavor being signed off (`/api/v1/health`, frontend root path).
- AceStream engine flavors (since 2026-08-27): the installer stage must build cleanly for `linux/arm64` and `linux/arm/v7` under QEMU (`backend/tests/docker/test_install_acestream.py -k android_apk_install_layout`, no engine execution), and the real engine must start and answer its HTTP API on `linux/amd64` (`backend/tests/docker/test_acestream_runtime_smoke.py`, always) and on `linux/arm64` (same test, parametrized; only runs when the host is arm64). `linux/arm/v7` is signed off as build-only while its manifest `support` is `experimental`. `scripts/ci/validate_docker_manifest_metadata.py` must pass (manifest schema, vendored files, `SHA256SUMS`, mirror URLs).

### Build and Validation Path

Use the canonical scripts:

```bash
# Build matrix (local dry-run checks)
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream

# Verify flavor-derived platform expectations
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-scraper.json --flavor scraper
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-scraper-acestream.json --flavor scraper-acestream

# Runtime smoke flow (baseline app image; the Android engine payload cannot
# execute under qemu-user, so engine-flavor runtime smoke runs on real hosts)
bash scripts/ci/phase5_arch_smoke.sh --platforms linux/arm/v7,linux/arm64

# AceStream manifest + vendored archive consistency
python3 scripts/ci/validate_docker_manifest_metadata.py

# AceStream engine: ARM installer layout (QEMU build, no engine execution) and
# real-engine runtime smoke (amd64 always; arm64 when run on an arm64 host)
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -k android_apk_install_layout
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py
```

CI orchestration:

- Jenkins multibranch PR validation is the canonical orchestration path and runs from the repository-root `Jenkinsfile`.
- Jenkins manual release publication is the canonical release path and runs from `jenkins/release.Jenkinsfile`.
- Jenkins validation (`Jenkinsfile`) is the sole PR gate; Jenkins manual release (`jenkins/release.Jenkinsfile`) is the sole publisher.
- Jenkins pipelines target the `dorat-nuc-ci` label and call `scripts/ci/bootstrap_jenkins_runner.sh` after `checkout scm`.
- `git` remains the practical prerequisite on the Jenkins node because checkout happens before repository bootstrap.
- Jenkins uses the named buildx builder `acestream-builder` unless `JENKINS_BUILDER` is explicitly overridden; the builder can be precreated by the operator or prepared during bootstrap.
- The PR job's `Acestream Engine Runtime Smoke` stage builds `scraper-acestream` pinned to `--platforms linux/amd64 --load` (the runner `dorat-nuc-ci` is amd64; `--load` needs a single platform) with `BUILDX_BUILDER=default --network host`, then runs `test_acestream_runtime_smoke.py` plus `test_install_acestream.py -k android_apk_install_layout`. `scripts/ci/run_jenkins_release.sh` repeats the same checks before pushing the multi-platform manifests, so the published `scraper-acestream`, `scraper-acestream-acexy`, `latest`, and version tags include `linux/arm64` and `linux/arm/v7`.
- Docker access must already work for the current Jenkins runtime user on that node.
- During the current transition and hardening period, the existing GitHub Actions workflows remain available as fallback/reference workflows. (Superseded 2026-08-26, commit e5657b9: all GitHub Actions workflows are retired.)
- GitHub Actions workflows serve these secondary parity roles: (superseded 2026-08-26, commit e5657b9 — none remain)
  - (GitHub Actions workflows are retired — all validation and publishing runs on Jenkins)
  The phase-specific scaffolding workflows (`phase1-safety-gates.yml`, `cutover-validation.yml`, `multiarch-validation.yml`) were retired once their gate runners landed in the canonical PR + release pipelines.
- `scripts/phase_gates/phase5_gate_runner.py` (`quick` and `full` profiles) remains a canonical script-level entrypoint used by CI flows.

### Android TV Notes

Android TV deployments should prefer `linux/arm64` when device firmware supports 64-bit containers.  
`linux/arm/v7` remains supported for older ARM32 devices but may need conservative runtime settings.

Recommended operator caveats:

- Prefer reduced background concurrency on lower-memory ARMv7 devices.
- Validate storage I/O performance for SQLite-backed deployments on removable media.
- Run the Phase 5 smoke checklist before production rollouts on new device classes.

See: `docs/migration/phase5-architecture-smoke-checklist.md`

### ARM AceStream Engine Notes

The in-container engine is opt-in on every platform (`ENABLE_ACESTREAM_ENGINE=false` by default), so the app itself is unaffected by the ARM engine work. `ACESTREAM_START_COMMAND` is unchanged for all platforms; on ARM `/opt/acestream/start-engine` (`docker/scripts/acestream-android/start-engine`) is the Linux launcher for the Android payload.

Runtime layout on ARM:

- `/opt/acestream`: the APK's engine payload (python-for-android CPython 3.8 + compiled engine modules) plus `main_linux.py` (a Linux copy of the APK bootstrap that keeps `--log-stdout` output in `docker logs`) and `app_bridge.py` (a fake Android RPC host answering device-id, `statvfs`, and meminfo queries).
- `/system`: the minimal Android 9 bionic userland (`bin/linker64` or `bin/linker`, `lib64/` or `lib/`, `etc/NOTICE-aosp-libs`). `start-engine` sets `ANDROID_ROOT=/system`, `PYTHONHOME`, `PYTHONPATH`, and `LD_LIBRARY_PATH`, then execs the bionic python with `main_linux.py`.
- `/var/lib/acestream` (`ACESTREAM_HOME`): `acestream.conf` (seeded on first start), `acestream.log`, `acestream_error.log`, `.device_id` (persistent per-install device id), and `.ACEStream/` state including the disk cache. Recommend a volume: `-v acestream-state:/var/lib/acestream`.
- Ports: `6878` HTTP API, `8621` tcp/udp P2P. Health: the backend calls `/server/api?api_version=3&method=get_status` and `get_network_connection_status` (both return 200 on the Android engine); `/webui/api/service?method=get_version` returns `{"platform":"android","version":"3.1.80"}`.

Operator caveats specific to the ARM engine:

- Kernel page size must be 4096. `start-engine` checks `getconf PAGESIZE` and exits with an explicit error otherwise, because the Android 9 bionic linker segfaults on 16 KB-page kernels. Raspberry Pi 5 defaults to the 64-bit `kernel_2712` (16 KB pages): set `kernel=kernel8.img` in `config.txt`.
- `linux/arm/v7` is experimental: build-tested only, never executed on real ARMv7/AArch32 hardware.
- Engine version skew: 3.1.80 on ARM vs 3.2.11 on amd64, and the platform reports `android`.
- No WebRTC transport on ARM (pywebrtc needs Android GPU/audio libraries; the engine logs a non-fatal error). A few CPython accelerator modules fall back to pure Python.
- No WARP on ARM images (`cloudflare-warp` is amd64-only; pre-existing limitation).
- Performance and streaming stability are not yet validated on real ARM hardware.
- Repackaging the official APK payload sits in a grey area under the AceStream user agreement's redistribution terms, shared by every community ARM image.
