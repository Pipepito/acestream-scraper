# Single PR Validation Pipeline Cutover Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse Jenkins PR gating to one canonical multibranch pipeline that reports a single GitHub status context named `PR Validation` while preserving the four existing gate behaviors as Jenkins stages.

**Architecture:** Extend the repo-root `Jenkinsfile` into a staged PR validation pipeline, reconfigure the canonical `acestream-scraper-pr` multibranch job to use the custom notification context trait, verify the new single-context flow on the current PR, then retire the temporary per-gate Jenkins jobs and update active operator docs.

**Tech Stack:** Jenkins declarative pipeline, Jenkins multibranch pipeline XML, GitHub Branch Source, github-scm-trait-notification-context, GitHub App auth, bash, Python venv, npm, Docker buildx.

---

## File Map

- Modify: `Jenkinsfile`
  - Convert the single `Validate` stage into the canonical staged PR pipeline.
- Modify: `docs/ops/jenkins-ci.md`
  - Update the operator guide to describe one `PR Validation` context and the live-controller credential-id caveat.
- Modify: `.tmp/jenkins/acestream-scraper-pr-config.xml`
  - Add the custom notification-context trait with label `PR Validation`.
- Delete: `jenkins/pr-phase1.Jenkinsfile`
  - Remove temporary per-gate entrypoint after canonical pipeline is verified.
- Delete: `jenkins/pr-required-checks.Jenkinsfile`
  - Remove temporary per-gate entrypoint after canonical pipeline is verified.
- Delete: `jenkins/pr-cutover.Jenkinsfile`
  - Remove temporary per-gate entrypoint after canonical pipeline is verified.
- Delete: `jenkins/pr-multiarch.Jenkinsfile`
  - Remove temporary per-gate entrypoint after canonical pipeline is verified.
- Operational change: live Jenkins job `acestream-scraper-pr`
  - Update config from `.tmp/jenkins/acestream-scraper-pr-config.xml`.
- Operational cleanup: live Jenkins jobs
  - Disable or delete `acestream-scraper-pr-phase1-app`
  - Disable or delete `acestream-scraper-pr-required-checks-app`
  - Disable or delete `acestream-scraper-pr-cutover-app`
  - Disable or delete `acestream-scraper-pr-multiarch-app`
  - Disable or delete older standalone status-setter jobs if still present.

## Chunk 1: Canonical Pipeline In Repo

### Task 1: Rewrite `Jenkinsfile` As The Single PR Gate Pipeline

**Files:**
- Modify: `Jenkinsfile`
- Reference: `jenkins/pr-phase1.Jenkinsfile`
- Reference: `jenkins/pr-required-checks.Jenkinsfile`
- Reference: `jenkins/pr-cutover.Jenkinsfile`
- Reference: `jenkins/pr-multiarch.Jenkinsfile`

- [ ] **Step 1: Write the failing test expectation as a diff checklist**

Treat this task as a pipeline-behavior change with command-level verification instead of an automated unit test. The failure condition to prove first is that the current `Jenkinsfile` does not yet define the required staged layout.

- [ ] **Step 2: Verify the current file is missing the target stage layout**

Run: `grep -n "Phase 1 Safety Gates\|Required Cutover Checks\|cutover-quick\|Multi-Arch Quick Profile" Jenkinsfile`

Expected: no matches or an incomplete layout.

- [ ] **Step 3: Replace the single-stage pipeline with the staged canonical pipeline**

Update `Jenkinsfile` so it contains:

- a `Checkout / Bootstrap` stage that performs:
  - `agent { label 'generic-gh-builder' }` remains unchanged at the pipeline level
  - `checkout scm`
  - `currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BRANCH_NAME ?: 'detached'}"`
  - `bash scripts/ci/bootstrap_jenkins_runner.sh`
  - `python3 -m venv --clear backend/venv`
  - `backend/venv/bin/pip install --upgrade pip`
  - `backend/venv/bin/pip install -r backend/requirements.txt`
  - `npm --prefix frontend ci`
  - `docker buildx use "${JENKINS_BUILDER:-acestream-builder}"`

- a `Phase 1 Safety Gates` stage that runs:

```bash
backend/venv/bin/python scripts/phase_gates/phase1_gate_runner.py --profile quick --json-output > phase1-gate-report.json
```

- a `Required Cutover Checks` stage that runs:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper --result-file phase5-build-result-pr-scraper.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper.json --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --result-file phase5-build-result-pr-scraper-acestream.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream.json --flavor scraper-acestream
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy --result-file phase5-build-result-pr-scraper-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acexy.json --flavor scraper-acexy
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy --result-file phase5-build-result-pr-scraper-acestream-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream-acexy.json --flavor scraper-acestream-acexy
bash scripts/ci/assert_no_legacy_paths.sh --strict
bash scripts/ci/run_cutover_required_checks.sh --profile quick
```

- a `cutover-quick` stage that runs:

```bash
backend/venv/bin/python scripts/phase_gates/phase3_gate_runner.py --profile quick --json-output > phase3-gate-report-quick.json
```

- a `Multi-Arch Quick Profile` stage that runs:

```bash
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper --result-file phase5-build-result-quick-scraper.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper.json --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --result-file phase5-build-result-quick-scraper-acestream.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acestream.json --flavor scraper-acestream
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy --result-file phase5-build-result-quick-scraper-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acexy.json --flavor scraper-acexy
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy --result-file phase5-build-result-quick-scraper-acestream-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acestream-acexy.json --flavor scraper-acestream-acexy
bash scripts/ci/phase5_arch_smoke.sh --dry-run --platforms linux/arm/v7,linux/arm64
backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py --profile quick --json-output > phase5-gate-report-quick.json
```

- post-archive blocks that preserve:
  - `phase1-gate-report.json`
  - `phase3-gate-report-quick.json`
  - `phase5-build-result-pr-*.json`
  - `phase5-build-result-quick-*.json`
  - `phase5-gate-report-quick.json`

- [ ] **Step 4: Run a structural diff check**

Run: `git diff -- Jenkinsfile`

Expected: staged pipeline shows the four required gate stages and archive blocks.

- [ ] **Step 5: Run formatting/sanity check on the pipeline file**

Run: `git diff --check -- Jenkinsfile`

Expected: no whitespace or patch-format errors.

- [ ] **Step 6: Commit**

```bash
git add Jenkinsfile
git commit -m "build: unify PR validation stages"
```

## Chunk 2: Jenkins Controller Cutover

### Task 2: Reconfigure The Canonical Multibranch Job To Report `PR Validation`

**Files:**
- Modify: `.tmp/jenkins/acestream-scraper-pr-config.xml`
- Operational target: live Jenkins job `acestream-scraper-pr`

- [ ] **Step 1: Write the failing configuration expectation**

The current canonical multibranch XML lacks the custom notification-context trait, so it cannot yet emit `PR Validation`.

- [ ] **Step 2: Verify the trait is absent from the current XML**

Run: `grep -n "NotificationContextTrait\|PR Validation" .tmp/jenkins/acestream-scraper-pr-config.xml`

Expected: no matches.

- [ ] **Step 3: Update the canonical multibranch XML**

Add this trait inside the GitHub SCM source `<traits>` block in `.tmp/jenkins/acestream-scraper-pr-config.xml`:

```xml
<org.jenkinsci.plugins.githubScmTraitNotificationContext.NotificationContextTrait>
  <contextLabel>PR Validation</contextLabel>
  <typeSuffix>false</typeSuffix>
  <multipleStatuses>false</multipleStatuses>
</org.jenkinsci.plugins.githubScmTraitNotificationContext.NotificationContextTrait>
```

Keep the live-controller credential id unchanged as `github-builder-app` unless the controller has been normalized separately.

- [ ] **Step 4: Verify the local XML now contains the target context**

Run: `grep -n "PR Validation" .tmp/jenkins/acestream-scraper-pr-config.xml`

Expected: one matching trait block.

- [ ] **Step 5: Apply the updated XML to Jenkins**

Run the Jenkins API update flow already used in this session, posting `.tmp/jenkins/acestream-scraper-pr-config.xml` to `http://192.168.1.210:8080/job/acestream-scraper-pr/config.xml` with the current admin/API token and crumb.

Expected: HTTP success and no controller error.

- [ ] **Step 6: Commit the local controller XML change**

```bash
git add .tmp/jenkins/acestream-scraper-pr-config.xml
git commit -m "build: set PR validation Jenkins context"
```

## Chunk 3: Repo Cleanup Preparation

## Chunk 4: Live Verification And Job Retirement

### Task 5: Verify The Single-Context PR Validation Flow End To End

**Files:**
- Modify: none
- Verify: live Jenkins `acestream-scraper-pr`
- Verify: GitHub PR statuses on the latest branch SHA

- [ ] **Step 1: Push the repo commits needed for cutover**

Run: `git push origin HEAD`

Expected: branch contains the updated `Jenkinsfile` and any required controller XML snapshot changes needed for the cutover run.

- [ ] **Step 2: Trigger a fresh build of `acestream-scraper-pr`**

Run the Jenkins API trigger for `acestream-scraper-pr`.

Expected: a new PR job build begins on the current commit.

- [ ] **Step 3: Verify Jenkins stage layout**

Query the Jenkins build or inspect console/stage view.

Expected: the build shows stages:

- `Checkout / Bootstrap`
- `Phase 1 Safety Gates`
- `Required Cutover Checks`
- `cutover-quick`
- `Multi-Arch Quick Profile`

- [ ] **Step 4: Verify GitHub status**

Run the public GitHub commit-status query.

Expected:

- `PR Validation` is present
- the new build is reporting through `PR Validation`

- [ ] **Step 5: Verify artifacts**

Inspect the completed Jenkins build.

Expected artifacts include:

- `phase1-gate-report.json`
- `phase3-gate-report-quick.json`
- `phase5-build-result-pr-*.json`
- `phase5-build-result-quick-*.json`
- `phase5-gate-report-quick.json`

- [ ] **Step 6: Update branch protection manually or confirm operator action**

Switch required Jenkins gating to `PR Validation`, keeping old required checks until the new single context has passed reliably.

Expected: branch protection now includes `PR Validation` and may still temporarily include the old required contexts during the proving window.

### Task 6: Retire Temporary Jenkins Jobs

**Files:**
- Modify: none
- Operational targets: live Jenkins jobs only

- [ ] **Step 1: Verify `PR Validation` is stable before cleanup**

Confirm at least one successful canonical PR run on the target branch/PR.

Expected: `PR Validation` is `success` on the current PR commit.

- [ ] **Step 2: Remove old required contexts from branch protection after stability is proven**

Update GitHub branch protection so the temporary per-gate Jenkins contexts are no longer required.

Expected: Jenkins merge gating depends on `PR Validation` instead of the temporary per-gate contexts.

- [ ] **Step 3: Disable or delete the App-backed per-gate jobs**

Retire:

- `acestream-scraper-pr-phase1-app`
- `acestream-scraper-pr-required-checks-app`
- `acestream-scraper-pr-cutover-app`
- `acestream-scraper-pr-multiarch-app`

- [ ] **Step 4: Disable or delete the older standalone status-setter jobs if still present**

Retire any of:

- `acestream-scraper-pr-phase1`
- `acestream-scraper-pr-required-checks`
- `acestream-scraper-pr-cutover`
- `acestream-scraper-pr-multiarch`

- [ ] **Step 5: Verify cleanup**

Query Jenkins job listings.

Expected: `acestream-scraper-pr` remains as the canonical PR gate job and the temporary PR gate jobs are disabled or removed.

- [ ] **Step 6: Commit any local XML/doc cleanup still tracked in git**

```bash
git status --short
```

If tracked cleanup files changed, commit them with a focused message before finishing.

### Task 7: Remove Temporary Per-Gate Repo Jenkinsfiles After Live Retirement

**Files:**
- Delete: `jenkins/pr-phase1.Jenkinsfile`
- Delete: `jenkins/pr-required-checks.Jenkinsfile`
- Delete: `jenkins/pr-cutover.Jenkinsfile`
- Delete: `jenkins/pr-multiarch.Jenkinsfile`

- [ ] **Step 1: Verify the canonical `Jenkinsfile` fully covers the four gate commands**

Run:

```bash
rg -n "phase1_gate_runner|run_cutover_required_checks|phase3_gate_runner|phase5_gate_runner|build_multiarch_images.sh" Jenkinsfile
```

Expected: all required gate commands are present in `Jenkinsfile`.

- [ ] **Step 2: Verify the live temporary jobs no longer depend on the repo gate Jenkinsfiles**

Confirm the temporary App-backed jobs have been disabled or deleted before removing their `scriptPath` targets from the repo.

Expected: no live Jenkins PR gate job still depends on `jenkins/pr-*.Jenkinsfile`.

- [ ] **Step 3: Delete the temporary per-gate Jenkinsfiles**

Remove:

- `jenkins/pr-phase1.Jenkinsfile`
- `jenkins/pr-required-checks.Jenkinsfile`
- `jenkins/pr-cutover.Jenkinsfile`
- `jenkins/pr-multiarch.Jenkinsfile`

- [ ] **Step 4: Verify git sees only those deletions**

Run:

```bash
git status --short -- jenkins/pr-phase1.Jenkinsfile jenkins/pr-required-checks.Jenkinsfile jenkins/pr-cutover.Jenkinsfile jenkins/pr-multiarch.Jenkinsfile
```

Expected: four deleted files.

- [ ] **Step 5: Commit**

```bash
git add jenkins/pr-phase1.Jenkinsfile jenkins/pr-required-checks.Jenkinsfile jenkins/pr-cutover.Jenkinsfile jenkins/pr-multiarch.Jenkinsfile
git commit -m "build: remove temporary PR gate Jenkinsfiles"
```

### Task 8: Update Operator Docs After Cutover Reaches Steady State

**Files:**
- Modify: `docs/ops/jenkins-ci.md`

- [ ] **Step 1: Write the failing documentation expectation**

The current operator guide still describes recording an observed Jenkins check name and standardizes a different GitHub App credential id than the live controller uses.

- [ ] **Step 2: Verify the outdated doc content exists**

Run:

```bash
rg -n "github-app-acestream-scraper|Record the exact check name|observed Jenkins check name|scripts/ci/run_jenkins_validation.sh" docs/ops/jenkins-ci.md
```

Expected: matches showing the older guidance.

- [ ] **Step 3: Update the operator guide**

Adjust `docs/ops/jenkins-ci.md` so it:

- describes one canonical PR validation job using root `Jenkinsfile`
- states the required GitHub context is `PR Validation`
- clarifies that the repo-standard credential id is `github-app-acestream-scraper`, but the current live controller is using `github-builder-app`
- adds `github-scm-trait-notification-context` to the controller/plugin prerequisites for the custom status-context path
- updates the branch-protection cutover section to add `PR Validation` first, verify stability, then remove old required contexts
- removes guidance that implies four separate Jenkins PR contexts are the steady state
- removes stale wording that tells operators to record an unknown Jenkins check name or assumes PR validation is still only `scripts/ci/run_jenkins_validation.sh`

- [ ] **Step 4: Verify the new doc wording**

Run:

```bash
rg -n "PR Validation|github-builder-app|github-scm-trait-notification-context|branch protection|single PR validation" docs/ops/jenkins-ci.md
```

Expected: matches for the updated steady-state guidance.

- [ ] **Step 5: Commit**

```bash
git add docs/ops/jenkins-ci.md
git commit -m "docs: update Jenkins PR validation guidance"
```

## Final Verification

- [ ] Run: `git diff --check`
Expected: no diff-format errors.

- [ ] Run: `git status --short`
Expected: no unintended tracked changes remain.

- [ ] Verify in GitHub PR UI that only `PR Validation` is required for Jenkins merge gating.

- [ ] Verify in Jenkins UI that the canonical PR build exposes all four gate stages.
