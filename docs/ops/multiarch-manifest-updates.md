# Multi-Architecture Manifest Updates

`docker/manifests/acestream.json` is the canonical declaration of which
container platforms have a working AceStream binary available. The flavor
platform resolver (`scripts/ci/flavor_platforms.py`) intersects each flavor's
declared platform set against this manifest, so anything not listed here is
silently dropped from `scraper-acestream`, `scraper-acestream-acexy`, and
`latest` builds.

Today the manifest lists `linux/amd64` only, which is correct for the
upstream AceStream binaries the project pins. When AceStream upstream ships
ARM builds, this is the playbook for enabling them.

## When to update

- A new upstream AceStream release adds platform support that we want our
  flavors to consume (for example, `linux/arm64`).
- An existing platform breaks and needs to be temporarily disabled.
- A pinned binary URL changes (download URL, archive layout, SHA256).

Manifest changes are operator-driven. There is no scheduled job that watches
upstream — by design. AceStream releases are infrequent and changes to the
container surface need explicit human approval before they ship.

## How to update

1. Locate the upstream release you want to pin (download URL, SHA256,
   archive type, binary path inside the archive).
2. Add a platform entry to `docker/manifests/acestream.json`. The schema
   matches what `Dockerfile`'s `acestream-installer` stage expects:
   ```json
   {
     "version": "<upstream release tag>",
     "platforms": {
       "linux/amd64": {
         "download_url": "...",
         "sha256": "...",
         "archive_type": "tar.gz",
         "strip_components": 1,
         "binary_path": "acestreamengine"
       },
       "linux/arm64": {
         "download_url": "...",
         "sha256": "...",
         "archive_type": "tar.gz",
         "strip_components": 1,
         "binary_path": "acestreamengine"
       }
     }
   }
   ```
3. **Do not** edit `docker/manifests/platforms.json` — that file declares the
   baseline platform matrix per flavor and is correct as-is. The intersection
   logic in `flavor_platforms.py` handles the rest.

## How to verify locally

```bash
# 1. Render the resolved platform list for each affected flavor.
python3 scripts/ci/flavor_platforms.py --flavor scraper-acestream
python3 scripts/ci/flavor_platforms.py --flavor scraper-acestream-acexy

# 2. Dry-run the build to confirm the matrix is accepted.
bash scripts/ci/build_multiarch_images.sh \
  --dry-run --flavor scraper-acestream \
  --result-file /tmp/phase5-build-result-scraper-acestream.json

bash scripts/ci/verify_multiarch_manifest.sh \
  --result-file /tmp/phase5-build-result-scraper-acestream.json \
  --flavor scraper-acestream

# 3. Run the full smoke profile (requires QEMU + Buildx; takes ~30-45 min).
python3 scripts/phase_gates/phase5_gate_runner.py --profile full \
  --json-output > /tmp/phase5-gate-report-full.json
```

The full-profile gate actually downloads the new binary, builds the image
under QEMU, boots it, and probes `/api/v1/health`. Build success alone is
not enough — pitfall #4 in `.planning/research/PITFALLS.md` calls out the
"build green but runtime broken" failure mode for ARM.

## How to verify in CI

A PR that touches `docker/manifests/acestream.json` automatically activates
the `multiarch-full` job in `.github/workflows/multiarch-validation.yml`
(see the `paths-filter` config — the manifest path is on that watch list
indirectly via the `docker/**` filter). The job runs the full profile
across every flavor and uploads the gate report as a workflow artifact.

For release branches, `.github/workflows/release.yml` requires the
`multiarch-runtime-smoke` job to pass before any image is pushed. That job
runs the full profile too and uploads `phase5-gate-report-full.json` as a
release artifact, so the evidence link in
`docs/release/phase5-multiarch-evidence.md` always points at a fresh result.

## Rollback

If a freshly-published manifest breaks runtime smoke on a new platform:

1. Revert the `docker/manifests/acestream.json` change.
2. Re-run the release workflow on the previous SHA.
3. Open an issue with the failing gate report attached so the next
   manifest attempt has the failure record to work from.

## Bumping the AceStream version

The AceStream payload is described entirely by `docker/manifests/acestream.json`.
The manifest is consumed at build time by `scripts/ci/build_multiarch_images.sh`
(via `scripts/ci/derive_acestream_build_args.py`), which converts each field
into a `--build-arg` for `docker buildx`. The CI runtime smoke
(`backend/tests/docker/test_acestream_runtime_smoke.py`, gated by
`.github/workflows/pull_request.yml`) verifies the engine actually starts
and responds on port 6878 in the resulting image.

### Steps

1. Find the upstream tarball URL on https://download.acestream.media/. As of
   AceStream 3.2.x, the URL pattern is
   `acestream_<VERSION>_ubuntu_22.04_x86_64_py3.10.tar.gz` and the tarball
   ships a top-level `start-engine` shell wrapper plus a real ELF binary
   `acestreamengine`. Older releases may use different filenames.
2. Compute the sha256: `curl -sL <url> | shasum -a 256`.
3. Update `docker/manifests/acestream.json`:
   - Set `version`, `platforms.linux/amd64.url`, and `sha256`.
   - For the standard 3.2.x layout, leave `install` as
     `{ "strip_components": 0, "kind": "executable", "binary_path": "start-engine", "engine_http_port": 6878 }`.
4. Run the manifest validator + docker tests locally:

   ```bash
   python3 scripts/ci/validate_docker_manifest_metadata.py
   PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker
   ```

5. (Optional) run the full flavor validator to catch fixture-mode regressions:

   ```bash
   bash scripts/ci/validate_docker_flavor_targets.sh
   ```

6. Open a PR. CI's `required-checks` job will (a) re-derive the manifest's
   build args via `derive_acestream_build_args.py`, (b) build
   `scraper-acestream` against the upstream URL with sha256 verification,
   and (c) run the runtime smoke that exercises the engine end-to-end.

### Notes for non-3.2.x releases

The current install pipeline supports a single `install.kind` value:
`executable`. The runtime image grafts a `python3.10` interpreter from
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

If a future release ships a tarball that does NOT include `start-engine`
at the root, you will need to add support for a different install kind
(e.g., a `python_module` or `command` kind that synthesizes a wrapper).
The schema has the `kind` discriminator in place — only
`scripts/ci/validate_docker_manifest_metadata.py` and
`docker/scripts/install-acestream.sh` need new branches.
