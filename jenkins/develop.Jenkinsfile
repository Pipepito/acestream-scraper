pipeline {
  agent { label 'dorat-nuc-ci' }

  environment {
    JENKINS_ENABLE_WARP = '1'
    PR_RUNNER_IMAGE = 'acestream-scraper-pr-ci:develop'
  }

  triggers {
    pollSCM('H/5 * * * *')
  }

  options {
    lock(resource: 'acestream-scraper-nuc-docker', reason: 'Exclusive Docker and BuildKit access on dorat-nuc-ci')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 4, unit: 'HOURS')
    timestamps()
  }

  stages {
    stage('Checkout / Trusted Branch Guard') {
      steps {
        checkout scm
        script {
          currentBuild.displayName = "#${env.BUILD_NUMBER} develop"
        }
        sh '''#!/usr/bin/env bash
set -euo pipefail
git fetch --no-tags origin develop
head_sha="$(git rev-parse HEAD)"
develop_sha="$(git rev-parse origin/develop)"
if [[ "$head_sha" != "$develop_sha" ]]; then
  echo "Develop pipeline requires the current origin/develop head." >&2
  echo "A newer develop commit exists; this stale build will not publish." >&2
  exit 1
fi
'''
      }
    }

    stage('Bootstrap trusted runner') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/cleanup_runner_docker.sh \
  --transient-age-hours 0 \
  --all-unused-images \
  --builder-keep 1GB \
  --min-free-gb 8
bash scripts/ci/bootstrap_jenkins_runner.sh
python3 -m venv --clear backend/venv
backend/venv/bin/pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements.txt
npm --prefix frontend ci
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"
docker build \
  --file docker/ci/pr-runner.Dockerfile \
  --tag "$PR_RUNNER_IMAGE" \
  .
'''
      }
    }

    stage('Docs checks') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/validate_command_builder.sh
bash scripts/ci/publish_wiki.sh --dry-run
bash scripts/ci/publish_pages.sh --dry-run
'''
      }
    }

    stage('Full application validation') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
artifact_dir="$WORKSPACE/.ci-develop-artifacts"
rm -rf "$artifact_dir"
mkdir -p "$artifact_dir"
host_uid="$(id -u)"
host_gid="$(id -g)"
docker run --rm \
  --network none \
  --read-only \
  --user "$host_uid:$host_gid" \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 1024 \
  --memory 8g \
  --memory-swap 8g \
  --cpus 3 \
  --tmpfs /tmp:rw,nosuid,nodev,exec,size=1g \
  --tmpfs /workspace:rw,nosuid,nodev,exec,size=3g,mode=1777 \
  --env GIT_CONFIG_COUNT=1 \
  --env GIT_CONFIG_KEY_0=safe.directory \
  --env GIT_CONFIG_VALUE_0=/workspace \
  --volume "$WORKSPACE:/source:ro" \
  --volume "$artifact_dir:/artifacts:rw" \
  --workdir /workspace \
  "$PR_RUNNER_IMAGE" \
  bash -c 'cp -R /source/. /workspace/ && CI_OUTPUT_DIR=/artifacts bash scripts/ci/run_develop_validation.sh'
cp "$artifact_dir"/*.json .
docker compose config -q
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase3-gate-report-full.json, phase3-phase1-full.json', allowEmptyArchive: true
        }
      }
    }

    stage('Publication policy and architecture plan') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py \
  --profile quick \
  --json-output > phase5-gate-report-quick.json
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-quick-*.json, phase5-gate-report-quick.json', allowEmptyArchive: true
        }
      }
    }

    stage('Acestream Engine Runtime Smoke') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/cleanup_runner_docker.sh \
  --transient-age-hours 0 \
  --all-unused-images \
  --builder-keep 1GB \
  --min-free-gb 8
export BUILDX_BUILDER=default
if ! bash scripts/ci/build_multiarch_images.sh \
  --flavor scraper-acestream \
  --platforms linux/amd64 \
  --network host; then
  echo "Smoke image build failed; pruning builder cache and retrying once"
  docker builder prune -af || true
  bash scripts/ci/build_multiarch_images.sh \
    --flavor scraper-acestream \
    --platforms linux/amd64 \
    --network host
fi
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/docker/test_acestream_runtime_smoke.py -v
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/docker/test_acexy_runtime_smoke.py -v
PYTHONPATH=backend backend/venv/bin/pytest -q \
  backend/tests/docker/test_install_acestream.py -v \
  -k "arm_oci_image_install_layout"
'''
      }
      post {
        always {
          sh '''#!/usr/bin/env bash
docker image prune -f >/dev/null 2>&1 || true
docker system df || true
'''
        }
      }
    }

    stage('Current develop guard') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
git fetch --no-tags origin develop
if [[ "$(git rev-parse HEAD)" != "$(git rev-parse origin/develop)" ]]; then
  echo "A newer develop commit arrived during validation; refusing to publish this stale revision." >&2
  exit 1
fi
'''
      }
    }

    stage('Publish develop channel') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/cleanup_runner_docker.sh \
  --transient-age-hours 0 \
  --all-unused-images \
  --builder-keep 1GB \
  --min-free-gb 8
'''
        withCredentials([usernamePassword(
          credentialsId: 'dockerhub-publish',
          usernameVariable: 'DOCKERHUB_USERNAME',
          passwordVariable: 'DOCKERHUB_TOKEN'
        )]) {
          sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/run_jenkins_release.sh --print-publish-plan --channel develop
bash scripts/ci/run_jenkins_release.sh --channel develop
'''
        }
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-channel-*.json', allowEmptyArchive: true
        }
      }
    }

    stage('Publish wiki') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'github-publish',
          usernameVariable: 'GITHUB_PUBLISH_USERNAME',
          passwordVariable: 'GITHUB_PUBLISH_TOKEN'
        )]) {
          script {
            def wikiStatus = sh(returnStatus: true, script: '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/publish_wiki.sh
''')
            if (wikiStatus == 3) {
              unstable('Wiki repository is not initialized; create its first page and rebuild.')
            } else if (wikiStatus != 0) {
              error("publish_wiki.sh failed with exit status ${wikiStatus}")
            }
          }
        }
      }
    }

    stage('Publish docs site') {
      steps {
        withCredentials([usernamePassword(
          credentialsId: 'github-publish',
          usernameVariable: 'GITHUB_PUBLISH_USERNAME',
          passwordVariable: 'GITHUB_PUBLISH_TOKEN'
        )]) {
          sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/publish_pages.sh
'''
        }
      }
    }
  }
}
