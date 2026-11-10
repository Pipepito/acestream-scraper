# Jenkins validation and releases

Jenkins is the application's validation and release system. Its pipelines and
trusted host tooling are maintained in the private
[acestream-scraper-infra](https://github.com/Pipepito/acestream-scraper-infra)
repository. Application contributors do not need access to that repository.

## Contributing and reproducing checks

Push a branch and open a pull request into `develop`. Fork and same-repository
branches have the same CI permissions. Only `develop` may open a release PR into
`main`. The required commit status is `PR Validation / develop` (or
`PR Validation / main` for the release PR).

Application tests, dependency manifests, runtime Dockerfiles, local Docker-build
commands and architecture validators remain public. `bash scripts/ci/local_gate.sh`
runs the checks that match your change (`--plan` lists them first). Individual
commands, from this repository:

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

See [code quality](code-quality.md) for optional local hooks, coverage collection,
and the staged rollout of self-hosted security reporting. Enabling report collection
does not grant permission to run host builds or publish images.

## What Jenkins runs

Automatic PR checks use a fixed administrator-managed pipeline and private host
validators. Application code runs in disposable containers without networking,
Jenkins credentials or the Docker socket. For every pull request, with no
maintainer action, Jenkins runs:

1. repository metadata, source and secret scans;
2. runtime contracts on amd64, arm64 and arm/v7;
3. the complete backend and frontend suite: generated API types, ESLint and
   TypeScript first, then backend tests, frontend tests and the production build.

Step 3 runs automatically when the branch's dependency manifests are the same
as on the target branch; the test environment is built from the target, never
from proposed manifests. If they differ, because you changed them or because the
target changed them after you branched, the suite runs in the authorized job
described below (updating your branch avoids that when you did not change them).
Known documentation/metadata-only changes use lightweight data validation instead.
Editing a public selector, validator or Jenkinsfile cannot change Jenkins policy.

Two things run on the build host with network access and therefore need
authorization for the exact PR number, head, base and target: installing changed
dependencies and building images. Jenkins rechecks that identity before and
after the work, and never publishes from a pull request.

| Pull request | Host work before merge |
| --- | --- |
| Portable application sources only, from the maintainer | Every image flavor built and started on amd64, automatically |
| Build, runtime or dependency inputs (`Dockerfile`, `docker/`, runtime scripts, manifests), or a release PR, from the maintainer | Every flavor on amd64, arm64 and arm/v7, automatically; changed dependencies are installed and tested first |
| Portable application sources only, from another contributor | None. The status turns green after the isolated checks; `develop` builds and tests every image after merge, before publishing |
| Build, runtime or dependency inputs, from another contributor | Waits for the maintainer to review and approve that exact revision, then every flavor and platform. The branch must include the latest target commit first, so the review covers exactly what is built |

New revisions need new authorization. The required status stays pending until
the work the change needs has succeeded. A wait holds neither an executor nor
the shared Docker lock.

### Reading the result on your pull request

You do not need access to Jenkins. Each run leaves one comment on the pull
request and updates it as work finishes, and the same text is in the
`Code Quality / develop` check:

- **Application tests and coverage**: test counts, line coverage and coverage of
  the lines you changed (advisory, goal 80%). On failure it names the failing
  step, lists up to twenty failed backend tests and frontend test files, and
  gives the command that reproduces the step locally. Test titles and output
  are not shown.
- **Image builds**: passed, running, waiting for the maintainer, or deferred to
  `develop`.
- **Source and security scan**: new findings compared with the target branch.

Test output and logs are not posted. If the summary is not enough to reproduce
a failure, ask in the pull request.

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
result from GitHub's commit status. Inspect the live state of the current release
PR before reporting readiness. A passing historical build does not validate
new commits. See [collaborator safety](jenkins-collaborator-safety.md).

## Production image acceptance

Private CI now has a public, standard-library probe in
`docker/testdata/image_acceptance.py`. It executes inside the production image
without mounting replacement application source or installing packages. Native
flavors exercise the real entrypoint, migrations, SPA, OpenAPI, FFmpeg, healthcheck
and enabled engines; the engine-free Acexy flavor uses a loopback-only synthetic
upstream. The existing checker lifecycle probe remains separate. ARM packaging
checks inspect the final image; emulation is not proof of Android engine runtime
support on real ARM hardware.

The private deployment pins a reviewed public test-contract commit so older
release application revisions can use the same acceptance checks. Tests remain
public, while only private orchestration may invoke host Docker operations.
Changes to that pinned contract require an infrastructure review/deployment.
The production Dockerfile places application copies after stable installation
layers so application edits do not reinstall bundled operating-system packages.

The dependency runner must install `libx264-dev` when building the application's
minimal FFmpeg; the production Dockerfile's packages do not carry into that
separate image. Production acceptance probes are pinned independently in private
policy. Their first-run account checks preserve compatibility with older protected
branches only when the account-status endpoint is absent (HTTP 404); authentication
and server errors still fail acceptance.
