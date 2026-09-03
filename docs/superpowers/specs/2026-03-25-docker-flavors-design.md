# Docker Flavor And Multi-Arch Packaging Design

## Goal

Split the current all-in-one container packaging into clear tag-based Docker flavors under `pipepito/acestream-scraper` while preserving the existing env-driven runtime behavior, keeping Cloudflare WARP available in every flavor, retaining ZeroNet support where practical, and allowing AceStream architecture support to be extended later through committed metadata files instead of Dockerfile rewrites.

## Current Problems

- The current Docker packaging mixes scraper app, WARP, ZeroNet, AceStream, and Acexy into one x86-oriented image.
- AceStream download details are hardcoded in the Dockerfile.
- Acexy installation is bundled into the same image rather than exposed as an explicit flavor choice.
- Release automation assumes one canonical image and one platform matrix.
- It is hard to add or remove platform support for AceStream without editing Docker build logic directly.

## Chosen Approach

Use one canonical multi-stage Dockerfile with named build targets and publish multiple tags from the same repository:

- `latest` = full image
- `scraper`
- `scraper-acestream`
- `scraper-acexy`
- `scraper-acestream-acexy`

The image tag determines which optional binaries are installed. Environment variables determine which installed services are actually started at runtime.

## Source Of Truth Files

This phase should introduce and standardize the following committed metadata files:

- `docker/manifests/platforms.json` - baseline build matrix and per-flavor platform rules
- `docker/manifests/acestream.json` - AceStream version, URL, checksum, and per-platform install metadata
- `docker/manifests/acexy.json` - Acexy source repository and pinned release/ref metadata

These file locations are part of the design and should not be treated as placeholders.

## Image Flavor Model

### Tags

Publish all images under the existing Docker Hub repository:

- `pipepito/acestream-scraper:latest`
- `pipepito/acestream-scraper:scraper`
- `pipepito/acestream-scraper:scraper-acestream`
- `pipepito/acestream-scraper:scraper-acexy`
- `pipepito/acestream-scraper:scraper-acestream-acexy`

Versioned equivalents should also be published for each flavor, for example:

- `pipepito/acestream-scraper:<version>` for the same payload as `latest`
- `pipepito/acestream-scraper:<version>-scraper`
- `pipepito/acestream-scraper:<version>-scraper-acestream`
- `pipepito/acestream-scraper:<version>-scraper-acexy`
- `pipepito/acestream-scraper:<version>-scraper-acestream-acexy`

### Tag Semantics

- `latest` is the same payload as `scraper-acestream-acexy`
- bare `<version>` is the same payload as `<version>-scraper-acestream-acexy`
- because the full image includes AceStream, `latest` and bare `<version>` are only published for platforms supported by the AceStream manifest
- unsupported platforms must use explicit flavor tags that do not require AceStream, such as `scraper` or `<version>-scraper-acexy`

### Flavor Responsibilities

- `scraper`: app runtime, WARP support, and shared scraper dependencies only
- `scraper-acestream`: `scraper` plus AceStream
- `scraper-acexy`: `scraper` plus Acexy
- `scraper-acestream-acexy`: `scraper` plus AceStream plus Acexy
- `latest`: alias of `scraper-acestream-acexy`

## Runtime Contract

### Environment-Driven Startup

Preserve the current startup philosophy from the existing `entrypoint.sh`:

- installation determines which binaries are available in the image
- environment variables determine which installed services are started
- optional runtime features remain disabled unless explicitly enabled

Key runtime flags remain:

- `ENABLE_WARP`
- `ENABLE_ACESTREAM_ENGINE`
- `ENABLE_ACEXY`
- `ACEXY_HOST`
- `ACEXY_PORT`
- `ACESTREAM_HTTP_HOST`
- `ACESTREAM_HTTP_PORT`
- `ZERONET_URL`
- related connection and port variables already used today

`ACESTREAM_HTTP_HOST` and `ACESTREAM_HTTP_PORT` remain the canonical variables for the in-container AceStream engine endpoint. `ACEXY_HOST` and `ACEXY_PORT` remain the canonical variables for where Acexy connects. The startup script may continue normalizing legacy convenience defaults, but this phase should not invent a second competing endpoint contract.

### Canonical Runtime Scripts

This phase should restore and standardize the root-level runtime scripts used by the image build:

- `entrypoint.sh`
- `warp-setup.sh`
- `healthcheck.sh`

`entrypoint.sh` becomes the canonical startup contract for all Docker flavors.

### Startup Order

The canonical startup sequence is:

1. create log directories and log rotation config
2. initialize WARP if `ENABLE_WARP=true`
3. normalize dependent env vars such as `ENABLE_ACESTREAM_ENGINE` and `ACESTREAM_HTTP_HOST`
4. validate requested optional services against what is installed in the selected flavor
5. prepare ZeroNet compatibility config
6. start optional services in dependency order
7. start the application server
8. monitor child processes and terminate cleanly on signal

The image should continue to behave as one container that can host multiple optional helper services when those helpers are installed in the selected flavor.

### Runtime Validation Rules

Startup must fail fast with a clear message when a requested optional service is not installed in the selected flavor.

Required checks:

- if `ENABLE_ACESTREAM_ENGINE=true` and the image does not include AceStream, exit clearly
- if `ENABLE_ACEXY=true` and the image does not include Acexy, exit clearly
- if `ENABLE_ACEXY=true` and `ENABLE_ACESTREAM_ENGINE=false`, require external engine settings instead of the in-container defaults
- keep the current validation that rejects Acexy startup against `localhost:6878` when AceStream is disabled and no external engine host/port is provided

### Acexy Runtime Contract

Acexy must support two valid operating modes:

1. bundled-engine mode
   - image flavor includes Acexy
   - `ENABLE_ACEXY=true`
   - `ENABLE_ACESTREAM_ENGINE=true`
   - Acexy talks to the locally installed in-container AceStream engine

2. external-engine mode
   - image flavor includes Acexy
   - `ENABLE_ACEXY=true`
   - `ENABLE_ACESTREAM_ENGINE=false`
   - `ACEXY_HOST` and `ACEXY_PORT` point to an external AceStream engine

Invalid mode:

- `ENABLE_ACEXY=true`
- `ENABLE_ACESTREAM_ENGINE=false`
- `ACEXY_HOST=localhost`
- `ACEXY_PORT=6878`

This combination must exit with a clear configuration error because it asks Acexy to use a local engine that is explicitly disabled.

## Shared Runtime Base

All published flavors should include:

- the scraper app backend/frontend runtime
- Cloudflare WARP tooling and its startup script support
- shared system dependencies needed by the app
- support for current scraper behaviors that still rely on ZeroNet flows through a compatible external ZeroNet endpoint contract

ZeroNet should not become a separate flavor in this phase.

## ZeroNet Model

For this phase, ZeroNet remains an optional external sidecar/service, not a bundled runtime inside every image.

Rules:

- the scraper app must preserve compatibility with ZeroNet scraping flows
- images must keep the configuration and client-side compatibility needed to talk to a ZeroNet endpoint via `ZERONET_URL`
- local compose examples may continue to run a separate ZeroNet service
- this phase does not require bundling a ZeroNet node inside every flavor

## WARP

WARP is baseline in every flavor because it is needed for connectivity to sources that may be blocked or fail DNS resolution under the host provider.

Rules:

- every runtime flavor installs WARP support
- `ENABLE_WARP` still controls whether WARP is started
- docs must continue to state the required runtime capabilities for WARP-enabled containers, such as `NET_ADMIN` and `SYS_ADMIN`

### WARP Failure Semantics

- if `ENABLE_WARP=false`, WARP setup is skipped and health checks must not fail because WARP is absent
- if `ENABLE_WARP=true` but the required container capabilities or runtime prerequisites are missing, startup must fail fast with a clear message
- health checks do not need to perform deep WARP tunnel validation, but they must not report success for a process that already failed during required WARP startup

## AceStream Metadata

### Manifest-Driven Install Source

AceStream download information must move out of the Dockerfile and into the committed metadata file `docker/manifests/acestream.json`.

The manifest should map each Docker platform to install metadata such as:

- platform identifier, e.g. `linux/amd64`, `linux/arm64`
- human-readable version label
- download URL
- optional checksum
- optional extraction or install hints if different archives require them later

Minimum schema fields:

- top-level `version`
- top-level `platforms`
- per-platform `url`
- per-platform `sha256` or explicit empty value when unavailable
- per-platform `archive_type` or equivalent install hint if needed

### Platform Support Rules

- `scraper` and `scraper-acexy` are built on the baseline multi-arch matrix
- `scraper-acestream` and `scraper-acestream-acexy` are built only for platforms present in the AceStream manifest
- adding support for a new AceStream architecture later should only require a manifest update if the installer shape is compatible *(superseded on 2026-08-27: the installer shape was **not** compatible for ARM — see the addendum below)*

### Addendum (2026-08-27): `android-apk` install kind for ARM

The "manifest update only" assumption above did not hold. Upstream publishes native Linux engine tarballs only for x86_64 (3.2.11); there is no ARM tarball for a manifest entry to point at. ARM support therefore needed a second installer shape, implemented on branch `arm-acestream-engine`:

- `linux/arm64` and `linux/arm/v7` use the official Android engine APKs from https://docs.acestream.media/products/ (`AceStreamCore-3.1.80.0-armv8_64.apk`, `AceStreamCore-3.1.80.0-armv7.apk`). The APK's engine payload (python-for-android CPython 3.8 + compiled engine modules) is unzipped to `/opt/acestream` and runs unmodified against a minimal Android 9 bionic userland copied to `/system` (`linker64`/`linker`, `libc`/`libdl`/`libm`/`libz`/`liblog`/`libc++`, plus a `libstdc++.so -> libc++.so` symlink) taken from the Termux package `aosp-libs 9.0.0-r76-4` (built from AOSP source; BSD/Apache-2.0 etc.; NOTICE files shipped under `/system/etc/NOTICE-aosp-libs`). No chroot, no `--privileged`, no seccomp changes and no extra capabilities are needed (verified on arm64).
- `linux/amd64` is unchanged: install kind `executable`, 3.2.11 tarball.
- Schema as implemented (validated by `scripts/ci/validate_docker_manifest_metadata.py`): top-level `version` (amd64 engine), `android_version`, `vendor_dir`, `mirror_base_url`, and `platforms{<platform>: {engine_version, support (stable|experimental), url, sha256, archive_type (tar.gz|apk), vendored_file, mirror_urls[], install{kind, engine_http_port, ...}}}`. `executable` installs add `strip_components` and `binary_path`; `android-apk` installs add `abi` (`arm64-v8a`|`armeabi-v7a`) and `bionic{package, url, sha256, vendor_dir, vendored_file, mirror_urls[], libdir (lib64|lib), linker (linker64|linker)}`.
- Support levels: `linux/arm64` is `stable` (engine verified: HTTP API answers within ~5 s, RSS ~95 MB idle; `/webui/api/service?method=get_version` returns `{"platform":"android","version":"3.1.80"}`). `linux/arm/v7` is `experimental`: it builds and installs but cannot be executed under qemu-user (32-bit bionic calls `personality(PER_LINUX32)`), so it needs real ARMv7/AArch32-capable hardware and has not been runtime-tested. The engine stays opt-in (`ENABLE_ACESTREAM_ENGINE=false` by default), so the app itself is unaffected.
- Consequence for Tag Semantics: `latest`, bare `<version>`, `scraper-acestream` and `scraper-acestream-acexy` are now published for `linux/amd64`, `linux/arm64` and `linux/arm/v7` (`scripts/ci/flavor_platforms.py` resolves this automatically).
- Install source: every engine archive and the bionic `.deb`s are vendored in `docker/vendor/acestream/` and `docker/vendor/bionic/` (each with `SHA256SUMS`), with identical copies published as GitHub Release assets at https://github.com/Pipepito/acestream-scraper/releases/tag/acestream-binaries-3.2.11-3.1.80.0. `docker/scripts/install-acestream.sh` resolves vendored copy → upstream `url` → `mirror_urls`, sha256-verified, so builds no longer need WARP/egress to download.acestream.media. Manual-by-manifest (Update Strategy below) still holds; bumping a pin is documented in `docker/vendor/acestream/README.md`.
- Build plumbing: the `acestream-installer` stage takes `ARG TARGETPLATFORM` and `ARG ACESTREAM_SOURCE=auto|explicit|fixture`; `docker/vendor` is bind-mounted into the stage rather than copied into a layer; `docker/scripts/acestream_manifest.py` is the shared resolver (also used by `scripts/ci/derive_acestream_build_args.py`). `scripts/ci/build_multiarch_images.sh` no longer injects global `ACESTREAM_*` build-args, because they would apply one engine to every platform of a multi-platform build; explicit `--build-arg ACESTREAM_*` still override. `ACESTREAM_SOURCE=fixture` builds the contract-test fixture (previously: omitting the URL).
- Runtime on ARM: `/opt/acestream/start-engine` (`docker/scripts/acestream-android/start-engine`) sets `ANDROID_ROOT=/system` plus the Python/linker environment, checks `getconf PAGESIZE == 4096` (the Android 9 bionic linker segfaults on 16 KB-page kernels — Raspberry Pi 5 needs `kernel=kernel8.img` in `config.txt`), seeds `ACESTREAM_HOME/acestream.conf`, and execs the bionic python. Engine state/cache/logs live in `ACESTREAM_HOME=/var/lib/acestream` (recommend `-v acestream-state:/var/lib/acestream`). `ACESTREAM_START_COMMAND` is unchanged for all platforms; ports and the backend health calls (`get_status`, `get_network_connection_status`) work the same.
- Known ARM limitations: engine version skew (3.2.17 on ARM64 and 3.1.80 on ARMv7 vs 3.2.11 on amd64; `platform` reports `android`); no WebRTC transport (pywebrtc needs Android GPU/audio libs; non-fatal engine error); a few CPython accelerator modules fall back to pure Python; no WARP on ARMv7 (Cloudflare publishes amd64 and arm64 packages only); performance/streaming stability not validated on real hardware; repackaging the APK is a licensing grey area shared by every community ARM image. See also `docs/release/arm-acestream-issue-draft.md`.
- Tests: `backend/tests/docker/` (`test_acestream_manifest.py`, `test_derive_args.py`, `test_install_acestream.py`, `test_acestream_runtime_smoke.py`) — run with `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker` — and `python3 scripts/ci/validate_docker_manifest_metadata.py` (also checks vendored files, `SHA256SUMS` and mirror URLs).

### Update Strategy

AceStream availability is intentionally manual-by-manifest. The repository owner controls when a new version or architecture becomes buildable by updating the committed metadata file.

## Acexy Metadata

### Repo-Pinned Manifest

Acexy should also stop being implicitly built from a floating head. Use the committed metadata file `docker/manifests/acexy.json` as the source of truth.

The manifest should include:

- repository URL
- pinned release, tag, or ref
- optional checksum or expected version string if useful for validation later

Minimum schema fields:

- `repo`
- `ref`
- `version`
- optional `expected_binary_name`

### Refresh Workflow

The build stays reproducible because the Docker build reads from the committed Acexy manifest. A helper script or workflow may later refresh that manifest to the latest GitHub release in a reviewable change, but the release pipeline itself should not silently discover a new version at build time.

## Dockerfile Design

Use one readable multi-stage Dockerfile with named targets.

Recommended structure:

- shared base stages for frontend and Python app assembly
- shared runtime base stage that installs WARP and common runtime dependencies
- optional installer stages for AceStream and Acexy
- final named targets for each published flavor

Named final targets should map directly to the published flavors:

- `scraper`
- `scraper-acestream`
- `scraper-acexy`
- `scraper-acestream-acexy`

The Dockerfile should remain readable enough that a human can follow it directly without a generator.

## Build And Release Orchestration

### Build Script Evolution

Extend the existing `scripts/ci/build_multiarch_images.sh` script so builds can be flavor-aware.

The orchestration layer should support:

- target/flavor name
- tag list
- per-flavor platform matrix
- manifest metadata inputs
- dry-run reporting that records which platforms were selected for each flavor

### Release Workflow

The release pipeline should build and publish all required tags instead of a single canonical image.

Release logic should:

- publish `latest` as the full flavor
- publish each explicit flavor tag
- publish versioned equivalents for each flavor
- use flavor-specific platform lists derived from the metadata files

### Version And Tag Source Of Truth

- `version.txt` remains the release version source of truth for versioned image tags in this phase
- PR and SHA builds may continue to use commit-based tags for validation, but they must become flavor-aware
- the current temporary `pipepito/acestream-scraper-v2` release target should be cut over to `pipepito/acestream-scraper` as part of this work

Required tag sets:

- PR/dry-run validation: flavor-aware ephemeral tags or cache-only outputs
- main/release build: `latest`, bare `<version>`, and explicit flavor tags with versioned equivalents

## Validation And Guardrails

### CI Checks

Validation should become flavor-aware instead of assuming one universal architecture matrix.

Required checks:

- dry-run build matrix validation for each flavor
- manifest verification for each flavor's required platform list
- early failure when an AceStream flavor is requested for a platform not present in the AceStream manifest

`docker/manifests/platforms.json` should define the baseline matrix explicitly instead of leaving it hardcoded inside shell defaults.

### Smoke Expectations

Smoke coverage should prove:

- `scraper` builds on the full baseline multi-arch matrix
- `scraper-acexy` builds on the baseline matrix if the Go build remains portable
- AceStream flavors only advertise platforms explicitly present in the AceStream manifest
- startup fails clearly when runtime env vars request binaries missing from the selected flavor
- full flavor still boots with optional services disabled by default

### Health Check Rules

- app health remains required in every flavor
- disabled optional services must not cause health check failures
- `scraper-acexy` and full flavors should only perform Acexy health checks when `ENABLE_ACEXY=true`
- if Acexy is enabled in external-engine mode, health checks should validate Acexy itself and only validate external engine reachability through the explicit external host/port contract

## Compose And Documentation Impact

- `docker-compose.yml` should be updated to point at the intended default image/tag behavior for local container usage
- Docker documentation should explain the flavor matrix and the meaning of `latest`
- docs should make clear that WARP is present in all flavors but still optional at runtime
- docs should explain that AceStream architecture support is controlled through the committed manifest file

## Non-Goals

- separate Docker repositories per flavor
- generating Dockerfiles from templates in this phase
- automatic AceStream latest-version discovery during release builds
- splitting ZeroNet into its own Docker flavor in this phase
