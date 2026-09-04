# Phase 5 Architecture Smoke Checklist

Use this checklist to validate runtime behavior for supported architecture targets.

The Quick/Full profiles and the manual probe below exercise the app (the `scraper` target: `/api/v1/health` and the frontend root). The in-container AceStream engine has its own section, `## AceStream Engine Smoke (ARM)`, because it cannot be exercised under QEMU.

## Scope

Required targets:

- `linux/arm/v7`
- `linux/arm64`

Optional baseline:

- `linux/amd64`

## Quick CI Profile

Run in CI-friendly mode:

```bash
python3 scripts/phase_gates/phase5_gate_runner.py --profile quick --json-output > phase5-gate-report-quick.json
```

Expected:

- Multi-arch build command validates target matrix.
- Required architecture matrix entries are asserted.
- Runtime smoke plan shape validates in dry-run mode.

## Full Validation Profile

Run full architecture validation:

```bash
python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output > phase5-gate-report-full.json
```

Expected:

- Buildx executes multi-arch build matrix (every flavor for every platform, including the ARM engine installer stages under QEMU).
- Required arch entries are validated.
- Runtime smoke script executes endpoint checks for required targets. It boots the app-only `scraper` target (`phase5_arch_smoke.sh` default `--target scraper`); the engine is not started.

## Manual Runtime Probe (Per Target)

If additional manual confidence is needed:

1. Build platform image (`--target scraper` matches what the smoke script boots; without it buildx builds the final `scraper-acestream-acexy` stage, which since 2026-08-27 also installs the Android engine for ARM and takes longer):
   ```bash
   docker buildx build --platform linux/arm64 --target scraper -t acestream-scraper-smoke:arm64 --load .
   ```
2. Run container:
   ```bash
   docker run --rm -d -p 18080:8000 --name phase5-smoke-arm64 acestream-scraper-smoke:arm64
   ```
3. Validate health and frontend root:
   ```bash
   curl -fsS http://127.0.0.1:18080/api/v1/health
   curl -fsS http://127.0.0.1:18080/
   ```
4. Stop container:
   ```bash
   docker rm -f phase5-smoke-arm64
   ```

Repeat for `linux/arm/v7`.

## AceStream Engine Smoke (ARM)

The engine flavors (`scraper-acestream`, `scraper-acestream-acexy`, `latest`) build for `linux/arm64` and `linux/arm/v7`. Both use the matching 3.2.17 platform variant from digest-pinned `jopsis/acestream:v3.2.17-fix`; the ARMv7 bionic payload still cannot execute under qemu-user, so its engine runtime check needs real ARMv7 hardware. Operator guide: `docs/ops/acestream-arm-engine.md`. Record results in `docs/release/phase5-multiarch-evidence.md`.

### On any host (build-level, QEMU)

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k arm_oci_image_install_layout
```

Expected:

- The arm64 and armv7 `acestream-installer` stages build from the vendored APKs and bionic `.deb`s under `docker/vendor/` (no network).
- `/opt/acestream/install-metadata.txt` reports `kind=oci-image`, engine 3.2.17, and the pinned jopsis image reference and digest.
- The staged `/system` tree contains the bionic linker and libraries.

This is what the Jenkins PR and release jobs run for ARM; it proves the install, not the engine.

### On an arm64 host (runtime) — required for `linux/arm64` signoff

Host: Raspberry Pi 4/5 with a 64-bit OS (Pi 5: `kernel=kernel8.img` in `config.txt`; `getconf PAGESIZE` must print `4096`) or any aarch64 Docker host.

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
```

The test parametrizes `linux/arm64` automatically on arm64 hosts. Expected:

- `scraper-acestream` builds for `linux/arm64` through `scripts/ci/build_multiarch_images.sh`.
- With `ENABLE_ACESTREAM_ENGINE=true` the app opens `:8000` and the engine answers `http://localhost:6878/webui/api/service?method=get_version` with `{"platform":"android","version":"3.2.17"}` (matching the manifest's `engine_version`).
- `/server/api?api_version=3&method=get_status` returns 200 (the backend's health probe).

Manual equivalent with a published image:

```bash
docker run --rm -d -p 18080:8000 -e ENABLE_ACESTREAM_ENGINE=true --name phase5-engine-arm64 pipepito/acestream-scraper:scraper-acestream
docker exec phase5-engine-arm64 curl -fsS "http://localhost:6878/webui/api/service?method=get_version"
docker exec phase5-engine-arm64 curl -fsS "http://localhost:6878/server/api?api_version=3&method=get_status"
curl -fsS http://127.0.0.1:18080/api/v1/health
docker rm -f phase5-engine-arm64
```

Then play a known-working channel for 30 minutes and watch `docker stats` / `docker logs` for stalls or restarts; CI cannot cover streaming stability.

### On ARMv7 hardware — required before promoting `linux/arm/v7`

`linux/arm/v7` is `support: experimental` in `docker/manifests/acestream.json`: it builds and installs but has never been executed (the 32-bit bionic engine calls `personality(PER_LINUX32)`, which qemu-user cannot honour). Run the manual probe above on a 32-bit ARM board (Raspberry Pi 3/4 with 32-bit Raspberry Pi OS) with `--platform linux/arm/v7` added to `docker run`, and record the outcome in an issue. Do not sign off `linux/arm/v7` engine support from QEMU results.

## Android TV Notes

- Prefer ARM64 images where supported.
- For ARMv7 devices, monitor memory pressure and startup time.
- Run this checklist before first rollout to each Android TV hardware class.
- If the in-container engine is enabled on the device, it needs a 4 KB kernel page size and a volume at `/var/lib/acestream`; `linux/arm/v7` engine support is experimental (see above).
