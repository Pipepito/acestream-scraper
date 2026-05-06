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

That means `latest` is not a universal multi-arch alias. Its availability follows the AceStream manifest because it is the same payload as `scraper-acestream-acexy`.

Required minimum compatibility claims for release signoff:

- Baseline flavors (`scraper`, `scraper-acexy`) succeed for ARM v7 and ARM64 and are included in architecture validation outputs.
- AceStream-enabled flavors (`scraper-acestream`, `scraper-acestream-acexy`, `latest`) only need to succeed for the platforms allowed by `docker/manifests/acestream.json`.
- Runtime smoke checks pass for the ARM targets required by the flavor being signed off (`/api/v1/health`, frontend root path).

### Build and Validation Path

Use the canonical scripts:

```bash
# Build matrix (local dry-run checks)
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream

# Verify flavor-derived platform expectations
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-scraper.json --flavor scraper
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-scraper-acestream.json --flavor scraper-acestream

# Runtime smoke flow
bash scripts/ci/phase5_arch_smoke.sh --platforms linux/arm/v7,linux/arm64
```

CI orchestration:

- Jenkins multibranch PR validation is the canonical orchestration path and runs from the repository-root `Jenkinsfile`.
- Jenkins manual release publication is the canonical release path and runs from `jenkins/release.Jenkinsfile`.
- Jenkins validation is intended to mirror `.github/workflows/pull_request.yml`.
- Jenkins manual release is intended to mirror `.github/workflows/release.yml`.
- Jenkins pipelines target the `dorat-nuc-ci` label and call `scripts/ci/bootstrap_jenkins_runner.sh` after `checkout scm`.
- `git` remains the practical prerequisite on the Jenkins node because checkout happens before repository bootstrap.
- Jenkins uses the named buildx builder `acestream-builder` unless `JENKINS_BUILDER` is explicitly overridden; the builder can be precreated by the operator or prepared during bootstrap.
- Docker access must already work for the current Jenkins runtime user on that node.
- During the current transition and hardening period, the existing GitHub Actions workflows remain available as fallback/reference workflows.
- GitHub Actions workflows serve these secondary parity roles:
  - `.github/workflows/pull_request.yml` — parity PR validation, fires on every PR
  - `.github/workflows/release.yml` — manual `workflow_dispatch` release readiness check (validation only; never publishes to Docker Hub)
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
