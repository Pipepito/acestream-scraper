# ARM AceStream engine support (target v2.1.0)

## Goal

Ship `scraper-acestream` and `scraper-acestream-acexy` flavors for `linux/arm/v7` and `linux/arm64` in the v2.1.0 release. v2.0.0 ships amd64-engine-only by design (see the v2 release plan); ARM users get `:scraper` and `:scraper-acexy` (no engine) until this lands.

## Why this is a real workstream, not a manifest tweak

AceStream upstream does not publish a Linux glibc ARM build. The download URLs at `https://download.acestream.media/products/android/acestream-core/{armv7,armv8_64}/latest` redirect to **`.apk` files** (currently `AceStreamCore-3.1.80.0-armv7.apk` and `AceStreamCore-3.1.80.0-armv8_64.apk`). The APK ships a 32-bit Bionic-linked engine plus an embedded Python interpreter; running it on Linux requires presenting an Android-shaped filesystem and `chroot`-ing into it. This is a known, working pattern — see references below.

## Reference implementations

| Repo | Approach | Notes |
|---|---|---|
| [`trananhtuan/acestream-armv7-docker`](https://github.com/trananhtuan/acestream-armv7-docker) | Alpine Docker, extracts `androidfs/` into `/system` + `/acestream.engine`, symlinks `/etc/{hosts,resolv.conf}`, runs `acestream.sh`. Requires custom seccomp profile with `personality(PER_LINUX32)` allowed. | Cleanest reference for our case (~30 line Dockerfile). Ships a stale 2020 prebuilt tarball — we'd repackage from the current APK. |
| [`sshmanko/acestream-armv7`](https://github.com/sshmanko/acestream-armv7) | Host-level chroot (no Docker), explicit bind-mounts of `/dev`, `/proc`, `/sys`. | Useful for understanding the chroot setup. Last activity 2019. |
| [`staycanuca/acestream.arm.libreelec`](https://github.com/staycanuca/acestream.arm.libreelec) | LibreELEC/Kodi addon variant of the same chroot trick. | Last activity 2018. |

## Scope

1. **`docker/scripts/install-acestream.sh`** — add a third install kind alongside `executable` and `python_module`: `android_apk`. Handler: download the architecture-specific APK, validate sha256 from manifest, `unzip` into a staging dir, lay out the `androidfs/` tree under `/opt/acestream/`.
2. **`docker/manifests/acestream.json`** — add `linux/arm/v7` and `linux/arm64` platform entries pinning APK URL + sha256 + `kind: android_apk`. Note version skew explicitly (ARM 3.1.80 vs amd64 3.2.11; if upstream updates the APK we re-pin).
3. **`Dockerfile`** — `acestream-installer` stage learns the new install kind. The `scraper-acestream` runtime stage on ARM needs `/system` + `/acestream.engine` laid out so `acestream.sh` can be invoked. Decide whether the runtime container itself acts as the chroot envelope (trananhtuan's approach) or whether we wrap it in an explicit `chroot` call (sshmanko's approach). Trananhtuan's is simpler.
4. **Seccomp profile** — ship `docker/seccomp/acestream-arm.json` (allow `personality(PER_LINUX32)` plus the standard default deny list). Document `--security-opt seccomp=…` in the README/runbook for ARM users.
5. **`scripts/ci/flavor_platforms.py`** — once the manifest declares ARM platforms, this picks them up automatically. Verify the resulting buildx matrix.
6. **Build args / start command** — the existing `ACESTREAM_START_COMMAND` (`env PYTHONPATH=… start-engine --client-console --http-port 6878`) only applies to amd64. ARM needs `chroot /opt/acestream /system/bin/acestream.sh` (or equivalent). Switch on architecture at entrypoint time.
7. **`backend/tests/docker/test_acestream_runtime_smoke.py`** — extend to cover ARM under QEMU. Real validation requires hardware (see below).
8. **README + `docs/architecture/deployment.md`** — document the ARM caveats: version skew, seccomp requirement, packet-loss / stuttering known issue from upstream's modded build.

## Real-hardware validation (mandatory)

QEMU smoke validates the build matrix and that the engine starts. It does **not** validate streaming reliability — AceStream is timing-sensitive and the modded ARM engine has documented stuttering/packet-loss. Need at minimum:
- Raspberry Pi 4 (ARMv8) — primary target.
- Raspberry Pi 3 / Pi Zero 2 W (ARMv7) — secondary, optional.

Test plan: pull `:scraper-acestream-acexy` on the Pi, start a known-working channel for ≥30 min, observe playback stability and engine logs. Compare CPU/RAM footprint vs amd64.

## Caveats / non-goals

- **Version skew is acceptable for v2.1.0.** ARM users will see `get_version` return `3.1.80` while amd64 returns `3.2.11`. Document; do not block.
- **Performance is not guaranteed.** trananhtuan documents "occasional stuttering and packet loss" with the modded build. Ship with the caveat in the README.
- **No fork PRs trigger ARM smoke** in the existing CI policy — keep that constraint.

## Out of scope

- Bionic-to-glibc native rebuild of the engine. Not feasible without upstream cooperation.
- Anbox / Waydroid / full Android emulation. Too heavy.

## Relates to

- v2 release pipeline cleanup (the cleanup PR notes this as deferred).
- `docker/manifests/acestream.json` — current single-platform manifest.
- `docs/release/v2-release-readiness.md` — should be updated when this issue is targeted at v2.1.0.
