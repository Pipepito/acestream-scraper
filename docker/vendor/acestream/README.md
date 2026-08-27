# Vendored AceStream engine payloads

Upstream mirror of the exact engine archives pinned in
`docker/manifests/acestream.json`, kept in-repo so image builds do not depend
on reaching `download.acestream.media` (geo-blocked from many networks; the
Jenkins runner normally needs WARP to fetch them).

| File | Platform | Upstream source |
| --- | --- | --- |
| `acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz` | `linux/amd64` (native Linux engine 3.2.11) | https://download.acestream.media/linux/acestream_3.2.11_ubuntu_22.04_x86_64_py3.10.tar.gz |
| `AceStreamCore-3.1.80.0-armv8_64.apk` | `linux/arm64` (Android engine 3.1.80.0, arm64-v8a) | https://download.acestream.media/products/android/acestream-core/armv8_64/latest → https://download.acestream.media/android/core.web/stable/AceStreamCore-3.1.80.0-armv8_64.apk |
| `AceStreamCore-3.1.80.0-armv7.apk` | `linux/arm/v7` (Android engine 3.1.80.0, armeabi-v7a) | https://download.acestream.media/products/android/acestream-core/armv7/latest → https://download.acestream.media/android/core.web/stable/AceStreamCore-3.1.80.0-armv7.apk |

`SHA256SUMS` holds the checksums; they must equal the `sha256` values in the
manifest. Verify with `shasum -a 256 -c SHA256SUMS` (macOS) or
`sha256sum -c SHA256SUMS` (Linux).

Upstream publishes native Linux tarballs for x86_64 only; the ARM engines are
the official Android APKs listed on https://docs.acestream.media/products/.

## How the build uses them

`docker/scripts/install-acestream.sh` resolves the engine archive in this
order and verifies the pinned sha256 whichever source wins:

1. a local copy under `docker/vendor/` (bind-mounted read-only into the
   `acestream-installer` build stage as `ACESTREAM_VENDOR_ROOT=/tmp/acestream-vendor`;
   nothing is copied into an image layer);
2. the upstream `url` from the manifest;
3. each entry of the manifest's `mirror_urls`, which point at the GitHub
   Release mirror of the same files:
   `https://github.com/Pipepito/acestream-scraper/releases/download/acestream-binaries-3.2.11-3.1.80.0/<file>`.

## Updating

1. Download the new upstream archive(s) and add them here; remove the
   superseded ones (old versions stay reachable in git history and on the
   corresponding GitHub Release).
2. Regenerate `SHA256SUMS` (`shasum -a 256 <files> > SHA256SUMS`).
3. Update `docker/manifests/acestream.json` (`url`, `sha256`, `vendored_file`,
   `mirror_urls`, `engine_version`, and the top-level `version` /
   `android_version` / `mirror_base_url`; for ARM also the `install.bionic`
   block when the `.deb` changes) and publish a new
   `acestream-binaries-<version>-<android_version>` GitHub Release with the
   same files, including the bionic packages the ARM `mirror_urls` point at:
   `gh release create <tag> --target main --latest=false
   docker/vendor/acestream/*.tar.gz docker/vendor/acestream/*.apk
   docker/vendor/acestream/SHA256SUMS docker/vendor/bionic/*.deb`.
4. Run `python3 scripts/ci/validate_docker_manifest_metadata.py` and
   `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker`.
