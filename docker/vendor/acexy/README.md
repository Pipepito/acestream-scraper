# Vendored Acexy source

Source archive of the exact Acexy release pinned in `docker/manifests/acexy.json`,
kept in-repo so image builds do not depend on cloning GitHub. The Jenkins
runner's egress goes through Cloudflare WARP, and GitHub intermittently answers
anonymous `git clone` from those exits with an auth challenge
(`could not read Username for 'https://github.com'`), which broke the
`scraper-acexy` builds and the Acexy runtime smoke test.

| File | Upstream source |
| --- | --- |
| `acexy-0.2.2.tar.gz` | https://github.com/Javinator9889/acexy/archive/refs/tags/0.2.2.tar.gz (tag `0.2.2`, commit `162972e`) |

`SHA256SUMS` holds the checksum; it must equal `sha256` in the manifest. Verify
with `shasum -a 256 -c SHA256SUMS` (macOS) or `sha256sum -c SHA256SUMS` (Linux).

## How the build uses it

`scripts/ci/build_multiarch_images.sh` derives `ACEXY_VENDORED_FILE` and
`ACEXY_SHA256` from the manifest for the Acexy-bearing flavors. The
`acexy-builder` stage in the root `Dockerfile` then picks the source in this
order:

1. `ACEXY_REPO=fixture` — the contract-test stub under `docker/testdata/acexy/`.
2. The vendored archive named by `ACEXY_VENDORED_FILE` (sha256-verified), bind-mounted from `docker/vendor`.
3. `git clone` of `ACEXY_REPO` at `ACEXY_REF` (explicit `--build-arg` overrides, or a manifest without a vendored file).
4. The fixture when no source is named at all.

Go module dependencies are still fetched from the Go module proxy at build time.

## Bumping the pin

1. Download `https://github.com/Javinator9889/acexy/archive/refs/tags/<version>.tar.gz` as `acexy-<version>.tar.gz` here.
2. Update `SHA256SUMS` and `docker/manifests/acexy.json` (`ref`, `version`, `vendored_file`, `sha256`).
3. Run `python3 scripts/ci/validate_docker_manifest_metadata.py` and `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_vendor.py`.
4. Remove the previous archive.
