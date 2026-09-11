# Phase 5: Multi-Arch Build and Runtime Validation - Research

**Researched:** 2026-02-27  
**Domain:** Multi-architecture container build/release and runtime smoke validation  
**Confidence:** HIGH

<user_constraints>
## User Constraints

### Locked Decisions
- Target architecture support must include `linux/arm/v7` and `linux/arm64`.
- Compatibility focus explicitly includes Android TV deployment contexts.
- Big-bang v2 cutover model is already complete; this phase should harden portability without reintroducing dual-stack behavior.

### Relevant Prior-Phase Constraints
- Root app ownership is canonical (`backend/`, `frontend/`, root `Dockerfile`, root `docker-compose.yml`).
- CI/CD already enforces strict required checks; Phase 5 should extend this discipline to architecture compatibility checks.
</user_constraints>

## Summary

Current repository state has partial readiness for multi-arch:

- Release workflow already uses Docker Buildx (`docker/setup-buildx-action`) but does not define `platforms` or manifest validation.
- No QEMU setup is present, which is required for reliable cross-arch CI builds on `ubuntu-latest`.
- No architecture-specific runtime smoke-test workflow exists yet.
- Deployment docs explicitly defer multi-arch details to Phase 5.

Phase 5 should ship in two focused plans:

1. **Build/Publish Hardening (COMP-01):** deterministic multi-arch image build + manifest validation (`linux/arm/v7`, `linux/arm64`, and likely `linux/amd64` baseline).
2. **Runtime Validation (COMP-02):** architecture-targeted smoke checks and operator-facing caveat documentation (including Android TV constraints).

## Current Gap Evidence

- `.github/workflows/release.yml` builds image with Buildx but without `platforms` matrix.
- `.github/workflows/pull_request.yml` validates backend/frontend build/tests but not architecture buildability.
- `docs/architecture/deployment.md` includes a placeholder section noting multi-arch work is pending Phase 5.

## Recommended Technical Direction

### Build Pipeline
- Use `docker/setup-qemu-action` + `docker/setup-buildx-action`.
- Standardize build command path in a script (`scripts/ci/build_multiarch_images.sh`) to avoid workflow drift.
- Define canonical platform set:
  - Required: `linux/arm/v7`, `linux/arm64`
  - Baseline parity: `linux/amd64`
- Add manifest inspection/verification script for merge/release evidence.

### Runtime Smoke Validation
- Introduce an architecture smoke runner script and profile config (mirroring phase-gate pattern already used in Phase 3).
- Validate minimal critical runtime behavior for each architecture:
  - container boots,
  - health endpoint responds,
  - core API endpoint(s) respond,
  - frontend static path is served by backend image as expected.
- Prefer CI-emulated smoke for continuous gate coverage and keep optional real-device smoke checklist for Android TV for final confidence.

### Documentation
- Extend deployment docs with:
  - supported architectures,
  - build/pull examples,
  - known caveats for ARMv7/Android TV resource constraints.
- Add release evidence template/report path for architecture validation outcomes.

## Common Pitfalls

1. **Buildx without QEMU setup**
   - Cross-arch builds may silently skip/flake.
2. **`push: false` with multi-platform assumptions**
   - Multi-platform manifest handling differs from single-arch local builds.
3. **Build-only confidence**
   - Successful image build does not guarantee runtime behavior on ARM targets.
4. **No artifact-level manifest verification**
   - Missing architectures can slip through if tags are not inspected post-build.

## Verification Strategy for Planning

- Plan 05-01 must provide executable checks proving platform matrix build configuration exists and is invoked consistently in CI.
- Plan 05-02 must include executable runtime smoke commands and produce machine-readable evidence artifacts.
- Requirement IDs must be covered:
  - `COMP-01` in build/publish plan(s)
  - `COMP-02` in runtime validation plan(s)

## Sources

- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `Dockerfile`
- `backend/Dockerfile`
- `frontend/Dockerfile`
- `.github/workflows/release.yml`
- `.github/workflows/pull_request.yml`
- `.github/workflows/cutover-validation.yml`
- `scripts/phase_gates/phase3_gate_config.yaml`
- `scripts/phase_gates/phase3_gate_runner.py`
- `docs/architecture/deployment.md`

