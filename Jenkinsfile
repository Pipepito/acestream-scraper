pipeline {
  agent { label 'dorat-nuc-ci' }

  options {
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timestamps()
  }

  stages {
    stage('Checkout / Bootstrap') {
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
npm --prefix frontend ci
docker buildx use "${JENKINS_BUILDER:-acestream-builder}"
'''
      }
    }

    stage('Phase 1 Safety Gates') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
backend/venv/bin/python scripts/phase_gates/phase1_gate_runner.py --profile quick --json-output > phase1-gate-report.json
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase1-gate-report.json', allowEmptyArchive: true
        }
      }
    }

    stage('Required Cutover Checks') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/run_v2_test_suite.sh --profile quick
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper --result-file phase5-build-result-pr-scraper.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper.json --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --result-file phase5-build-result-pr-scraper-acestream.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream.json --flavor scraper-acestream
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy --result-file phase5-build-result-pr-scraper-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acexy.json --flavor scraper-acexy
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy --result-file phase5-build-result-pr-scraper-acestream-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream-acexy.json --flavor scraper-acestream-acexy
bash scripts/ci/assert_no_legacy_paths.sh --strict
bash scripts/ci/run_cutover_required_checks.sh --profile quick
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-pr-*.json', allowEmptyArchive: true
        }
      }
    }

    stage('Acestream Engine Runtime Smoke') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
# Pin buildx to the docker-driver builder so RUN steps inherit the host's
# WARP-routed network. The default JENKINS_BUILDER (acestream-builder) uses
# the docker-container driver whose isolated buildkit network does NOT
# inherit host routes, causing curl to download.acestream.media to fail.
export BUILDX_BUILDER=default
# The self-hosted runner's build cache can rot ("failed to prepare
# extraction snapshot ... parent snapshot ... does not exist" at the image
# export step). Prune the corrupted cache and retry once before failing.
if ! bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --load --network host --tag acestream-scraper:smoke; then
  echo "Smoke image build failed; pruning builder cache and retrying once"
  docker builder prune -af || true
  bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --load --network host --tag acestream-scraper:smoke
fi
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
'''
      }
    }

    stage('cutover-quick') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
backend/venv/bin/python scripts/phase_gates/phase3_gate_runner.py --profile quick --json-output > phase3-gate-report-quick.json
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase3-gate-report-quick.json', allowEmptyArchive: true
        }
      }
    }

    stage('Multi-Arch Quick Profile') {
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
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
