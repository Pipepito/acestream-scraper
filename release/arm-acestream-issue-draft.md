# ARM AceStream engine support (target v2.1.0)

> **Status (2026-08-27): implemented on branch `arm-acestream-engine`.**
> `scraper-acestream`, `scraper-acestream-acexy`, `latest` and the version tags
> now build for `linux/amd64`, `linux/arm64` and `linux/arm/v7`
> (`scripts/ci/flavor_platforms.py` picks the platforms up from
> `docker/manifests/acestream.json`). The plan below is kept as the historical
> record; the implementation differs from it on these points:
>
> - **Direct exec, not chroot / seccomp.** The APK's engine payload
>   (python-for-android CPython 3.8 + compiled engine modules) is unzipped to
>   `/opt/acestream` and runs unmodified against a minimal Android 9 bionic
>   userland copied to `/system` (`linker64`/`linker` +
>   `libc`/`libdl`/`libm`/`libz`/`liblog`/`libc++` and a
>   `libstdc++.so -> libc++.so` symlink), taken from the Termux package
>   `aosp-libs 9.0.0-r76-4` (built from AOSP source; BSD/Apache-2.0 etc.;
>   NOTICE files shipped under `/system/etc/NOTICE-aosp-libs`).
>   `/opt/acestream/start-engine` (`docker/scripts/acestream-android/start-engine`)
>   sets `ANDROID_ROOT=/system`, `PYTHONHOME`/`PYTHONPATH`/`LD_LIBRARY_PATH`
>   and execs the bionic python with `main_linux.py` plus a Linux
>   `app_bridge.py`. **No `docker/seccomp/acestream-arm.json`, no
>   `--security-opt seccomp=…`, no `--privileged`, no extra capabilities**
>   (scope item 4 and the `chroot` parts of items 3 and 6 were not needed;
>   verified on arm64). `ACESTREAM_START_COMMAND` is unchanged for all
>   platforms.
> - **Manifest schema.** The install kind is `android-apk` (not
>   `android_apk`); each platform entry also carries `engine_version`,
>   `support` (`stable` | `experimental`), `vendored_file`, `mirror_urls[]`
>   and a `bionic{...}` block.
> - **Support level differs per platform.** `linux/arm64` is **stable**
>   (engine HTTP API answers within ~5 s, RSS ~95 MB idle;
>   `/webui/api/service?method=get_version` returns
>   `{"platform":"android","version":"3.1.80"}`). `linux/arm/v7` is
>   **experimental**: it builds and installs, but cannot be executed under
>   qemu-user (32-bit bionic calls `personality(PER_LINUX32)`), so it needs
>   real ARMv7/AArch32-capable hardware and has not been runtime-tested.
> - **Vendored binaries + GitHub Release mirror** (not in the draft). Every
>   engine archive and the bionic `.deb`s live in `docker/vendor/acestream/`
>   and `docker/vendor/bionic/` (with `SHA256SUMS`); identical copies are
>   published at
>   <https://github.com/Pipepito/acestream-scraper/releases/tag/acestream-binaries-3.2.11-3.1.80.0>.
>   `docker/scripts/install-acestream.sh` resolves vendored copy → upstream
>   `url` → `mirror_urls`, sha256-verified, so builds no longer need
>   WARP/egress to `download.acestream.media`. Pin updates:
>   `docker/vendor/acestream/README.md`.
> - **CI is Jenkins, not GitHub Actions.** The PR job's
>   `Acestream Engine Runtime Smoke` stage runs
>   `backend/tests/docker/test_acestream_runtime_smoke.py` (amd64 always;
>   arm64 only when the host is arm64) plus
>   `backend/tests/docker/test_install_acestream.py -k android_apk_install_layout`
>   (QEMU builds of the arm64 + armv7 installer stage, no engine execution);
>   `scripts/ci/run_jenkins_release.sh` does the same before pushing the
>   multi-platform manifests. Scope item 7's "ARM under QEMU" runtime smoke is
>   therefore not possible for the engine itself.
> - **Still pending:** the real-hardware validation plan below. Two runtime
>   notes for it: mount `-v acestream-state:/var/lib/acestream` (engine
>   state, cache and logs live in `ACESTREAM_HOME`), and on a Raspberry Pi 5
>   boot with `kernel=kernel8.img` in `config.txt` — the Android 9 bionic
>   linker segfaults on 16 KB-page kernels, and `start-engine` refuses to
>   start when `getconf PAGESIZE` is not 4096.

## Goal

Ship `scraper-acestream` and `scraper-acestream-acexy` flavors for `linux/arm/v7` and `linux/arm64` in the v2.1.0 release. v2.0.0 ships amd64-engine-only by design (see the v2 release plan); ARM users get `:scraper` and `:scraper-acexy` (no engine) until this lands. (Landed 2026-08-27 on branch `arm-acestream-engine`.)

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

> Status 2026-08-27: **still pending.** Only the local arm64 engine smoke on
> Apple Silicon has been run (see `docs/release/phase5-multiarch-evidence.md`).

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
- `docker/manifests/acestream.json` — current single-platform manifest. (Superseded on 2026-08-27: now three platforms, see the status block above.)
- `docs/release/v2-release-readiness.md` — should be updated when this issue is targeted at v2.1.0. (Annotated on 2026-08-27 together with `docs/release/v2-release-notes.md` and `docs/release/phase5-multiarch-evidence.md`.)
