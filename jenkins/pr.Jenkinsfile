pipeline {
  agent { label 'dorat-nuc-ci' }

  environment {
    PR_RUNNER_REPOSITORY = 'acestream-scraper-pr-ci'
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
          env.PR_VALIDATION_REF = env.CHANGE_FORK \
            ? "refs/remotes/origin/${env.CHANGE_TARGET}" \
            : 'HEAD'
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

    stage('Build isolated trusted runner') {
      steps {
        script {
          def runnerInputsChanged = sh(
            returnStatus: true,
            script: '''#!/usr/bin/env bash
git diff --quiet "refs/remotes/origin/${CHANGE_TARGET}"...HEAD -- \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile
'''
          ) != 0

          if (env.CHANGE_FORK && runnerInputsChanged) {
            error('This fork changes dependency or runner-image inputs. Those inputs can execute code during installation, so an automatic fork build will not install them with network access. Move the reviewed commit to a maintainer-owned branch to validate the dependency change.')
          }

          // Every PR gets a disposable runner. For forks the build context is
          // exported from the trusted target ref, never from contributor files.
          // This removes the mutable :develop image as an availability and
          // freshness dependency without allowing a fork to install packages.
          def runnerSha = sh(
            returnStdout: true,
            script: 'git rev-parse "$PR_VALIDATION_REF"'
          ).trim()
          env.PR_RUNNER_IMAGE = "${env.PR_RUNNER_REPOSITORY}:pr-${env.BUILD_NUMBER}-${env.EXECUTOR_NUMBER}-${runnerSha.take(12)}"
          env.PR_RUNNER_EPHEMERAL = '1'
          sh '''#!/usr/bin/env bash
set -euo pipefail
trusted_builder="$WORKSPACE@tmp/build-pr-runner-${BUILD_NUMBER}.sh"
git show "${PR_VALIDATION_REF}:scripts/ci/build_pr_runner.sh" > "$trusted_builder"
bash "$trusted_builder" \
  --source "$WORKSPACE" \
  --ref "$PR_VALIDATION_REF" \
  --tag "$PR_RUNNER_IMAGE"
'''
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
  --tmpfs /tmp:rw,nosuid,nodev,exec,size=1g \
  --tmpfs /workspace:rw,nosuid,nodev,exec,size=3g,mode=1777 \
  --env CI=true \
  --env HOME=/tmp/ci-home \
  --env PYTHONDONTWRITEBYTECODE=1 \
  --env GIT_CONFIG_COUNT=1 \
  --env GIT_CONFIG_KEY_0=safe.directory \
  --env GIT_CONFIG_VALUE_0=/workspace \
  --env "PR_VALIDATION_REF=$PR_VALIDATION_REF" \
  --volume "$WORKSPACE:/source:ro" \
  --workdir /workspace \
  "$PR_RUNNER_IMAGE" \
  bash -c 'cp -R /source/. /workspace/ && trusted_script=/workspace/scripts/ci/.jenkins-trusted-pr-validation.sh && rm -f "$trusted_script" && git show "${PR_VALIDATION_REF}:scripts/ci/run_pr_validation.sh" > "$trusted_script" && bash "$trusted_script"'
'''
      }
    }

    stage('Isolated architecture runtime contracts') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
trusted_arch_runner="$WORKSPACE@tmp/run-pr-arch-contracts-${BUILD_NUMBER}.sh"
git show "${PR_VALIDATION_REF}:scripts/ci/run_pr_arch_contracts.sh" > "$trusted_arch_runner"
bash "$trusted_arch_runner" \
  --source "$WORKSPACE" \
  --validation-ref "$PR_VALIDATION_REF" \
  --name-prefix "$PR_SANDBOX_NAME"
'''
      }
    }
  }

  post {
    always {
      sh '''#!/usr/bin/env bash
docker rm --force "$PR_SANDBOX_NAME" >/dev/null 2>&1 || true
for platform in linux-amd64 linux-arm64 linux-arm-v7; do
  docker rm --force "${PR_SANDBOX_NAME}-${platform}" >/dev/null 2>&1 || true
done
if [[ "${PR_RUNNER_EPHEMERAL:-0}" == "1" ]]; then
  docker image rm --force "$PR_RUNNER_IMAGE" >/dev/null 2>&1 || true
fi
'''
      deleteDir()
    }
  }
}
