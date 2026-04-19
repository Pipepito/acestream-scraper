pipeline {
  agent { label 'generic-gh-builder' }

  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timestamps()
  }

  stages {
    stage('Multi-Arch Quick Gates') {
      steps {
        checkout scm
        script {
          currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BRANCH_NAME ?: 'detached'}"
        }
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/bootstrap_jenkins_runner.sh
python3 -m venv --clear backend/venv
backend/venv/bin/pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements.txt
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"

bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper --result-file phase5-build-result-quick-scraper.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper.json --flavor scraper

bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --result-file phase5-build-result-quick-scraper-acestream.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acestream.json --flavor scraper-acestream

bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy --result-file phase5-build-result-quick-scraper-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acexy.json --flavor scraper-acexy

bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy --result-file phase5-build-result-quick-scraper-acestream-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-quick-scraper-acestream-acexy.json --flavor scraper-acestream-acexy

bash scripts/ci/phase5_arch_smoke.sh --dry-run --platforms linux/arm/v7,linux/arm64
backend/venv/bin/python scripts/phase_gates/phase5_gate_runner.py --profile quick --json-output > phase5-gate-report-quick.json
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-quick-*.json', allowEmptyArchive: true
          archiveArtifacts artifacts: 'phase5-gate-report-quick.json', allowEmptyArchive: true
        }
      }
    }
  }
}
