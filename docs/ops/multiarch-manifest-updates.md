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
| `linux/arm64` | official Android engine 3.1.80.0 (`arm64-v8a` APK) on a bionic userland | `android-apk` | `stable` |
| `linux/arm/v7` | official Android engine 3.1.80.0 (`armeabi-v7a` APK) on a bionic userland | `android-apk` | `experimental` |

Upstream publishes native Linux engine tarballs only for x86_64; the ARM
engines are the official Android APKs from
https://docs.acestream.media/products/. Every engine archive and the bionic
runtime packages are vendored under `docker/vendor/` and mirrored on a GitHub
Release, so builds do not depend on reaching `download.acestream.media`. How
the ARM engine works at runtime is documented in
`docs/ops/acestream-arm-engine.md`.

> History: until 2026-08-27 the manifest listed `linux/amd64` only and this
> document was the playbook for "when AceStream upstream ships ARM builds".
> Superseded on 2026-08-27 by the `android-apk` install kind (branch
> `arm-acestream-engine`); the ARM entries above are the result.

## When to update

- A new upstream AceStream release (Linux tarball for amd64, Android APK for
  ARM) that we want our flavors to consume.
- A new upstream platform we want to add, or an existing platform that breaks
  and needs to be temporarily disabled (remove its entry; the flavor resolver
  drops it from the matrix).
- A pinned archive changes (download URL, archive layout, SHA256, vendored
  file name, mirror URL).
- The bionic runtime package (`aosp-libs`) for the `android-apk` platforms
  needs to change.
- A platform's `support` level changes (for example promoting `linux/arm/v7`
  from `experimental` to `stable` after real-hardware validation).

Manifest changes are operator-driven. There is no scheduled job that watches
upstream — by design. AceStream releases are infrequent and changes to the
container surface need explicit human approval before they ship.

## How to update

1. Locate the upstream release you want to pin (download URL, SHA256,
   archive type; for `executable` the binary path inside the archive, for
   `android-apk` the ABI plus the matching `aosp-libs` package).
2. Add the archive(s) to `docker/vendor/acestream/` (engine) and, only if it
   changed, `docker/vendor/bionic/` (bionic runtime); regenerate that
   directory's `SHA256SUMS` (`shasum -a 256 <files> > SHA256SUMS`, or
   `sha256sum` on Linux). The installer prefers these copies over any
   download, and `scripts/ci/validate_docker_manifest_metadata.py` fails
   when a manifest entry has no matching vendored file or checksum.
3. Publish the same files as a GitHub Release so the `mirror_urls` resolve
   (exact command under **Bumping the AceStream version** below).
4. Add or update the platform entry in `docker/manifests/acestream.json`.
   The schema is what `docker/scripts/acestream_manifest.py` resolves for
   `$TARGETPLATFORM` inside the `Dockerfile`'s `acestream-installer` stage
   (one entry of each kind shown; `linux/arm/v7` has the same shape as
   `linux/arm64` with the `armv7` APK, the `_arm.deb` package,
   `"libdir": "lib"` and `"linker": "linker"`):
   ```json
   {
     "version": "3.2.11",
     "android_version": "3.1.80.0",
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
         "engine_version": "3.1.80.0",
         "support": "stable",
         "url": "https://download.acestream.media/android/core.web/stable/AceStreamCore-3.1.80.0-armv8_64.apk",
         "sha256": "...",
         "archive_type": "apk",
         "vendored_file": "AceStreamCore-3.1.80.0-armv8_64.apk",
         "mirror_urls": ["<mirror_base_url>/AceStreamCore-3.1.80.0-armv8_64.apk"],
         "install": {
           "kind": "android-apk",
           "abi": "arm64-v8a",
           "engine_http_port": 6878,
           "bionic": {
             "package": "aosp-libs 9.0.0-r76-4 (Termux, built from AOSP android-security-9.0.0_r76)",
             "url": "https://packages-cf.termux.dev/apt/termux-main/pool/main/a/aosp-libs/aosp-libs_9.0.0-r76-4_aarch64.deb",
             "sha256": "...",
             "vendor_dir": "docker/vendor/bionic",
             "vendored_file": "aosp-libs_9.0.0-r76-4_aarch64.deb",
             "mirror_urls": ["<mirror_base_url>/aosp-libs_9.0.0-r76-4_aarch64.deb"],
             "libdir": "lib64",
             "linker": "linker64"
           }
         }
       }
     }
   }
   ```

   Field notes (enforced by `scripts/ci/validate_docker_manifest_metadata.py`):

   - Top level: `version` (amd64 engine), `vendor_dir`, `mirror_base_url`
     are required; `android_version` is informational and must equal the
     ARM entries' `engine_version` (checked by the docker tests).
   - Per platform: `engine_version`, `support` (`stable` | `experimental`),
     `url` (https), `sha256`, `archive_type` (`tar.gz` for `executable`,
     `apk` for `android-apk`), `vendored_file` (bare file name that must
     exist in `vendor_dir` with a matching `SHA256SUMS` line), `mirror_urls`
     (non-empty, https, each ending in `/<vendored_file>`, at least one
     under `mirror_base_url`), and `install` with `kind` + `engine_http_port`.
   - `install.kind = executable`: `strip_components`, `binary_path`.
   - `install.kind = android-apk`: `abi` (`arm64-v8a` | `armeabi-v7a`) and a
     `bionic` object with `url`, `sha256`, `vendor_dir`, `vendored_file`,
     `mirror_urls` (same rules as above), `libdir`/`linker` (`lib64`/`linker64`
     or `lib`/`linker`), plus a free-form `package` description.

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
#    "AceStream engine for <platform>: kind=... version=... support=... source=vendored ..."
#    line per platform before the buildx command.
bash scripts/ci/build_multiarch_images.sh \
  --dry-run --flavor scraper-acestream \
  --result-file /tmp/phase5-build-result-scraper-acestream.json

bash scripts/ci/verify_multiarch_manifest.sh \
  --result-file /tmp/phase5-build-result-scraper-acestream.json \
  --flavor scraper-acestream

# 5. Build-level docker tests (QEMU for the non-native platforms). The ARM
#    installer-layout tests build the arm64 + armv7 installer stages from the
#    vendored archives but never execute the engine.
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
  `test_install_acestream.py -k android_apk_install_layout` (QEMU builds of
  the arm64 and armv7 installer stages, asserting the engine payload and
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

The AceStream payload is described entirely by `docker/manifests/acestream.json`
plus the vendored archives it names. The manifest is consumed at build time by
the `Dockerfile`'s `acestream-installer` stage: `docker/scripts/install-acestream.sh`
calls `docker/scripts/acestream_manifest.py` for `$TARGETPLATFORM` and installs
the matching engine (vendored copy -> upstream `url` -> `mirror_urls`,
sha256-verified whichever source wins). `scripts/ci/build_multiarch_images.sh`
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

1. Find the upstream archives:
   - amd64: the tarball on https://download.acestream.media/. As of
     AceStream 3.2.x, the URL pattern is
     `acestream_<VERSION>_ubuntu_22.04_x86_64_py3.10.tar.gz` and the tarball
     ships a top-level `start-engine` shell wrapper plus a real ELF binary
     `acestreamengine`. Older releases may use different filenames.
   - arm64 / armv7: the Android engine APKs listed on
     https://docs.acestream.media/products/. The
     `https://download.acestream.media/products/android/acestream-core/{armv8_64,armv7}/latest`
     links redirect to `.../android/core.web/stable/AceStreamCore-<VERSION>-armv8_64.apk`
     and `...-armv7.apk`; pin the resolved `.apk` URL, not the redirect.
2. Download them into `docker/vendor/acestream/`, remove the superseded
   archives (old versions stay in git history and on their GitHub Release),
   and regenerate the checksums:
   `cd docker/vendor/acestream && shasum -a 256 *.tar.gz *.apk > SHA256SUMS`
   (`sha256sum` on Linux). Only touch `docker/vendor/bionic/` if the bionic
   runtime package changes.
3. Update `docker/manifests/acestream.json`:
   - Top level: `version` (amd64 engine), `android_version`, and
     `mirror_base_url` (the new release tag from step 4).
   - Per platform: `engine_version`, `url`, `sha256`, `vendored_file`,
     `mirror_urls`. Keep `support` as is unless the runtime evidence changed.
   - For the standard 3.2.x layout, leave the amd64 `install` as
     `{ "kind": "executable", "strip_components": 0, "binary_path": "start-engine", "engine_http_port": 6878 }`.
   - For the APKs, leave `install.kind = android-apk` with the same `abi`,
     `bionic.libdir`, and `bionic.linker`; check that the new APK still
     ships `assets/engine/<abi>_private_py.zip`, `<abi>_private_res.zip`, and
     `public_res.zip` (`unzip -l <apk> | grep assets/engine/`) — the
     installer fails the build otherwise.
4. Publish the vendored files as GitHub Release assets so the mirrors
   resolve. The tag is `acestream-binaries-<amd64 version>-<android version>`:

   ```bash
   gh release create acestream-binaries-<VERSION>-<ANDROID_VERSION> --target main --latest=false \
     docker/vendor/acestream/*.tar.gz docker/vendor/acestream/*.apk docker/vendor/acestream/SHA256SUMS \
     docker/vendor/bionic/*.deb
   ```

5. Run the manifest validator + docker tests locally:

   ```bash
   python3 scripts/ci/validate_docker_manifest_metadata.py
   PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker
   ```

6. (Optional) run the full flavor validator. It now builds in auto mode,
   i.e. with the real vendored engine for `PLATFORM` (default `linux/amd64`).
   Set `ACESTREAM_SOURCE=fixture` for the fast contract-test fixture build
   that omitting the download URL used to produce:

   ```bash
   bash scripts/ci/validate_docker_flavor_targets.sh
   ACESTREAM_SOURCE=fixture bash scripts/ci/validate_docker_flavor_targets.sh
   PLATFORM=linux/arm64 bash scripts/ci/validate_docker_flavor_targets.sh   # QEMU on amd64 hosts
   ```

7. Runtime-test the ARM engine on hardware (arm64 at minimum) before merging
   a new Android pin: `docs/ops/acestream-arm-engine.md`, "Testing on a
   Raspberry Pi".
8. Open a PR. The Jenkins `acestream-scraper-pr` job will (a) dry-run the
   flavor matrices, which re-resolves the manifest per platform, (b) build
   `scraper-acestream` for `linux/amd64` with sha256 verification from the
   vendored copy, (c) run the amd64 runtime smoke that exercises the engine
   end-to-end, and (d) build the arm64 + armv7 installer stages under QEMU
   and assert their layout.

### Notes on install kinds

The install pipeline supports two `install.kind` values: `executable` and
`android-apk`. (Superseded on 2026-08-27: this section previously stated that
`executable` was the only kind.)

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

`android-apk` (arm64, armv7): the APK payload brings its own bionic CPython
3.8, so no interpreter is grafted; instead the runtime stage copies the
staged bionic userland to `/system` (the payload's ELF interpreter path is
hard-coded to `/system/bin/linker*`). The Linux-side glue lives in
`docker/scripts/acestream-android/` (`start-engine`, `main_linux.py`,
`app_bridge.py`, `acestream.conf`). A new APK that changes the bootstrap
contract (`main.py` arguments, `app_bridge` RPC methods, `acestream.conf`
tokens) is where breakage would show up — diff the new APK's `main.py` and
`app_bridge.py` against the `*.android-orig` copies from the previous build.
The bionic package only needs bumping if a new engine needs symbols missing
from Android 9's libc/libc++; any bionic change must be re-verified on
hardware (the page-size guard in `start-engine` reflects the Android 9
linker's 4 KB requirement).

If a future release ships an archive that fits neither kind (for example a
tarball without `start-engine` at the root), add a new kind rather than
overloading these two. The `kind` discriminator is in place; the branches to
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
