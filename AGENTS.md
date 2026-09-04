# Codex repository guide

This is the repository-wide instruction file for Codex. More specific guidance is
layered in `backend/AGENTS.md`, `frontend/AGENTS.md`, and `e2e/AGENTS.md`; Codex
loads the applicable file when working below those directories.

## Start here

- The active integration branch is `develop`; `main` is the release branch.
- The current release PR is GitHub PR #162, `develop` -> `main`, titled
  "Migration to V2, Api and FE." It supersedes #113 after the integration branch
  was renamed. This is a large v2 cutover, not a routine feature PR.
- Treat live PR and CI state as volatile. Before reporting it, run
  `gh pr view 162 --json state,mergeable,mergeStateStatus,statusCheckRollup,updatedAt,url`
  or inspect the PR in GitHub. On 2026-09-03 at commit `e5bc9e0`, the PR was open,
  clean/mergeable, and Jenkins PR-162 build #20 / `PR Validation` was successful.
- `backend/` and `frontend/` are the only canonical application roots. Do not
  restore the retired root Flask runtime, root `app/`, root `tests/`, `manage.py`,
  `run_dev.py`, or `wsgi.py`. The root `pyproject.toml` contains legacy package
  metadata and is not the runtime dependency source.
- Read `CLAUDE.md` for the most detailed project narrative. Use this file for
  Codex-specific operating rules and the layered files for implementation details.

## Repository map

- `backend/`: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, APScheduler, pytest.
- `frontend/`: React 18, TypeScript, Vite, MUI v5, React Query v5, Jest/RTL.
- `e2e/`: Playwright/Firefox journeys against the built SPA and real sidecars.
- `Dockerfile`, `docker/`, `entrypoint.sh`: multi-flavor, multi-architecture image.
- `jenkins/pr.Jenkinsfile`: fork-aware, credential-free multibranch PR validation.
- `jenkins/develop.Jenkinsfile`: trusted `develop` validation and automatic channel/docs publish.
- `jenkins/release.Jenkinsfile`: manual release job, allowed from `main` only.
- `scripts/ci/`: required checks, Docker builds, publishing, and CI helpers.
- `docs/ops/jenkins-ci.md`: authoritative Jenkins and release runbook.
- `docs/migration/development-progress.md`: live migration status.
- `.planning/codebase/`: generated codebase map useful for orientation, not a
  substitute for checking the implementation.

## Working agreements

- Inspect the working tree first. Preserve user changes and unrelated edits.
- Prefer existing patterns and the narrowest change that completes the request.
- Keep the frontend TypeScript-only. Do not add `.js` or `.jsx` application files.
- Keep API endpoint modules thin; business logic belongs in services and DB-only
  access belongs in repositories.
- Use timezone-aware datetimes. Do not introduce `datetime.utcnow()`.
- Do not use `Base.metadata.create_all()` as a production migration strategy.
  Schema changes require an Alembic revision and migration-path tests.
- If an API contract changes, update Pydantic schemas, regenerate
  `frontend/src/types/api-generated.ts`, update services/tests, and verify drift.
- If ports, environment options, or image flavors change, update
  `docs/builder/runtime-options.json` and run the command-builder contract check.
- Changes to sidecar installation/runtime behavior must consider image flavor,
  CPU architecture, supervisor behavior, health probes, and Docker documentation.
- ARM64 and ARMv7 AceStream builds use the matching platform variants from the
  digest-pinned `jopsis/acestream:v3.2.17-fix` OCI image. ARMv7 remains
  experimental until its engine is runtime-tested on real ARMv7 hardware.
- User-facing UI copy is plain, concise, and operational. Preserve both themes,
  responsive behavior, keyboard access, reduced motion, and non-color status cues.
- Do not commit generated/runtime data such as local SQLite databases, E2E stack
  state, Playwright reports, logs, caches, or secrets.

## Verification

Choose checks proportionate to the change and report exactly what ran.

Quick cross-stack gate from the repository root:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/assert_no_legacy_paths.sh --strict
```

Useful focused checks:

```bash
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/path/to/test_file.py
cd frontend && npm test -- --runInBand path/to/Test.test.tsx
cd frontend && npm run typecheck && npm run lint -- --max-warnings=0
cd frontend && npm run build:backend
cd e2e && npm run typecheck
python3 scripts/ci/validate_docker_manifest_metadata.py
bash scripts/ci/validate_command_builder.sh
```

Use `bash scripts/ci/run_v2_test_suite.sh --profile full` for broad validation.
Docker packaging/smoke tests are separate and may require Docker/buildx and much
more time. Playwright is valuable for user-visible or integration changes, but is
not part of the required PR gate; see `e2e/AGENTS.md` before running it.

## Branch and release policy

- Feature and hotfix PRs target `develop`.
- Only `develop` may open a PR into `main`; `jenkins/pr.Jenkinsfile` enforces this.
- Both protected branches require the `PR Validation` status and disallow direct
  pushes, force-pushes, and deletion.
- A validated trusted `develop` job publishes only floating `:develop*` tags.
  It must never publish `:latest` or version tags.
- Releases are manual through `acestream-scraper-release` on `main`. Publishing
  version tags and promoting `:latest` are separate, deliberate phases.
- Never trigger a release, publish images, promote tags, merge the release PR,
  change branch protection, or mutate Jenkins configuration unless the user has
  explicitly authorized that action.
- Before a release, follow the current checklist in `docs/ops/jenkins-ci.md` and
  `docs/release/v2-release-readiness.md`; do not rely on an old PR body.

## Jenkins and infrastructure

- Jenkins is the sole repository validation and release system. GitHub Actions
  application workflows were retired; the remaining Pages workflow is not the
  application CI gate.
- The local, git-ignored `infra-details.md` contains the current controller URL,
  operator identity/token, build-agent address, and job names. See
  `docs/ops/codex-infrastructure-access.md` before using it.
- Treat every value in `infra-details.md` as sensitive even if it looks harmless.
  Never quote the file in output, copy values into tracked docs, logs, commands
  likely to be recorded, issue/PR text, screenshots, or test fixtures.
- Infrastructure inspection is read-only by default. Triggering/cancelling jobs,
  replaying builds, changing Jenkins jobs/credentials/nodes, or publishing artifacts
  is an external mutation and needs explicit user authorization.
- The multibranch validation job is `acestream-scraper-pr`; trusted publication
  uses `acestream-scraper-develop`, and manual releases use
  `acestream-scraper-release`. All currently launch on `dorat-nuc-ci`, but fork
  code runs only inside network-disabled containers; it must never receive the
  Docker socket or a Jenkins credential. Each fork build creates a disposable
  dependency runner from the trusted target ref, then runs runtime contracts in
  pinned amd64, arm64, and arm/v7 userlands. Do not execute a fork-controlled
  Dockerfile or install fork-controlled dependency inputs automatically.
- When Jenkins and GitHub disagree, distinguish the Jenkins build result from the
  GitHub commit status and record the commit SHA each result belongs to.

## Code review rules

- Flag any reintroduction of legacy root runtime paths as release-blocking.
- Flag schema/model drift without an Alembic revision or upgrade-path test.
- Flag API changes without generated-client and frontend service/test updates.
- Flag SSRF regressions in scraper/EPG URL handling or accidental weakening of
  optional API-token enforcement.
- Flag secrets, local infrastructure coordinates, or credentials in tracked files.
- Flag release/channel logic that could publish `:latest`, a version tag, or Docker
  credentials from an unvalidated/non-release context.
- Flag blocking I/O added to async request paths or unbounded work moved into app
  startup. The deferred v1 EPG migration must remain resumable and non-blocking.
- Flag platform assumptions that silently drop amd64, arm64, or arm/v7 behavior.

## Documentation expectations

- Update the nearest durable document when behavior, commands, deployment, or
  operator procedure changes.
- Keep `CLAUDE.md` and the applicable `AGENTS.md` aligned when changing a core
  workflow that both agents need to know.
- Do not turn dated CI status into timeless documentation. Label snapshots with a
  date and commit, and include the command/source future agents should recheck.
