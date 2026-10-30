# Local quality feedback and Jenkins reports

Jenkins is authoritative. Its administrator-managed infrastructure policy cannot
be replaced by a PR, including same-repository branches. Scanners run locally on
the self-hosted workers; no code or findings are uploaded to a scanner service.

Install Ruff 0.17.3 and Gitleaks 8.30.1 from their official releases. Python test
dependencies include pytest-cov 7.0.0. Use the existing frontend `npm ci` setup.

```sh
bash scripts/ci/quality_local.sh fast   # syntax checks, ESLint and TypeScript
bash scripts/ci/quality_local.sh full   # full suite with separate coverage reports
git config --local core.hooksPath .githooks
```

The optional pre-commit hook scans the staged diff for secrets and checks changed
Python files. Ruff findings are advisory in both hooks during rollout; Ruff
execution/configuration failures and detected secrets still fail. Pre-push always
continues from advisory Ruff findings to the existing ESLint/TypeScript gates.
Hooks can be bypassed locally and do
not replace Jenkins. To uninstall them, unset `core.hooksPath` in local Git config.
Do not add real credentials to fixtures; use clearly synthetic test data.

The full suite writes backend Cobertura/JUnit and frontend Cobertura/Jest JSON
under `.quality-reports/`. Generated TypeScript API declarations, declarations,
test helpers/tests and build output are excluded from coverage; runtime code is
not excluded to improve the percentage. Jenkins additionally normalizes Jest to
JUnit and compares executable changed lines against the authenticated target's
merge base. No changed executable lines means N/A, not 100%.

Initial enforcement blocks failed tests, missing/invalid expected reports,
scanner execution failures, new secrets and serious new findings under reviewed
private policy. Existing findings are technical debt. Coverage is initially
advisory with an 80% changed-line goal for each component separately. Docs-only
PRs still receive secret/static checks and an explicit test/coverage applicability
summary. Full existing release and image validation remains mandatory.

Detailed findings and trends remain in Jenkins. GitHub gets conclusions, counts
and report links, not source snippets or discovered secrets. Report false positives
to the maintainer; exceptions require a fingerprint, reason, reviewer and expiry
in the infrastructure repository. PR-owned suppressions do not weaken CI policy.
