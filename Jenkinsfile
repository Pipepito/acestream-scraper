pipeline {
  agent { label 'dorat-nuc-ci' }

  environment {
    // WARP is opt-in in bootstrap_jenkins_runner.sh (the engine archives are
    // vendored); keep it on the runner for any remaining geo-blocked fetch.
    JENKINS_ENABLE_WARP = '1'
  }

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
# Reclaim runner disk before doing anything heavy (build #29 died with
# ENOSPC): drop every transient CI image left by earlier runs, dangling
# layers, unused images older than a day, and cap the BuildKit cache. The
# multibranch job no longer builds a branch that also has a PR, so no
# sibling build is in flight and a zero-age sweep is safe.
bash scripts/ci/cleanup_runner_docker.sh --transient-age-hours 0
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
# BUILD_TAG (jenkins-<job path>-<number>) is unique across the PR job and
# the branch job, which run the same commit concurrently and share the
# docker daemon — BUILD_NUMBER alone collides across them. Sanitize it to
# docker-tag characters.
SMOKE_TAG="acestream-scraper:smoke-$(printf '%s' "${BUILD_TAG}" | tr -cs 'a-zA-Z0-9_.-' '-' | cut -c1-100)"
echo "$SMOKE_TAG" > .smoke-tag
# The self-hosted runner's build cache can rot ("failed to prepare
# extraction snapshot ... parent snapshot ... does not exist" at the image
# export step). Prune the corrupted cache and retry once before failing.
# scraper-acestream now resolves to amd64 + arm64 + arm/v7; --load needs a
# single platform, so pin the runner's native one here. The engine archives
# are vendored in docker/vendor, so this no longer depends on WARP egress.
if ! bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --load --network host --tag "$SMOKE_TAG"; then
  echo "Smoke image build failed; pruning builder cache and retrying once"
  docker builder prune -af || true
  bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --load --network host --tag "$SMOKE_TAG"
fi
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
# The acexy flavor must ship the real upstream proxy, not the build fixture.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v
# ARM engine flavors: the Android engine payload + bionic runtime must install
# cleanly for both ARM platforms (QEMU build, no engine execution — the
# 32-bit bionic engine cannot run under qemu-user; arm64 runtime smoke runs on
# arm64 hosts via the same pytest).
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k "android_apk_install_layout"
'''
      }
      post {
        always {
          sh '''#!/usr/bin/env bash
# The smoke image is multi-GB (vendored engine payloads); leaking one per
# build filled the runner's disk (build #29 ENOSPC). Always remove this
# build's tag and trim dangling layers.
if [ -f .smoke-tag ]; then
  docker image rm -f "$(cat .smoke-tag)" >/dev/null 2>&1 || true
  rm -f .smoke-tag
fi
docker image prune -f >/dev/null 2>&1 || true
'''
        }
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
