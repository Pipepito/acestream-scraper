# Jenkins CI/CD Operator Guide

## Overview

This document is the primary operator guide for Jenkins CI/CD in this repository.

Current rollout state:

- GitHub Actions remains unchanged and continues to auto-run until Jenkins setup is verified.
- Jenkins assets in this repository are ready to be wired into your homelab controller and agent.

Important constraint for this setup:

- Jenkins should be configured through the Jenkins UI.
- Do not copy `Jenkinsfile`, `jenkins/release.Jenkinsfile`, shell scripts, or helper files into the Jenkins Docker container.
- Jenkins should load pipeline definitions directly from this Git repository through SCM configuration in the UI.

Current workflow parity goal:

- Jenkins multibranch validation is the Jenkins replacement for `.github/workflows/pull_request.yml`.
- Jenkins manual release is the Jenkins replacement for `.github/workflows/release.yml`.
- The repository files that make this work are `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, and `scripts/ci/run_jenkins_release.sh`.
- Those files must be pushed to GitHub before Jenkins can load them through SCM.

Current limitation:

- The checked-in Jenkins scripts currently assume the VM has already been bootstrapped with the required system packages.
- Passwordless `sudo` steps are included below so you can prepare the agent for future self-healing bootstrap work, but the current Jenkins scripts do not yet install Docker, Node, or Python for you.

After cutover:

- Jenkins multibranch pipelines are the canonical path for pull request validation.
- Jenkins manual release jobs are the canonical path for release publication.
- GitHub Actions can be reduced to fallback and manual validation paths once you decide the Jenkins setup is proven.

Responsibility split:

- Repo-owned: `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, `scripts/ci/run_jenkins_release.sh`, build/test scripts, and supporting documentation.
- User-owned: Jenkins controller installation, dedicated build VM lifecycle, plugin installation, credentials, GitHub App registration, webhook exposure, branch protection cutover, and rollback decisions.

## User Action Required

The following steps require operator intervention outside the repository:

- Provision a dedicated Jenkins controller and a dedicated Docker-capable build VM.
- Install the required Jenkins plugins.
- Bootstrap the Ubuntu 24.04 build VM dependencies.
- Create or select the named Docker buildx builder `acestream-builder`.
- Configure the Jenkins SSH agent labeled `acestream-docker-multiarch`.
- Register the GitHub App, install it on the repository, and store its credentials in Jenkins.
- Expose Jenkins webhook endpoints over reachable HTTPS with working DNS or a reverse proxy/tunnel.
- Create the Jenkins multibranch validation job from `Jenkinsfile`.
- Create the Jenkins manual release job from `jenkins/release.Jenkinsfile`.
- Observe the Jenkins check name reported back to GitHub and update branch protection to require it.
- Keep GitHub Actions fallback workflows enabled until Jenkins cutover is verified.

## Complete Setup Checklist

Use this as the end-to-end checklist for a fresh Jenkins controller running in Docker on your homelab.

## Start Here

If you want the shortest path from a fresh Jenkins container to working PR and release jobs, do these three checklists in order.

### A. Ubuntu VM First

- [ ] Create the Ubuntu 24.04 VM.
- [ ] SSH into the VM as your admin user.
- [ ] Run the bootstrap commands from `## Ubuntu 24.04 Bootstrap`.
- [ ] Run the passwordless-sudo commands from `## Passwordless Sudo For The Jenkins Agent`.
- [ ] Create `/home/jenkins/.ssh/authorized_keys` and add the Jenkins SSH public key.
- [ ] Verify:
  - [ ] `sudo -iu jenkins sudo -n true`
  - [ ] `sudo -iu jenkins docker version`
  - [ ] `sudo -iu jenkins docker buildx version`
- [ ] Create/bootstrap the `acestream-builder` builder.
- [ ] Confirm the VM is reachable from your Jenkins host over SSH.

### B. Jenkins UI Next

- [ ] Log into Jenkins as admin.
- [ ] Set the Jenkins base URL.
- [ ] Install the required plugins.
- [ ] Add SSH credential `acestream-build-agent-ssh`.
- [ ] Add GitHub App credential `github-app-acestream-scraper`.
- [ ] Add Docker Hub credential `dockerhub-publish`.
- [ ] Create the permanent SSH agent labeled `acestream-docker-multiarch`.
- [ ] Confirm the node comes online.
- [ ] Push the repo branch/commit that contains:
  - [ ] `Jenkinsfile`
  - [ ] `jenkins/release.Jenkinsfile`
  - [ ] `scripts/ci/run_jenkins_validation.sh`
  - [ ] `scripts/ci/run_jenkins_release.sh`
- [ ] Create the multibranch PR-validation job from `Jenkinsfile`.
- [ ] Create the manual release job from `jenkins/release.Jenkinsfile`.

### C. GitHub App And Validation Last

- [ ] Create and install the GitHub App on this repository.
- [ ] Configure webhook reachability to Jenkins over HTTPS.
- [ ] Trigger an initial multibranch scan.
- [ ] Open or update a test PR.
- [ ] Confirm Jenkins reports a status/check back to GitHub.
- [ ] Record the exact Jenkins check name.
- [ ] Run the manual release job with `CONFIRM_RELEASE=true` and `DRY_RUN=true`.
- [ ] Only after Jenkins is stable, add the Jenkins check to branch protection.
- [ ] Leave GitHub Actions unchanged until you are happy with the Jenkins setup.

### Quick Outcome Check

You are ready to rely on Jenkins for the next phase when all of these are true:

- [ ] Jenkins agent is online and builds on the VM
- [ ] multibranch PR validation runs successfully
- [ ] GitHub shows the Jenkins PR check
- [ ] release dry-run succeeds
- [ ] you know the exact branch-protection check name

### 1. Jenkins Controller Basics

- [ ] Confirm the Jenkins Docker container is running and persistent storage is mounted for Jenkins home.
- [ ] Sign in to the Jenkins UI with an admin account.
- [ ] Set the Jenkins base URL under `Manage Jenkins` -> `System`.
- [ ] Decide how GitHub will reach Jenkins over HTTPS.
- [ ] Confirm the public URL works from outside your LAN if you are using GitHub webhooks.

### 1.5. Push The Jenkins Repo Files First

- [ ] Push the branch or commit that contains `Jenkinsfile`.
- [ ] Push the branch or commit that contains `jenkins/release.Jenkinsfile`.
- [ ] Push the branch or commit that contains `scripts/ci/run_jenkins_validation.sh`.
- [ ] Push the branch or commit that contains `scripts/ci/run_jenkins_release.sh`.
- [ ] Push the updated operator docs so you can follow the checked-in guidance from the same repo state Jenkins will use.
- [ ] Confirm GitHub shows those files in the branch or `main` revision Jenkins will read.

### 2. Install Jenkins Plugins

- [ ] Open `Manage Jenkins` -> `Plugins`.
- [ ] Install:
  - [ ] GitHub Branch Source
  - [ ] GitHub Checks
  - [ ] Pipeline
  - [ ] Multibranch Scan Webhook Trigger
  - [ ] SSH Build Agents
  - [ ] Credentials
  - [ ] Credentials Binding
  - [ ] Plain Credentials
  - [ ] Docker Pipeline
  - [ ] Timestamper
  - [ ] Workspace Cleanup
- [ ] Restart Jenkins if required.

### 3. Prepare The Build VM

- [ ] Provision the Ubuntu 24.04 VM.
- [ ] Verify it has enough CPU, RAM, and disk.
- [ ] Install Git, Python, Docker, Buildx, Compose plugin, Node 20, `jq`, and `curl`.
- [ ] Create the `jenkins` user.
- [ ] Enable passwordless `sudo` for the `jenkins` user.
- [ ] Add the `jenkins` user to the `docker` group.
- [ ] Verify `jenkins` can run `docker version` and `docker buildx version`.
- [ ] Create or select the named builder `acestream-builder`.
- [ ] Bootstrap the builder and confirm it supports the required platforms.

### 4. Prepare SSH Access For The Agent

- [ ] Generate or choose the SSH keypair Jenkins will use.
- [ ] Put the public key into `/home/jenkins/.ssh/authorized_keys` on the VM.
- [ ] Verify you can SSH to the VM as `jenkins` using that key.
- [ ] Verify SSH login still has Docker access.

### 5. Add The Agent In Jenkins UI

- [ ] Open `Manage Jenkins` -> `Credentials`.
- [ ] Add SSH private key credential with id `acestream-build-agent-ssh`.
- [ ] Open `Manage Jenkins` -> `Nodes` or `Manage Nodes and Clouds`.
- [ ] Create a permanent node for the VM.
- [ ] Set remote root directory to `/home/jenkins`.
- [ ] Set label to `acestream-docker-multiarch`.
- [ ] Set launch method to `Launch agents via SSH`.
- [ ] Select credential `acestream-build-agent-ssh`.
- [ ] Save and wait for the node to come online.
- [ ] Run a simple test job on that label to confirm Python, Node, Docker, and Buildx work.

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
- [ ] In Jenkins, add the Docker Hub username/password credential with id `dockerhub-publish`.
- [ ] Confirm the SSH credential id is `acestream-build-agent-ssh`.
- [ ] Do not rename these ids unless you also plan to change the checked-in pipeline files.

### 8. Configure GitHub Webhook Reachability

- [ ] Expose Jenkins over HTTPS using DNS, reverse proxy, or tunnel.
- [ ] Configure the webhook secret in GitHub and Jenkins if required by your setup.
- [ ] Point GitHub webhook delivery to the Jenkins webhook endpoint.
- [ ] Trigger a test delivery and confirm GitHub receives HTTP 2xx.

### 9. Make Sure Jenkins Can Read This Repo

- [ ] Confirm the GitHub App has access to this repository.
- [ ] Confirm Jenkins can discover the repository using the GitHub App credential.
- [ ] Do not copy repository files into the Jenkins container.
- [ ] Use SCM-based jobs so Jenkins reads `Jenkinsfile` and `jenkins/release.Jenkinsfile` directly from git.
- [ ] Confirm the branch or `main` revision Jenkins will read already contains the Jenkins repo files listed above.

### 10. Create The PR Validation Job In Jenkins UI

- [ ] Create a new `Multibranch Pipeline` job.
- [ ] Connect it to this GitHub repository using `github-app-acestream-scraper`.
- [ ] Set script path to `Jenkinsfile`.
- [ ] Enable branch discovery.
- [ ] Enable pull request discovery.
- [ ] Treat fork PRs as restricted until you explicitly validate that trust model.
- [ ] Enable webhook-based indexing or scan triggers.
- [ ] Run an initial scan and confirm Jenkins sees `main` and your working branches.

Expected parity:

- This job is the Jenkins-side equivalent of `.github/workflows/pull_request.yml`.
- It should run the same quick validation path through `scripts/ci/run_jenkins_validation.sh`.

### 11. Create The Manual Release Job In Jenkins UI

- [ ] Create a new `Pipeline` job.
- [ ] Configure it as `Pipeline script from SCM`.
- [ ] Point SCM at this repository.
- [ ] Set branch to `main`.
- [ ] Set script path to `jenkins/release.Jenkinsfile`.
- [ ] Leave the job manual-only.
- [ ] Confirm the job exposes `CONFIRM_RELEASE` and `DRY_RUN` parameters.

Expected parity:

- This job is the Jenkins-side equivalent of `.github/workflows/release.yml`.
- It should run the same release preflight and publish flow through `scripts/ci/run_jenkins_release.sh`.

### 12. Verify The Agent Contract

- [ ] Run a build on the multibranch job.
- [ ] Confirm Jenkins executes on label `acestream-docker-multiarch`.
- [ ] Confirm the job runs on the VM workspace, not inside the controller container.
- [ ] Confirm `docker buildx use "${JENKINS_BUILDER:-acestream-builder}"` succeeds.
- [ ] Confirm the validation wrapper runs successfully.

### 13. Verify GitHub PR Reporting

- [ ] Open or update a test PR.
- [ ] Confirm Jenkins runs automatically.
- [ ] Confirm GitHub shows the Jenkins-reported check on the PR.
- [ ] Record the exact check name from the PR UI.

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

- [ ] Open GitHub branch protection settings.
- [ ] Add the observed Jenkins check name as a required status check.
- [ ] Keep GitHub Actions required checks until Jenkins has passed repeatedly.
- [ ] Once confident, remove GitHub Actions from required checks.

### 17. Later Cutover Of GitHub Actions

- [ ] Only after Jenkins is proven stable, convert GitHub Actions to fallback/manual-only.
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

## Required Jenkins Plugins

Install these plugins before creating jobs:

- GitHub Branch Source
- GitHub Checks
- Pipeline
- Multibranch Scan Webhook Trigger
- SSH Build Agents
- Credentials
- Credentials Binding
- Plain Credentials
- Docker Pipeline
- Matrix Authorization Strategy if your controller uses role-based access control
- Timestamper
- Workspace Cleanup

`Jenkinsfile` and `jenkins/release.Jenkinsfile` are declarative pipelines, so the Pipeline plugin family is mandatory. GitHub App and multibranch discovery rely on GitHub Branch Source. SSH Build Agents is required for the dedicated Docker host model described below.

## Dedicated VM Requirements

Use a dedicated VM for Jenkins Docker builds instead of sharing a general-purpose host.

Minimum expectations:

- Ubuntu 24.04 LTS
- 4 vCPU minimum; 8 vCPU recommended for faster multi-arch preflight
- 16 GB RAM minimum; 32 GB recommended if concurrent builds are allowed later
- 150 GB SSD minimum, with headroom for Docker layers, buildx cache, and workspace archives
- Outbound access to GitHub, Docker Hub, Ubuntu package repositories, NodeSource, and any reverse-proxy or tunnel endpoint you use
- Inbound SSH from the Jenkins controller to the build VM

Operational requirements:

- The Docker daemon must be available to the Jenkins agent user.
- The VM should be treated as cattle, not pet infrastructure: document bootstrap and be ready to rebuild.
- Keep this host dedicated to CI so buildx cache growth and Docker cleanup do not compete with unrelated workloads.

## Ubuntu 24.04 Bootstrap

These commands are user-run bootstrap steps for the dedicated Jenkins build VM.

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg jq git python3 python3-venv python3-pip
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

This is optional for the current checked-in Jenkins scripts, but it matches the future direction you asked for and is safe to prepare now.

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

Validation commands:

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

This repository expects a named buildx builder called `acestream-builder`. Both `Jenkinsfile` and `jenkins/release.Jenkinsfile` run `docker buildx use "${JENKINS_BUILDER:-acestream-builder}" || true`, and the backing scripts fail if the builder does not exist.

Create or select it on the Jenkins build VM:

```bash
docker buildx inspect acestream-builder >/dev/null 2>&1 || docker buildx create --name acestream-builder --driver docker-container --use
docker buildx use acestream-builder
docker buildx inspect --bootstrap acestream-builder
```

If you intentionally use another builder name, set `JENKINS_BUILDER` in the Jenkins job or agent environment, but the default and documented expectation is `acestream-builder`.

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

## Jenkins SSH Agent Setup

User action required.

Recommended model:

- Run the Jenkins controller separately from the Docker build VM.
- Connect the build VM as an SSH agent.
- Apply the label `acestream-docker-multiarch` because both pipeline files require it.

Suggested steps:

1. Create a dedicated `jenkins` user on the build VM.
2. Install the agent user's SSH public key in `~jenkins/.ssh/authorized_keys`.
3. Ensure the `jenkins` user can run Docker via the `docker` group.
4. In Jenkins, create an SSH credential with id `acestream-build-agent-ssh`.
5. Add a permanent SSH agent pointing to the VM and assign the label `acestream-docker-multiarch`.
6. Confirm a test pipeline on that label can run `python3 --version`, `node --version`, and `docker buildx version`.

### VM-Side Agent Steps

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
ssh -i /path/to/private_key jenkins@<vm-ip> 'whoami && docker version && docker buildx version'
```

Expected result:

- user is `jenkins`
- Docker server is reachable
- `docker buildx version` works
- `sudo -n true` succeeds

### Jenkins UI Agent Steps

Do this in the Jenkins UI only.

1. Go to `Manage Jenkins` -> `Credentials`.
2. Add a new SSH private key credential.
3. Set the credential id to `acestream-build-agent-ssh`.
4. Go to `Manage Jenkins` -> `Nodes` or `Manage Nodes and Clouds`.
5. Create a new permanent agent.
6. Set:
   - Node name: `acestream-docker-multiarch`
   - Remote root directory: `/home/jenkins`
   - Labels: `acestream-docker-multiarch`
   - Launch method: `Launch agents via SSH`
   - Host: `<vm-ip-or-hostname>`
   - Credentials: `acestream-build-agent-ssh`
7. Save and let Jenkins connect.

Recommended node settings:

- Usage: `Only build jobs with label expressions matching this node`
- Executors: start with `1`
- Availability: `Keep this agent online as much as possible`

### Agent Verification Checklist

After Jenkins connects to the VM, use the agent's `Script Console`/test job path indirectly by running a simple pipeline step on that label with:

```bash
whoami
pwd
python3 --version
node --version
docker version
docker buildx version
docker buildx use "${JENKINS_BUILDER:-acestream-builder}" || true
docker buildx inspect acestream-builder
```

Expected result:

- workspace is on the VM, not inside the Jenkins controller container
- Python, Node, Docker, and Buildx are available
- `acestream-builder` exists or can be selected

If Jenkins connects but Docker commands fail, the usual causes are:

- `jenkins` user not in the `docker` group
- group membership not refreshed after login
- Docker service not running
- buildx builder not created for that user context

## GitHub App Setup

User action required.

Use a GitHub App instead of a personal access token for multibranch discovery and status reporting.

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

GitHub must be able to reach Jenkins over HTTPS.

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

## Jenkins Credential IDs

Create these Jenkins credentials with these exact ids so the checked-in pipeline files work without modification:

- `github-app-acestream-scraper`: GitHub App credential used for repository discovery, webhook integration, and commit/check reporting
- `acestream-build-agent-ssh`: SSH private key credential for the dedicated build VM agent
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
6. Enable webhook-based indexing or scan triggers.

Expected behavior:

- PR validation runs on label `acestream-docker-multiarch`.
- The pipeline executes `bash scripts/ci/run_jenkins_validation.sh`.
- Build result JSON artifacts are archived for each flavor validation run.

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

## Branch Protection Cutover

User action required.

Do not guess the required check name. Observe the exact Jenkins-reported check on a real pull request first, then update GitHub branch protection.

Cutover sequence:

1. Run the multibranch PR validation on a test pull request.
2. Open the PR checks tab and record the exact Jenkins check name shown by GitHub.
3. Add that observed Jenkins check name to branch protection as a required status check.
4. Keep the current GitHub Actions PR check requirement in place until Jenkins has passed repeatedly.
5. Once stable, remove GitHub Actions from required checks and keep them as fallback/manual workflows.

This avoids blocking merges on a mismatched check name.

## Fork Pull Request Policy

Treat fork PRs as restricted until verified.

- Do not assume untrusted fork builds can safely access the Docker-capable agent.
- Keep fork PR discovery disabled or non-building until you validate the Jenkins trust settings, credential exposure, and workspace isolation model.
- If fork PR support is required later, document the exact trust and approval policy before enabling it.

## GitHub Actions During Cutover

Until you finish the Jenkins rollout, the existing GitHub Actions workflows stay in their current automatic form.

After Jenkins cutover, GitHub Actions can be reduced to fallback/manual flows:

- `.github/workflows/pull_request.yml`: fallback PR validation reference
- `.github/workflows/release.yml`: fallback/manual release reference
- `.github/workflows/multiarch-validation.yml`: extra multi-arch validation path
- `.github/workflows/cutover-validation.yml`: cutover verification path
- `.github/workflows/phase1-safety-gates.yml`: legacy phase 1 safety-gate fallback path

Expected operating model after cutover:

- Jenkins is primary for PR validation and release publication.
- GitHub Actions are retained for rollback, comparison, or manual assurance runs.
- Do not delete the workflows until Jenkins has proven stable and rollback is no longer needed.

## Rollback Guidance

If Jenkins cutover causes merge or release risk:

1. Re-enable GitHub Actions checks in branch protection immediately.
2. Remove the Jenkins check from required branch protection if it is unstable or unreachable.
3. Pause manual Jenkins releases.
4. Use `.github/workflows/release.yml` or `.github/workflows/multiarch-validation.yml` for temporary fallback validation/publish flow.
5. Preserve Jenkins logs, webhook delivery logs, and agent diagnostics before making major controller changes.

Rollback is complete only when GitHub Actions are again sufficient to validate and ship the repository without Jenkins.

## Ownership Matrix

| Area | Repo-owned | User-owned |
|---|---|---|
| Pipeline definitions | `Jenkinsfile`, `jenkins/release.Jenkinsfile`, `scripts/ci/run_jenkins_validation.sh`, `scripts/ci/run_jenkins_release.sh` | Job creation and Jenkins global/job settings |
| Build environment contract | Required builder name, labels, scripts, result artifacts | VM provisioning, Docker daemon, Node/Python installation, buildx bootstrap |
| GitHub integration | Documented credential ids and pipeline expectations | GitHub App registration, installation, webhook secret, webhook routing |
| Branch policy | Documentation of cutover order and fallback behavior | Branch protection updates, required check selection, rollback decision |
| Release publication | Docker Hub login binding in release pipeline | Docker Hub credential management and manual release approval |
