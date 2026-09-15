# Development

The application has a FastAPI backend in `backend/` and a React/TypeScript frontend in `frontend/`. Docker is the easiest way to use Scraper; this guide is for contributors running from source.

## Run locally

Clone the [repository](https://github.com/Pipepito/acestream-scraper), check out `develop`, and create your feature branch. Use Python 3.13 (the container runtime) and Node.js 20 with npm. FFmpeg must be on your PATH for browser playback.

From the repository root, start the backend:

```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 --no-proxy-headers
```

In a second terminal, start the frontend:

```bash
cd frontend
npm ci
npm start
```

Open `http://localhost:3000`; the development server forwards API requests to port 8000. To serve a built UI from the backend instead, run `npm run build:backend` in `frontend/` and open `http://localhost:8000`.

Settings use environment variables and the application database. Relative database paths resolve from the backend's working directory. See [Configuration](Configuration.md) and [manual installation](Installation.md#manual-installation) for runtime setup.

## Repository map

| Folder | Purpose |
|---|---|
| `backend/` | API, services, database migrations, scrapers, and Python tests |
| `frontend/` | React/TypeScript application and UI tests |
| `e2e/` | Browser journeys and their local test stack |
| `docker/` | Image components, manifests, and installers |
| `scripts/` and `jenkins/` | Validation, operations, and publication |
| `wiki/` | Source for the published user guides |
| `docs/` | Technical guides and the Docker command builder |

## Check your changes

Run checks appropriate to the files you changed. For application changes, the quick cross-stack gate is:

```bash
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/assert_no_legacy_paths.sh --strict
```

For user documentation changes:

```bash
python3 scripts/ci/validate_documentation.py
python3 scripts/ci/validate_docker_docs_contract.py
bash scripts/ci/validate_command_builder.sh
bash scripts/ci/publish_wiki.sh --dry-run
bash scripts/ci/prepare_pages.sh
python3 scripts/ci/publish_dockerhub_description.py --dry-run
```

These previews do not publish. Documentation-only PRs use lightweight checks; application, packaging, dependency, CI, and unknown changes retain full validation. Manual releases always retain the release gate.

## Send a contribution

Open feature and fix PRs against `develop`. `main` is the release branch. Include what changed and the checks you ran. Read the root and relevant directory's `AGENTS.md` and `CLAUDE.md` for repository conventions.

Edit the user docs in `wiki/`; the manual release job mirrors them to GitHub's wiki after successful latest promotion. GitHub Pages serves `main/docs`; rebuild and commit `docs/recipes/` with `bash scripts/ci/prepare_pages.sh` when the extraction helper changes. Edit Docker Hub text in `docs/dockerhub/` and copy it to Docker Hub manually. Develop validates documentation without publishing it. Keep the root README focused on what the project does and where to start.

See the [technical documentation index](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/README.md), [Jenkins runbook](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/jenkins-ci.md), and [test ownership guide](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/testing/test-ownership-matrix.md) for deeper work.
