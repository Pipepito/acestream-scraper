# v2 Folder Retirement Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the obsolete root `v2/` folder after redirecting all live repo references to canonical root `backend/` and `frontend/` paths.

**Architecture:** The repo already treats root `backend/` and `frontend/` as the canonical v2 stack. This cleanup only updates remaining workflow, gate, docs, and ignore-path references, then removes the dead duplicate tree and verifies that validation commands now resolve through root paths only.

**Tech Stack:** GitHub Actions, pytest, JSON/YAML config, markdown docs, repository filesystem cleanup

---

### Task 1: Redirect live path references

**Files:**
- Modify: `.github/workflows/cutover-validation.yml`
- Modify: `scripts/phase_gates/phase1_gate_config.yaml`
- Modify: `docs/ops/reliability-runbook.md`
- Modify: `.gitignore`

- [x] Update `cutover-validation.yml` to create and use `backend/venv` as the canonical environment path.
- [x] Update `phase1_gate_config.yaml` commands to use `backend/venv/bin/python` and `backend/tests/...` paths.
- [x] Update the reliability runbook regression command to use `backend/venv/bin/pytest`.
- [x] Remove dead `v2/...` ignore rules while preserving root `backend/` and `frontend/` runtime artifact ignores.

### Task 2: Remove obsolete duplicated tree

**Files:**
- Delete: `v2/`

- [x] Confirm no remaining live references point into `v2/`.
- [x] Delete the entire `v2/` directory tree.

### Task 3: Verify repo after retirement

**Files:**
- Verify only

- [x] Run a targeted search for retired duplicate-tree paths to confirm only historical/planning references remain if any.
- [x] Run the phase-gate command references or equivalent smoke checks to confirm the new root paths are valid.
- [x] Run `git status --short` and confirm the expected cleanup footprint.
