# Single PR Validation Pipeline Design

## Summary

Collapse Jenkins PR validation back to one canonical multibranch pipeline job named `acestream-scraper-pr`, with a single GitHub-reported status context named `PR Validation`. The pipeline will execute the existing PR gates as sequential Jenkins stages in one build so that any single gate failure blocks merge while still preserving stage-level visibility and artifacts inside Jenkins.

## Goals

- Use one Jenkins PR job as the source of truth for merge gating.
- Report one stable GitHub required status context: `PR Validation`.
- Preserve the existing PR gate coverage now split across multiple Jenkins jobs:
  - `Run Phase 1 Parity Safety Gates`
  - `Required Cutover Checks`
  - `cutover-quick`
  - `Multi-Arch Quick Profile`
- Keep debugging practical by exposing each gate as a separate Jenkins stage and preserving relevant artifacts.
- Continue using the existing GitHub App credential path instead of introducing a PAT.

## Non-Goals

- Preserve four separate GitHub status contexts.
- Add GitHub Checks-based stage publishing.
- Change release-job behavior.
- Change builder-node selection away from `generic-gh-builder`.

## Current State

The documented repo baseline is still a single PR validation multibranch job from the root `Jenkinsfile`. The live controller currently has additional temporary PR gate jobs created during Jenkins parity work:

- One broad PR validation pipeline in `Jenkinsfile`.
- Four dedicated PR gate Jenkinsfiles under `jenkins/`.
- Four App-backed multibranch jobs that publish four distinct GitHub contexts.
- Older standalone jobs that attempted `GitHubCommitStatusSetter` publishing and are not part of the desired steady state.

This live-controller drift produces correct gating coverage, but at the cost of extra controller job sprawl and a reporting model that no longer matches the desired operational rule: the PR should be mergeable only when the entire Jenkins PR validation pipeline passes.

## Desired State

### Canonical Job

`acestream-scraper-pr` becomes the only Jenkins PR validation job required for branch protection.

- Job type: GitHub App-backed multibranch pipeline.
- Builder label: `generic-gh-builder`.
- GitHub status context: `PR Validation`, implemented through the `github-scm-trait-notification-context` trait on the GitHub App-backed multibranch source.
- Source of pipeline logic: repo-root `Jenkinsfile`.

### Pipeline Stages

The single `Jenkinsfile` will run these stages in order:

1. `Checkout / Bootstrap`
2. `Phase 1 Safety Gates`
3. `Required Cutover Checks`
4. `cutover-quick`
5. `Multi-Arch Quick Profile`

The pipeline fails on the first failing stage. This preserves the merge-blocking behavior while keeping the reason visible in Jenkins stage output.

## Stage Responsibilities

### Checkout / Bootstrap

- Check out SCM.
- Set display name.
- Run `scripts/ci/bootstrap_jenkins_runner.sh`.
- Prepare reusable dependencies needed by later stages.

This stage exists to avoid duplicating expensive setup in every gate stage.

### Phase 1 Safety Gates

- Prepare Python runtime as needed.
- Run the phase 1 quick gate runner.
- Archive the generated phase 1 JSON report.

### Required Cutover Checks

- Prepare Python and frontend dependencies.
- Run the quick v2 suite.
- Run the dry-run multi-arch build and manifest verification steps currently used by the required-checks pipeline.
- Run strict legacy-path assertions.
- Run the quick required cutover checks script.
- Archive relevant build-result JSON artifacts.

### cutover-quick

- Prepare Python runtime as needed.
- Run the phase 3 quick gate runner.
- Archive the phase 3 JSON report.

### Multi-Arch Quick Profile

- Prepare Python runtime as needed.
- Ensure the configured buildx builder is active.
- Run the dry-run multi-arch image and manifest validation sequence.
- Run the dry-run arch smoke step.
- Run the phase 5 quick gate runner.
- Archive quick multi-arch build artifacts and the phase 5 JSON report.

## Reporting Model

### GitHub

GitHub branch protection will require only one Jenkins-reported status context:

- `PR Validation`

This is the only status users need to understand merge eligibility. This design deliberately uses one GitHub status context, not four separate status contexts and not stage-level GitHub Checks publishing.

### Jenkins

Jenkins remains the place for detailed gate breakdown:

- Stage view identifies which PR gate failed.
- Build logs preserve each gate's console output.
- Archived artifacts preserve the current evidence files for diagnosis.

## Reuse and Refactoring Approach

The implementation should favor minimal change:

- Reuse the existing repo-root `Jenkinsfile` instead of keeping multiple PR gate Jenkinsfiles as active pipeline entrypoints.
- Move only the gate commands necessary into staged sections of the canonical `Jenkinsfile`.
- Avoid inventing a new shared library or helper layer unless duplication becomes clearly harmful.

The four dedicated PR Jenkinsfiles may be removed from the repo after successful cutover, or left briefly during migration if needed for safe rollback. The preferred steady state is to remove them once the single pipeline is verified.

## Controller Changes

### Keep

- `github-scm-trait-notification-context` plugin.
- Existing GitHub App credential on the live controller. Repo docs standardize `github-app-acestream-scraper`; the current live controller uses `github-builder-app`, so the implementation must preserve the working live-controller credential id unless the controller is normalized separately.
- Existing multibranch PR job `acestream-scraper-pr`.

### Change

- Set the custom notification context on `acestream-scraper-pr` to `PR Validation`.
- Ensure the job still discovers the branch and PR heads needed for PR validation.

### Retire

After verification, disable or delete:

- `acestream-scraper-pr-phase1-app`
- `acestream-scraper-pr-required-checks-app`
- `acestream-scraper-pr-cutover-app`
- `acestream-scraper-pr-multiarch-app`
- The older standalone status-setter jobs if still present.

## Failure Semantics

- Any failed stage causes the single PR validation job to fail.
- A failed or unstable `PR Validation` status blocks merge.
- Build queue delay is acceptable because merge gating now depends on one canonical job, not independent partial success across multiple jobs.

## Verification Strategy

Verification for the cutover must confirm:

1. `acestream-scraper-pr` publishes `PR Validation` to GitHub for the target PR commit.
2. The pipeline exposes the four agreed gate stages in Jenkins.
3. A successful run produces the expected archived artifacts.
4. Branch protection can be switched from the previous required contexts to `PR Validation` without losing merge safety.
5. The extra App-backed gate jobs can be disabled without losing any required PR coverage.

## Risks and Mitigations

### Risk: Loss of separate GitHub check names

This is intentional. The design chooses simpler, clearer merge gating over multiple visible GitHub contexts.

Mitigation:

- Preserve clear stage names in Jenkins.
- Keep stage artifacts for diagnosis.

### Risk: Longer single-job runtime

Running all gates in one pipeline may lengthen a single build compared with separately visible jobs.

Mitigation:

- Reuse bootstrap/setup work where possible.
- Keep the stage order aligned with fastest/highest-signal failures first.

### Risk: Cleanup removes rollback path too early

Mitigation:

- Verify the single-job flow on the current PR first.
- Only disable or delete extra jobs after GitHub and Jenkins verification succeeds.

## Cutover Sequence

1. Update `Jenkinsfile` to include the four gate stages.
2. Reconfigure `acestream-scraper-pr` to use the custom status context `PR Validation`.
3. Trigger a fresh PR run on the current branch.
4. Verify GitHub status, Jenkins stages, and artifacts.
5. Update GitHub branch protection to require `PR Validation`, while temporarily keeping existing required checks until the new context has proven stable.
6. Remove the now-obsolete required contexts from branch protection only after `PR Validation` is confirmed stable.
7. Disable the extra App-backed gate jobs.
8. Remove obsolete repo-side PR gate Jenkinsfiles if no longer needed.
9. Update active Jenkins documentation to describe the new steady state and note the observed live credential id if it still differs from repo docs.

## Success Criteria

- The PR shows a single Jenkins context named `PR Validation`.
- The single Jenkins PR job contains all four required gate stages.
- Any failing gate prevents merge by failing `PR Validation`.
- The extra App-backed jobs are no longer needed for PR gating.
- The design remains GitHub App-based and does not require a PAT.
