# Jenkins validation and releases

Jenkins is the application's validation and release system. Its pipelines and
trusted host tooling are maintained in the private
[acestream-scraper-infra](https://github.com/Pipepito/acestream-scraper-infra)
repository. Application contributors do not need access to that repository.

## Contributing and reproducing checks

Push a branch and open a pull request into `develop`. Fork and same-repository
branches have the same CI permissions. Only `develop` may open a release PR into
`main`. The required commit status is `PR Validation`.

Application tests, dependency manifests, runtime Dockerfiles, local Docker-build
commands and architecture validators remain public. From this repository:

```sh
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/run_v2_test_suite.sh --profile full
bash scripts/ci/assert_no_legacy_paths.sh --strict
python3 scripts/ci/validate_docker_manifest_metadata.py
bash scripts/ci/validate_command_builder.sh
python3 scripts/phase_gates/phase5_gate_runner.py --profile quick
```

See [CLAUDE.md](../../CLAUDE.md) and the component guides for dependency setup,
backend/frontend development and individual tests. The architecture gate retains
public build-plan and manifest checks; infrastructure publication-policy tests
live alongside the private pipelines.

## What Jenkins runs

Automatic PR checks use a fixed administrator-managed pipeline and private host
validators. Application code runs in disposable containers without networking,
Jenkins credentials or the Docker socket. A verified runner is selected from
protected dependency inputs. Changed dependencies need maintainer approval before
installation; architecture contracts still run automatically on amd64, arm64 and
arm/v7. Known documentation/metadata-only changes use lightweight data validation.
Editing a public selector, validator or Jenkinsfile cannot change Jenkins policy.

Application PRs additionally wait for owner-approved host image validation. The
approval binds the PR number, exact head, protected base and target branch. Jenkins
rechecks that identity before and after the work, and builds supported image
flavors/platforms without publishing. New revisions need new approval. The required
status stays pending until the approved validation succeeds. An approval wait
holds neither an executor nor the shared Docker lock.

All Docker workloads acquire the same FIFO lock before their agent and retain it
through cleanup. Existing executions retain the policy with which they started.
Every new deployment pins an infrastructure commit and a checksum-verified bundle;
the application cannot select either. Private Git credentials never go to agents.

## Publication

Only the maintainer may merge into protected `develop` and `main`; the required PR
and CI rules remain enforced. A validated current `develop` revision may publish
floating `develop*` tags. It cannot publish version tags or `latest`.

Main releases remain manual, with explicit release confirmation and a dry-run
option. `version.txt` selects the version. Existing version tags block publication
unless the maintainer deliberately selects the overwrite option. Latest promotion
is a separate decision after canary validation. GitHub release/tag and wiki
publication follow successful non-dry-run latest promotion.

Publishing credentials are scoped to the trusted publication folder. PR jobs have
no access to them. Only the owner's Jenkins account may administer or approve host
builds. Operational deployment, rollback and publication commands are documented in
the private repository; secrets remain in Jenkins and local ignored configuration.

GitHub Pages serves committed `main/docs`; Jenkins does not publish Pages or Docker
Hub descriptions. Prepare Pages assets with `bash scripts/ci/prepare_pages.sh`.
Docker Hub text is copied manually. Public wiki and release notes remain here.

## Verification

A repository change is not proof that Jenkins has deployed it. Compare the app
commit SHA and infrastructure revision in build logs, and distinguish the Jenkins
result from GitHub's commit status. PR #207 is the current release PR; inspect its
live state before reporting readiness. A passing historical build does not validate
new commits. See [collaborator safety](jenkins-collaborator-safety.md).
