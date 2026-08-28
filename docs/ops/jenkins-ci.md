# Jenkins CI/CD Operator Guide

## Overview

This document is the primary operator guide for Jenkins CI/CD in this repository.

Current rollout state:

- Jenkins is the canonical path for pull request validation and release publication in this repository.
- GitHub Actions remain available during the current proving window as fallback/reference workflows while operators build confidence in Jenkins hardening.
- Jenkins assets in this repository are ready to be wired into your homelab controller and agent.

Important constraint for this setup:

- Jenkins should be configured through the Jenkins UI.
- Do not copy `Jenkinsfile`, `jenkins/release.Jenkinsfile`, shell scripts, or helper files into the Jenkins Docker container.
- Jenkins should load pipeline definitions directly from this Git repository through SCM configuration in the UI.

Current workflow parity goal:

- Jenkins multibranch validation (`Jenkinsfile`) is the canonical PR validation path.
- Jenkins manual release (`jenkins/release.Jenkinsfile`) is the canonical release path. The GitHub Actions workflows are retired.
- The repository files that make this work are `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, and `scripts/ci/run_jenkins_release.sh`.
- Those files must be pushed to GitHub before Jenkins can load them through SCM.

Current limitation:

- The checked-in Jenkinsfiles still run directly on whatever executor matches the label `dorat-nuc-ci`; they do not currently define Docker-based ephemeral agents for you.
- After `checkout scm`, both pipelines call `scripts/ci/bootstrap_jenkins_runner.sh` from the repository checkout to prepare the runtime.
- The first build no longer assumes Python, Node, Docker, Buildx, or Docker Compose are already installed, but `git` must already be present so the initial `checkout scm` can succeed.
- Passwordless `sudo` is only required when the bootstrap script needs to install missing software.
- Builds may currently run as the operator runtime user before a dedicated `jenkins` user is fully ready, so Docker access must work for whichever user Jenkins actually uses on that node.

Current ownership stance:

- Jenkins multibranch pipelines are the canonical path for pull request validation.
- Jenkins manual release jobs are the canonical path for release publication.
- GitHub Actions should be retained as fallback/reference workflows until you decide the Jenkins setup is proven.

Responsibility split:

- Repo-owned: `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, `scripts/ci/run_jenkins_release.sh`, build/test scripts, and supporting documentation.
- User-owned: Jenkins controller installation, build-node launch model, dedicated build VM lifecycle, plugin installation, credentials, GitHub App registration, optional webhook exposure or polling setup, branch protection cutover, and rollback decisions.

Networking model:

- Jenkins does not need to be exposed to the public internet if you are willing to use periodic scans or manual rescans instead of GitHub webhooks.
- Jenkins only needs outbound access to GitHub to fetch SCM metadata and report commit statuses/checks.
- GitHub only needs inbound access to Jenkins if you want webhook-triggered scans or builds.

Executor model:

- The repository only requires a Jenkins executor labeled `dorat-nuc-ci`.
- That executor can be an SSH-launched node, an inbound or WebSocket agent installed on the VM, or another Jenkins node model that lands builds directly on the Docker-capable host.
- SSH is a documented example path, not a hard requirement of the checked-in pipelines.

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
- Create the Jenkins multibranch validation job from `Jenkinsfile`.
- Create the Jenkins manual release job from `jenkins/release.Jenkinsfile`.
- Observe the Jenkins check name reported back to GitHub and update branch protection to require it.
- Keep GitHub Actions fallback/reference workflows available until Jenkins hardening is verified; do not treat `main` publication through GitHub Actions as the primary operating path.

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
- [ ] Add Docker Hub credential `dockerhub-publish`.
- [ ] Create the build executor and apply label `dorat-nuc-ci`.
- [ ] Confirm the node comes online.
- [ ] Push the repo branch/commit that contains:
  - [ ] `Jenkinsfile`
  - [ ] `jenkins/release.Jenkinsfile`
  - [ ] `scripts/ci/bootstrap_jenkins_runner.sh`
  - [ ] `scripts/ci/run_jenkins_validation.sh`
  - [ ] `scripts/ci/run_jenkins_release.sh`
- [ ] Create the multibranch PR-validation job from `Jenkinsfile`.
- [ ] Create the manual release job from `jenkins/release.Jenkinsfile`.

### C. GitHub App And Validation Last

- [ ] Create and install the GitHub App on this repository.
- [ ] Choose your trigger model: public webhook delivery or private periodic scan/manual scan.
- [ ] Trigger an initial multibranch scan.
- [ ] Open or update a test PR.
- [ ] Confirm Jenkins reports the `PR Validation` status context back to GitHub.
- [ ] Run the manual release job with `CONFIRM_RELEASE=true` and `DRY_RUN=true`.
- [ ] Only after Jenkins is stable, add the Jenkins check to branch protection.
- [ ] Keep GitHub Actions available as fallback/reference workflows until you are happy with the Jenkins setup.

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
- [ ] In Jenkins, add the Docker Hub username/password credential with id `dockerhub-publish`.
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
- [ ] Enable branch discovery.
- [ ] Enable pull request discovery.
- [ ] Add the custom GitHub notification context trait with label `PR Validation`.
- [ ] Treat fork PRs as restricted until you explicitly validate that trust model.
- [ ] Enable either webhook-based indexing, periodic scans, or a manual rescan workflow.
- [ ] Run an initial scan and confirm Jenkins sees `main` and your working branches.

Expected parity:

- This job is the sole PR validation pipeline (the GitHub Actions equivalent has been retired).
- It should run the complete staged PR validation flow from the root `Jenkinsfile` and report the single GitHub status context `PR Validation`.

### 11. Create The Manual Release Job In Jenkins UI

- [ ] Create a new `Pipeline` job.
- [ ] Configure it as `Pipeline script from SCM`.
- [ ] Point SCM at this repository.
- [ ] Set branch to `main`.
- [ ] Set script path to `jenkins/release.Jenkinsfile`.
- [ ] Leave the job manual-only.
- [ ] Confirm the job exposes `CONFIRM_RELEASE` and `DRY_RUN` parameters.

Expected parity:

- This job is the sole release pipeline (the GitHub Actions equivalent has been retired).
- It should run the same release preflight and publish flow through `scripts/ci/run_jenkins_release.sh`.

### 12. Verify The Agent Contract

- [ ] Run a build on the multibranch job.
- [ ] Confirm Jenkins executes on label `dorat-nuc-ci`.
- [ ] Confirm the job runs on the VM workspace, not inside the controller container.
- [ ] Confirm `checkout scm` succeeds because `git` was already present before bootstrap.
- [ ] Confirm the build calls `scripts/ci/bootstrap_jenkins_runner.sh` from the repository checkout.
- [ ] Confirm Docker access works for the current runtime user and `docker buildx use "${JENKINS_BUILDER:-acestream-builder}"` succeeds.
- [ ] Confirm the validation wrapper runs successfully.

### 13. Verify GitHub PR Reporting

- [ ] Open or update a test PR.
- [ ] Confirm Jenkins runs automatically.
- [ ] Confirm GitHub shows the Jenkins-reported `PR Validation` status on the PR.

### 14. Verify The Manual Release Job Safely

- [ ] Run the release job with `CONFIRM_RELEASE=true` and `DRY_RUN=true`.
- [ ] Confirm it runs the full checks.
- [ ] Confirm it does not require Docker Hub login in dry-run mode.
- [ ] Confirm it completes without pushing tags.

### 15. Optional Real Release Verification

- [ ] Only when ready, run the release job with `CONFIRM_RELEASE=true` and `DRY_RUN=false`.
- [ ] Confirm Docker Hub login succeeds.
- [ ] Confirm tags are published as expected.
- [ ] Confirm remote manifest verification passes.

### 16. Cutover To Jenkins PR Gates

- Jenkins is already the canonical PR-validation path; this checklist is about hardening branch protection around that operating model.

- [ ] Open GitHub branch protection settings.
- [ ] Add `PR Validation` as a required status check.
- [ ] Keep GitHub Actions required checks until Jenkins has passed repeatedly.
- [ ] If older temporary Jenkins per-gate contexts are still required, leave them in place only during the proving window.
- [ ] Once `PR Validation` is proven stable, remove the temporary Jenkins per-gate contexts from required checks.
- [ ] Once confident, remove GitHub Actions from required checks.

### 17. Later Hardening Of GitHub Actions

- [ ] Keep GitHub Actions positioned as fallback/reference workflows during the proving window.
- [ ] Keep the workflows in the repo for rollback.
- [ ] Do not delete them until rollback risk is acceptably low.

## UI-Only Jenkins Setup

This repository is designed so Jenkins can stay stateless.

Use this model:

- Jenkins controller configuration happens in the Jenkins UI.
- Pipeline definitions stay in git.
- The Jenkins container does not need repo files copied into it.
- The build VM runs the checked-out repository workspace that Jenkins fetches through SCM.

That means:

- the multibranch job reads `Jenkinsfile` from the repository root
- the manual release job reads `jenkins/release.Jenkinsfile` from the repository
- the shell scripts under `scripts/ci/` run from the repository checkout on the agent workspace

If you find yourself editing files inside the Jenkins Docker container, stop and move that change back into the repository instead.

## Jenkins Plugins

Install these baseline plugins before creating jobs:

- GitHub Branch Source
- GitHub Checks
- github-scm-trait-notification-context
- Pipeline
- Credentials
- Credentials Binding
- Plain Credentials
- Timestamper
- Workspace Cleanup

Install these optional plugins only when they match your setup:

- Multibranch Scan Webhook Trigger if you want webhook-triggered multibranch scans
- SSH Build Agents if you choose the SSH-launch model for the build node
- Docker Pipeline if your Jenkins setup expects that plugin for Docker-aware pipeline features
- Matrix Authorization Strategy if your controller uses role-based access control

`Jenkinsfile` and `jenkins/release.Jenkinsfile` are declarative pipelines, so the Pipeline plugin family is mandatory. GitHub App and multibranch discovery rely on GitHub Branch Source. The single-context `PR Validation` status model also relies on `github-scm-trait-notification-context`. `Multibranch Scan Webhook Trigger`, `SSH Build Agents`, and `Docker Pipeline` are only needed when your trigger model or agent launch model uses them.

## Dedicated VM Requirements

Use a dedicated VM for Jenkins Docker builds instead of sharing a general-purpose host.

Minimum expectations:

- Ubuntu 24.04 LTS
- 4 vCPU minimum; 8 vCPU recommended for faster multi-arch preflight
- 16 GB RAM minimum; 32 GB recommended if concurrent builds are allowed later
- 150 GB SSD minimum, with headroom for Docker layers, buildx cache, and workspace archives
- Outbound access to GitHub, Docker Hub, Ubuntu package repositories, NodeSource, and any reverse-proxy or tunnel endpoint you use
- Either inbound SSH from the Jenkins controller to the build VM or an inbound or WebSocket agent connection from the VM to Jenkins

Operational requirements:

- The Docker daemon must be available to the current Jenkins runtime user.
- The VM should be treated as cattle, not pet infrastructure: document bootstrap and be ready to rebuild.
- Keep this host dedicated to CI so buildx cache growth and Docker cleanup do not compete with unrelated workloads.

## Ubuntu 24.04 Bootstrap

These commands are operator-run preinstall steps for a dedicated Jenkins build VM. The repository bootstrap now handles missing Python, Node, Docker, Buildx, and Docker Compose after checkout, so only `git` is a hard prerequisite before the first build.

```bash
sudo apt-get update
sudo apt-get install -y git
```

If you want to preinstall the rest of the toolchain instead of letting `scripts/ci/bootstrap_jenkins_runner.sh` install it on demand, continue with:

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
sudo useradd --create-home --shell /bin/bash jenkins || true
sudo usermod -aG docker,sudo jenkins
```

After group changes, restart the Jenkins agent session or reboot the VM before first use.

## Passwordless Sudo For The Jenkins Agent

This is only required when `scripts/ci/bootstrap_jenkins_runner.sh` needs to install missing software. If your node is already fully provisioned, the pipelines can run without passwordless `sudo`.

Run on the VM:

```bash
echo 'jenkins ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/jenkins >/dev/null
sudo chmod 440 /etc/sudoers.d/jenkins
sudo visudo -cf /etc/sudoers.d/jenkins
sudo -iu jenkins sudo -n true
```

Expected result:

- `visudo` reports the file parses correctly
- `sudo -iu jenkins sudo -n true` exits successfully without prompting for a password

If you prefer to narrow this later, start with full passwordless `sudo` so setup is simple, then replace it with a more restricted sudoers rule after the Jenkins environment is stable.

Validation commands for a fully preinstalled node:

```bash
git --version
python3 --version
python3 -m pip --version
node --version
docker version
docker buildx version
docker compose version
jq --version
curl --version
```

## Buildx Builder Setup

This repository expects a named buildx builder called `acestream-builder`. Both `Jenkinsfile` and `jenkins/release.Jenkinsfile` call `scripts/ci/bootstrap_jenkins_runner.sh` after checkout, then run `docker buildx use "${JENKINS_BUILDER:-acestream-builder}"` before the backing scripts continue. If that builder is missing or cannot be selected, the build fails.

Create or select it on the Jenkins build VM:

```bash
docker buildx inspect acestream-builder >/dev/null 2>&1 || docker buildx create --name acestream-builder --driver docker-container --use
docker buildx use acestream-builder
docker buildx inspect --bootstrap acestream-builder
```

If you intentionally use another builder name, set `JENKINS_BUILDER` in the Jenkins job or agent environment, but the default and documented expectation is `acestream-builder`.

## Cloudflare WARP On The Build Host

Some upstream artifacts (`download.acestream.media`, etc.) are blocked at certain ISPs. The Jenkins bootstrap script (`scripts/ci/setup_jenkins_warp.sh`) installs and connects Cloudflare WARP on the build VM, idempotently, so all host (and inherited Docker daemon) egress flows through Cloudflare.

Operator notes:

- WARP runs in `warp` (full-tunnel) mode on the build host, registered as a free WARP user. No Zero Trust subscription is required for the default routing this repository needs.
- Installation requires the runtime user to have passwordless `sudo`. This is already a stated bootstrap prerequisite.
- Once WARP is connected, the bootstrap on subsequent builds is a no-op verification (one HTTP fetch to `https://www.cloudflare.com/cdn-cgi/trace`).
- If you ever need to disconnect WARP for diagnosis: `warp-cli --accept-tos disconnect`. Reconnect: `warp-cli --accept-tos connect`. The next bootstrap will reconnect automatically.
- WARP affects the host's network stack. The Docker daemon inherits WARP routes by default; no additional Docker config is required.
- Since 2026-08-27 the AceStream engine archives (amd64 tarball, arm64 and armv7 Android APKs) and the bionic runtime packages for ARM are vendored under `docker/vendor/` and mirrored on the GitHub Release `acestream-binaries-3.2.11-3.1.80.0`; `docker/scripts/install-acestream.sh` resolves vendored copy -> upstream URL -> mirror, sha256-verified. Image builds therefore no longer need WARP to reach `download.acestream.media`. WARP stays installed for other geo-blocked artifacts and is harmless otherwise; the engine smoke stages still set `BUILDX_BUILDER=default --network host`, which is only load-bearing when a pin points at a file that is not vendored yet.

## Runner Disk Hygiene

`dorat-nuc-ci` has a small disk and the PR job and the branch job build the same commit concurrently (build #29 died with `No space left on device`). The PR pipeline (`Jenkinsfile`) therefore:

- sweeps, in `Checkout / Bootstrap`, this repo's transient CI images older than an hour (`acestream-scraper:smoke-*`, `acestream-scraper-smoke:*`, `acestream-installer-test:*` — leaked when a test run dies before its finalizers), prunes dangling layers and caps the BuildKit cache at 30 GB;
- tags its multi-GB smoke image from `BUILD_TAG` (unique across both jobs — `BUILD_NUMBER` alone collides) and removes it in `post { always }`.

`scripts/ci/run_jenkins_release.sh` does the equivalent after its engine smoke and before the multi-platform publish builds via `scripts/ci/cleanup_runner_docker.sh` (transient images older than 3 h, unused images older than 24 h, BuildKit cache capped at 20 GB; `--dry-run` prints what it would remove, `--keep <image:tag>` protects a tag). If a build still fails with `No space left on device`, check the node's disk monitor (`/computer/api/json`) and run `docker system df` on the runner.

## AceStream Engine Smoke Coverage

Both pipelines run the engine checks below — the `Acestream Engine Runtime Smoke` stage in `Jenkinsfile` and the pre-publish block in `scripts/ci/run_jenkins_release.sh` (publish runs only; `DRY_RUN=true` exits after the dry-run preflight) — except the Acexy runtime smoke, which is PR-job only.

| Check | Platform | What it proves |
|---|---|---|
| `bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --load --network host --tag ...` | `linux/amd64` | The manifest-driven install works from the vendored tarball. The flavor now resolves to `linux/amd64,linux/arm/v7,linux/arm64`, and `--load` accepts a single platform, so the runner's native one is pinned. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v` | `linux/amd64` on the amd64 runner; `linux/arm64` is added automatically only when the host is arm64 | The engine boots, `get_version` matches the manifest's `engine_version`, and `get_status` answers. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v` | `linux/amd64` (PR job only) | The acexy flavors ship the real proxy, not the build fixture. |
| `PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k android_apk_install_layout` | `linux/arm64`, `linux/arm/v7` (QEMU builds of the installer stage) | The Android engine payload and the Android 9 bionic userland install with the expected layout. No engine execution. |

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

- Use Jenkins build retention; both pipelines already discard old build records after 20 runs.
- Periodically prune stopped containers and unused images during a maintenance window:

```bash
docker system prune -af
docker buildx prune --builder acestream-builder -af
```

- Remove abandoned workspaces if jobs are renamed or deleted.
- If disk pressure is recurring, increase VM disk before aggressively pruning every run; warm cache improves CI stability and duration.

## Jenkins Build Node Setup

User action required.

Recommended model:

- Run the Jenkins controller separately from the Docker build VM.
- Run builds on any Jenkins executor that lands directly on the Docker-capable host.
- Apply the label `dorat-nuc-ci` because both pipeline files require it.

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

Create these Jenkins credentials with these exact ids so the checked-in pipeline files work without modification:

- `github-app-acestream-scraper`: GitHub App credential used for repository discovery, webhook integration, and commit/check reporting
- `acestream-build-agent-ssh`: SSH private key credential for the dedicated build VM agent if you use the SSH-launch model
- `dockerhub-publish`: username/password credential used by `jenkins/release.Jenkinsfile` for Docker Hub publication

Changing these ids would require repository changes, so treat them as part of the CI/CD contract.

## Multibranch Validation Job

User action required.

Create a multibranch pipeline job that points at this repository and uses the repository-root `Jenkinsfile`.

This is UI-only setup. Do not copy `Jenkinsfile` into the Jenkins container.

Recommended configuration:

1. New Item -> Multibranch Pipeline.
2. Add the repository using the GitHub App credential `github-app-acestream-scraper`.
3. Set the script path to `Jenkinsfile`.
4. Discover branches and pull requests from the origin repository.
5. Treat fork pull requests as restricted until you explicitly verify the trust model.
6. Enable one trigger model: webhook-based indexing, periodic scans, or manual rescans.

Expected behavior:

- PR validation runs on label `dorat-nuc-ci`.
- After checkout, the pipeline runs `scripts/ci/bootstrap_jenkins_runner.sh`.
- The pipeline executes `bash scripts/ci/run_jenkins_validation.sh`.
- Build result JSON artifacts are archived for each flavor validation run.
- The `Acestream Engine Runtime Smoke` stage builds `scraper-acestream` pinned to `--platforms linux/amd64 --load`, runs the amd64 engine runtime smoke and the Acexy runtime smoke, then builds the arm64 + armv7 installer stages under QEMU (`test_install_acestream.py -k android_apk_install_layout`). See `## AceStream Engine Smoke Coverage`.

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

- `CONFIRM_RELEASE=true` is required or the pipeline aborts.
- `DRY_RUN=true` performs preflight only.
- `DRY_RUN=false` performs Docker Hub login and publishes tags.
- The job archives release result JSON files and `phase5-build-result-release-metadata.json`.
- Before publishing, the script builds `scraper-acestream` locally pinned to `--platforms linux/amd64 --load` (the flavor now resolves to `linux/amd64,linux/arm/v7,linux/arm64` and `--load` needs a single platform), runs `backend/tests/docker/test_acestream_runtime_smoke.py` (the amd64 engine boots and answers on `:6878`), and then `backend/tests/docker/test_install_acestream.py -k android_apk_install_layout` (QEMU builds of the arm64 + armv7 installer stages; layout only, no engine execution). If either fails, no Docker Hub login or push happens. The engine archives are vendored, so this step does not depend on WARP.
- The pushed `scraper-acestream`, `scraper-acestream-acexy`, `latest`, and version tags are multi-platform manifests that include `linux/arm64` and `linux/arm/v7`; `verify_multiarch_manifest.sh --image <tag> --flavor <flavor>` checks each remote manifest after the push. The arm64 engine runtime is not exercised by this job (amd64 runner); see `## AceStream Engine Smoke Coverage`.
- Keep this path manual-only. Jenkins is the sole publisher; the GitHub Actions release workflow has been retired.

## v2.0.0 Release Runbook

Sequence for shipping the v2 codebase from `ai-coding-documentation` (or any subsequent feature branch) to Docker Hub:

1. Confirm `version.txt` reads the intended release tag (currently `v2.0.0`).
2. Open a pull request from the release branch to `main`. Wait for `acestream-scraper-pr` (Jenkins multibranch) to go green.
3. Merge the PR to `main`. No automatic Docker Hub publish happens — Jenkins requires a manual trigger.
4. In Jenkins, build `acestream-scraper-release` with parameters `CONFIRM_RELEASE=true` and `DRY_RUN=true`. This runs the full cutover suite and the multi-arch dry-run preflight without binding Docker Hub credentials (the engine smoke only runs on the publish run; `scripts/ci/run_jenkins_release.sh --dry-run` exits after the preflight). Verify it goes green.
5. Re-run `acestream-scraper-release` with `CONFIRM_RELEASE=true` and `DRY_RUN=false`. The pipeline will rerun the full cutover suite, dry-run preflight, the AceStream engine smoke (amd64 runtime + ARM installer layout, see `## AceStream Engine Smoke Coverage`), then log into Docker Hub and push the four flavors as multi-platform manifests (`linux/amd64`, `linux/arm64`, `linux/arm/v7`).
6. Verify the published tags on Docker Hub: `pipepito/acestream-scraper:latest`, `:${VERSION}`, plus the four flavor tags (`scraper`, `scraper-acestream`, `scraper-acexy`, `scraper-acestream-acexy`) and their version-prefixed variants. Each should list all three platforms (`docker buildx imagetools inspect <tag>`).
7. Smoke-test on a fresh amd64 host: `docker pull pipepito/acestream-scraper:latest && docker run --rm -p 8000:8000 -p 6878:6878 -e ENABLE_ACESTREAM_ENGINE=true pipepito/acestream-scraper:latest` and confirm the FastAPI app and engine respond. Repeat on an arm64 host (Raspberry Pi 4/5 64-bit, 4 KB-page kernel) to confirm the Android engine answers `curl "http://localhost:6878/webui/api/service?method=get_version"` with `"platform":"android"`; CI does not cover that path. See `docs/ops/acestream-arm-engine.md`.

## Branch Protection Cutover

User action required.

Do not guess the required check name. Observe the exact Jenkins-reported check on a real pull request first, then update GitHub branch protection.

Cutover sequence:

1. Run the multibranch PR validation on a test pull request.
2. Open the PR checks tab and record the exact Jenkins check name shown by GitHub.
3. Add that observed Jenkins check name to branch protection as a required status check.
4. Keep the current GitHub Actions PR check requirement in place until Jenkins has passed repeatedly.
5. Once stable, remove GitHub Actions from required checks and keep them as fallback/reference workflows.

This avoids blocking merges on a mismatched check name.

## Fork Pull Request Policy

Treat fork PRs as restricted until verified.

- Do not assume untrusted fork builds can safely access the Docker-capable agent.
- Keep fork PR discovery disabled or non-building until you validate the Jenkins trust settings, credential exposure, and workspace isolation model.
- If fork PR support is required later, document the exact trust and approval policy before enabling it.

## GitHub Actions During The Proving Window

Jenkins is the canonical CI and release path. During the proving window, two GitHub Actions workflows remain as parity validators:

- All GitHub Actions workflows are retired; every gate (tests, four-flavor dry-run multi-arch builds, AceStream engine runtime smoke, cutover required checks, phase gates) runs on the Jenkins pipelines above.

The phase-specific GA scaffolding workflows (`phase1-safety-gates.yml`, `cutover-validation.yml`, `multiarch-validation.yml`) were removed once their gate runners were absorbed into the canonical PR + release pipelines.

Expected operating model:

- Jenkins is the canonical path for PR validation and release publication.
- GitHub Actions PR workflow stays on for parity. GA release workflow is manual-only validation; it never pushes to Docker Hub.
- Removing GA entirely is a future cleanup once Jenkins has proven stable across multiple releases.

## Rollback Guidance

If Jenkins cutover causes merge or release risk:

1. Re-enable GitHub Actions checks in branch protection immediately.
2. Remove the Jenkins check from required branch protection if it is unstable or unreachable.
3. Pause manual Jenkins releases.
4. If Jenkins is unavailable, run the validation and publish steps manually from a workstation: `bash scripts/ci/run_cutover_required_checks.sh --profile full`, then `bash scripts/ci/run_jenkins_release.sh` with the Docker Hub credential exported (preview first with `--print-publish-plan`).
5. Preserve Jenkins logs, webhook delivery logs, and agent diagnostics before making major controller changes.

Rollback is complete only when GitHub Actions are again sufficient to validate and ship the repository without Jenkins.

## Ownership Matrix

- Pipeline definitions:
  Repo-owned: `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/bootstrap_jenkins_runner.sh`, `scripts/ci/run_jenkins_validation.sh`, `scripts/ci/run_jenkins_release.sh`
  User-owned: Job creation and Jenkins global or job settings

- Build environment contract:
  Repo-owned: required builder name, label, `scripts/ci/bootstrap_jenkins_runner.sh`, validation/release wrappers, result artifacts
  User-owned: VM provisioning, `git` prerequisite, Docker daemon availability, Docker access for the runtime user, optional preinstallation, optional sudoers setup, node launch model

- GitHub integration:
  Repo-owned: documented credential ids and pipeline expectations
  User-owned: GitHub App registration, installation, and optional webhook or polling setup

- Branch policy:
  Repo-owned: documentation of cutover order and fallback behavior
  User-owned: branch protection updates, required check selection, rollback decision

- Release publication:
  Repo-owned: Docker Hub login binding in the release pipeline
  User-owned: Docker Hub credential management and manual release approval
