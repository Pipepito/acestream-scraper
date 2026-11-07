# GitHub contribution setup

Feature and fix PRs target `develop`; only `develop` targets `main`. Jenkins remains
the application validation and release system. GitHub Actions performs PR metadata
assignment only.

## Rulesets

The importable JSON in `.github/rulesets/` records the intended repository settings.
Editing or merging these files does **not** apply settings automatically. Inspect
live settings under [Settings → Rules → Rulesets](https://github.com/Pipepito/acestream-scraper/settings/rules)
or with `gh api repos/Pipepito/acestream-scraper/rulesets` before changing them.
Changes to live protection require explicit maintainer authorization.

| Ruleset | Targets | Requirements |
| --- | --- | --- |
| Protected integration and release branches | `main`, `develop` | PR required, review conversations resolved, Jenkins `PR Validation` successful; no deletion or force pushes; no bypass actors |
| Pull request review | `main`, `develop` | One approval, dismissed when reviewable commits change; `Pipepito` is automatically exempt from this review-only ruleset |
| Immutable version tags | `v*` tags | Existing tags cannot be updated or deleted; new tag creation remains manual and permitted |

The review exception uses the `User` actor for `Pipepito` (ID `1348529`) with
`bypass_mode: exempt`. GitHub does not evaluate this review-only ruleset for that
account, so no approval or manual bypass is needed when Pipepito merges. This is
an exemption for the merging user, not the PR author: Pipepito can also merge
collaborator PRs without approval. Collaborators remain subject to the review
requirement when they merge. This tradeoff was explicitly selected by the owner.
Jenkins and baseline PR/conversation rules still apply to everyone through the
separate ruleset with no exemptions. Direct pushes remain blocked. The baseline preserves the existing
non-strict status policy (no new requirement to update branches after every merge).

`PR Validation` is bound to GitHub App ID `3430282`, matching the classic branch
protections inspected on 2026-10-21. Existing classic protections are retained;
GitHub combines applicable protections. Recheck the App identity if Jenkins
authentication changes. Linear history is not required because release PRs merge
`develop` into `main`. Signed commits and merge queues are not required.

Live settings verified on 2026-10-21, while preparing this change from develop
`f46d1b9`: [baseline ruleset](https://github.com/Pipepito/acestream-scraper/rules/25541845),
[review ruleset](https://github.com/Pipepito/acestream-scraper/rules/25541859), and
[tag ruleset](https://github.com/Pipepito/acestream-scraper/rules/25541861) are active.
Recheck with the API command above; this is a dated snapshot, not a live status.

## Automatic PR assignment

`.github/workflows/assign-pull-requests.yml` adds `Pipepito` to PRs opened by other
accounts, including forks and bots, on open, reopen, or ready-for-review events.
Existing assignees remain, and already assigned PRs and Pipepito's own PRs are
skipped. Assignment is different from a review request; it does not approve a PR.

The workflow uses `pull_request_target` and a GitHub-hosted runner, with only
`pull-requests: write`. It calls the assignee API using the built-in `GITHUB_TOKEN`
and runner-provided `gh`. It has no checkout, third-party action, project command,
dependency install, cache, Jenkins access, or publication step. Never add execution
of PR-controlled code to this privileged metadata workflow.

The workflow must reach the default branch (`main`) before it can operate. It does
not backfill existing PRs without a matching event. Validate YAML and shell syntax
locally; after merging through `develop` into `main`, verify it on the next real
contributor PR by checking its Actions run and assignees.

## Issue forms

`.github/ISSUE_TEMPLATE/` provides bug, feature, documentation, and help forms.
Required fields collect reproduction steps, deployment details, evidence, user
needs, or attempted troubleshooting according to the issue type. Labels use the
repository's existing `bug`, `enhancement`, `documentation`, and `question` labels.
The chooser links to documentation and disables blank submissions through the UI.

Forms become available in the chooser only after they reach the default branch
(`main`). Use the normal feature PR to `develop` and release PR to `main`; do not
push directly or merge the release PR just to activate templates. After promotion,
open [New issue](https://github.com/Pipepito/acestream-scraper/issues/new/choose) and
preview all four forms without submitting a test issue.

GitHub documentation: [rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets),
[issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms),
and [workflow events](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request_target).

## Lightweight validation

Jenkins classifies issue-form YAML, ruleset JSON and the exact assignment workflow
as contribution metadata. It checks their structure and the workflow's trusted
behavior contract without building application images. Other workflows and
validator/pipeline changes retain full checks. Run locally with:

```bash
bash scripts/ci/validate_repository_metadata.sh "$PWD"
```

The validator installs only integrity-locked parser dependencies in a temporary
directory with install scripts disabled. PRs use target-owned policy; this CI
change itself must pass the old full gate before future PRs can use the shortcut.

## Collaborator access and publication control

The new `maintainer-merges.json` adds a separate update restriction to `main` and
`develop`, with only Pipepito exempt. It reserves merging into auto-published
integration/release branches to the owner while preserving the existing no-bypass
PR/CI baseline. This file is intended policy, **not a report of live activation**.
Apply it during the [Jenkins collaborator rollout](jenkins-collaborator-safety.md)
and inspect live rules before inviting repository writers. Collaborators still
push feature branches and open PRs; internal branches receive no extra CI trust.
