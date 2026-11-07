# Codex infrastructure access

This runbook explains how repository agents may inspect the project's current
infrastructure without putting private connection details in Git.

## Source of truth

The repository root may contain a local file named `infra-details.md`. It is
git-ignored and currently records:

- the Jenkins controller endpoint;
- the Jenkins operator identity and API token;
- the Jenkins build-agent host;
- the multibranch PR-validation job name;
- the manual release job name.

Never copy literal values from that file into tracked files, chat responses, PRs,
issues, screenshots, fixtures, shell traces, or build logs. Do not add the file to
Git. If the file is missing or stale, ask the operator for a current secure source;
do not infer credentials or scan the local network.

## Default authorization boundary

Reading job/build metadata is inspection. The following are mutations and require
an explicit user request naming or clearly authorizing the action:

- triggering, rebuilding, replaying, stopping, or deleting a build;
- editing jobs, folders, credentials, plugins, nodes, executors, or webhooks;
- running the manual release job or any non-dry-run publish path;
- publishing Docker tags, promoting `:latest`, or changing branch protection.

For any mutation, resolve the exact job, branch, commit, parameters, and expected
effect first. Prefer a dry-run or publish-plan command when the repository provides
one.

## Read-only Jenkins checks

Use the controller's JSON API or UI. Keep the URL, user, and token in runtime-only
variables sourced privately from `infra-details.md`; do not paste credential values
into the command itself and do not enable shell tracing.

Typical read-only endpoints are:

```text
<controller>/api/json
<controller>/job/Acestream-Scraper/api/json
<controller>/job/Acestream-Scraper/job/acestream-scraper-pr/api/json
<controller>/job/Acestream-Scraper/job/acestream-scraper-pr/job/PR-162/api/json
<controller>/job/Acestream-Scraper/job/acestream-scraper-pr/job/PR-162/lastBuild/api/json
```

Jenkins folder and multibranch job path segments each require their own `/job/`.
Request only the fields needed, for example with `tree=number,result,building,url,
timestamp,duration,actions[lastBuiltRevision[SHA1],parameters[name,value]]`.

Cross-check a Jenkins result against GitHub with:

```bash
gh pr view 162 --json headRefOid,state,mergeable,mergeStateStatus,statusCheckRollup,updatedAt,url
```

Always record the commit SHA. A green historical build is not evidence for a newer
head, and a GitHub Pages check is not the Jenkins `PR Validation` gate.

## Repository-owned previews

These commands inspect release behavior without publishing:

```bash
bash scripts/ci/run_jenkins_release.sh --print-publish-plan --channel develop
bash scripts/ci/run_jenkins_release.sh --dry-run --channel develop
bash scripts/ci/run_jenkins_release.sh --print-publish-plan
```

The channel variants describe floating `:develop*` tags. The non-channel plan is
for the manual release path. Review `docs/ops/jenkins-ci.md` and
`docs/release/v2-release-readiness.md` before drawing release conclusions.

## Incident hygiene

- If a token appears in tracked content, terminal output shared outside the local
  session, a screenshot, or a PR/issue, stop and tell the operator to rotate it.
- Do not attempt to rotate or replace credentials unless explicitly authorized.
- Redact controller/agent coordinates when sharing diagnostics publicly.
- Prefer build number, stage name, commit SHA, timestamps, and a sanitized error
  summary over copying a full Jenkins log.
