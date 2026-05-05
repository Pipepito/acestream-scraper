# Phase 5 Multi-Arch Evidence

## How evidence is produced for a release

The release pipeline (`.github/workflows/release.yml`) requires the
`multiarch-runtime-smoke` job to pass before any image is built or pushed.
That job invokes:

```
python3 scripts/phase_gates/phase5_gate_runner.py --profile full \
  --json-output > phase5-gate-report-full.json
```

against the release commit. The full profile builds every flavor for every
required platform, runs `phase5_arch_smoke.sh` against `linux/arm/v7` and
`linux/arm64` images under QEMU, and probes `/api/v1/health`. The resulting
`phase5-gate-report-full.json` plus the four
`phase5-build-result-full-{scraper,scraper-acestream,scraper-acexy,scraper-acestream-acexy}.json`
files are uploaded as the workflow artifact `phase5-multiarch-full-evidence`.

For PRs, `multiarch-validation.yml::multiarch-full` runs the same profile
when the PR touches `Dockerfile`, `docker/**`, `scripts/ci/build_multiarch_*`,
`scripts/ci/verify_multiarch_*`, `scripts/ci/phase5_arch_smoke.sh`,
`scripts/ci/flavor_platforms.py`, `scripts/phase_gates/phase5_*`, or any of
the runtime entrypoint scripts. PRs without changes in those areas only run
the dry-run quick profile to keep everyday CI cost predictable; risky
multi-arch changes get real smoke before merge automatically.

We deliberately do **not** check `phase5-build-result-*.json` files into the
repo anymore. They were checked in once, became stale, and started reading
like signoff evidence when they were really configuration snapshots. The
current contract: evidence lives on the workflow run, this doc links to the
specific run for the release SHA.

## Per-release record (template)

When tagging a release, fill in this section by linking the artifact from
the corresponding GitHub Actions release run.

| Field | Value |
|---|---|
| Release tag | `<v2.0.0>` |
| Commit SHA | `<full sha>` |
| Tag date | `<YYYY-MM-DD>` |
| Workflow run | `<https://github.com/.../actions/runs/<id>>` |
| `phase5-gate-report-full.json` | `<artifact link>` |
| `linux/amd64` build + smoke | `<Pass / Fail>` |
| `linux/arm64` build + smoke | `<Pass / Fail>` |
| `linux/arm/v7` build + smoke | `<Pass / Fail>` |
| AceStream-flavor platforms | `<from docker/manifests/acestream.json — currently amd64 only>` |
| Operator signoff | `<name + date>` |

## Architecture coverage by flavor

Source of truth: `docker/manifests/platforms.json` and
`docker/manifests/acestream.json`, intersected by
`scripts/ci/flavor_platforms.py`.

| Flavor | Platforms |
|---|---|
| `scraper` | `linux/amd64`, `linux/arm/v7`, `linux/arm64` |
| `scraper-acexy` | `linux/amd64`, `linux/arm/v7`, `linux/arm64` |
| `scraper-acestream` | intersection of baseline ∩ `acestream.json` (today: `linux/amd64`) |
| `scraper-acestream-acexy` (== `latest`) | intersection of baseline ∩ `acestream.json` (today: `linux/amd64`) |

To enable ARM for the AceStream-bearing flavors, see
`docs/ops/multiarch-manifest-updates.md`.

## Android TV caveats

`docs/architecture/deployment.md` "Android TV Notes" calls out:

- Prefer `linux/arm64` over `linux/arm/v7` when the device firmware allows
  64-bit containers.
- Reduced background concurrency recommended on lower-memory ARMv7 devices.
- Validate storage I/O on removable media before production rollouts.
- Run the Phase 5 smoke checklist (`docs/migration/phase5-architecture-smoke-checklist.md`)
  before signing off a new device class.

The release workflow's runtime smoke covers QEMU emulation only — first-time
Android TV class rollouts should still run the manual checklist on a real
device before declaring a flavor production-ready for that hardware.
