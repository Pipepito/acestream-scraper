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
