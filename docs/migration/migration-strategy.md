# Migration Strategy (Current)

## Objective

Complete a strict big-bang cutover to a single root stack while preserving scraper behavior and improving architecture quality.

## Operating Rules

1. Root `backend/` + `frontend/` are the only canonical runtime/build paths.
2. Legacy runtime/deployment entrypoints are retired rather than wrapped.
3. CI blocks legacy-reference reintroduction via strict guard scripts.
4. Cutover verification is script-driven and reproducible.

## Execution Sequence

1. Promote root ownership to `backend/` + `frontend/`.
2. Rewire workflows and required checks around root stack.
3. Retire obsolete legacy files and stale deployment paths.
4. Reconcile docs to post-cutover truth only.
5. Continue with UX, multi-arch, and reliability phases.

## Configuration Compatibility Policy

The v2.0 release line provided a one-release alias window. Starting with v2.1,
only canonical names are read; the alias map and its enable switch are removed.
The regression gate asserts their absence independently of `version.txt`.
See [v2.1 upgrade notes](../release/v2.1-release-notes.md) for the rename table.
