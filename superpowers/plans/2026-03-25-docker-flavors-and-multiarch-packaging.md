# Docker Flavors And Multi-Arch Packaging Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current single-purpose Docker packaging with one readable multi-stage Dockerfile that publishes tag-based flavors under `pipepito/acestream-scraper`, keeps WARP in all images, preserves ZeroNet compatibility via sidecar-friendly configuration, and drives AceStream/Acexy availability from committed metadata manifests.

**Architecture:** Create one shared Docker packaging system with flavor-specific final targets and manifest-driven install metadata. Extend the existing buildx scripts and GitHub workflows so each flavor advertises only the platforms it truly supports, while preserving the env-driven runtime contract through canonical `entrypoint.sh`, `warp-setup.sh`, and `healthcheck.sh` scripts.

**Tech Stack:** Docker multi-stage builds, Docker Buildx, GitHub Actions, Bash, JSON manifests, Python backend runtime, Node frontend build, Go-based Acexy build, Cloudflare WARP

---

## File Structure

- Modify: `Dockerfile` - replace the current single image build with named multi-stage flavor targets
- Modify: `docker-compose.yml` - align local defaults with the new tag/flavor model and explicit ZeroNet sidecar contract
- Create: `docker/manifests/platforms.json` - baseline platform matrix plus per-flavor platform rules
- Create: `docker/manifests/acestream.json` - AceStream install metadata keyed by Docker platform
- Create: `docker/manifests/acexy.json` - Acexy pinned source metadata
- Create: `entrypoint.sh` - canonical runtime startup script for all Docker flavors
- Modify: `warp-setup.sh` - keep WARP startup compatible with the new runtime contract and fail-fast behavior
- Modify: `healthcheck.sh` - make health checks flavor-aware and env-aware
- Modify: `scripts/ci/build_multiarch_images.sh` - support flavor targets, manifest inputs, tag lists, and flavor-specific platform derivation
- Modify: `scripts/ci/verify_multiarch_manifest.sh` - support flavor-aware verification inputs and explicit required platform derivation
- Modify: `.github/workflows/release.yml` - publish `pipepito/acestream-scraper` flavor tags instead of a single `-v2` image target
- Modify: `.github/workflows/multiarch-validation.yml` - validate each flavor’s dry-run matrix
- Modify: `.github/workflows/pull_request.yml` - keep PR multi-arch checks aligned with the flavor-aware build script if needed
- Modify: `scripts/ci/phase5_arch_smoke.sh` - support flavor-aware smoke checks if current defaults assume one universal image
- Modify: `scripts/phase_gates/phase5_gate_config.yaml` - reflect flavor-aware multi-arch verification commands if phase gates consume the old one-image assumption
- Modify: `wiki/Docker.md` - document new tags, runtime env expectations, and WARP/ZeroNet behavior
- Modify: `README.md` and/or `docs/architecture/deployment.md` - update container usage examples and release expectations
- Create: focused tests or validation fixtures only if existing CI script coverage is insufficient to lock the new manifest/tag behavior

## Chunk 1: Metadata Manifests And Flavor Rules

### Task 1: Add committed metadata manifests for platforms, AceStream, and Acexy

**Files:**
- Create: `docker/manifests/platforms.json`
- Create: `docker/manifests/acestream.json`
- Create: `docker/manifests/acexy.json`
- Reference: `docs/superpowers/specs/2026-03-25-docker-flavors-design.md`

- [ ] **Step 1: Write the failing manifest validation check**

Use either a focused shell check or a small Python test helper to assert the expected files and minimum schema keys exist.

Example expectation:

```python
def test_docker_manifests_define_required_flavor_metadata():
    platforms = load_json('docker/manifests/platforms.json')
    acestream = load_json('docker/manifests/acestream.json')
    acexy = load_json('docker/manifests/acexy.json')
    assert 'baseline_platforms' in platforms
    assert 'flavors' in platforms
    assert 'version' in acestream
    assert 'platforms' in acestream
    assert 'repo' in acexy
    assert 'ref' in acexy
```

- [ ] **Step 2: Run the manifest check to verify it fails**

Run: the smallest relevant validation command you added
Expected: FAIL because the manifest files do not exist yet

- [ ] **Step 3: Create `docker/manifests/platforms.json`**

Define:
- baseline multi-arch matrix for flavors that do not require AceStream
- explicit flavor-to-platform rules
- the fact that `latest` and bare version tags map to the full AceStream+Acexy flavor

- [ ] **Step 4: Create `docker/manifests/acestream.json`**

Include:
- current supported AceStream platform entries
- per-platform URL
- version label
- checksum field or explicit empty value when unavailable
- any archive/install hints needed by the Dockerfile

- [ ] **Step 5: Create `docker/manifests/acexy.json`**

Include:
- upstream repository URL
- pinned ref/version
- expected binary metadata if useful

- [ ] **Step 6: Run the manifest check to verify it passes**

Run: the same focused validation command
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add docker/manifests/platforms.json docker/manifests/acestream.json docker/manifests/acexy.json
git commit -m "feat: add Docker flavor metadata manifests"
```

## Chunk 2: Canonical Runtime Scripts And Fail-Fast Startup

### Task 2: Restore and standardize Docker runtime scripts

**Files:**
- Create: `entrypoint.sh`
- Modify: `warp-setup.sh`
- Modify: `healthcheck.sh`

- [ ] **Step 1: Write failing runtime contract tests or script assertions**

Add focused validation for these cases:
- enabling AceStream in a flavor without AceStream exits clearly
- enabling Acexy in a flavor without Acexy exits clearly
- enabling Acexy with `ENABLE_ACESTREAM_ENGINE=false` and default localhost engine settings exits clearly
- disabled optional services do not make health checks fail

- [ ] **Step 2: Run the runtime validation to verify it fails**

Run: the smallest script/test command covering the new cases
Expected: FAIL because the canonical runtime script and validations do not exist yet

- [ ] **Step 3: Create `entrypoint.sh` from the approved runtime contract**

Implement:
- log directory setup
- optional WARP initialization
- env normalization
- flavor capability checks
- optional AceStream/Acexy startup
- ZeroNet compatibility config for sidecar-driven use
- app startup and process monitoring

- [ ] **Step 4: Update `warp-setup.sh` for explicit fail-fast semantics**

Ensure:
- `ENABLE_WARP=false` skips setup cleanly
- `ENABLE_WARP=true` surfaces capability/setup failures clearly

- [ ] **Step 5: Update `healthcheck.sh` to be feature-aware**

Ensure:
- app health is always checked
- Acexy is only checked when enabled
- external-engine mode checks use the explicit external host/port contract
- disabled features do not fail health checks

- [ ] **Step 6: Run the runtime validation again**

Run: the same focused runtime validation command
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add entrypoint.sh warp-setup.sh healthcheck.sh
git commit -m "feat: standardize Docker runtime startup contract"
```

## Chunk 3: Multi-Stage Dockerfile With Flavor Targets

### Task 3: Replace the Dockerfile with named flavor targets

**Files:**
- Modify: `Dockerfile`
- Reference: `docker/manifests/platforms.json`
- Reference: `docker/manifests/acestream.json`
- Reference: `docker/manifests/acexy.json`

- [ ] **Step 1: Write a failing dry-run build check for all flavor targets**

Cover:
- `scraper`
- `scraper-acestream`
- `scraper-acexy`
- `scraper-acestream-acexy`

The check should prove the Dockerfile exposes named targets and accepts the required build arguments.

- [ ] **Step 2: Run the dry-run build check to verify it fails**

Run: a minimal `docker buildx build --target ... --dry-run` style validation or the repo’s equivalent script wrapper
Expected: FAIL because the current Dockerfile only defines one image shape

- [ ] **Step 3: Implement the shared base stages**

Add stages for:
- frontend build
- Python app dependencies
- shared runtime base with WARP and common dependencies

- [ ] **Step 4: Implement optional installer stages**

Add stages for:
- AceStream install from manifest-driven build args
- Acexy build/install from manifest-driven build args

- [ ] **Step 5: Add final named flavor targets**

Ensure final targets map directly to:
- `scraper`
- `scraper-acestream`
- `scraper-acexy`
- `scraper-acestream-acexy`

- [ ] **Step 6: Wire in runtime scripts and required env defaults**

Copy:
- `entrypoint.sh`
- `warp-setup.sh`
- `healthcheck.sh`

Preserve the env-driven runtime behavior from the spec.

- [ ] **Step 7: Run the dry-run build check again**

Run: the same flavor-target validation command
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add Dockerfile entrypoint.sh warp-setup.sh healthcheck.sh
git commit -m "feat: add Docker flavor build targets"
```

## Chunk 4: Flavor-Aware Multi-Arch Build Scripts

### Task 4: Make CI build scripts derive platforms and tags from manifests

**Files:**
- Modify: `scripts/ci/build_multiarch_images.sh`
- Modify: `scripts/ci/verify_multiarch_manifest.sh`
- Modify: `scripts/ci/phase5_arch_smoke.sh` if needed

- [ ] **Step 1: Write failing script-level checks for flavor-aware build metadata**

Cover:
- selecting a flavor target
- deriving its allowed platforms from `docker/manifests/platforms.json`
- restricting AceStream flavors to the AceStream-supported platform subset
- writing result metadata that records flavor and selected platforms

- [ ] **Step 2: Run the script-level checks to verify they fail**

Run: focused dry-run invocations of the existing build scripts
Expected: FAIL because the scripts currently assume one image and one hardcoded matrix

- [ ] **Step 3: Extend `build_multiarch_images.sh`**

Add support for:
- flavor/target input
- one or many tags per invocation
- manifest file inputs or standard manifest lookup paths
- flavor-specific platform derivation
- result metadata that records flavor name and target tag set

- [ ] **Step 4: Extend `verify_multiarch_manifest.sh`**

Allow verification to work cleanly with flavor-specific expectations rather than one universal required platform list.

- [ ] **Step 5: Update smoke/dry-run helpers if they assume a single canonical image**

Keep changes minimal and aligned with the flavor metadata model.

- [ ] **Step 6: Re-run dry-run flavor checks**

Run: focused flavor-aware dry-run commands for at least one baseline flavor and one AceStream flavor
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add scripts/ci/build_multiarch_images.sh scripts/ci/verify_multiarch_manifest.sh scripts/ci/phase5_arch_smoke.sh
git commit -m "feat: make Docker build scripts flavor-aware"
```

## Chunk 5: GitHub Actions And Release Tag Publishing

### Task 5: Publish flavor tags under `pipepito/acestream-scraper`

**Files:**
- Modify: `.github/workflows/release.yml`
- Modify: `.github/workflows/multiarch-validation.yml`
- Modify: `.github/workflows/pull_request.yml` if needed
- Modify: `scripts/phase_gates/phase5_gate_config.yaml` if phase gates encode the old assumptions
- Reference: `version.txt`

- [ ] **Step 1: Write failing workflow-level expectations**

Check that:
- release no longer targets `pipepito/acestream-scraper-v2`
- workflows run flavor-aware dry-run validation
- `latest` and bare version tags map to the full flavor
- explicit flavor tags are also built

- [ ] **Step 2: Run the workflow expectation check to verify it fails**

Run: focused grep/assertion command or scripted check against the workflow files
Expected: FAIL because the workflows still assume one canonical `-v2` image

- [ ] **Step 3: Update `release.yml`**

Implement:
- cutover to `pipepito/acestream-scraper`
- flavor-aware build invocations
- tag sets for `latest`, bare version, and explicit flavor tags
- flavor-specific platform verification

- [ ] **Step 4: Update `multiarch-validation.yml` and related CI workflows**

Ensure dry-run checks cover flavor-aware build matrices rather than one universal image.

- [ ] **Step 5: Update phase gate config if needed**

Keep the build verification consistent with the new flavor-aware scripts.

- [ ] **Step 6: Run the workflow expectation check again**

Run: the same focused validation command
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/release.yml .github/workflows/multiarch-validation.yml .github/workflows/pull_request.yml scripts/phase_gates/phase5_gate_config.yaml
git commit -m "feat: publish Docker image flavors"
```

## Chunk 6: Compose And Documentation Alignment

### Task 6: Update local compose and user-facing Docker docs

**Files:**
- Modify: `docker-compose.yml`
- Modify: `wiki/Docker.md`
- Modify: `README.md`
- Modify: `docs/architecture/deployment.md` if needed

- [ ] **Step 1: Write failing doc/config assertions**

Check that docs/config reflect:
- `latest` as the full image
- explicit flavor tags
- WARP in all flavors
- ZeroNet as an external sidecar/service contract
- AceStream platform availability via manifest-driven support

- [ ] **Step 2: Run the assertions to verify they fail**

Run: focused grep/assertion checks or a small docs validation script
Expected: FAIL because current docs still describe the older single-image model

- [ ] **Step 3: Update `docker-compose.yml`**

Align it with:
- the new image/tag strategy
- the explicit ZeroNet sidecar model
- current runtime env expectations

- [ ] **Step 4: Update Docker docs**

Document:
- what each tag installs
- what `latest` means
- how env vars enable installed features
- required WARP capabilities
- how to add new AceStream architectures through `docker/manifests/acestream.json`

- [ ] **Step 5: Re-run the doc/config assertions**

Run: the same focused validation command
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml wiki/Docker.md README.md docs/architecture/deployment.md
git commit -m "docs: explain Docker image flavors and runtime options"
```

## Chunk 7: Full Verification

### Task 7: Verify flavor metadata, scripts, workflows, and Docker targets together

**Files:**
- Modify only if verification uncovers a real gap

- [ ] **Step 1: Run manifest validation**

Run: the manifest validation command introduced in Chunk 1
Expected: PASS

- [ ] **Step 2: Run flavor-aware build dry-runs**

Run at least:

```bash
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy
```

Expected: PASS with flavor-specific platform metadata

- [ ] **Step 3: Verify platform expectations**

Run flavor-aware manifest/result verification commands for:
- one baseline flavor
- one AceStream flavor

Expected: PASS with correct platform subsets

- [ ] **Step 4: Run workflow/config validation**

Run: the workflow/doc assertion commands introduced earlier
Expected: PASS

- [ ] **Step 5: If local Docker is available, run one smoke build per flavor target**

Use the smallest practical platform-loaded checks.

Expected:
- all targets build
- AceStream flavors only build on supported platforms

- [ ] **Step 6: If verification reveals a mismatch, add a focused regression check before fixing it**

Prefer the smallest script or assertion that prevents recurrence.

- [ ] **Step 7: Commit**

```bash
git add Dockerfile docker/manifests scripts .github/workflows docker-compose.yml wiki/Docker.md README.md docs/architecture/deployment.md
git commit -m "test: verify Docker flavor packaging workflow"
```
