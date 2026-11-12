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
| Protected integration and release branches | `main`, `develop` | No deletion or force pushes; no bypass actors |
| PR validation for develop | `develop` | PR required, review conversations resolved, Jenkins `PR Validation / develop` successful; `Pipepito` may bypass these, including with a direct update |
| PR validation for main | `main` | PR required, review conversations resolved, Jenkins `PR Validation / main` successful; no bypass actors |
| Maintainer-controlled integration and release | `main`, `develop` | Only `Pipepito` may update these branches |
| Pull request review | `main`, `develop` | One approval, dismissed when reviewable commits change; `Pipepito` is automatically exempt from this review-only ruleset |
| Immutable version tags | `v*` tags | Existing tags cannot be updated or deleted; new tag creation remains manual and permitted |

The review exception uses the `User` actor for `Pipepito` (ID `1348529`) with
`bypass_mode: exempt`. GitHub does not evaluate this review-only ruleset for that
account, so no approval or manual bypass is needed when Pipepito merges. This is
an exemption for the merging user, not the PR author: Pipepito can also merge
collaborator PRs without approval. Collaborators remain subject to the review
requirement when they merge. This tradeoff was explicitly selected by the owner.
The PR/conversation rules live in the per-branch rulesets below: everyone on
`main`, everyone but the owner on `develop`. The status rules keep the
non-strict policy (no requirement to update branches after every merge).

The required Jenkins status is separate for each target, so a result for
`develop` can never satisfy `main`. Both contexts are bound to GitHub App ID
`3430282`; recheck that identity if Jenkins authentication changes. Jenkins'
native `PR Validation` context may still appear on commits as information. It is
not a merge requirement.

On `develop`, the PR and status ruleset lists `Pipepito` with `bypass_mode:
always`. The owner selected this on 2026-11-12 so that **Update branch** on the
release pull request can merge `main` into `develop` without a second pull
request. GitHub cannot limit a bypass to that button: the owner can also push
any commit to `develop` directly, and can merge a pull request there without a
green status (GitHub asks for confirmation). Nobody else can, because the update
restriction lets only the owner update the branch. A direct update still starts
the develop pipeline, which tests it after the fact.

`main` has no bypass: every change needs a pull request and `PR Validation /
main`. The same pull-request rule is recorded in both per-branch rulesets because
a bypass applies to a whole ruleset. To withdraw the owner's direct access to
`develop`, remove that bypass actor from the live ruleset and from
`pr-validation-develop.json` together.

Existing classic protections are retained; GitHub combines applicable
protections. Linear history is not required because release PRs merge `develop`
into `main`. Signed commits and merge queues are not required.

Live settings verified on 2026-11-12 with the API command above:
[baseline](https://github.com/Pipepito/acestream-scraper/rules/25541845),
[develop status](https://github.com/Pipepito/acestream-scraper/rules/25727775),
[main status](https://github.com/Pipepito/acestream-scraper/rules/25727778),
[maintainer merges](https://github.com/Pipepito/acestream-scraper/rules/25711165),
[review](https://github.com/Pipepito/acestream-scraper/rules/25541859) and
[tag](https://github.com/Pipepito/acestream-scraper/rules/25541861) rulesets are
active. This is a dated snapshot, not a live status.

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

`maintainer-merges.json` adds a separate update restriction to `main` and
`develop`, with only Pipepito exempt. It reserves merging into auto-published
integration/release branches to the owner and is active on GitHub. Inspect live
rules again before inviting repository writers; see the
[Jenkins collaborator rollout](jenkins-collaborator-safety.md). Collaborators
still push feature branches and open PRs; internal branches receive no extra CI
trust.
