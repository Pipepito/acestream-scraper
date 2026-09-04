# Jenkins CI/CD Operator Guide

## Overview

This document is the primary operator guide for Jenkins CI/CD in this repository.

Current rollout state:

- Jenkins is the canonical path for pull request validation and release publication in this repository.
- (Superseded 2026-08-26, e5657b9) GitHub Actions remain available during the current proving window as fallback/reference workflows while operators build confidence in Jenkins hardening. Current state: the last workflows (`.github/workflows/pull_request.yml`, `.github/workflows/release.yml`) were deleted in e5657b9 and `.github/workflows/` no longer exists; Jenkins is the sole validation and release path. Older "proving window" statements below are kept as the historical record and annotated as superseded.
- Jenkins assets in this repository are ready to be wired into your homelab controller and agent.

Important constraint for this setup:

- Jenkins should be configured through the Jenkins UI.
- Do not copy `Jenkinsfile`, `jenkins/release.Jenkinsfile`, shell scripts, or helper files into the Jenkins Docker container.
- Jenkins should load pipeline definitions directly from this Git repository through SCM configuration in the UI.

Current job model (adopted 2026-09-04):

- `acestream-scraper-pr` is a multibranch job loading `jenkins/pr.Jenkinsfile`. It discovers origin and fork PRs, reports `PR Validation`, never binds a credential, and confines contributor code to the trusted PR-runner container.
- `acestream-scraper-develop` is a Pipeline-from-SCM job loading `jenkins/develop.Jenkinsfile` from `develop`. It runs the full application suite and privileged Docker/runtime smokes, rejects stale revisions, then publishes the floating `develop` channel, wiki, and Pages.
- `acestream-scraper-release` loads `jenkins/release.Jenkinsfile` from `main` and remains manual-only.
- GitHub Actions workflows are retired; Jenkins is the sole CI/CD implementation.

Security boundary:

- Jenkins itself launches on the trusted Docker-capable executor labeled `dorat-nuc-ci`, but fork-controlled files execute only inside `acestream-scraper-pr-ci:develop`.
- The PR container receives only the checked-out workspace. It receives no Jenkins credential, no Docker socket, no host network, and no inherited Jenkins environment. It runs as the agent's unprivileged uid with all Linux capabilities dropped, `no-new-privileges`, and CPU/memory/PID limits. Forks execute the validation orchestrator from the target branch; maintainer-owned origin PRs may exercise their proposed orchestrator. Every PR runs the complete non-Docker backend and frontend suites from the pinned dependency image; privileged engine and packaging smokes stay on trusted `develop`.
- The runner image is built only by the trusted `develop` job from digest-pinned official Python and Node base images. A fork build fails closed if the image is missing.
- Privileged Docker builds, engine runtime smokes, Docker Hub credentials, and GitHub publication credentials exist only in the trusted develop/release pipelines.
- The container boundary reduces host and credential exposure; it does not replace maintainer review. Tests and repository scripts are contributor-controlled inputs.

Current ownership stance:

- Jenkins multibranch pipelines are the canonical path for pull request validation.
- Jenkins manual release jobs are the canonical path for release publication.
- (Superseded 2026-08-26, e5657b9) GitHub Actions should be retained as fallback/reference workflows until you decide the Jenkins setup is proven. Current state: the workflows are deleted; if Jenkins is unavailable the fallback is the workstation procedure in `## Rollback Guidance`, not GitHub Actions.

Responsibility split:

- Repo-owned: `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, `scripts/ci/run_jenkins_release.sh`, build/test scripts, and supporting documentation.
- User-owned: Jenkins controller installation, build-node launch model, dedicated build VM lifecycle, plugin installation, credentials, GitHub App registration, optional webhook exposure or polling setup, branch protection cutover, and rollback decisions.

Networking model:

- Jenkins does not need to be exposed to the public internet if you are willing to use periodic scans or manual rescans instead of GitHub webhooks.
- Jenkins only needs outbound access to GitHub to fetch SCM metadata and report commit statuses/checks.
- GitHub only needs inbound access to Jenkins if you want webhook-triggered scans or builds.

Executor model:

- The three pipelines currently launch on `dorat-nuc-ci`; the PR pipeline uses its Docker daemon only to start the hardened container and never mounts that daemon into the container.
- The trusted develop and release jobs retain direct Docker/Buildx access for runtime smoke and publication.
- SSH is a documented example agent-launch path, not a pipeline requirement.

## Branching Model And Pre-release Channel

Adopted 2026-08-28. The integration branch `ai-coding-documentation` was renamed to `develop`; the rename auto-closed PR #113, and its successor is the release PR #162 (`develop` -> `main`).

Branch roles:

- `develop` is the permanent pre-release branch. Feature PRs target `develop`.
- `main` is the release branch. The only way into `main` is a `develop` -> `main` pull request (the release PR).
- Hotfixes go through `develop` too: branch off `develop`, PR the fix into `develop`, then cut a `develop` -> `main` release PR. Never open a PR into `main` from any other branch; the pipeline rejects it (below).

Protections (GitHub, identical on `develop` and `main`): pull requests only (no direct pushes), required status check `PR Validation`, force-push and deletion disabled.

Pipeline enforcement in `jenkins/pr.Jenkinsfile` (multibranch job `acestream-scraper-pr`):

- `Branch Policy` stage: runs when `env.CHANGE_TARGET == 'main'` and fails the build when `env.CHANGE_BRANCH != 'develop'` (`Pull requests into main must come from develop ...`). Feature PRs into `develop` skip it.
- `Credential-free PR validation` runs quick backend/frontend, generated API, runtime, docs, and architecture-plan checks inside the restricted container. It never publishes and cannot access the Docker daemon.

Pipeline enforcement in `jenkins/develop.Jenkinsfile` (trusted job `acestream-scraper-develop`):

- The job polls `develop`, requires checked-out `HEAD == origin/develop`, builds the trusted PR-runner image, and runs full application validation inside that pinned Python 3.12/Node runner with networking disabled. Compose validation and Docker/runtime smokes remain on the trusted host.
- It repeats the `HEAD == origin/develop` comparison immediately before publication so an older queued build cannot move the channel backwards.
- It then binds `dockerhub-publish` and runs `bash scripts/ci/run_jenkins_release.sh --channel develop`. Missing credentials or push failures fail the build.
  - Channel mode logs into Docker Hub, builds the four flavors multi-platform (`linux/amd64`, `linux/arm64`, `linux/arm/v7`) with `--push`, and verifies every pushed manifest.
  - Tags pushed (floating only): `pipepito/acestream-scraper:develop` (= the full `scraper-acestream-acexy` payload, mirroring what `:latest` means for releases), `:develop-scraper`, `:develop-scraper-acestream`, `:develop-scraper-acexy`, `:develop-scraper-acestream-acexy`. Never a version tag, never `:latest`, no immutable per-commit tags. The channel tags move on every validated `develop` build.
  - Artifacts: `phase5-build-result-channel-develop-<flavor>.json` per flavor plus `phase5-build-result-channel-develop-metadata.json` (`mode: channel`, channel, version, git sha, builder, tags), archived by the stage as `phase5-build-result-channel-*.json`.

Versioning:

- `version.txt` on `develop` carries the next version with a `-dev` suffix (for example `v2.1.0-dev`) once `v2.0.0` ships; a PR into `develop` bumps it to the final version right before the `develop` -> `main` release PR (the release PR's head is `develop`, so the bump cannot live in the release PR itself). As of 2026-08-28 `version.txt` reads `v2.0.0` (PR #162 is the v2.0.0 release PR), so the suffix convention starts with the next cycle.
- Guard: `scripts/ci/run_jenkins_release.sh` refuses a release run (no `--channel`) while `version.txt` contains `-dev`: `Refusing to release a development version (version.txt = ...). Land the version bump on develop (via PR) before the develop -> main release PR.` The channel publish accepts a `-dev` version.
- `scripts/phase_gates/check_workflow_publish_guard.py` enforces the PR sandbox, credential separation, exact-develop guard, channel tags, release tags, and `:latest` promotion boundary.

How a release is cut:

1. Merge feature PRs into `develop` only after `PR Validation` and maintainer review. The separate trusted develop job reruns the full/privileged gates and refreshes `:develop*` only when they pass.
2. Land the `version.txt` bump (`vX.Y.Z-dev` -> `vX.Y.Z`) on `develop` through its own PR, then open (or let Jenkins rebuild) the `develop` -> `main` release PR from `vX.Y.Z-dev` to `vX.Y.Z`. `Branch Policy` passes because the head is `develop`; the PR's builds keep publishing the channel.
3. Merge the release PR. Nothing is published automatically on merge.
4. Run the manual `acestream-scraper-release` job from `main` (`CONFIRM_RELEASE`, `DRY_RUN`, `PUBLISH_LATEST`): phase 1 pushes `:vX.Y.Z` plus the flavor tags; after canary validation, `PUBLISH_LATEST=true` retags the canaried version manifest to `:latest` (`scripts/ci/promote_latest.sh`). See `## Manual Release Job` and `## v2.0.0 Release Runbook`.
5. Back on `develop` (through a PR), bump `version.txt` to the next `-dev` version.

Operator preview commands (from any checkout, no credentials needed):

```bash
bash scripts/ci/run_jenkins_release.sh --print-publish-plan --channel develop
bash scripts/ci/run_jenkins_release.sh --dry-run --channel develop
```

The first prints the channel tag plan per flavor; the second runs the dry-run build matrix per flavor (`build_multiarch_images.sh --dry-run`) and writes the `phase5-build-result-channel-develop-<flavor>.json` files without logging in or pushing. The existing `--print-publish-plan` / `--dry-run` without `--channel` preview a release the same way.

For testers: `docker pull pipepito/acestream-scraper:develop` (or `:develop-<flavor>`) is the pre-release build; Docker Compose users set `image: pipepito/acestream-scraper:develop` in place of `:latest` in `docker-compose.yml`. Expect the tags to move on every validated `develop` build.

## User Action Required

The following steps require operator intervention outside the repository:

- Provision a dedicated Jenkins controller and a dedicated Docker-capable build VM.
- Install the required Jenkins plugins.
- Ensure `git` is already installed on the build node before the first real Jenkins build runs.
- Decide whether to preinstall the rest of the toolchain or let `scripts/ci/bootstrap_jenkins_runner.sh` install missing software during the build.
- Ensure Docker access works for the current Jenkins runtime user on the node that will execute the pipelines.
- Configure a Jenkins executor labeled `dorat-nuc-ci`.
- Register the GitHub App, install it on the repository, and store its credentials in Jenkins.
- If you want webhook-driven scans, expose Jenkins webhook endpoints over reachable HTTPS with working DNS or a reverse proxy/tunnel.
- Create the Jenkins multibranch validation job from `jenkins/pr.Jenkinsfile`.
- Create the automatic trusted develop job from `jenkins/develop.Jenkinsfile`.
- Create the Jenkins manual release job from `jenkins/release.Jenkinsfile`.
- Observe the Jenkins check name reported back to GitHub and update branch protection to require it (done 2026-08-28 on `main` and `develop`).
- Store `dockerhub-publish` and `github-publish` only in a trusted publication subfolder containing the develop and release jobs. The PR multibranch job must not be able to resolve them.
- (Superseded 2026-08-26, e5657b9) Keep GitHub Actions fallback/reference workflows available until Jenkins hardening is verified; do not treat `main` publication through GitHub Actions as the primary operating path. Current state: GitHub Actions are retired; `main` is validated only by the Jenkins `PR Validation` status and published only by the manual Jenkins release job.

## Complete Setup Checklist

Use this as the end-to-end checklist for a fresh Jenkins controller running in Docker on your homelab.

- `## Start Here` below is the concise operator path for getting Jenkins online quickly.
- The numbered sections later in this document are the expanded, authoritative reference for the same setup and should win if the shorter checklist feels ambiguous.

## Start Here

If you want the shortest path from a fresh Jenkins container to working PR and release jobs, do these three checklists in order.

If you prefer to wire Jenkins jobs first and let the repository bootstrap the runner on first use, that also works. The important constraint is simpler than the checklist order: `git` must already exist for `checkout scm`, and Docker access must already work for the current runtime user on the executor labeled `dorat-nuc-ci`.

### A. Ubuntu VM First

- [ ] Create the Ubuntu 24.04 VM.
- [ ] SSH into the VM as your admin user.
- [ ] Install `git` so Jenkins can complete the initial `checkout scm`.
- [ ] Ensure Docker access already works for the user Jenkins will run as on this node.
- [ ] Decide whether the first builds will run as your operator user or a dedicated `jenkins` user.
- [ ] If you want repository bootstrap to install missing software, run the passwordless-sudo steps from `## Passwordless Sudo For The Jenkins Agent` for that runtime user.
- [ ] If you are using SSH-launched nodes with a dedicated `jenkins` user, create `/home/jenkins/.ssh/authorized_keys` and add the Jenkins SSH public key.
- [ ] Verify:
  - [ ] `git --version`
  - [ ] `docker version`
  - [ ] If using passwordless bootstrap installs, `sudo -n true`
- [ ] If you are using SSH-launched nodes, confirm the VM is reachable from your Jenkins host over SSH.

### B. Jenkins UI Next

- [ ] Log into Jenkins as admin.
- [ ] Set the Jenkins base URL.
- [ ] Install the required plugins.
- [ ] If you are using SSH-launched nodes, add SSH credential `acestream-build-agent-ssh`.
- [ ] Add GitHub App credential `github-app-acestream-scraper`.
      If your live controller already uses a different working credential id such as `github-builder-app`, keep using that live id until you intentionally normalize the controller configuration.
- [ ] Add `dockerhub-publish` and `github-publish` inside the trusted publication subfolder only.
- [ ] Create the build executor and apply label `dorat-nuc-ci`.
- [ ] Confirm the node comes online.
- [ ] Push the repo branch/commit that contains:
  - [ ] `jenkins/pr.Jenkinsfile`
  - [ ] `jenkins/develop.Jenkinsfile`
  - [ ] `jenkins/release.Jenkinsfile`
  - [ ] `scripts/ci/bootstrap_jenkins_runner.sh`
  - [ ] `scripts/ci/run_jenkins_validation.sh`
  - [ ] `scripts/ci/run_jenkins_release.sh`
- [ ] Create the multibranch PR-validation job from `jenkins/pr.Jenkinsfile`.
- [ ] Create the automatic develop job from `jenkins/develop.Jenkinsfile`.
- [ ] Create the manual release job from `jenkins/release.Jenkinsfile`.

### C. GitHub App And Validation Last

- [ ] Create and install the GitHub App on this repository.
- [ ] Choose your trigger model: public webhook delivery or private periodic scan/manual scan.
- [ ] Trigger an initial multibranch scan.
- [ ] Open or update a test PR.
- [ ] Confirm Jenkins reports the `PR Validation` status context back to GitHub.
- [ ] Run the manual release job with `CONFIRM_RELEASE=true` and `DRY_RUN=true` (leave `PUBLISH_LATEST` off; see `### 11.`).
- [x] Only after Jenkins is stable, add the Jenkins check to branch protection. Done 2026-08-28: `PR Validation` is the required status check on `main` and on `develop`.
- [x] (Superseded 2026-08-26, e5657b9) Keep GitHub Actions available as fallback/reference workflows until you are happy with the Jenkins setup. No action required: the workflows are retired.

### Quick Outcome Check

You are ready to rely on Jenkins for the next phase when all of these are true:

- [ ] Jenkins agent is online and builds on the VM
- [ ] multibranch PR validation runs successfully
- [ ] GitHub shows the Jenkins PR check
- [ ] release dry-run succeeds
- [ ] GitHub shows `PR Validation`

### 1. Jenkins Controller Basics

- [ ] Confirm the Jenkins Docker container is running and persistent storage is mounted for Jenkins home.
- [ ] Sign in to the Jenkins UI with an admin account.
- [ ] Set the Jenkins base URL under `Manage Jenkins` -> `System`.
- [ ] Decide whether you want public GitHub webhooks or a private controller with periodic scans/manual rescans.
- [ ] Only if you are using GitHub webhooks, confirm the public URL works from outside your LAN.

### 1.5. Push The Jenkins Repo Files First

- [ ] Push the branch or commit that contains `Jenkinsfile`.
- [ ] Push the branch or commit that contains `jenkins/release.Jenkinsfile`.
- [ ] Push the branch or commit that contains `scripts/ci/bootstrap_jenkins_runner.sh`.
- [ ] Push the branch or commit that contains `scripts/ci/run_jenkins_validation.sh`.
- [ ] Push the branch or commit that contains `scripts/ci/run_jenkins_release.sh`.
- [ ] Push the updated operator docs so you can follow the checked-in guidance from the same repo state Jenkins will use.
- [ ] Confirm GitHub shows those files in the branch or `main` revision Jenkins will read.

### 2. Install Jenkins Plugins

- [ ] Open `Manage Jenkins` -> `Plugins`.
- [ ] Install the required baseline plugins:
  - [ ] GitHub Branch Source
  - [ ] GitHub Checks
  - [ ] Pipeline
  - [ ] Credentials
  - [ ] Credentials Binding
  - [ ] Plain Credentials
  - [ ] Timestamper
  - [ ] Workspace Cleanup
  - [ ] github-scm-trait-notification-context
- [ ] Install `Multibranch Scan Webhook Trigger` if you want webhook-triggered multibranch scans.
- [ ] Install `SSH Build Agents` only if you will use the SSH-launch model for the build node.
- [ ] Install `Docker Pipeline` if your Jenkins setup expects that plugin for Docker-aware pipeline features.
- [ ] Restart Jenkins if required.

### 3. Prepare The Build VM

- [ ] Provision the Ubuntu 24.04 VM.
      There is no single repo-owned command for VM creation because this depends on your hypervisor or cloud. As soon as the VM exists, connect to it as your admin user and use the remaining commands below.

  ```bash
  ssh <admin-user>@<vm-ip>
  ```

- [ ] Verify it has enough CPU, RAM, and disk.
      Run on the VM:

  ```bash
  lscpu | grep -E 'Architecture|CPU\(s\)|Model name'
  free -h
  df -h /
  lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
  ```

- [ ] Install `git` as a hard prerequisite for the initial Jenkins checkout.
      Run on the VM:

  ```bash
  sudo apt-get update
  sudo apt-get install -y git
  ```

- [ ] Decide whether to preinstall the rest of the toolchain now or let `scripts/ci/bootstrap_jenkins_runner.sh` handle missing packages during the build.
      Preinstalling is still a valid operator choice, but it is no longer required for first bootstrapping. If you want the node fully provisioned ahead of time, run on the VM:

  ```bash
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl gnupg jq python3 python3-venv python3-pip
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
  echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | sudo tee /etc/apt/sources.list.d/nodesource.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin nodejs
  sudo systemctl enable --now docker
  ```

- [ ] Decide which runtime user Jenkins will use on this node.
      Builds may currently run under your operator user before a dedicated `jenkins` user is ready. If you want a dedicated `jenkins` user, run on the VM:

  ```bash
  sudo useradd --create-home --shell /bin/bash jenkins || true
  id jenkins
  ```

- [ ] Enable passwordless `sudo` only if you want repository bootstrap to install missing software for the runtime user.
      Replace `jenkins` below with the actual runtime user if the node is still running builds as your operator account. Run on the VM:

  ```bash
  echo 'jenkins ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/jenkins >/dev/null
  sudo chmod 440 /etc/sudoers.d/jenkins
  sudo visudo -cf /etc/sudoers.d/jenkins
  sudo -iu jenkins sudo -n true
  ```

- [ ] Ensure the runtime user has Docker access before the first build.
      Replace `jenkins` below with the actual Jenkins runtime user if needed. Run on the VM:

  ```bash
  sudo usermod -aG docker,sudo jenkins
  sudo -iu jenkins id
  ```

- [ ] If you preinstalled Docker now, verify the runtime user can run Docker commands.
      Replace `jenkins` below with the actual Jenkins runtime user if needed. Run on the VM:

  ```bash
  sudo -iu jenkins docker version
  sudo -iu jenkins docker buildx version
  sudo -iu jenkins docker compose version
  ```

- [ ] Optional: if you preinstalled Docker now, pre-create the named builder `acestream-builder`.
      The repository bootstrap can create/select the builder during the build, but precreating it can shorten the first run. Replace `jenkins` below with the actual Jenkins runtime user if needed. Run on the VM:

  ```bash
  sudo -iu jenkins docker buildx inspect acestream-builder >/dev/null 2>&1 || sudo -iu jenkins docker buildx create --name acestream-builder --driver docker-container --use
  sudo -iu jenkins docker buildx use acestream-builder
  sudo -iu jenkins docker buildx inspect --bootstrap acestream-builder | grep -E 'Name:|Driver:|Platforms:'
  ```

  Expected baseline platform support for this repository includes `linux/amd64`, `linux/arm/v7`, and `linux/arm64`.

### 4. Prepare SSH Access For The Agent (SSH-Launched Node Option Only)

- [ ] Generate or choose the SSH keypair Jenkins will use.
      Run on the Jenkins host or whichever machine will hold the SSH private key used by Jenkins:

  ```bash
  ssh-keygen -t ed25519 -f ~/.ssh/acestream-build-agent -C "jenkins build agent"
  ```

- [ ] Put the public key into `/home/jenkins/.ssh/authorized_keys` on the VM.
      Run on the Jenkins host:

  ```bash
  cat ~/.ssh/acestream-build-agent.pub | ssh <admin-user>@<vm-ip> 'sudo install -d -m 700 -o jenkins -g jenkins /home/jenkins/.ssh && sudo touch /home/jenkins/.ssh/authorized_keys && sudo chmod 600 /home/jenkins/.ssh/authorized_keys && sudo tee -a /home/jenkins/.ssh/authorized_keys >/dev/null && sudo chown -R jenkins:jenkins /home/jenkins/.ssh'
  ```

- [ ] Verify you can SSH to the VM as `jenkins` using that key.
      Run on the Jenkins host:

  ```bash
  ssh -i ~/.ssh/acestream-build-agent jenkins@<vm-ip> 'whoami && id && sudo -n true'
  ```

- [ ] Optional: if you preinstalled Docker now, verify SSH login already has Docker access.
      Run on the Jenkins host:

  ```bash
  ssh -i ~/.ssh/acestream-build-agent jenkins@<vm-ip> 'docker version && docker buildx version && docker buildx inspect acestream-builder'
  ```

### 5. Add The Agent In Jenkins UI

- [ ] Open `Manage Jenkins` -> `Credentials`.
- [ ] If you are using `Launch agents via SSH`, add SSH private key credential with id `acestream-build-agent-ssh`.
- [ ] Open `Manage Jenkins` -> `Nodes` or `Manage Nodes and Clouds`.
- [ ] Create a permanent node for the VM or another executor that lands builds directly on the Docker-capable host.
- [ ] Set remote root directory to the home or workspace path for the actual Jenkins runtime user on that node.
- [ ] If you are using a dedicated `jenkins` user, `/home/jenkins` is the expected path.
- [ ] Set label to `dorat-nuc-ci`.
- [ ] Choose a launch method that matches your model.
  - `Launch agents via SSH` if the Jenkins controller can SSH into the VM.
  - `Launch agent by connecting it to the controller` or WebSocket if the VM should dial out to Jenkins.
- [ ] If you picked SSH launch, select credential `acestream-build-agent-ssh`.
- [ ] Save and wait for the node to come online.
- [ ] Run a simple test job on that label to confirm `checkout scm` works with `git` present and `scripts/ci/bootstrap_jenkins_runner.sh` can prepare the runner.

### 6. Create GitHub App Access

- [ ] In GitHub, create a GitHub App for this repo.
- [ ] Grant repository permissions:
  - [ ] Metadata: Read-only
  - [ ] Contents: Read-only
  - [ ] Pull requests: Read-only
  - [ ] Commit statuses: Read and write
  - [ ] Checks: Read and write
- [ ] Subscribe to events:
  - [ ] Pull request
  - [ ] Push
  - [ ] Check suite
  - [ ] Check run
  - [ ] Repository
- [ ] Install the app on this repository.
- [ ] Download or copy the app credentials needed by Jenkins.

### 7. Add Jenkins Credentials

- [ ] In Jenkins, add the GitHub App credential with id `github-app-acestream-scraper`.
      If your live controller already uses `github-builder-app`, keep that id in the Jenkins job configuration unless you are intentionally normalizing the controller.
- [ ] In Jenkins, add the Docker Hub username/password credential with id `dockerhub-publish` inside the trusted publication subfolder. Only the develop and release jobs should inherit it.
- [ ] If you are using SSH launch, confirm the SSH credential id is `acestream-build-agent-ssh`.
- [ ] Do not rename these ids unless you also plan to change the checked-in pipeline files.

### 8. Choose Webhooks Or Polling

- [ ] If you want event-driven scans, expose Jenkins over HTTPS using DNS, reverse proxy, or tunnel.
- [ ] If you want event-driven scans, configure the webhook secret in GitHub and Jenkins if required by your setup.
- [ ] If you want event-driven scans, point GitHub webhook delivery to the Jenkins webhook endpoint.
- [ ] If you want event-driven scans, trigger a test delivery and confirm GitHub receives HTTP 2xx.
- [ ] If Jenkins stays private, configure periodic multibranch scans or plan to trigger scans manually from the Jenkins UI.

### 9. Make Sure Jenkins Can Read This Repo

- [ ] Confirm the GitHub App has access to this repository.
- [ ] Confirm Jenkins can discover the repository using the GitHub App credential.
- [ ] Do not copy repository files into the Jenkins container.
- [ ] Use SCM-based jobs so Jenkins reads `Jenkinsfile` and `jenkins/release.Jenkinsfile` directly from git.
- [ ] Confirm the branch or `main` revision Jenkins will read already contains the Jenkins repo files listed above.

### 10. Create The PR Validation Job In Jenkins UI

- [ ] Create a new `Multibranch Pipeline` job.
- [ ] Connect it to this GitHub repository using `github-app-acestream-scraper`.
      If the live controller is already using `github-builder-app`, keep the working live credential id until you explicitly normalize it.
- [ ] Set script path to `Jenkinsfile`.
- [ ] Enable branch discovery with the strategy `Exclude branches that are also filed as PRs` (set on the live controller 2026-08-28). A branch with an open PR then builds once, as its PR job (for the pre-rename `ai-coding-documentation` that was `PR-113`; superseded 2026-08-28: the rename to `develop` closed #113, the release PR is now #162, `develop` -> `main`, so `develop` builds as `PR-162` while it is open), instead of once per branch and once per PR; this is also what makes the zero-age image sweep in `Checkout / Bootstrap` safe (see `## Runner Disk Hygiene

`dorat-nuc-ci` has a **32 GB root disk** (16 GB RAM) shared with other jobs, so
disk is the runner's scarcest resource: on 2026-08-28 it hit 100 % twice
(`PR-162 #2`/`#3` died with Jenkins' "wrapper script does not seem to be touching
the log file" once the workspace could not be written). Where the space went:
the docker-container builder `acestream-builder` keeps its BuildKit cache in its
own volume (6 GB after one three-platform build; it does not show under
`docker system df`'s "Build Cache" and a plain `docker builder prune` never
touches it), the default builder's cache (4.8 GB), and ~1.1 GB per Jenkins
workspace including the ones of dead branch/PR jobs.

What the pipelines do about it:

- `Checkout / Bootstrap` runs `bash scripts/ci/cleanup_runner_docker.sh --transient-age-hours 0` first: removes this repo's transient CI images (`acestream-scraper:smoke-*`, `acestream-scraper-smoke:*`, `acestream-installer-test:*`, `acestream-scraper-task3:*`), prunes dangling layers and unused images older than 24 h, and prunes **every** builder listed by `docker buildx ls` down to `--builder-keep` (default **3 GB**), printing each builder's `docker buildx du` total. `--dry-run` shows the plan.
- `scripts/ci/bootstrap_jenkins_runner.sh` creates `acestream-builder` with a `buildkitd.toml` that enables BuildKit garbage collection (`gckeepstorage`, 4 GB) and caps parallel build steps (`max-parallelism = 2`), so the cache is bounded *during* a multi-platform publish, not only between builds; when that config changes the bootstrap recreates the builder.
- Multi-platform pushes build one platform at a time (next section), which also bounds the cache growth per step.
- The PR smoke stage exports no image (cache-only warm-up); the pytest builds and removes its own run-scoped image; `post { always }` prunes dangling layers.
- `scripts/ci/run_jenkins_release.sh` runs the same cleanup after its engine smoke, before the multi-platform publish builds.

Manual reclaim (Jenkins script console, or a shell on the runner) when a build still fails with `No space left on device` or the heartbeat error: `docker buildx prune --builder acestream-builder -af`, `docker builder prune -af`, `docker buildx rm acestream-builder` (bootstrap recreates it), and delete workspaces of dead branch/PR jobs under `/home/jenkins/agent/workspace/` (Jenkins' own `WorkspaceCleanupThread` only does that after 30 days). The multibranch job's orphaned-item strategy keeps 20 dead branch projects; their workspaces linger until then. The durable fix is a bigger disk (or moving Docker's `data-root` to a larger volume).

## Docs Site And Wiki Publishing

Adopted 2026-08-29. The user-facing documentation is published from the repository without GitHub Actions workflows of our own.

What is published, and how:

- The Docker command builder is a static page (plain HTML/CSS/JS, no build step) at `docs/index.html` with its script, stylesheet and data under `docs/builder/`. It generates the `docker run` command or `docker-compose.yml` for a chosen flavor, platform and feature set. GitHub Pages serves it at `https://pipepito.github.io/acestream-scraper/` from the `gh-pages` branch ("Deploy from a branch": `gh-pages`, `/` root), which Jenkins pushes on every validated `develop` build via `scripts/ci/publish_pages.sh` — a validated build *is* the deployment (adopted 2026-08-29; supersedes the earlier `main`+`/docs` plan from the same day, which would have waited on a release and exposed all of `docs/` as raw files). The published payload is only `index.html`, `builder/` and `.nojekyll` — the rest of `docs/` (this guide included) stays off the Pages site. The facts the page offers (flavors, platforms, ports, volumes, conditional runtime settings and notes) live in `docs/builder/runtime-options.json`; the option wiring lives in `docs/builder/app.js`. Controls that cannot affect the selected flavor, platform or enabled service are omitted rather than shown disabled.
- `wiki/` holds the GitHub wiki pages as normal Markdown. Jenkins mirrors them to the wiki repository `https://github.com/Pipepito/acestream-scraper.wiki.git`; the folder is the source of truth, so pages that exist in the wiki but not in `wiki/` are deleted on sync. The pre-2026 wiki (numbered pages such as `2.1-Docker`) is replaced by the folder's page names on the first sync.

Pipeline behaviour (`Jenkinsfile`):

- `Docs checks` stage, every build: `bash scripts/ci/validate_command_builder.sh` checks that the JSON parses, the flavor ids equal the Dockerfile targets, the ports and env toggles the page emits still exist in `entrypoint.sh`/`Dockerfile`/`docker-compose.yml`, `docs/.nojekyll` exists and `node --check` passes on the script; `bash scripts/ci/publish_wiki.sh --dry-run` renders `wiki/**` into the flat page set the wiki needs (no folders), rewriting relative `.md` links to wiki page names (`[FAQ](FAQ.md)` -> `[FAQ](FAQ)`, `Docker.md#anchor` -> `Docker#anchor`) and failing on duplicate page names; `bash scripts/ci/publish_pages.sh --dry-run` assembles and lists the Pages payload.
- `Publish wiki` stage, after every validation stage has passed in the trusted develop job: `bash scripts/ci/publish_wiki.sh` clones the wiki repository, replaces its content with the rendered pages and pushes only when something changed. Docs go live from validated `develop`; PR jobs and `main` never publish them.
- `Publish docs site` stage, same gating: `bash scripts/ci/publish_pages.sh` assembles the builder payload (`docs/index.html`, `docs/builder/`, `.nojekyll`), clones `gh-pages` (creating the branch on the first publish), replaces its content and pushes only when something changed.
- Credential (both publish stages): `github-publish` (see `## Jenkins Credential IDs`), bound as `GITHUB_PUBLISH_USERNAME`/`GITHUB_PUBLISH_TOKEN` and passed to git through `GIT_ASKPASS`, so the token never lands in a URL, a log line or a `.git/config`.
- Outcomes: missing credentials and publication errors fail the trusted develop build; an uninitialized wiki repository (`publish_wiki.sh` exit status 3) remains `UNSTABLE` with an operator instruction.

One-time operator setup:

1. GitHub Pages: repository Settings -> Pages -> Build and deployment -> Source `Deploy from a branch`, Branch `gh-pages`, folder `/ (root)` (or `gh api -X POST repos/Pipepito/acestream-scraper/pages -f build_type=legacy -f 'source[branch]=gh-pages' -f 'source[path]=/'`). The branch only appears after the first `Publish docs site` run, so do this after the first publishing build — or create an empty `gh-pages` branch first. GitHub Pages is free for public repositories. Note that "deploy from a branch" is executed by GitHub's own managed `pages build and deployment` run, which shows up in the repository's Actions tab; nothing about it is authored or maintained here, but disabling Actions for the repository entirely would stop it.
2. Wiki: repository Settings -> General -> Features -> Wikis enabled, and at least one page saved once in the Wiki tab (GitHub creates `<repo>.wiki.git` on the first save; verified present on 2026-08-29).
3. Jenkins credential `github-publish` in the same store as `dockerhub-publish` (verified 2026-08-29: the system store, `Manage Jenkins -> Credentials -> System -> Global`), kind *Username with password*.
4. Nothing else. Both documentation publish stages run only in the trusted develop job; the PR multibranch job never publishes.

Local preview and checks:

- `bash scripts/ci/validate_command_builder.sh`, `bash scripts/ci/publish_wiki.sh --dry-run` (lists the rendered pages and sample rewritten links) and `bash scripts/ci/publish_pages.sh --dry-run` (lists the Pages payload). All run without credentials.
- Open the page locally with any static server, e.g. `python3 -m http.server 8765 --directory docs` then `http://127.0.0.1:8765/` (the page fetches `builder/runtime-options.json`, so `file://` will not work).

## Multi-platform Publishes Are Platform-major And Push By Digest

A publish (the `develop` channel and the release phase 1) no longer runs one three-platform BuildKit build per flavor. That ran two QEMU emulations plus the native build concurrently and starved the runner until Jenkins' durable-task wrapper stopped heartbeating (`PR-162 #2`), and even sequential per-flavor builds accumulated more cache than the 32 GB disk holds (`PR-162 #3`/`#4`). `scripts/ci/run_jenkins_release.sh` (`publish_platform_major`) now:

1. iterates **platforms first, flavors second** — all four flavors are built for `linux/amd64`, then for `linux/arm/v7`, then for `linux/arm64` — so flavors reuse each other's cached base stages and the peak cache is one platform's worth of layers;
2. builds each (flavor, platform) with `scripts/ci/build_multiarch_images.sh --push-by-digest --repo <repo> --digest-file …` (image pushed by digest, no temporary tags);
3. prunes the builder's BuildKit cache down to `PUBLISH_CACHE_CAP` (default `2GB`) after each platform;
4. assembles every flavor's tags with `docker buildx imagetools create` from its per-platform digests and verifies each remote manifest with `verify_multiarch_manifest.sh --image`.

`--dry-run` prints the 12 per-platform builds, the prunes and the four `imagetools create` calls. The plain `build_multiarch_images.sh --push` with several platforms does the same sequencing for a single flavor (and `--prune-builder-after <cap>` prunes after each platform); single-platform `--load`/`--push` and cache-only builds are unchanged. Push-by-digest needs a docker-container (or remote) builder — Jenkins' `acestream-builder` — not the plain docker driver.

The Dockerfile also cuts what a foreign platform has to build: the frontend bundle and the Acexy Go binary are built on the build host (`FROM --platform=$BUILDPLATFORM`; Go cross-compiles with `GOARCH`/`GOARM`) and copied into every target platform, so QEMU only runs the Python stages.

For a local end-to-end check against a throwaway registry, the script accepts `RELEASE_IMAGE_REPO`, `RELEASE_LOGIN_SERVER` and `JENKINS_BUILDER` overrides (see `backend/tests/test_runtime_integration_guards.py` for the dry-run contract).

## AceStream Engine Smoke Coverage

The trusted develop pipeline and non-dry-run release pipeline run all of the checks below. Fork PR validation deliberately excludes these privileged Docker smokes. No Docker tag is published unless the corresponding trusted smoke path passes.

| Check | Platform | What it proves |
|---|---|---|
| `bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --network host` (cache-only, retried once after a builder-cache prune) | `linux/amd64` | The manifest-driven install works from the vendored tarball and the layers are cached for the pytest below. The flavor resolves to `linux/amd64,linux/arm/v7,linux/arm64`; the runner's native platform is pinned. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v` | `linux/amd64` on the amd64 runner; `linux/arm64` is added automatically only when the host is arm64 | The engine boots, `get_version` matches the manifest's `engine_version`, and `get_status` answers. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v` | `linux/amd64` (PR job and release publish run) | The acexy flavors ship the real proxy, not the build fixture. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k "arm_oci_image_install_layout"` | `linux/arm64`, `linux/arm/v7` (installer-stage builds) | Both platform variants from the digest-pinned jopsis OCI image install with their expected bionic layouts. No ARMv7 engine execution. |

Coverage gaps and how to close them:

- `linux/arm64` runtime: the Android engine cannot run under qemu-user, so the runtime smoke only covers arm64 when pytest runs on an arm64 host. `dorat-nuc-ci` is amd64. Until an arm64 Jenkins node exists, run `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v` on an arm64 machine (Raspberry Pi 4/5 64-bit with a 4 KB-page kernel, or any aarch64 Docker host) before publishing a new ARM engine pin; the test parametrizes `linux/arm64` there automatically.
- `linux/arm/v7` runtime: needs real ARMv7 hardware; the platform is `support: experimental` in `docker/manifests/acestream.json` for that reason.
- The published `scraper-acestream`, `scraper-acestream-acexy`, `latest`, and version tags include `linux/arm64` and `linux/arm/v7`; `verify_multiarch_manifest.sh --image <tag> --flavor <flavor>` checks each remote manifest after the push.
- Operator guide with the manual procedure: `docs/ops/acestream-arm-engine.md`.

## Cache, Disk Growth, and Cleanup

Multi-arch Docker builds will grow disk usage quickly.

Monitor:

- `docker system df`
- `docker buildx du --builder acestream-builder`
- Jenkins workspace usage under the agent root

Cleanup guidance:

- Use Jenkins build retention; all three pipelines discard old build records after 20 runs.
- Periodically prune stopped containers and unused images during a maintenance window:

```bash
docker system prune -af
docker buildx prune --builder acestream-builder -af
```

- Remove abandoned workspaces if jobs are renamed or deleted.
- If disk pressure is recurring, increase VM disk before aggressively pruning every run; warm cache improves CI stability and duration.

### After A Runner Reboot Or Disk Resize

- `binfmt_misc` registrations do not survive a reboot, and Docker restarts the `acestream-builder` buildkitd container (restart policy) before Jenkins runs anything. A docker-container builder only detects emulated platforms when buildkitd starts, so the first build after a reboot used to fail in Bootstrap with `Buildx builder 'acestream-builder' is missing linux/arm64 or linux/arm/v7 support after bootstrap` (seen 2026-08-29 after the VM disk resize). `bootstrap_jenkins_runner.sh` now re-registers the handlers, runs `docker buildx stop acestream-builder` and lets `buildx inspect --bootstrap` start it again, retrying up to `BUILDER_BOOTSTRAP_ATTEMPTS` (4) times `BUILDER_RETRY_DELAY_SECONDS` (5) apart. Nothing to do by hand; just re-run the build.
- Growing the VM disk in the hypervisor does not grow the filesystem. Check with `lsblk` / `df -h /`: if `sda` is larger than `sda2`, run `sudo growpart /dev/sda 2 && sudo resize2fs /dev/sda2` (ext4; `xfs_growfs /` for XFS) — no reboot needed. Until then the runner still only has the old capacity.

## Jenkins Build Node Setup

User action required.

Recommended model:

- Run the Jenkins controller separately from the Docker build VM.
- Run builds on any Jenkins executor that lands directly on the Docker-capable host.
- Apply the label `dorat-nuc-ci` because the current PR, develop, and release pipelines require it.

Current repo executor contract:

- The checked-in Jenkinsfiles use `agent { label 'dorat-nuc-ci' }`.
- They run `checkout scm`, then call `scripts/ci/bootstrap_jenkins_runner.sh` from the repository checkout before the validation or release wrappers.
- `git` must already exist on that node so `checkout scm` can work.
- Python, Node, Docker, Buildx, Docker Compose, and the `acestream-builder` builder may be preinstalled by the operator or prepared by the bootstrap script during the build, but the named builder still must exist and be selectable before the validation or release wrapper continues.
- Passwordless `sudo` is only needed if that bootstrap step must install missing software.
- Docker access must already work for the current runtime user. If it does not, the build fails with an explicit remediation message.
- The node may temporarily run builds as the operator user until a dedicated `jenkins` user is fully ready.

Supported node-launch models for this repository:

- SSH-launched permanent node
- Inbound or WebSocket permanent agent installed on the VM
- Another Jenkins node model that still executes the pipeline directly on the Docker-capable host

Suggested steps:

1. Create a dedicated `jenkins` user on the build VM.
2. If using SSH launch, install the agent user's SSH public key in `~jenkins/.ssh/authorized_keys`.
3. Ensure the runtime user can run Docker via the `docker` group.
4. If using SSH launch, create an SSH credential with id `acestream-build-agent-ssh`.
5. Add a permanent node or agent for the VM and assign the label `dorat-nuc-ci`.
6. Confirm a test pipeline on that label can run `git --version`, `docker version`, and the repository bootstrap path successfully.

### Option A: SSH-Launched Node

Run these on the Ubuntu VM:

```bash
sudo useradd --create-home --shell /bin/bash jenkins || true
sudo mkdir -p /home/jenkins/.ssh
sudo chmod 700 /home/jenkins/.ssh
sudo touch /home/jenkins/.ssh/authorized_keys
sudo chmod 600 /home/jenkins/.ssh/authorized_keys
sudo chown -R jenkins:jenkins /home/jenkins/.ssh
sudo usermod -aG docker,sudo jenkins
echo 'jenkins ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/jenkins >/dev/null
sudo chmod 440 /etc/sudoers.d/jenkins
sudo visudo -cf /etc/sudoers.d/jenkins
```

Then add the public key that Jenkins will use for SSH authentication into:

- `/home/jenkins/.ssh/authorized_keys`

If you want to verify SSH access manually before touching Jenkins:

```bash
ssh -i /path/to/private_key jenkins@<vm-ip> 'whoami && git --version && sudo -n true'
```

Expected result:

- user is `jenkins`
- `git` is available for the initial Jenkins checkout
- `sudo -n true` succeeds

### Jenkins UI Node Steps

Do this in the Jenkins UI only.

1. Go to `Manage Jenkins` -> `Credentials`.
1. If using SSH launch, add a new SSH private key credential.
1. If using SSH launch, set the credential id to `acestream-build-agent-ssh`.
1. Go to `Manage Jenkins` -> `Nodes` or `Manage Nodes and Clouds`.
1. Create a new permanent agent.
1. Set the node name to any operator-chosen value that helps you identify the machine.
1. Set the remote root directory to the home or workspace path for the actual Jenkins runtime user on that node.
1. If you are using a dedicated `jenkins` user, use `/home/jenkins`.
1. Set the labels to `dorat-nuc-ci`.
1. Choose the launch method that matches your deployment.
1. If using SSH launch, set the host to `<vm-ip-or-hostname>`.
1. If using SSH launch, select credential `acestream-build-agent-ssh`.
1. Save and let Jenkins connect.

Recommended node settings:

- Usage: `Only build jobs with label expressions matching this node`
- Executors: start with `1`
- Availability: `Keep this agent online as much as possible`

If you prefer an inbound or WebSocket agent, create the node in Jenkins with the matching launch method and then install or run the Jenkins agent process on the VM. The VM still needs `git` plus working Docker access for the runtime user before the first real build will pass; the repository bootstrap can prepare the rest.

### Agent Verification Checklist

After Jenkins connects to the VM, use the agent's `Script Console`/test job path indirectly by running a simple pipeline step on that label with:

```bash
whoami
pwd
git --version
bash scripts/ci/bootstrap_jenkins_runner.sh
python3 --version
node --version
docker version
docker buildx version
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"
docker buildx inspect acestream-builder
```

Expected result:

- workspace is on the VM, not inside the Jenkins controller container
- `checkout scm` succeeded because `git` was already present
- `scripts/ci/bootstrap_jenkins_runner.sh` completed and prepared Python, Node, Docker, and Buildx as needed
- `acestream-builder` exists or can be selected

If Jenkins connects but Docker commands fail, the usual causes are:

- current runtime user not in the `docker` group
- group membership not refreshed after login
- Docker service not running
- buildx builder not created for that user context

## GitHub App Setup

User action required.

Use a GitHub App instead of a personal access token for multibranch discovery and status reporting. This works fine with a private Jenkins controller because Jenkins talks out to GitHub; GitHub does not need to call back into Jenkins unless you choose webhook-based scans.

Recommended repository permissions:

- Contents: Read-only
- Metadata: Read-only
- Pull requests: Read-only
- Commit statuses: Read and write
- Checks: Read and write
- Webhooks: Read and write if your GitHub tier/plugin combination requires app-managed hooks

Subscribe the app to these events:

- Pull request
- Push
- Check suite
- Check run
- Repository

Store the app in Jenkins as credential id `github-app-acestream-scraper` and use that credential for the GitHub Branch Source organization or multibranch job.

## Webhook Reachability Requirements

User action required.

This section only applies if you want GitHub webhooks to trigger scans or builds automatically. If your Jenkins controller stays private, skip public webhook exposure and use periodic scans or manual rescans instead.

Requirements:

- Public HTTPS URL terminating on a valid certificate
- Stable DNS name or a maintained reverse proxy/tunnel endpoint
- Webhook secret configured on both GitHub and Jenkins
- Reachable webhook endpoint validation from outside your LAN

Validation checklist:

1. Open the Jenkins URL from a public network and confirm the certificate chain is valid.
2. Confirm the GitHub webhook delivery page shows HTTP 2xx responses.
3. Confirm webhook payloads reach the multibranch job scan endpoint or GitHub Branch Source listener.
4. Re-run validation after any DNS, reverse proxy, firewall, or tunnel changes.

Treat local-only HTTP, self-signed certificates, or unstable tunnels as non-production.

Private-controller alternative:

1. Keep Jenkins private.
2. Configure your multibranch job to run periodic scans, or use manual `Scan Multibranch Pipeline Now` when needed.
3. Let Jenkins use outbound GitHub API access for repository discovery and PR status reporting.
4. Accept that builds will not start instantly from GitHub events unless you add a reachable webhook path later.

## Jenkins Credential IDs

Create these Jenkins credentials with these exact ids so the checked-in pipeline files work without modification. Scope them at the lowest usable folder:

- `github-app-acestream-scraper` (the live controller currently uses `github-builder-app`): GitHub App credential used for repository discovery and commit/check reporting. Keep it at the `Acestream-Scraper` folder rather than system-global.
- `acestream-build-agent-ssh`: SSH private key credential for the dedicated build VM agent if you use the SSH-launch model
- `dockerhub-publish`: username/password credential used only by `jenkins/develop.Jenkinsfile` and `jenkins/release.Jenkinsfile`. Store it inside the trusted publication subfolder.
- `github-publish`: username/password credential used only by the trusted develop job for the wiki and `gh-pages`. Store it beside `dockerhub-publish`.

Changing these ids would require repository changes, so treat them as part of the CI/CD contract.

## Multibranch Validation Job

User action required.

Create a multibranch pipeline job that points at this repository and uses `jenkins/pr.Jenkinsfile`.

Do not copy the Jenkinsfile into the controller container; load it from SCM.

Recommended configuration:

1. New Item -> Multibranch Pipeline.
2. Add the repository using the GitHub App credential `github-app-acestream-scraper`.
3. Set the script path to `jenkins/pr.Jenkinsfile`.
4. Disable ordinary branch discovery; this job is for PR revisions only.
5. Discover origin PR merge revisions.
6. Discover fork PR merge revisions and set trust to **Nobody**. Jenkins then loads the Jenkinsfile from the target branch while checking out the proposed merge revision.
7. Keep the notification context exactly `PR Validation`.
8. Enable one trigger model: webhook-based indexing, periodic scans, or manual rescans.

Expected behavior:

- Jenkins launches on `dorat-nuc-ci`, but contributor code runs only in the restricted PR container.
- The job never calls `withCredentials`, never mounts `/var/run/docker.sock`, and never gives the container network access.
- The container executes `scripts/ci/run_pr_validation.sh` as read from the target branch's first parent, using dependencies baked by the trusted develop job. A fork cannot replace the top-level validation orchestrator.
- A missing runner image fails fork builds closed; only a trusted origin PR may build a one-use candidate image.
- `Branch Policy` (since 2026-08-28): a PR into `main` fails unless its head is `develop`.
- Docker/runtime smokes and every real publish are intentionally absent from this job.

## Trusted Develop Job

Create a Pipeline-from-SCM job inside the trusted publication subfolder. Point it at `*/develop` and set the script path to `jenkins/develop.Jenkinsfile`.

- It polls SCM every five minutes, verifies the checkout is the current `origin/develop`, and refreshes the trusted PR-runner image.
- It runs full application checks offline in the pinned runner, followed by trusted-host Compose validation, dry-run architecture/publication policy, and the amd64/Acexy/ARM installer smokes.
- It checks `origin/develop` again immediately before publication.
- Only then does it bind `dockerhub-publish` and `github-publish`, push the floating `:develop*` tags, and update the wiki and Pages.
- Missing credentials and publication failures fail the build. The wiki's one-time uninitialized state remains `UNSTABLE` with an operator message.

## Manual Release Job

User action required.

Create a separate pipeline job for manual releases using `jenkins/release.Jenkinsfile`.

This is also UI-only setup. The job should load `jenkins/release.Jenkinsfile` from SCM, not from the Jenkins container filesystem.

Recommended configuration:

1. New Item -> Pipeline.
2. Point SCM at this repository and the `main` branch.
3. Set the script path to `jenkins/release.Jenkinsfile`.
4. Run it only manually.
5. Supply the `dockerhub-publish` credential to the controller so the pipeline can bind it at runtime.

Release behavior:

- The job runs only from `main`: `jenkins/release.Jenkinsfile` errors on any other `BRANCH_NAME` and requires the checked-out `HEAD` to equal `origin/main`.
- `CONFIRM_RELEASE=true` is required or the pipeline aborts.
- Since 2026-08-28 `scripts/ci/run_jenkins_release.sh` also refuses any release run while `version.txt` contains `-dev` (`Refusing to release a development version`); only the `--channel develop` publish from the trusted develop pipeline accepts such a version.
- `DRY_RUN=true` (default) performs preflight only: `bash scripts/ci/run_jenkins_release.sh --dry-run` runs the full cutover suite and the four-flavor multi-arch dry-run builds, then exits without binding `dockerhub-publish`.
- `DRY_RUN=false` binds `dockerhub-publish`, prints the publish plan (`bash scripts/ci/run_jenkins_release.sh --print-publish-plan`), runs the smoke block below, performs Docker Hub login and publishes tags.
- `PUBLISH_LATEST` (default `false`, since 2026-08-26, 5ffed1d) controls the floating `:latest` tag. The Jenkinsfile exports it as `PUBLISH_LATEST=1`/`0`. With `0` (phase 1) the build pushes `:${VERSION}`, `:<flavor>` and `:${VERSION}-<flavor>` tags and never touches `:latest`. With `1` (phase 2) the script skips every build and test and runs `scripts/ci/promote_latest.sh`, which retags the canary-validated `pipepito/acestream-scraper:${VERSION}` manifest (the `scraper-acestream-acexy` payload) to `:latest` and verifies its platforms; `DRY_RUN=true` with `PUBLISH_LATEST=true` only prints that promotion plan. Only the full payload flavor can ever become `:latest`.
- The job archives release result JSON files and `phase5-build-result-release-metadata.json`.
- Before publishing, the script builds `scraper-acestream` for amd64, runs the engine and Acexy runtime smokes, then runs both ARM installer layout tests. If any fails, no Docker Hub login or push happens. Both ARM variants use the same digest-pinned multi-platform jopsis source image and require Docker Hub access on a cold builder; the amd64 archive remains vendored. The same checks run in the trusted develop job; on the release job they run only on the publish run, not the dry run.
- The pushed `scraper-acestream`, `scraper-acestream-acexy`, version tags (and, after the phase-2 retag, `latest`) are multi-platform manifests that include `linux/arm64` and `linux/arm/v7`; `verify_multiarch_manifest.sh --image <tag> --flavor <flavor>` checks each remote manifest after the push. The arm64 engine runtime is not exercised by this job (amd64 runner); see `## AceStream Engine Smoke Coverage`.
- Keep this path manual-only. Jenkins is the sole publisher; the GitHub Actions release workflow has been retired.

## v2.0.0 Release Runbook

Sequence for shipping the v2 codebase from `develop` to Docker Hub through the release PR #162 (`develop` -> `main`; PR #113 from the pre-rename branch `ai-coding-documentation` was auto-closed by the rename on 2026-08-28). Under the branching model in `## Branching Model And Pre-release Channel` this is the template for every later release as well. Status 2026-08-28: no `v2.0.0` git tag or GitHub release exists yet; steps 1-2 are in progress.

One-off prerequisites (operator, outside the repo): the Jenkins credential `dockerhub-publish` exists inside the trusted publication subfolder, and the `acestream-scraper-release` job's branch specifier points at `*/main` (the job refuses any other branch and requires `HEAD == origin/main`).

1. Confirm `version.txt` reads the intended release tag (currently `v2.0.0`; from the next cycle on, a PR into `develop` bumps it right before the release PR from `vX.Y.Z-dev`, otherwise `scripts/ci/run_jenkins_release.sh` refuses the release in step 5).
2. Use the `develop` -> `main` release PR (#162; the `Branch Policy` stage rejects any PR into `main` whose head is not `develop`). Wait for `acestream-scraper-pr` (GitHub status `PR Validation`) to go green and confirm the latest `acestream-scraper-develop` build for the same `develop` SHA passed its full suite, Docker/runtime smokes, and channel publication.
3. Merge the PR to `main`. No automatic Docker Hub publish happens — Jenkins requires a manual trigger.
4. In Jenkins, build `acestream-scraper-release` with parameters `CONFIRM_RELEASE=true`, `DRY_RUN=true`, `PUBLISH_LATEST=false`. This runs the full cutover suite and the multi-arch dry-run preflight without binding Docker Hub credentials. The release job's engine smoke does not run on a dry run (`scripts/ci/run_jenkins_release.sh --dry-run` exits after the preflight); it runs on the publish run in step 5 and already ran in the trusted develop job. Verify it goes green.
5. Publish phase 1: re-run `acestream-scraper-release` with `CONFIRM_RELEASE=true`, `DRY_RUN=false`, `PUBLISH_LATEST=false`. The pipeline reruns the full cutover suite, the dry-run preflight, the AceStream engine smoke + Acexy smoke + ARM installer layout (see `## AceStream Engine Smoke Coverage`), reclaims runner disk, then logs into Docker Hub and pushes `:v2.0.0`, the four flavor tags (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`) and their `v2.0.0-<flavor>` variants as multi-platform manifests (`linux/amd64`, `linux/arm64`, `linux/arm/v7`). `:latest` is not touched.
6. Verify the published tags on Docker Hub: `pipepito/acestream-scraper:v2.0.0`, the four flavor tags and their version-prefixed variants. Each should list all three platforms (`docker buildx imagetools inspect <tag>`). `:latest` still points at the previous release at this point.
7. Canary: smoke-test `:v2.0.0` on a fresh amd64 host: `docker pull pipepito/acestream-scraper:v2.0.0 && docker run --rm -p 0.0.0.0:8000:8000 -p 6878:6878 -e ENABLE_ACESTREAM_ENGINE=true pipepito/acestream-scraper:v2.0.0` and confirm the FastAPI app and engine respond. Repeat on an arm64 host (Raspberry Pi 4/5 64-bit, 4 KB-page kernel) to confirm the Android engine answers `curl "http://localhost:6878/webui/api/service?method=get_version"` with `"platform":"android"`; CI does not cover that path. See `docs/ops/acestream-arm-engine.md`. If the canary fails, fix forward on `main` and restart from step 2; `:latest` never moved.
8. Tag the release and publish the GitHub release (maintainer, from a workstation). Tag the exact `main` commit the release job built (the job requires `HEAD == origin/main`, so it is `origin/main` at the time of step 5) and use `docs/release/v2-release-notes.md` as the release body:

   ```bash
   git fetch origin main
   git tag -a v2.0.0 -m "v2.0.0" origin/main
   git push origin v2.0.0
   gh release create v2.0.0 --verify-tag --title "v2.0.0" --notes-file docs/release/v2-release-notes.md
   ```

9. Publish phase 2 (promote `:latest`): re-run `acestream-scraper-release` with `CONFIRM_RELEASE=true`, `DRY_RUN=false`, `PUBLISH_LATEST=true`. Nothing is rebuilt: `scripts/ci/promote_latest.sh` retags `pipepito/acestream-scraper:${VERSION}` to `:latest` (same digest as the canary) and verifies the platforms. Confirm `docker buildx imagetools inspect pipepito/acestream-scraper:latest` lists all three platforms and that `docker pull pipepito/acestream-scraper:latest` on the amd64 canary host now runs the v2 app.
10. Start the next cycle on `develop`: through a PR into `develop`, set `version.txt` to the next version with the `-dev` suffix (for example `v2.1.0-dev`). Until a PR into `develop` bumps it back to a final version ahead of the next release PR, `:develop` keeps publishing and the release script refuses to publish a release.

## Branch Protection Cutover

User action required.

Do not guess the required check name. Observe the exact Jenkins-reported check on a real pull request first, then update GitHub branch protection.

Status 2026-09-04: `PR Validation` remains the required Jenkins context on `main` and `develop`. The multibranch job discovers PR merge revisions only, including forks with trust set to Nobody; ordinary branch and publication work lives in the separate trusted develop job.

Cutover sequence (historical record):

1. Run the multibranch PR validation on a test pull request. (Done.)
2. Open the PR checks tab and record the exact Jenkins check name shown by GitHub. (Done: `PR Validation`.)
3. Add that observed Jenkins check name to branch protection as a required status check. (Done 2026-08-28.)
4. (Superseded 2026-08-26, e5657b9) Keep the current GitHub Actions PR check requirement in place until Jenkins has passed repeatedly. No GitHub Actions checks exist any more.
5. (Superseded 2026-08-26, e5657b9) Once stable, remove GitHub Actions from required checks and keep them as fallback/reference workflows. The workflows were deleted instead; nothing remains to keep.

This avoids blocking merges on a mismatched check name.

## Fork Pull Request Policy

Fork PRs are discovered, but remain untrusted by construction:

- GitHub Branch Source trust is **Nobody**, so `jenkins/pr.Jenkinsfile` is always loaded from the PR's target branch for a fork. A fork cannot replace or weaken the container boundary in its PR.
- The proposed merge revision is mounted read-only, copied into a size-limited tmpfs workspace, and executed on a read-only container filesystem with `--network none`, `--cap-drop ALL`, `no-new-privileges`, an unprivileged uid, and finite CPU, memory, and PID limits.
- The container never receives a Jenkins credential, the Docker socket, host paths other than its workspace, or Jenkins environment variables.
- Dependency installation happens while the trusted develop job builds the runner image, not while fork code executes. A fork that changes dependency or runner-image inputs fails closed and must be moved to a maintainer-owned branch after review; an origin PR gets a one-use candidate runner that cannot replace the shared develop image.
- PR validation intentionally omits privileged image builds and engine runtime smokes. The trusted develop pipeline reruns the full suite and those smokes before any `:develop*` or documentation publication.
- Maintainer review remains mandatory. CI confinement protects infrastructure; it does not prove that a contribution is benign or correct.

## GitHub Actions During The Proving Window

Superseded 2026-08-26 (e5657b9). Jenkins is the canonical and only CI and release path; `.github/workflows/` no longer exists in the repository. (Historical: during the proving window, two GitHub Actions workflows remained as parity validators.)

- All GitHub Actions workflows are retired; every gate (tests, four-flavor dry-run multi-arch builds, AceStream engine runtime smoke, cutover required checks, phase gates) runs on the Jenkins pipelines above.

The phase-specific GA scaffolding workflows (`phase1-safety-gates.yml`, `cutover-validation.yml`, `multiarch-validation.yml`) were removed once their gate runners were absorbed into the canonical PR + release pipelines. The last two workflows (`pull_request.yml`, the parity PR validator, and `release.yml`, the manual-only release validator) were deleted in e5657b9 on 2026-08-26.

Expected operating model:

- Jenkins is the canonical path for PR validation and release publication.
- (Superseded 2026-08-26, e5657b9) GitHub Actions PR workflow stays on for parity. GA release workflow is manual-only validation; it never pushes to Docker Hub. Current state: both workflows are deleted.
- (Superseded 2026-08-26, e5657b9) Removing GA entirely is a future cleanup once Jenkins has proven stable across multiple releases. Outcome: done in e5657b9.

## Rollback Guidance

If Jenkins cutover causes merge or release risk:

(Superseded 2026-08-26, e5657b9) Step 1 and the closing sentence below assumed the GitHub Actions workflows still existed. They do not; the workstation path in step 4 is the fallback.

1. (Superseded) Re-enable GitHub Actions checks in branch protection immediately. Current state: no GitHub Actions checks exist. If Jenkins is down and a merge cannot wait, a repository admin must temporarily relax the `PR Validation` requirement on `main`, run `bash scripts/ci/run_cutover_required_checks.sh --profile full` locally as the substitute gate, and restore the requirement afterwards.
2. Remove the Jenkins check from required branch protection if it is unstable or unreachable.
3. Pause manual Jenkins releases.
4. If Jenkins is unavailable, run the validation and publish steps manually from a workstation: `bash scripts/ci/run_cutover_required_checks.sh --profile full`, then `bash scripts/ci/run_jenkins_release.sh` with `DOCKERHUB_USERNAME`/`DOCKERHUB_TOKEN` exported (preview first with `--print-publish-plan`; export `PUBLISH_LATEST=1` only for the `:latest` promotion run, matching the two-phase flow in `## Manual Release Job`). The pre-release channel can be refreshed the same way from a `develop` checkout with `bash scripts/ci/run_jenkins_release.sh --channel develop`.
5. Preserve Jenkins logs, webhook delivery logs, and agent diagnostics before making major controller changes.

(Superseded 2026-08-26, e5657b9) Rollback is complete only when GitHub Actions are again sufficient to validate and ship the repository without Jenkins. Current state: rollback is complete when the workstation path in step 4 has validated and shipped the release, or when Jenkins is restored and `PR Validation` is required on `main` again.

## Ownership Matrix

- Pipeline definitions:
  Repo-owned: `jenkins/pr.Jenkinsfile`, `jenkins/develop.Jenkinsfile`, `jenkins/release.Jenkinsfile`, `docker/ci/pr-runner.Dockerfile`, and the scripts under `scripts/ci/`
  User-owned: Job creation and Jenkins global or job settings

- Build environment contract:
  Repo-owned: required builder name, label, `scripts/ci/bootstrap_jenkins_runner.sh`, validation/release wrappers, result artifacts
  User-owned: VM provisioning, `git` prerequisite, Docker daemon availability, Docker access for the runtime user, optional preinstallation, optional sudoers setup, node launch model

- GitHub integration:
  Repo-owned: documented credential ids and pipeline expectations
  User-owned: GitHub App registration, installation, and optional webhook or polling setup

- Branch policy:
  Repo-owned: documentation of cutover order and fallback behavior, and the `Branch Policy` stage in `jenkins/pr.Jenkinsfile` (PRs into `main` must come from `develop`)
  User-owned: branch protection updates, required check selection, rollback decision

- Release publication:
  Repo-owned: Docker Hub bindings in the trusted develop and manual release pipelines; the PR pipeline has no credential binding or publication path
  User-owned: Docker Hub credential management and manual release approval
