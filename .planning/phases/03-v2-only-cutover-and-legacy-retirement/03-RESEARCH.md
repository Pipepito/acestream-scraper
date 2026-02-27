# Phase 3: v2-Only Cutover and Legacy Retirement - Research

**Researched:** 2026-02-27  
**Domain:** Big-bang v2 promotion to root ownership, legacy retirement, and strict cutover verification  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

### Cutover Ownership
- Hard cutover only: root entrypoints must become v2-derived runtime/build paths.
- Promote `v2/backend` and `v2/frontend` into canonical root `backend/` and `frontend/`.
- After cutover there should be no canonical `v2/...` route ownership.
- Remove legacy root runtime/build/deployment paths directly once cutover succeeds.

### CI and Release Policy
- CI/release stays rooted in `.github/workflows` and targets canonical root backend/frontend.
- Required checks are strict blockers on PR and on main/release pushes.
- Artifacts use new canonical naming (no legacy/dual naming).
- Add automated enforcement to prevent legacy path/reference reintroduction.

### Verification and Rollback Policy
- Go/no-go requires parity + tests + build + smoke/regression checks.
- Smoke depth is extended/full regression for cutover signoff.
- Any required gate failure blocks merge.
- Fix-forward on branch is the rollback strategy (do not merge until green).

### Environment and Conventions
- Legacy env vars are temporarily auto-mapped for one release window.
- New env var names win conflicts; conflicts should log warnings.
- Repo conventions after promotion: root `backend/`, root `frontend/`, centralized `scripts/`, centralized `docs/`.
- Enforce conventions automatically in CI.

### PR Structure
- Single PR with logically grouped commits.
- Commit order expectation: path promotion -> ref rewrites -> CI/release updates -> docs/checklist -> verification evidence.
- Standard review process is acceptable, but PR description must include Scope, Risks, Verification sections.

### Claude's Discretion
- Exact shape of CI guard scripts and legacy-reference detection rules.
- Exact layout under `scripts/` and `docs/` as long as root conventions are enforced.
- Exact evidence file format so long as required sections and gate outputs are captured.

### Deferred Ideas
None - discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MIGR-01 | Production runtime uses v2 stack only | Promotion-first root ownership and removal of root legacy runtime entrypoints |
| MIGR-02 | Root legacy deployment/build paths retired or redirected | Explicit deletion/retirement rules + CI guardrails for forbidden legacy refs |
| MIGR-04 | Big-bang cutover executable on one release branch | Branch-gated mandatory cutover checklist + fix-forward policy |
| COMP-03 | Release docs reflect v2-only deployment expectations | Documentation rewrite to root canonical runtime/build/deploy model |
</phase_requirements>

## Summary

Phase 3 should be executed as a strict one-way cutover, not as a compatibility bridge. The safest pattern is promotion-first: make root own the v2 stack, then remove legacy paths, then enforce guardrails that prevent any legacy drift from reappearing.

Current repository evidence shows a split ownership problem:
- Root CI/release still targets legacy files (`Dockerfile`, `entrypoint.sh`, `requirements*.txt`, `wsgi.py`, `manage.py`).
- Active implementation and tests live under `v2/`.
- Root docs and runtime instructions still describe legacy Flask-root behavior.

This phase closes that split by converting root into the only runtime/build/release truth and turning legacy references into explicit failures.

## Current Gap Evidence

### Deployment and Runtime Split
- Root `Dockerfile`, `docker-compose.yml`, `entrypoint.sh`, `wsgi.py`, and `run_dev.py` still represent legacy runtime ownership.
- `v2/backend/main.py` and `v2/frontend` are the active stack but not canonical root ownership yet.

### CI/Release Drift
- `.github/workflows/release.yml` path filters and jobs are anchored to legacy root files.
- `.github/workflows/pull_request.yml` still installs/runs root test and lint flows.
- `.github/workflows/phase1-safety-gates.yml` uses `v2/backend/...` paths, which will become stale after promotion unless updated.

### Documentation Drift
- Root `README.md` and deployment docs still communicate legacy runtime commands and file paths.
- Historical migration docs describe dual-stack transition patterns that no longer match the locked strict-cutover model.

## Recommended Implementation Pattern

### Pattern 1: Promotion-First Cutover
- Perform directory/path ownership promotion first (`v2/backend` -> `backend`, `v2/frontend` -> `frontend`).
- Rewrite internal and workflow path references immediately after promotion.
- Keep scraper behavior untouched; cutover changes ownership, not core scraping logic.

### Pattern 2: Strict CI Contract + Legacy Guards
- Introduce explicit cutover check scripts under root `scripts/`.
- Fail CI on forbidden references (`v2/` runtime paths, legacy root entrypoints, deprecated command strings).
- Make full required gate set run on PR and main/release pushes.

### Pattern 3: Evidence-Driven Branch Signoff
- Add executable phase-3 gate runner and cutover checklist docs.
- Record outputs for parity, tests, build, and smoke/regression checks.
- Use fix-forward branch policy: no merge until all required checks are green.

## Don’t Hand-Roll

| Problem | Avoid | Use Instead | Why |
|---------|-------|-------------|-----|
| Manual cutover verification | Ad-hoc command runs and chat-only signoff | Scripted gate runner + checklist artifact | Ensures repeatability and auditable evidence |
| Legacy drift prevention by review only | Reviewer memory and tribal knowledge | CI enforcement script for forbidden refs | Prevents accidental regression during future PRs |
| Dual naming transition | Temporary duplicate artifact names | Single canonical naming after cutover | Aligns with strict root ownership decision |

## Common Pitfalls

### Pitfall 1: Partial promotion
Leaving some runtime/build references on `v2/...` after promotion creates hidden dual ownership.

### Pitfall 2: Docs lagging behind runtime truth
Cutover can technically succeed while operators still follow legacy instructions.

### Pitfall 3: Gate set not treated as merge-blocking
If any required check is effectively optional, big-bang cutover confidence is lost.

### Pitfall 4: Env compatibility without an expiry
Auto-mapping legacy env vars permanently undermines the post-cutover canonical config model.

## Validation Strategy for Phase 3

1. **Promotion and ownership checks**
   - Root contains canonical `backend/` and `frontend/`.
   - No canonical runtime path depends on legacy root stack.

2. **CI/release checks**
   - PR and main/release workflows run full required gate set.
   - Legacy-reference enforcement is active and blocking.

3. **Documentation checks**
   - Root docs describe only post-cutover runtime/deploy truth.
   - Release/cutover checklist and evidence sections are present and current.

4. **Branch cutover verification**
   - Parity gates pass.
   - Backend/frontend test suites pass.
   - Build and smoke/regression checks pass.
   - Required checks all green before merge.

## Sources

### Primary (HIGH confidence)
- `.planning/phases/03-v2-only-cutover-and-legacy-retirement/03-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/STACK.md`
- `.planning/codebase/CONCERNS.md`
- `.github/workflows/pull_request.yml`
- `.github/workflows/release.yml`
- `.github/workflows/phase1-safety-gates.yml`
- `docker-compose.yml`
- `v2/docker-compose.yml`
- `Dockerfile`
- `v2/backend/Dockerfile`
- `README.md`
- `v2/README.md`
- `docs/architecture/deployment.md`
- `docs/migration/migration-strategy.md`
- `docs/migration/development-phases.md`
- `docs/migration/development-progress.md`

## Metadata

**Confidence breakdown:**
- Promotion-first cutover strategy: HIGH
- CI/release consolidation approach: HIGH
- Legacy-retirement enforcement approach: HIGH
- Cutover verification/evidence strategy: HIGH

**Research date:** 2026-02-27  
**Valid until:** 2026-03-31
