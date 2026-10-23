# Collaborator-safe Jenkins validation

This is the rollout contract for the collaborator trust boundary. Merging these
files alone does **not** activate it. Do not invite repository writers until the
live configuration checks and acceptance checks below pass.

## Trust and execution

All PRs, including the owner's and same-repository collaborators', use the same
administrator-managed `jenkins/pr.Jenkinsfile`. The multibranch job uses **Pipeline:
Multibranch with defaults**, a managed Groovy config with ID
`acestream-isolated-pr-v1`, and the Groovy sandbox. It never `load`s, evaluates,
or executes a contributor's Jenkinsfile. Merely setting fork trust to Nobody does
not protect origin branches; merely editing the repository Jenkinsfile is not a
security boundary.

Only PR head revisions are discovered (origin and fork strategy 2); fork trust
is Nobody. Branch and tag discovery are disabled. The repository head must match
`refs/pull/<number>/head`. Targets are restricted to `develop` and `main`, and only
this repository's `develop` may target `main`. The automatic job resolves its protected target
once to a commit hash for every host-side selector, validator and runner helper.
The approved job obtains host orchestration from a reviewed full commit SHA pinned
by the administrator in its managed definition. It is not a build parameter or a
moving branch. This also permits rollout before merging the helper PR and permits
release PRs targeting a pre-rollout `main`.
Neither PR authors, origin/fork location, labels, nor ordinary GitHub approvals
can authorize host execution.

The automatic job runs data-only documentation/metadata checks or offline,
restricted application and architecture checks. Proposed dependency inputs are
never installed automatically. If those inputs differ from the target's runner,
the automatic application suite is deferred to approved validation; architecture
checks still run. Application changes always need the approved image job.
Documentation/metadata-only changes retain their lightweight path.

After automatic checks and cleanup, the parent releases its Docker lock and waits
for the separate administrator-owned `jenkins/pr-privileged.Jenkinsfile` job.
`PR Validation` stays pending until that child succeeds; a failed, timed-out or
aborted child fails the parent. Do not configure an independent early-success
status with that context. Discovery must remain head-only so Jenkins reports the
same real head SHA that was validated.

The child displays the PR number, head SHA, protected target and base SHA. Its
`input` submitter is one exact Jenkins user ID, rendered by the configuration
preparer, not a build parameter. Jenkins administrators retain their inherent
ability to approve. The owner reviews all proposed build/dependency/lifecycle
code before approving: approval deliberately permits that revision's host code.
There is no general isolation guarantee for code the owner explicitly approves.

Approval holds no executor or Docker lock. After approval, the child obtains the
shared FIFO lock, checks current remote refs and GitHub PR metadata, runs the full
application gate with the approved dependency set, builds every supported image
combination without publishing, and checks PR metadata again before success.
Closed PRs, new head commits, target changes and base updates invalidate the run.
Metadata outages/rate limits fail closed. A new build requires new approval.
Multiple revisions may wait independently; they never abort a running Docker
workload. Decline/cancel superseded pending approvals in Jenkins.

Each of the automatic, approved, develop and release Docker workloads holds
`acestream-scraper-nuc-docker` for its complete execution and cleanup, acquired
before its agent. The parent must never wait for the child while holding this
lock. Preserve existing runner reuse, disk-pressure cleanup and architecture
coverage. Approval waits have a seven-day limit; each Docker workload has a
four-hour limit.

## Credentials, permissions and trusted branches

Keep the multibranch job and approved-image job **outside** the trusted
publication folder. Neither may resolve `dockerhub-publish`, `github-publish`,
or unrelated global credentials. Store publication credentials only at the
publication folder containing develop/release. Inspect both ancestor folders and
global credential scope; an absence of `withCredentials` in today's script is not
proof of credential isolation. Keep agent-launch credentials controller-only.
The GitHub discovery/status App must be limited to this repository and the minimum
necessary permissions. Candidate code receives no credentials or Docker socket in
validation containers; approved image builds use empty Docker authentication.

Only the owner/administrators may Configure, Replay, edit managed files, approve
scripts, or change credentials/permissions for these jobs. Do not grant repository
collaborators a Jenkins login with broad inherited permissions. Build/Cancel access
to approved-image and publication jobs remains owner-controlled (the fixed parent
can schedule its child). Restrict release-job Build permission as well as keeping
its confirmation/dry-run controls. Audit actual authorization strategy and group
membership; generated job XML does not configure a security realm or ACL.

Apply `.github/rulesets/maintainer-merges.json` as a separate update-restriction
rule for `main`/`develop`. Only Pipepito is exempt from this rule. The existing
no-bypass PR/CI baseline remains separate and mandatory. This prevents two
collaborators from approving/merging a change into automatically published
`develop` without the owner. It does not grant a direct-push or CI bypass.

GitHub personal-repository writers can also edit GitHub release metadata. Jenkins
hardening does not change that GitHub role or grant access to the Docker registry.

## Prepare and audit configuration

Use a trusted checkout containing these changes. Export the existing multibranch
job's `config.xml` privately. It may contain private settings: never track or print
it. The preparer reads it as data, preserves the existing source credential and
notification settings, switches to a fixed managed definition, and emits private
configuration files. Supply the real Jenkins login (not automatically the GitHub
login) and the approved job's absolute item path using runtime-only variables.

```bash
python3 scripts/ops/prepare_jenkins_collaboration.py \
  --pr-config "$PR_CONFIG_EXPORT" \
  --approver "$JENKINS_APPROVER" \
  --policy-sha "$REVIEWED_POLICY_SHA" \
  --privileged-job "$PRIVILEGED_JOB_PATH" \
  --output "$NEW_PRIVATE_BUNDLE_DIRECTORY"
```

The new output directory must not exist. It has mode 0700 and its XML/Groovy files
have mode 0600. `sha256.json` records bundle hashes. The command performs no
network requests or mutations. Bundle contents:

- `pr-pipeline.groovy`: managed **Groovy file** content, ID `acestream-isolated-pr-v1`.
- `pr-job.xml`: patched multibranch configuration, preserving existing SCM/status setup.
- `privileged-job.xml`: new Pipeline job with fixed sandboxed inline definition and
  initial parameter definitions; no SCM-selected definition or automatic triggers.

After installing, export the actual job XMLs and managed script again and run:

```bash
python3 scripts/ops/prepare_jenkins_collaboration.py --audit \
  --pr-config "$LIVE_PR_CONFIG_EXPORT" \
  --privileged-config "$LIVE_PRIVILEGED_CONFIG_EXPORT" \
  --managed-script "$LIVE_MANAGED_SCRIPT_EXPORT" \
  --approver "$JENKINS_APPROVER" \
  --policy-sha "$REVIEWED_POLICY_SHA" \
  --privileged-job "$PRIVILEGED_JOB_PATH"
```

This verifies definition content, sandboxing, head-only PR discovery, fork trust,
and the lack of child triggers. It explicitly does not certify live credential
scope or ACLs; complete the manual inspections above as well.

## Activation order and acceptance

1. Keep new collaborator invitations on hold. Inspect current jobs, plugin
   versions, credentials, ACLs and in-flight builds. Back up the job configs
   privately. Let active Docker work finish; never cancel or prune its resources
   as part of this migration.
2. Commit and push the reviewed helper revision to this repository without
   merging or triggering publication. Render the child with that exact full SHA
   as `--policy-sha`. Review the helpers from that commit; no moving branch or PR
   parameter may select host orchestration. No release or develop merge is needed
   to bootstrap the managed definitions.
3. Install/verify Pipeline: Multibranch with defaults and Config File Provider.
   Create the managed Groovy file, create the approved-image job outside publication,
   apply job ACLs/credential separation, then update the multibranch factory and
   discovery settings. Preserve the GitHub App-bound `PR Validation` context.
4. Disable/drain any queued or waiting builds using old definitions before inviting
   collaborators. Re-index and check existing PR child jobs use the new defaults
   binder; changing the parent factory is not evidence that an already-running
   build switched definitions. Never replay an old contributor-controlled run.
5. Apply the owner-only merge rule separately without relaxing baseline checks.
6. Run the offline config audit against fresh live exports. Validate both pipeline
   definitions with Jenkins' Declarative linter. Perform the credential and ACL
   inspection, including inherited/global permissions.
7. Use a harmless internal-branch PR that changes its Jenkinsfile and a host-helper
   script to write a sentinel. Neither sentinel may execute during automatic
   validation. Check fork and internal PRs behave identically, with head-only status
   reporting and credential-free, network-disabled containers.
8. Verify a non-owner cannot approve the child; the owner can. Push another commit
   while approval is pending: approving the obsolete request must fail before any
   candidate code executes. Repeat with a changed base/target and closed PR.
9. A failed image build or rejected approval must leave `PR Validation` non-successful.
   A docs-only PR should finish without privileged approval. A dependency-changing
   PR must wait for approval and then run the full gate against its proposed runner.
   Observe the FIFO lock and confirm no images/tags are published by either PR job.
10. Only after these checks pass, invite collaborators. Keep release publishing
    manual and develop publishing limited to owner-merged protected commits.

For later pipeline changes, review and re-render the managed definitions explicitly;
merging a changed PR Jenkinsfile or helper does not silently update controller policy.
Pin a newly reviewed helper SHA when re-rendering the privileged definition. If
rollout fails, keep invitations suspended and jobs fail-closed. Restoring an old
SCM-selected definition reintroduces the original trust boundary and is not a
collaborator-safe rollback.

References: [Jenkins multibranch credential boundaries](https://www.jenkins.io/doc/book/security/securing-org-folders-and-multibranch-pipelines/)
and [default pipeline configuration](https://github.com/jenkinsci/pipeline-multibranch-defaults-plugin).
