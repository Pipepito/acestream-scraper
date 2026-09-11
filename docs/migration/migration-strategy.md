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

A one-release env alias window is allowed for cutover safety.

- Legacy aliases are auto-mapped to canonical vars.
- Canonical vars win conflicts.
- Conflicts emit warnings.
- Alias mapping can be disabled via `ENABLE_LEGACY_ENV_ALIASES=false`.

This compatibility window is temporary and must not become permanent baseline behavior.
