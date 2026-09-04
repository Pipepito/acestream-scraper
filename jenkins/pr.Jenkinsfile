pipeline {
  agent { label 'dorat-nuc-ci' }

  environment {
    PR_RUNNER_IMAGE = 'acestream-scraper-pr-ci:develop'
  }

  options {
    skipDefaultCheckout(true)
    disableConcurrentBuilds(abortPrevious: true)
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 45, unit: 'MINUTES')
    timestamps()
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BRANCH_NAME ?: 'pull-request'}"
          env.PR_SANDBOX_NAME = "acestream-${env.JOB_BASE_NAME}-${env.BUILD_NUMBER}"
            .replaceAll('[^A-Za-z0-9_.-]', '-')
        }
      }
    }

    stage('Branch Policy') {
      when { expression { env.CHANGE_TARGET == 'main' } }
      steps {
        script {
          if (env.CHANGE_BRANCH != 'develop') {
            error("Pull requests into main must come from develop (this one comes from '${env.CHANGE_BRANCH}'). Target develop instead; releases are cut with a develop -> main PR.")
          }
        }
      }
    }

    stage('Select trusted runner') {
      steps {
        script {
          def imageExists = sh(
            returnStatus: true,
            script: 'docker image inspect "$PR_RUNNER_IMAGE" >/dev/null 2>&1'
          ) == 0
          def runnerInputsChanged = sh(
            returnStatus: true,
            script: '''#!/usr/bin/env bash
git diff --quiet HEAD^1 -- \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile
'''
          ) != 0

          if (!imageExists || runnerInputsChanged) {
            if (env.CHANGE_FORK) {
              def reason = runnerInputsChanged ? 'changes runner dependency inputs' : 'needs a runner image that is unavailable'
              error("This fork ${reason}. Move the reviewed commit to a maintainer-owned branch so Jenkins can build a one-use candidate runner; fork code will not be allowed to build its own dependencies.")
            }

            // Bootstrap only this trusted origin PR. The candidate image is
            // build-local and removed afterwards; it can never replace the
            // shared image that is built exclusively from develop.
            env.PR_RUNNER_IMAGE = "acestream-scraper-pr-ci:candidate-${env.BUILD_NUMBER}-${env.EXECUTOR_NUMBER}"
            env.PR_RUNNER_EPHEMERAL = '1'
            sh '''#!/usr/bin/env bash
set -euo pipefail
docker build \
  --file docker/ci/pr-runner.Dockerfile \
  --tag "$PR_RUNNER_IMAGE" \
  .
'''
          }
        }
      }
    }

    stage('Credential-free PR validation') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail

host_uid="$(id -u)"
host_gid="$(id -g)"

docker run --rm --init \
  --name "$PR_SANDBOX_NAME" \
  --network none \
  --read-only \
  --user "$host_uid:$host_gid" \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --pids-limit 1024 \
  --memory 8g \
  --memory-swap 8g \
  --cpus 3 \
  --tmpfs /tmp:rw,nosuid,nodev,size=1g \
  --tmpfs /workspace:rw,nosuid,nodev,size=3g,mode=1777 \
  --env CI=true \
  --env HOME=/tmp/ci-home \
  --env PYTHONDONTWRITEBYTECODE=1 \
  --volume "$WORKSPACE:/source:ro" \
  --workdir /workspace \
  "$PR_RUNNER_IMAGE" \
  bash -c 'cp -R /source/. /workspace/ && git show HEAD^1:scripts/ci/run_pr_validation.sh > /tmp/trusted-pr-validation.sh && bash /tmp/trusted-pr-validation.sh'
'''
      }
    }
  }

  post {
    always {
      sh '''#!/usr/bin/env bash
docker rm --force "$PR_SANDBOX_NAME" >/dev/null 2>&1 || true
if [[ "${PR_RUNNER_EPHEMERAL:-0}" == "1" ]]; then
  docker image rm --force "$PR_RUNNER_IMAGE" >/dev/null 2>&1 || true
fi
'''
      deleteDir()
    }
  }
}
