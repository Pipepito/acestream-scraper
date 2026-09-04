# Multi-Architecture Manifest Updates

`docker/manifests/acestream.json` is the canonical declaration of which
container platforms have a working AceStream engine available and how it is
installed. The flavor platform resolver (`scripts/ci/flavor_platforms.py`)
intersects the baseline platform set against this manifest, so anything not
listed here is silently dropped from `scraper-acestream`,
`scraper-acestream-acexy`, and `latest` builds.

The manifest covers all three baseline platforms:

| Platform | Engine | `install.kind` | `support` |
|---|---|---|---|
| `linux/amd64` | native Linux engine 3.2.11 (upstream tarball) | `executable` | `stable` |
| `linux/arm64` | Android engine 3.2.17 from digest-pinned `jopsis/acestream:v3.2.17-fix` | `oci-image` | `stable` |
| `linux/arm/v7` | Android engine 3.2.17 from digest-pinned `jopsis/acestream:v3.2.17-fix` | `oci-image` | `experimental` |

Upstream publishes native Linux engine tarballs only for x86_64. ARM64 and
ARMv7 use their matching platform variants from
[`jopsis/acestream`](https://hub.docker.com/r/jopsis/acestream) under one pinned
multi-platform digest. Conventional archives and bionic packages retained under
`docker/vendor/` are used by archive installs or kept for reproducibility. How
the ARM engine works at runtime is documented in
`docs/ops/acestream-arm-engine.md`.

> History: until 2026-08-27 the manifest listed `linux/amd64` only and this
> document was the playbook for "when AceStream upstream ships ARM builds".
> Superseded first on 2026-08-27 by the Android payload work and again on
> 2026-09-03 when both ARM entries moved to the jopsis `oci-image` source.

## When to update

- A new upstream AceStream release (Linux tarball for amd64 or a jopsis
  multi-platform image for ARM) that we want our flavors to consume.
- A new upstream platform we want to add, or an existing platform that breaks
  and needs to be temporarily disabled (remove its entry; the flavor resolver
  drops it from the matrix).
- A pinned archive or OCI image changes (download/image reference, layout,
  digest/checksum, vendored file name, or mirror URL).
- A legacy `android-apk` entry or its bionic runtime package changes.
- A platform's `support` level changes (for example promoting `linux/arm/v7`
  from `experimental` to `stable` after real-hardware validation).

Manifest changes are operator-driven. There is no scheduled job that watches
upstream — by design. AceStream releases are infrequent and changes to the
container surface need explicit human approval before they ship.

## How to update

1. Locate the upstream release you want to pin (download URL and SHA256 for
   archives, or a tagged multi-arch image plus index digest for `oci-image`,
   archive type; for `executable` the binary path inside the archive, or for
   `android-apk` the ABI plus the matching `aosp-libs` package).
2. For archive installs, add the archive(s) to `docker/vendor/acestream/` (engine) and, only if it
   changed, `docker/vendor/bionic/` (bionic runtime); regenerate that
   directory's `SHA256SUMS` (`shasum -a 256 <files> > SHA256SUMS`, or
   `sha256sum` on Linux). The installer prefers these copies over any
   download, and `scripts/ci/validate_docker_manifest_metadata.py` fails
   when a manifest entry has no matching vendored file or checksum.
3. For archive installs, publish the same files as a GitHub Release so the `mirror_urls` resolve
   (exact command under **Bumping the AceStream version** below).
4. Add or update the platform entry in `docker/manifests/acestream.json`.
   The schema is what `docker/scripts/acestream_manifest.py` resolves for
   `$TARGETPLATFORM` inside the `Dockerfile`'s `acestream-installer` stage
   (both ARM entries use the documented `oci-image` shape):
   ```json
   {
     "version": "3.2.11",
     "android_version": "3.2.17",
     "vendor_dir": "docker/vendor/acestream",
     "mirror_base_url": "https://github.com/Pipepito/acestream-scraper/releases/download/acestream-binaries-3.2.11-3.1.80.0",
     "platforms": {
       "linux/amd64": {
         "engine_version": "3.2.11",
         "support": "stable",
         "url": "https://download.acestream.media/linux/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz",
         "sha256": "...",
         "archive_type": "tar.gz",
         "vendored_file": "acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz",
         "mirror_urls": ["<mirror_base_url>/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz"],
         "install": {
           "kind": "executable",
           "strip_components": 0,
           "binary_path": "start-engine",
           "engine_http_port": 6878
         }
       },
       "linux/arm64": {
         "engine_version": "3.2.17",
         "support": "stable",
         "distribution": "jopsis/acestream v3.2.17-fix",
         "distribution_url": "https://hub.docker.com/r/jopsis/acestream",
         "source_url": "https://github.com/jopsis/docker-acestream-aceserve",
         "image_ref": "jopsis/acestream:v3.2.17-fix",
         "image_digest": "sha256:<64 hex characters>",
         "install": {
           "kind": "oci-image",
           "engine_http_port": 6878
         }
       },
       "linux/arm/v7": {
         "engine_version": "3.2.17",
         "support": "experimental",
         "distribution": "jopsis/acestream v3.2.17-fix",
         "distribution_url": "https://hub.docker.com/r/jopsis/acestream",
         "source_url": "https://github.com/jopsis/docker-acestream-aceserve",
         "image_ref": "jopsis/acestream:v3.2.17-fix",
         "image_digest": "sha256:<same multi-platform index digest>",
         "install": {
           "kind": "oci-image",
           "engine_http_port": 6878
         }
       }
     }
   }
   ```

   Field notes (enforced by `scripts/ci/validate_docker_manifest_metadata.py`):

   - Top level: `version` (amd64 engine), `vendor_dir`, `mirror_base_url`
     are required; `android_version` is informational and must equal the
     ARM entries' `engine_version` (checked by the docker tests).
   - Every platform: `engine_version`, `support` (`stable` | `experimental`),
     and `install` with `kind` + `engine_http_port`.
   - Archive installs additionally require
     `url` (https), `sha256`, `archive_type` (`tar.gz` for `executable`,
     `apk` for `android-apk`), `vendored_file` (bare file name that must
     exist in `vendor_dir` with a matching `SHA256SUMS` line), `mirror_urls`
     (non-empty, https, each ending in `/<vendored_file>`, at least one
     under `mirror_base_url`).
   - `install.kind = executable`: `strip_components`, `binary_path`.
   - `install.kind = android-apk`: `abi` (`arm64-v8a` | `armeabi-v7a`) and a
     `bionic` object with `url`, `sha256`, `vendor_dir`, `vendored_file`,
     `mirror_urls` (same rules as above), `libdir`/`linker` (`lib64`/`linker64`
     or `lib`/`linker`), plus a free-form `package` description.
   - `install.kind = oci-image`: `distribution`, `distribution_url`,
     `source_url`, a tagged `image_ref`, and a `sha256:` `image_digest`. Keep
     the Dockerfile's `ACESTREAM_COMMUNITY_IMAGE` pin identical.

   See **Bumping the AceStream version** below for the canonical step-by-step
   when only updating the version pin.
5. **Do not** edit `docker/manifests/platforms.json` — that file declares the
   baseline platform matrix per flavor and is correct as-is. The intersection
   logic in `flavor_platforms.py` handles the rest: as soon as a platform has
   an entry here, `scraper-acestream`, `scraper-acestream-acexy`, and the
   `latest`/version aliases build and publish for it.

## How to verify locally

```bash
# 1. Render the resolved platform list for each affected flavor. Arguments
#    are positional: <platforms.json> <acestream.json> <flavor>. The
#    latest/version aliases are not flavor names; check
#    scraper-acestream-acexy, which they point at.
python3 scripts/ci/flavor_platforms.py docker/manifests/platforms.json docker/manifests/acestream.json scraper-acestream
python3 scripts/ci/flavor_platforms.py docker/manifests/platforms.json docker/manifests/acestream.json scraper-acestream-acexy

# 2. Inspect what the build will install per platform.
python3 docker/scripts/acestream_manifest.py docker/manifests/acestream.json --all --format json
python3 scripts/ci/derive_acestream_build_args.py docker/manifests/acestream.json scraper-acestream linux/arm64

# 3. Validate the manifest, vendored files, SHA256SUMS and mirror URLs.
python3 scripts/ci/validate_docker_manifest_metadata.py

# 4. Dry-run the build to confirm the matrix is accepted. The script resolves
#    every platform first and prints one
#    "AceStream engine for <platform>: kind=... version=... support=... source=..."
#    line per platform before the buildx command.
bash scripts/ci/build_multiarch_images.sh \
  --dry-run --flavor scraper-acestream \
  --result-file /tmp/phase5-build-result-scraper-acestream.json

bash scripts/ci/verify_multiarch_manifest.sh \
  --result-file /tmp/phase5-build-result-scraper-acestream.json \
  --flavor scraper-acestream

# 5. Build-level docker tests (QEMU for the non-native platforms). The ARM
#    installer-layout tests build the arm64 + armv7 installer stages from the
#    pinned OCI image but never execute the engine.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker

# 6. Engine runtime smoke: builds scraper-acestream for the platforms this
#    host can execute (linux/amd64 always; linux/arm64 only on an arm64 host)
#    and probes the engine on :6878.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v

# 7. Full app-level architecture profile (requires QEMU + Buildx; ~30-45 min).
#    Builds every flavor for every platform and boots the app-only `scraper`
#    target under QEMU; it does not start the engine.
python3 scripts/phase_gates/phase5_gate_runner.py --profile full \
  --json-output > /tmp/phase5-gate-report-full.json
```

Build success alone is not enough — pitfall #4 in
`.planning/research/PITFALLS.md` calls out the "build green but runtime
broken" failure mode for ARM. The Android engine cannot run under qemu-user
(the 32-bit variant calls `personality(PER_LINUX32)`; the 64-bit one has only
been verified natively), so:

- `linux/arm64` engine changes must be runtime-smoked on an arm64 host (step 6
  above on a Raspberry Pi 4/5 64-bit with a 4 KB-page kernel, or any aarch64
  Docker host).
- `linux/arm/v7` engine changes can only be runtime-tested on real ARMv7
  hardware; until that happens the platform stays `support: experimental`.

`docs/ops/acestream-arm-engine.md` ("Testing on a Raspberry Pi") has the
manual procedure.

## How to verify in CI

Jenkins is the only CI (`docs/ops/jenkins-ci.md`). A PR that touches
`docker/manifests/acestream.json` or `docker/vendor/` runs the multibranch PR
job `acestream-scraper-pr` (`Jenkinsfile`), which:

- dry-runs the four-flavor multi-arch matrix and verifies each result file
  (`Required Cutover Checks` and `Multi-Arch Quick Profile` stages; the
  latter also runs `phase5_gate_runner.py --profile quick`);
- in the `Acestream Engine Runtime Smoke` stage builds `scraper-acestream`
  pinned to `--platforms linux/amd64 --load` (the flavor now resolves to
  three platforms and `--load` needs exactly one), runs
  `backend/tests/docker/test_acestream_runtime_smoke.py` (the amd64 engine
  boots and answers on `:6878`), `test_acexy_runtime_smoke.py`, and
  `test_install_acestream.py -k "arm_oci_image_install_layout"` (builds of
  the ARM installer stages, asserting the engine payload and
  bionic layout — no engine execution).

The runner `dorat-nuc-ci` is amd64, so the arm64 runtime smoke never runs in
CI; the same pytest parametrizes `linux/arm64` only when the host is arm64.

The manual release job `acestream-scraper-release`
(`jenkins/release.Jenkinsfile` -> `scripts/ci/run_jenkins_release.sh`) runs
`run_cutover_required_checks.sh --profile full`, the same four-flavor dry-run
preflight, and — on publish runs (`DRY_RUN=false`) — the same amd64 engine
smoke plus the ARM installer-layout test before logging into Docker Hub. The
pushed `scraper-acestream`, `scraper-acestream-acexy`, `latest`, and version
tags include `linux/arm64` and `linux/arm/v7`, and
`verify_multiarch_manifest.sh --image <tag> --flavor <flavor>` checks every
remote manifest after the push. The job archives
`phase5-build-result-release-*.json` and
`phase5-build-result-release-metadata.json`; link that build from
`docs/release/phase5-multiarch-evidence.md`. The heavier
`phase5_gate_runner.py --profile full` is not wired into either job — run it
manually (step 7 above) before merging risky multi-arch changes.

> Superseded on 2026-08-27: earlier revisions of this section pointed at the
> GitHub Actions `Release Pipeline` (`workflow_dispatch`) and a
> `multiarch-runtime-smoke` job that uploaded `phase5-gate-report-full.json`.
> All GitHub Actions workflows are retired; the Jenkins jobs above are the
> only CI path.

## Rollback

If a freshly-published manifest breaks the engine on a new platform:

1. Revert the `docker/manifests/acestream.json` change (and the vendored
   files it introduced) on `main` through a PR; `acestream-scraper-pr`
   re-validates the reverted matrix.
2. Re-run `acestream-scraper-release` from the reverted `main`. The job only
   builds `origin/main` HEAD, so revert first rather than re-running on an
   old SHA. Leave `PUBLISH_LATEST` off unless `latest` itself was affected.
3. Open an issue with the failing smoke output and engine logs attached so
   the next manifest attempt has the failure record to work from.

If only one platform is broken, removing that platform's entry (rather than
reverting the whole pin) drops it from the flavor matrix while keeping the
other platforms published.

## Bumping the AceStream version

The AceStream payload is described by `docker/manifests/acestream.json` plus
any conventional archives it names. The manifest is consumed at build time by
the `Dockerfile`'s `acestream-installer` stage: `docker/scripts/install-acestream.sh`
calls `docker/scripts/acestream_manifest.py` for `$TARGETPLATFORM` and installs
the matching engine. Conventional archives resolve as vendored copy -> upstream
`url` -> `mirror_urls`, sha256-verified whichever source wins; `oci-image`
entries copy from the pinned source-image digest. `scripts/ci/build_multiarch_images.sh`
no longer injects global `ACESTREAM_*` build-args (they would apply one engine
to every platform of a multi-platform build); it validates that each resolved
platform has an installable entry and prints the
`AceStream engine for <platform>: ...` summary. Explicit
`--build-arg ACESTREAM_*` values still override the manifest for
single-platform experiments, and `scripts/ci/derive_acestream_build_args.py
<acestream.json> <flavor> [<platform>]` prints them for inspection. The CI
runtime smoke (`backend/tests/docker/test_acestream_runtime_smoke.py`, run by
`Jenkinsfile` and `scripts/ci/run_jenkins_release.sh`) verifies the engine
actually starts and responds on port 6878 in the resulting image.

> Superseded on 2026-08-27: the description above replaces the earlier
> "build_multiarch_images.sh converts each manifest field into a
> `--build-arg`" model, which only worked while the manifest had one platform.

### Steps

1. Resolve the new sources:
   - amd64: the tarball on https://download.acestream.media/. As of
     AceStream 3.2.x, the URL pattern is
     `acestream_<VERSION>_ubuntu_22.04_x86_64_py3.10.tar.gz` and the tarball
     ships a top-level `start-engine` shell wrapper plus a real ELF binary
     `acestreamengine`. Older releases may use different filenames.
   - arm64 / armv7: choose a jopsis tag that publishes both `linux/arm64` and
     `linux/arm/v7`. Inspect it with
     `docker buildx imagetools inspect jopsis/acestream:<TAG>` and record the
     immutable multi-platform index digest. Do not pin a single-platform child
     manifest because both entries intentionally share the index digest and
     Docker selects the matching platform variant.
2. For amd64, download the tarball into `docker/vendor/acestream/`, remove the
   superseded archive (old versions remain in git history and on its GitHub
   Release), and regenerate `SHA256SUMS`. ARM OCI-image updates do not add files
   under `docker/vendor/`.
3. Update `docker/manifests/acestream.json`:
   - Top level: `version` (amd64 engine), `android_version`, and
     `mirror_base_url` (the new release tag from step 4).
   - Per platform: `engine_version` and `support`. For amd64 also update `url`,
     `sha256`, `vendored_file`, and `mirror_urls`; for both ARM entries update
     `distribution`, `distribution_url`, `source_url`, `image_ref`, and the
     shared `image_digest`.
   - For the standard 3.2.x layout, leave the amd64 `install` as
     `{ "kind": "executable", "strip_components": 0, "binary_path": "start-engine", "engine_http_port": 6878 }`.
   - For ARM, leave `install.kind = oci-image`; confirm the new variants still
     provide `/acestream`, `/system/bin/linker64` (arm64) or
     `/system/bin/linker` (armv7), and the engine Python executable. The
     installer-layout test fails if this contract changes.
4. When the amd64 archive changes, publish the vendored files as GitHub Release
   assets so its mirrors resolve. The tag is
   `acestream-binaries-<amd64 version>-<android version>`:

   ```bash
   gh release create acestream-binaries-<VERSION>-<ANDROID_VERSION> --target main --latest=false \
     docker/vendor/acestream/*.tar.gz docker/vendor/acestream/SHA256SUMS
   ```

5. Run the manifest validator + docker tests locally:

   ```bash
   python3 scripts/ci/validate_docker_manifest_metadata.py
   PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker
   ```

6. (Optional) run the full flavor validator. It now builds in auto mode,
   i.e. with the real engine for `PLATFORM` (default `linux/amd64`).
   Set `ACESTREAM_SOURCE=fixture` for the fast contract-test fixture build
   that omitting the download URL used to produce:

   ```bash
   bash scripts/ci/validate_docker_flavor_targets.sh
   ACESTREAM_SOURCE=fixture bash scripts/ci/validate_docker_flavor_targets.sh
   PLATFORM=linux/arm64 bash scripts/ci/validate_docker_flavor_targets.sh   # QEMU on amd64 hosts
   ```

7. Runtime-test the ARM engine on hardware before promoting it: arm64 at
   minimum for the stable entry, and real ARMv7 hardware before changing that
   entry from experimental. See `docs/ops/acestream-arm-engine.md`, "Testing
   on a Raspberry Pi".
8. Open a PR. The Jenkins `acestream-scraper-pr` job will (a) dry-run the
   flavor matrices, which re-resolves the manifest per platform, (b) build
   `scraper-acestream` for `linux/amd64` with sha256 verification from the
   vendored copy, (c) run the amd64 runtime smoke that exercises the engine
   end-to-end, and (d) build the arm64 + armv7 OCI installer stages under QEMU
   and assert their layout.

### Notes on install kinds

The install pipeline supports three `install.kind` values: `executable`,
`android-apk`, and `oci-image`. Current manifests use `executable` for amd64
and `oci-image` for both ARM targets; `android-apk` remains available for
legacy or experimental entries.

`executable` (amd64): the runtime image grafts a `python3.10` interpreter from
`python:3.10-slim` because the ELF binary directly links
`libpython3.10.so.1.0`. If a future release moves to a different Python
version, update the `COPY --from=python:3.10-slim …` block in the
`scraper-acestream` stage of the `Dockerfile` accordingly.

The bundled engine runtime deps in the tarball's `requirements.txt`
(currently `apsw`, `lxml`, `pycryptodome`, `pynacl`, `iso8601`, `aiohttp`,
`psutil`) are pip-installed at build time into `/opt/acestream/python-deps`
and added to `PYTHONPATH` at engine launch via the `ACESTREAM_START_COMMAND`
ENV in the Dockerfile. If the upstream `requirements.txt` ever changes in
ways that break the install, the failure surfaces during
`bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream` —
no manifest schema change is needed for typical dep bumps.

`oci-image` (arm64 and armv7): the payload brings its own bionic CPython
3.8, so no interpreter is grafted; instead the runtime stage copies the
staged bionic userland to `/system` (the payload's ELF interpreter path is
hard-coded to `/system/bin/linker*`). The Linux-side glue lives in
`docker/scripts/acestream-android/` (`start-engine`, `main_linux.py`,
`app_bridge.py`, `acestream.conf`). A new APK that changes the bootstrap
contract (`main.py` arguments, `app_bridge` RPC methods, `acestream.conf`
tokens) is where breakage would show up — inspect those files in the staged
source image and compare them with the previous pin. Any source-image userland
change must be re-verified on hardware (the page-size guard in `start-engine`
reflects the Android 9 linker's 4 KB requirement).

If a future release fits none of these kinds, add a new kind rather than
overloading an existing one. The `kind` discriminator is in place; the branches to
extend are `INSTALL_KINDS` / `build_args_for()` in
`docker/scripts/acestream_manifest.py`, the `case "$INSTALL_KIND"` dispatch
in `docker/scripts/install-acestream.sh`,
`scripts/ci/validate_docker_manifest_metadata.py`, and the `Dockerfile`
`ARG`s if the kind needs new build-args.

## Acexy pin (`docker/manifests/acexy.json`)

`scripts/ci/build_multiarch_images.sh` derives `ACEXY_REPO`, `ACEXY_REF` and
`ACEXY_BINARY_NAME` from this manifest for the `scraper-acexy` and
`scraper-acestream-acexy` flavors. Without them the Dockerfile compiles the
build fixture (a stub that only prints `fixture acexy`), so after bumping the
pin always confirm the ref exists upstream and re-run the runtime smoke:

```bash
git ls-remote --tags https://github.com/Javinator9889/acexy.git
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy | grep ACEXY_
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py
```

## ffmpeg (`docker/manifests/ffmpeg.json`)

The web player transcodes AceStream output to HLS with a minimal static
ffmpeg that the `ffmpeg-builder` Dockerfile stage cross-compiles from the
vendored source (`docker/vendor/ffmpeg`, `docker/scripts/build-ffmpeg.sh`).
It rides in `runtime-base`, so **every flavor and every platform** ships
`/opt/ffmpeg/bin/ffmpeg` and `ffprobe`; `runtime-base` also bakes
`FFMPEG_BINARY_PATH=/opt/ffmpeg/bin/ffmpeg`, and `entrypoint.sh` exports
`IMAGE_HAS_FFMPEG` from `-x "$FFMPEG_BINARY_PATH"` (so a stripped-down mount
or a bare-metal run is detected rather than assumed). When nothing executable
sits at that path the entrypoint clears `FFMPEG_BINARY_PATH` before handing it
to the app, which is `Settings.FFMPEG_BINARY_PATH`'s declared default and means
"resolve `ffmpeg` from `PATH`" — the app is never given a path it cannot spawn.

Keys: `version`, `vendor_dir` (must be `docker/vendor/ffmpeg` — the Dockerfile
bind-mounts `docker/vendor`), `vendored_file`, `sha256`, `source_url`,
`mirror_base_url`, `mirror_urls`.
`scripts/ci/build_multiarch_images.sh` derives `FFMPEG_VENDORED_FILE`,
`FFMPEG_SHA256`, `FFMPEG_SOURCE_URL` and `FFMPEG_MIRROR_URLS` (space-separated)
from them for every flavor; the build script resolves vendored copy →
`source_url` → each mirror and verifies the sha256 either way.

Bumping the pin is `docker/vendor/ffmpeg/README.md` (download the release
tarball, refresh `SHA256SUMS` and the manifest, upload the archive to the
release tag named by `mirror_base_url`), then:

```bash
python3 scripts/ci/validate_docker_manifest_metadata.py
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper | tr ' ' '\n' | grep FFMPEG_
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/docker/test_ffmpeg_vendor.py backend/tests/docker/test_ffmpeg_build.py
```

`test_ffmpeg_build.py` builds the stage for `linux/amd64`, `linux/arm64` and
`linux/arm/v7` and runs the resulting binary on each target against
`backend/tests/docker/fixtures/`: copy remux TS→HLS, AC-3→AAC into fMP4 HLS,
and the web player's exact command line, so a configure set that drops a
muxer, encoder or bitstream filter fails here rather than at playback.
The Jenkins `Acestream Engine Runtime Smoke` stage runs both files.
