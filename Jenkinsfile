pipeline {
  agent { label 'acestream-docker-multiarch' }

  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timestamps()
  }

  stages {
    stage('Validate') {
      steps {
        checkout scm
        script {
          currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BRANCH_NAME ?: 'detached'}"
        }
        sh '''#!/usr/bin/env bash
set -euo pipefail
python3 --version
node --version
docker version
docker buildx version
docker buildx use "${JENKINS_BUILDER:-acestream-builder}" || true
bash scripts/ci/run_jenkins_validation.sh
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-pr-*.json', allowEmptyArchive: true
        }
      }
    }
  }
}
