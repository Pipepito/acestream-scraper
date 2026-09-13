# External Integrations

**Analysis date:** 2026-09-03
**Mapped revision:** `develop` at `e5bc9e0` (the branch currently proposed for merge into `main`)

## Secret Handling

- `infra-details.md` is the local, untracked source for Jenkins controller connection details and operator credentials. Read it only when an infrastructure action is explicitly required. Never copy its host/account/token values into tracked files, logs, prompts, screenshots, issue text, or command history.
- Jenkins secrets belong in the Jenkins credential store and are referenced from pipeline code only by credential ID. Current non-secret IDs include `github-builder-app`, `dockerhub-publish`, and `github-publish`.
- The checked-in `.tmp/jenkins/*-config.xml` files are read-only snapshots for diffing, not live configuration. Editing them does not update Jenkins.
- Application `API_TOKEN`, WARP license material, registry tokens, and GitHub publishing tokens are secret values. Pass them through environment/credential bindings; never commit them.

## Jenkins and GitHub CI

Jenkins is the canonical and only CI/release path on this branch. GitHub Actions workflows have been retired.

### Controller and agents

- Controller URL, operator account, API token, and infrastructure addresses are intentionally omitted here; retrieve them from local `infra-details.md` when authorized.
- The pipelines select Jenkins agent label `dorat-nuc-ci`. The physical runner is a small-disk NUC-class host, so the pipeline cleans transient Docker state and caps BuildKit cache.
- `scripts/ci/bootstrap_jenkins_runner.sh` prepares Python, Node, Docker/Buildx, QEMU/binfmt, and optionally WARP. The expected builder defaults to `acestream-builder` and can be changed through `JENKINS_BUILDER`.
- Repository-owned Jenkins behavior is in `Jenkinsfile`, `jenkins/release.Jenkinsfile`, and `scripts/ci/`. Controller/node/job/credential configuration remains operator-owned.

### PR and branch validation job

- Job: `acestream-scraper-pr`, configured as a multibranch pipeline in Jenkins folder `Acestream-Scraper`.
- SCM: GitHub Branch Source reads the repository with `github-builder-app`; the checked-in snapshot shows periodic indexing and origin-PR discovery.
- Pipeline source: root `Jenkinsfile`.
- GitHub status context: `PR Validation`, required on both `develop` and `main`.
- Branch discovery excludes redundant branch builds while the same head is represented by a PR. The open `develop` -> `main` release PR is therefore the validation surface for this branch while it remains open.
- PRs targeting `main` fail unless their head is exactly `develop`.

The validation pipeline performs controller checkout/bootstrap, docs checks, phase/cutover suites, strict legacy-path checks, four-flavor multi-arch dry-run/manifest verification, native engine/Acexy runtime smoke, ARM installer-layout checks, and artifact archiving. It then conditionally performs `develop` publishing.

### Develop-channel publishing

For a validated `develop` branch build or a PR whose head is `develop`, the root pipeline:

- binds `dockerhub-publish` and calls `scripts/ci/run_jenkins_release.sh --channel develop`;
- publishes only `pipepito/acestream-scraper:develop` for the full payload and `:develop-<flavor>` for each flavor;
- never publishes a version tag, per-commit tag, or `:latest` in channel mode;
- archives `phase5-build-result-channel-*.json` evidence;
- binds `github-publish` to mirror `wiki/` to the GitHub wiki and publish the constrained docs payload to `gh-pages`.

A missing publishing credential is deliberately reported as `UNSTABLE` rather than hiding a validation failure. For a protected release PR this still prevents the required status from being green, so the operator must fix the credential scope rather than bypass the checks.

### Manual release job

- Job: `acestream-scraper-release`; pipeline source `jenkins/release.Jenkinsfile`; SCM is fixed to `main`.
- It requires `CONFIRM_RELEASE=true`, defaults `DRY_RUN=true`, verifies checked-out `HEAD == origin/main`, and refuses non-`main` branches.
- `version.txt` must be a final version: `scripts/ci/run_jenkins_release.sh` refuses normal releases containing `-dev`.
- Phase 1 (`PUBLISH_LATEST=false`) validates, smokes, logs into Docker Hub, and publishes versioned and flavor manifests by per-platform digest.
- Phase 2 (`PUBLISH_LATEST=true`) does not rebuild; `scripts/ci/promote_latest.sh` retags the already canary-validated full-payload version manifest to `:latest` and verifies it.
- Pipeline artifacts record build and release metadata; keep them with Jenkins logs when diagnosing failures.

Operational runbooks, rollback procedure, job setup, and live-state notes are in `docs/ops/jenkins-ci.md`. Use the local controller access from `infra-details.md` only to inspect or operate Jenkins; do not duplicate it in agent documentation.

## GitHub and Documentation Publishing

- GitHub is the source repository and provider of branch/PR status. Jenkins uses the GitHub App credential for discovery/status reporting through outbound GitHub API access; a public Jenkins webhook is optional, not required.
- `scripts/ci/publish_pages.sh` pushes only `docs/index.html`, `docs/builder/`, and `.nojekyll` to the `gh-pages` branch. GitHub Pages serves the Docker command builder.
- `scripts/ci/publish_wiki.sh` treats `wiki/` as the source of truth and mirrors it to the repository's separate wiki Git repository.
- Both publishers use temporary authenticated remotes assembled from the `github-publish` binding. Do not log remote URLs containing credentials.
- GitHub Release assets are mirrors for vendored AceStream/bionic build inputs, while local vendored archives are preferred in normal builds.

## Docker Hub

- Production image repository: `pipepito/acestream-scraper`.
- Authentication is late-bound through Jenkins `dockerhub-publish`; scripts consume `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` and use password-stdin.
- Four image flavors are published. Builds are platform-major and pushed by digest before multi-platform manifests are assembled and verified.
- The full `scraper-acestream-acexy` payload backs the unqualified version tag, `:develop`, and eventually `:latest`.
- Publication can be redirected to a throwaway registry only for local end-to-end tests through the explicitly supported release-script overrides.

## Runtime Service Integrations

### AceStream Engine

- The backend talks to the HTTP engine selected by `ACE_ENGINE_URL` (legacy alias `ACESTREAM_ENGINE_URL`). Container entrypoint derives it from `ACESTREAM_HTTP_HOST`/`ACESTREAM_HTTP_PORT` when not explicitly set.
- Health/version probes use the engine's HTTP/WebUI API, including `webui/api/service?method=get_version`; streaming/search/status services use the engine server API.
- Engine service may be embedded (`ENABLE_ACESTREAM_ENGINE=true` in an engine-bearing flavor) or external. `IMAGE_HAS_ACESTREAM` states packaging capability, not whether it is running.
- No application-level engine authentication is present; protect exposure at the network/container boundary.

### Acexy

- Acexy is an optional reverse proxy/bridge to AceStream, bundled only in Acexy flavors and started with `ENABLE_ACEXY=true`.
- Target engine is configured by `ACEXY_HOST`/`ACEXY_PORT`; listener/status behavior also respects `ACEXY_LISTEN_ADDR` rather than assuming the image-default status port.
- Probes use `/ace/status`. If the embedded engine is disabled, Acexy must point to a genuinely reachable external engine and cannot silently target container-local `localhost:6878`.
- The build uses checksum-verified vendored Acexy 0.2.2 source before any upstream Git fallback.

### Cloudflare WARP

- Optional WARP support is driven by `ENABLE_WARP`; package availability is amd64/arm64 only and runtime needs `/dev/net/tun` plus `NET_ADMIN` and `SYS_ADMIN`.
- `warp-setup.sh` supervises registration, optional license application, mode selection, and connection through `warp-cli`/`warp-svc`/D-Bus.
- The backend WARP service invokes the local CLI and probes Cloudflare trace/network state. Any license key is a secret runtime input.
- Jenkins optionally enables WARP for remaining geo-blocked fetches, but vendored engine and Acexy inputs prevent those builds from depending on WARP-routed anonymous GitHub cloning.

### IPFS / IPNS via Kubo

- `ipfs://` and `ipns://` sources are translated to the HTTP gateway set by `IPFS_GATEWAY_URL`.
- Kubo may run embedded with `ENABLE_IPFS=true` on amd64/arm64, or the app may use an external gateway while the daemon is disabled.
- Embedded defaults: repository `/data/ipfs`, swarm 4001, RPC API 5001 bound to loopback, gateway 8081 (Acexy owns 8080). Never expose the unauthenticated RPC API to an untrusted network.
- Kubo is unavailable in arm/v7 images. Startup detects the installed binary and refuses an impossible enable request.

### ZeroNet and Tor

- `zero://` sources are resolved through the HTTP node selected by `ZERONET_URL`.
- A pinned ZeroNet node can run embedded only on amd64 with `ENABLE_ZERONET=true`; otherwise configure an external node. State defaults to `/data/zeronet`, UI to 43110, and fileserver to 26552.
- `ENABLE_TOR` only affects the embedded ZeroNet node and has no effect when ZeroNet is disabled.
- Remote access to the embedded ZeroNet UI requires explicit host allow-listing (`ZERONET_UI_HOST`).

### User-provided HTTP content

- Users can configure ordinary HTTP/HTTPS pages, M3U/M3U8 playlists, EPG/XMLTV sources, and IPFS/ZeroNet locations.
- Scrapers use `aiohttp` with timeouts/retries. The regular HTTP scraper follows redirects manually so every hop passes `backend/app/utils/url_guard.py` SSRF validation; configured gateway/node hosts receive narrowly scoped exemptions.
- These are pull integrations. No general outgoing webhook system exists.

## Application API Authentication and Browser Integration

- The API is open by default for trusted-network compatibility. Setting `API_TOKEN` protects all `/api/v1` routes except `/api/v1/health`, plus player-facing playlist/EPG routes.
- Accepted clients may send `Authorization: Bearer`, `X-Api-Token`, or a `token` query parameter (the latter supports IPTV/XMLTV clients that accept only URLs).
- The React client stores the operator-supplied value and attaches `X-Api-Token`. Never embed the token in the frontend build.
- Vite proxies `/api` to the local backend during development. Production is same-origin because FastAPI serves the SPA; `CORS_ORIGINS` covers intentional cross-origin development/clients.

## Data, Monitoring, and Absent Integrations

- SQLite and mounted files are local persistence, not external managed services. Alembic owns the canonical schema.
- FastAPI health, sidecar probes, APScheduler task status, application logs, Jenkins console output, and archived JSON/JUnit/Playwright artifacts provide observability.
- No Sentry/New Relic/OpenTelemetry backend, analytics SDK, OAuth provider, email/SMS provider, Redis/cache, message broker, cloud object store, or inbound application webhook was found on this revision.

---

*Refresh this file when endpoints, credential IDs, controller/job topology, registry behavior, or optional sidecars change. Keep all secret values in their designated local or credential-store source.*
