# Development Phases (Roadmap-Aligned)

This document mirrors the active migration roadmap.

## Phase 1: Parity Baseline and Safety Gates

- Lock scraper/output parity behavior.
- Add migration acceptance checks and gate runners.

## Phase 2: Backend Contract and Structure Hardening

- Normalize API contracts and response shapes.
- Clarify endpoint/service/repository boundaries.
- Harden operational error handling and logging.

## Phase 3: v2-Only Cutover and Legacy Retirement

- Promote and enforce root `backend/` + `frontend/` ownership.
- Retire legacy runtime/deployment paths.
- Reconcile docs and cutover policy to root-only truth.

## Phase 4: Frontend UX Modernization

- Redesign core flows for clarity and speed.
- Improve responsive behavior for desktop and constrained displays.

## Phase 5: Multi-Arch Build and Runtime Validation

- Build and publish `linux/arm/v7` and `linux/arm64` images.
- Validate runtime smoke behavior on supported architectures.

## Phase 6: Reliability, Test Ownership, and Optimization

- Rebuild critical test ownership in new structure.
- Burn down high-impact defects.
- Improve DB and high-churn path performance.
