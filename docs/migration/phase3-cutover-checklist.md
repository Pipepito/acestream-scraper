# Phase 3 Big-Bang Cutover Checklist

This checklist is the merge-blocking contract for Phase 3 branch cutover validation.

## Scope

- Validate that root `backend/` + `frontend/` ownership is fully operational.
- Confirm required parity/test/build/smoke gates pass in deterministic order.
- Produce auditable evidence for branch signoff.

## Blocking Policy

- Any required gate failure is a **blocker**.
- Blockers must be fixed on-branch before merge.
- Manual signoff without gate evidence is not allowed.

## Execution Steps

1. Run quick profile:
   - `python3 scripts/phase_gates/phase3_gate_runner.py --profile quick --json-output > phase3-gate-report-quick.json`
2. Run full profile:
   - `python3 scripts/phase_gates/phase3_gate_runner.py --profile full --json-output > phase3-gate-report-full.json`
3. Collect evidence from full report:
   - `bash scripts/ci/collect_cutover_evidence.sh --report phase3-gate-report-full.json`
4. Confirm generated evidence includes required Scope, Risks, and Verification sections.

## Fix-Forward Policy

- If any blocker appears, apply fix-forward changes directly in this branch.
- Re-run quick/full profiles after each fix-forward change.
- Merge remains blocked until all required checks are green.

## Signoff Requirements

All of the following must be present:

- `phase3-gate-report-full.json` with `passed: true`.
- `docs/release/phase3-cutover-evidence.md` updated by evidence collector.
- PR description containing Scope, Risks, Verification.

