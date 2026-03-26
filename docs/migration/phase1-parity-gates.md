# Phase 1 Parity Safety Gates

This document defines how to execute and approve Phase 1 parity gates.

## Purpose

Phase 1 gates protect scraper/output behavior during migration by enforcing:

- Scraper parity for HTTP/M3U and ZeroNet flows.
- Field-level channel integrity checks for core fields.
- Playlist and EPG output validity checks.
- Explicit separation of blocking vs non-blocking source classes.

## Gate Entry Point

Use the single gate runner for all checks:

```bash
python scripts/phase_gates/phase1_gate_runner.py --profile quick
python scripts/phase_gates/phase1_gate_runner.py --profile full
```

Available profiles:

- `quick`: PR-friendly parity checks.
- `full`: pre-cutover parity + existing smoke suite.

## Source Class Policy

- `active` and `gate_critical: true` checks are blocking.
- `legacy` and `disabled` checks are non-blocking by default.
- Auth/region-dependent sources stay visible via `env_tags` and are reported even when non-blocking.

Blocking failures return non-zero exit code and must be fixed before merge/cutover.

## Checklist (Reviewer/Operator)

1. Run quick profile locally:
   - `python scripts/phase_gates/phase1_gate_runner.py --profile quick`
2. Confirm CI workflow passes:
   - `.github/workflows/phase1-safety-gates.yml`
3. Run full profile before cutover milestone:
   - `python scripts/phase_gates/phase1_gate_runner.py --profile full`
4. Inspect report for blocking/non-blocking sections:
   - Blocking failures must be zero.
   - Non-blocking failures must be reviewed and acknowledged.
5. Confirm parity snapshots are current and approved:
   - `backend/tests/parity/snapshots/scraper_channels_snapshot.json`
   - `backend/tests/parity/snapshots/output_validity_snapshot.json`
6. Record sign-off evidence in PR notes:
   - Command output or uploaded artifact.
   - Snapshot version used.
   - Reviewer acknowledgment.

## Snapshot Change Control

Snapshot updates are allowed only when:

- Behavior change is intentional and reviewed.
- Snapshot version is bumped.
- Rationale is documented in commit/PR notes.
- Gates are re-run and evidence attached.

## Evidence Requirements

Minimum evidence for Phase 1 acceptance:

- Quick profile output (local or CI).
- Full profile output for transition/cutover checks.
- Explicit statement: `blocking_failures: []`.
- Any non-blocking failure summary + decision.

## Sign-Off Template

Use this in PR or release notes:

```text
Phase 1 Gate Sign-off
- Profile(s): quick/full
- Blocking failures: 0
- Non-blocking failures: <count and IDs>
- Snapshot version: <version>
- Reviewer: <name>
- Date: <YYYY-MM-DD>
```
