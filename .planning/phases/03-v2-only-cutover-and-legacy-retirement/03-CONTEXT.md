# Phase 3: v2-Only Cutover and Legacy Retirement - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete root-to-v2 replacement for runtime, build, and release ownership by promoting the v2 app into root ownership, retiring legacy root paths, and validating a strict big-bang cutover on branch before merge.

</domain>

<decisions>
## Implementation Decisions

### Cutover mode and path ownership
- Hard switch only: root entrypoints must be v2-only after cutover.
- Promote app directories to root structure:
  - `v2/backend` -> `backend`
  - `v2/frontend` -> `frontend`
- Remove the `v2/` path from canonical runtime/build/deploy routes.
- No lingering internal `v2/...` references after cutover; rewrite to promoted root paths in the same phase.

### Legacy retirement policy
- Strict removal in the same phase once promoted structure passes validation.
- Delete obsolete legacy runtime/build/deploy code paths directly (no archive folder in repo).
- Remove legacy command paths; no compatibility wrappers/stubs for old commands.
- Rewrite docs to the new post-cutover truth only (no dual docs, no legacy appendix).
- Add automated CI enforcement so legacy paths/references cannot be reintroduced.

### CI and release ownership
- Keep CI workflows at root (`.github/workflows`) with jobs targeting root `backend/` and `frontend/`.
- Strict required checks: merge blocked unless all required checks pass.
- Use new canonical v2-only artifact naming (do not keep legacy naming).
- Run full cutover pipeline on PRs and on pushes to main/release branch.

### Verification, gating, and rollback behavior
- Go/no-go requires full mandatory gate set:
  - parity checks
  - backend/frontend tests
  - build verification
  - cutover smoke/operational checks
- Smoke/regression depth should be extended full regression coverage.
- Any required check failure blocks merge.
- Rollback strategy is fix-forward on branch (branch remains unmerged until all gates pass).

### Environment/config migration rules
- Support temporary legacy env compatibility by auto-mapping legacy env names to new names.
- Compatibility window is one release window only (phase cutover release).
- If both legacy and new vars are set, new vars win; emit warning for conflicts.
- Use explicit required env set plus safe defaults for non-critical settings.

### Post-promotion repository conventions
- Canonical root app layout is `backend/` + `frontend/`.
- Centralize operational scripts under root `scripts/` (organized with subfolders such as `scripts/ci`, `scripts/release`, `scripts/ops`).
- Centralize operational/deployment/cutover docs in root `docs/`.
- Enforce root conventions with CI checks (forbid deprecated layout patterns).

### Cutover PR structure and evidence
- Deliver cutover in a single PR with logically grouped commits.
- Commit ordering:
  1. path promotion
  2. internal reference rewrites
  3. CI/release updates
  4. docs and cutover checklist updates
  5. verification evidence
- Review policy: standard review process (not special owner-only flow).
- PR description must include sections: Scope, Risks, Verification.

### Claude's Discretion
- Exact CI check implementation details and detection patterns for forbidden legacy references.
- Exact script/doc subfolder naming details under the enforced `scripts/` and `docs/` root conventions.
- Exact formatting of verification evidence artifacts, as long as Scope/Risks/Verification sections and required proof are present.

</decisions>

<specifics>
## Specific Ideas

- "The content of v2 must become the content of the root so v2 virtually won't exist in routes."
- Keep cutover strict and deterministic: no dual-stack runtime, no temporary legacy command surface.
- The branch-based big-bang approach remains acceptable as long as merge gates are strict.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 03-v2-only-cutover-and-legacy-retirement*
*Context gathered: 2026-02-27*
