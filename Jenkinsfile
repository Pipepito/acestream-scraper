pipeline {
  agent { label 'generic-gh-builder' }

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
bash scripts/ci/bootstrap_jenkins_runner.sh
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"
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
