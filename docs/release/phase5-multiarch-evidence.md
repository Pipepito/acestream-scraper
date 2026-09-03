# Phase 5 Multi-Arch Evidence

## How evidence is produced for a release

All CI runs on Jenkins (`docs/ops/jenkins-ci.md`). The GitHub Actions
workflows — including the former `multiarch-runtime-smoke` job and its
`phase5-multiarch-full-evidence` artifact that earlier revisions of this
document referenced — were retired on 2026-08-26.

**PR job (`acestream-scraper-pr`, `Jenkinsfile`)** — every PR runs:

- `Multi-Arch Quick Profile`: dry-run `build_multiarch_images.sh` +
  `verify_multiarch_manifest.sh` for all four flavors,
  `phase5_arch_smoke.sh --dry-run --platforms linux/arm/v7,linux/arm64`, and
  `scripts/phase_gates/phase5_gate_runner.py --profile quick`; archives
  `phase5-build-result-quick-*.json` and `phase5-gate-report-quick.json`.
- `Acestream Engine Runtime Smoke`: builds `scraper-acestream` for the
  runner's native platform (`--platforms linux/amd64 --load`) and runs
  `backend/tests/docker/test_acestream_runtime_smoke.py` (parametrized over
  the manifest platforms the host can execute: `linux/amd64` always,
  `linux/arm64` only on an arm64 host), `test_acexy_runtime_smoke.py`, and
  `test_install_acestream.py -k android_apk_install_layout` (QEMU builds of
  the `linux/arm64` + `linux/arm/v7` installer stage — no engine execution,
  the Android engine payload cannot run under qemu-user).

**Release pipeline (`acestream-scraper-release`, `jenkins/release.Jenkinsfile`
→ `scripts/ci/run_jenkins_release.sh`)** — before any tag reaches Docker Hub:

1. `bash scripts/ci/run_cutover_required_checks.sh --profile full`;
2. dry-run build + `verify_multiarch_manifest.sh` per flavor
   (`phase5-build-result-release-<flavor>.json`);
3. the same real engine smoke as the PR job
   (`test_acestream_runtime_smoke.py` + `android_apk_install_layout`);
4. multi-platform `--push` per flavor, then `verify_multiarch_manifest.sh
   --image <tag>` against every published tag;
5. `phase5-build-result-release-*.json` and
   `phase5-build-result-release-metadata.json` (version, git SHA, tag list)
   are archived on the Jenkins build.

The heavier Phase 5 **full** profile — real QEMU builds of every flavor for
every platform plus `phase5_arch_smoke.sh --platforms linux/arm/v7,linux/arm64`
(boots the baseline `scraper` target under QEMU and probes `/api/v1/health`)
— is not wired into either Jenkins job. Run it manually on the release
commit before merging risky multi-arch changes:

```
python3 scripts/phase_gates/phase5_gate_runner.py --profile full \
  --json-output > phase5-gate-report-full.json
```

It writes `phase5-gate-report-full.json` plus the four
`phase5-build-result-full-{scraper,scraper-acestream,scraper-acexy,scraper-acestream-acexy}.json`
files; attach them to the per-release record below.

We deliberately do **not** check `phase5-build-result-*.json` files into the
repo anymore. They were checked in once, became stale, and started reading
like signoff evidence when they were really configuration snapshots. The
current contract: evidence lives on the Jenkins build (archived artifacts),
this doc links to the specific build for the release SHA.

## Per-release record (template)

When tagging a release, fill in this section by linking the archived
artifacts from the corresponding Jenkins `acestream-scraper-release` build.

| Field | Value |
|---|---|
| Release tag | `<v2.0.0>` |
| Commit SHA | `<full sha>` |
| Tag date | `<YYYY-MM-DD>` |
| Jenkins build | `<acestream-scraper-release build URL>` |
| `phase5-build-result-release-metadata.json` | `<artifact link>` |
| `phase5-gate-report-full.json` (manual full profile) | `<artifact link or "not run">` |
| `linux/amd64` build + smoke | `<Pass / Fail>` |
| `linux/arm64` build + smoke | `<Pass / Fail>` |
| `linux/arm/v7` build + smoke | `<Pass / Fail>` |
| AceStream-flavor platforms | `<from docker/manifests/acestream.json — currently linux/amd64 (stable), linux/arm64 (stable), linux/arm/v7 (experimental)>` |
| AceStream engine smoke on ARM | `<linux/arm64: Pass / Fail / Pending; linux/arm/v7: Pending (real hardware only)>` |
| Operator signoff | `<name + date>` |

## Architecture coverage by flavor

Source of truth: `docker/manifests/platforms.json` and
`docker/manifests/acestream.json`, intersected by
`scripts/ci/flavor_platforms.py`.

| Flavor | Platforms |
|---|---|
| `scraper` | `linux/amd64`, `linux/arm/v7`, `linux/arm64` |
| `scraper-acexy` | `linux/amd64`, `linux/arm/v7`, `linux/arm64` |
| `scraper-acestream` | intersection of baseline ∩ `acestream.json` (today: `linux/amd64`, `linux/arm/v7`, `linux/arm64`) |
| `scraper-acestream-acexy` (== `latest`) | intersection of baseline ∩ `acestream.json` (today: `linux/amd64`, `linux/arm/v7`, `linux/arm64`) |

Until 2026-08-27 the AceStream-bearing flavors resolved to `linux/amd64`
only. Branch `arm-acestream-engine` added `linux/arm64` (`support: stable`)
and `linux/arm/v7` (`support: experimental`) to `docker/manifests/acestream.json`
using the official Android engine; the engine archives are vendored under
`docker/vendor/` (update procedure: `docker/vendor/acestream/README.md`,
manifest schema notes: `docs/ops/multiarch-manifest-updates.md`). Check the
resolved matrix and the manifest locally with:

```
python3 scripts/ci/flavor_platforms.py docker/manifests/platforms.json docker/manifests/acestream.json scraper-acestream
python3 scripts/ci/validate_docker_manifest_metadata.py
```

## AceStream engine on ARM — local smoke evidence

The ARM engine flavors run the official Android engine payload
(`AceStreamCore-3.1.80.0-armv8_64.apk` / `AceStreamCore-3.1.80.0-armv7.apk`)
directly against a minimal Android 9 bionic userland at `/system` — no
chroot, `--privileged`, seccomp profile or extra capabilities. Background:
the status block in `docs/release/arm-acestream-issue-draft.md`; user-facing
caveats: "Known issues" in `docs/release/v2-release-notes.md`.

| Field | Value |
|---|---|
| Date | 2026-08-27 |
| Branch | `arm-acestream-engine` |
| Host | Apple Silicon (arm64), Docker Desktop 28.3 (`docker version` → `28.3.0 linux/arm64`) |
| Command | `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v` (on an arm64 host this parametrizes `linux/amd64` and `linux/arm64`) |
| `linux/arm64` engine smoke | **Pass (2026-09-03)** — `scraper-acestream` built natively with digest-pinned `jopsis/acestream:v3.2.17-fix`; `/webui/api/service?method=get_version` reported `{"platform":"android","version":"3.2.17"}`; the app and image healthcheck passed, search returned the engine catalogue, and `/api/v1/system/services` reported the linked package attribution. [Dashboard evidence](arm64-engine-dashboard.png). A byte-limited request for one current catalogue item returned `failed to load content` identically in the unmodified source container and integrated image, so no successful media-transfer claim is made. |
| `linux/arm/v7` engine smoke | **Pending** — installer stage verified by `test_install_acestream.py -k android_apk_install_layout` (QEMU build); the 32-bit bionic engine cannot execute under qemu-user (`personality(PER_LINUX32)`), so execution needs real ARMv7/AArch32-capable hardware |
| Real-hardware validation | **Pending** — Raspberry Pi 4 / ARMv7 plan in `docs/release/arm-acestream-issue-draft.md` (≥30 min playback, CPU/RAM vs amd64) |

## Android TV caveats

`docs/architecture/deployment.md` "Android TV Notes" calls out:

- Prefer `linux/arm64` over `linux/arm/v7` when the device firmware allows
  64-bit containers.
- Reduced background concurrency recommended on lower-memory ARMv7 devices.
- Validate storage I/O on removable media before production rollouts.
- Run the Phase 5 smoke checklist (`docs/migration/phase5-architecture-smoke-checklist.md`)
  before signing off a new device class.

The release pipeline's runtime smoke executes the AceStream engine on the
amd64 runner only and covers the ARM images through QEMU builds (baseline
app boot under the manual full profile; engine install layout only for the
engine flavors) — first-time Android TV class rollouts should still run the
manual checklist on a real device before declaring a flavor production-ready
for that hardware.
