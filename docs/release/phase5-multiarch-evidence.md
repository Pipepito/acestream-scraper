# Phase 5 Multi-Arch Evidence

## Release Metadata

- Release ref: `Pending (not captured in this quick evidence pass)`
- Commit SHA: `5aa11f74cfa4b1119c8dcf0092120b61161ca4dd`
- Date: `2026-04-24`

## Required Architecture Claims

- Checked-in dry-run metadata shows `linux/arm/v7` in the configured platform matrix for `scraper` and `scraper-acexy`; this pass does not include evidence of a successful `linux/arm/v7` build.
- Checked-in dry-run metadata shows `linux/arm64` in the configured platform matrix for `scraper` and `scraper-acexy`; this pass does not include evidence of a successful `linux/arm64` build.
- Runtime smoke checks for non-`amd64` targets remain pending; no supported runtime signoff artifact was captured in this quick evidence pass.

## Evidence Artifacts

- Inspected dry-run PR artifacts: `phase5-build-result-pr-scraper.json`, `phase5-build-result-pr-scraper-acestream.json`, `phase5-build-result-pr-scraper-acexy.json`, `phase5-build-result-pr-scraper-acestream-acexy.json`
- Inspected dry-run release artifacts: `phase5-build-result-release-scraper.json`, `phase5-build-result-release-scraper-acestream.json`, `phase5-build-result-release-scraper-acexy.json`, `phase5-build-result-release-scraper-acestream-acexy.json`
- Supported artifact observations from those eight files: all are `dry_run: true`, `push: false`, and `load: false`; PR and release pairs are materially the same except `generated_at`.
- Supported scope of those artifacts: they prove matrix/configuration encoding only. They do not prove successful builds, pushes, manifest publication, runtime smoke results, or release signoff.
- Pending artifacts not captured in this quick evidence pass: `phase5-gate-report-full.json`, `phase5-build-result-full.json`, and any release signoff record demonstrating successful multi-arch build/push/runtime completion.

## Command Record

```bash
git rev-parse HEAD
date +%F
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/run_cutover_required_checks.sh --profile quick
rg -n "<placeholder>" docs/release/phase5-multiarch-evidence.md
```

Full-profile command/artifact not run in this pass:

```bash
python3 scripts/phase_gates/phase5_gate_runner.py --profile full --json-output > phase5-gate-report-full.json
```

## Result Summary

Configuration evidence from inspected dry-run artifacts is listed separately from quick validation results captured in this pass.

| Check | Status | Notes |
|------|--------|-------|
| Multi-arch matrix includes `linux/arm/v7` | Configured in inspected dry-run artifacts for `scraper` and `scraper-acexy`; absent from inspected `scraper-acestream` variants | This is configuration evidence only, confirmed from the eight checked-in dry-run JSON artifacts inspected in this pass. |
| Multi-arch matrix includes `linux/arm64` | Configured in inspected dry-run artifacts for `scraper` and `scraper-acexy`; absent from inspected `scraper-acestream` variants | This is configuration evidence only, confirmed from the eight checked-in dry-run JSON artifacts inspected in this pass. |
| Quick profile validation result | Passed | Separate from the dry-run matrix/configuration evidence above: fresh repo-level quick verification now passes for `bash scripts/ci/run_v2_test_suite.sh --profile quick` and `bash scripts/ci/run_cutover_required_checks.sh --profile quick` on this commit. |
| Runtime smoke (`linux/arm/v7`) | Pending | No supported runtime smoke artifact or signoff for `linux/arm/v7` was captured in this quick evidence pass. |
| Runtime smoke (`linux/arm64`) | Pending | No supported runtime smoke artifact or signoff for `linux/arm64` was captured in this quick evidence pass. |

## Android TV Caveat Acknowledgement

- Android TV deployment-note review status: Pending (not captured in this quick evidence pass).
- Target device class smoke-check status: Pending (not captured in this quick evidence pass).
