# Phase 1 Parity Snapshots

This directory stores versioned golden snapshots for Phase 1 parity gates.

## Files

- `scraper_channels_snapshot.json`: expected channel outputs for baseline scraper sources.
- `output_validity_snapshot.json`: expected playlist/EPG output assertions.

## Governance

- Snapshot updates are change-controlled.
- Any snapshot update must include:
  - Baseline version bump in the snapshot file.
  - A short rationale in the commit message or PR notes.
  - Regenerated parity test evidence.

## Source Classes and Gate Policy

- `active` and explicitly `gate_critical: true` sources are blocking.
- `legacy` and disabled sources are reported separately and are non-blocking unless promoted.
- Auth/region-dependent sources remain visible through `env_tags`.
