pipeline {
  agent { label 'generic-gh-builder' }

  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timestamps()
  }

  parameters {
    booleanParam(name: 'CONFIRM_RELEASE', defaultValue: false, description: 'Required to run the release pipeline.')
    booleanParam(name: 'DRY_RUN', defaultValue: true, description: 'Run preflight only without Docker Hub credentials.')
  }

  stages {
    stage('Release') {
      steps {
        checkout scm
        script {
          if (env.BRANCH_NAME && env.BRANCH_NAME != 'main') {
            error("Release pipeline only runs from main; current branch is '${env.BRANCH_NAME}'.")
          }

          if (!params.CONFIRM_RELEASE) {
            error('CONFIRM_RELEASE must be enabled to run the release pipeline.')
          }

          currentBuild.displayName = "#${env.BUILD_NUMBER} release ${params.DRY_RUN ? 'dry-run' : 'publish'}"
        }
        sh '''#!/usr/bin/env bash
set -euo pipefail
git fetch --no-tags origin main
head_sha="$(git rev-parse HEAD)"
origin_main_sha="$(git rev-parse origin/main)"

if [[ "$head_sha" != "$origin_main_sha" ]]; then
  printf 'Release pipeline requires the checked-out commit to match origin/main.\n' >&2
  printf 'Current HEAD: %s\n' "$head_sha" >&2
  printf 'origin/main: %s\n' "$origin_main_sha" >&2
  printf 'Merge or push the intended release commit to main, then rerun this pipeline.\n' >&2
  exit 1
fi

bash scripts/ci/bootstrap_jenkins_runner.sh
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"
'''
        script {
          if (params.DRY_RUN) {
            sh 'bash scripts/ci/run_jenkins_release.sh --dry-run'
          } else {
            withCredentials([
              usernamePassword(
                credentialsId: 'dockerhub-publish',
                usernameVariable: 'DOCKERHUB_USERNAME',
                passwordVariable: 'DOCKERHUB_TOKEN'
              )
            ]) {
              sh 'bash scripts/ci/run_jenkins_release.sh'
            }
          }
        }
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-release-*.json', allowEmptyArchive: true
          archiveArtifacts artifacts: 'phase5-build-result-release-metadata.json', allowEmptyArchive: true
        }
      }
    }
  }
}
