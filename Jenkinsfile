pipeline {
  agent { label 'dorat-nuc-ci' }

  environment {
    // WARP is opt-in in bootstrap_jenkins_runner.sh (the engine archives and
    // the Acexy source are vendored); keep it on the runner for any remaining
    // geo-blocked fetch. Anonymous GitHub clones through its exit get refused,
    // which is why nothing in the Dockerfile may depend on one.
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

    stage('Branch Policy') {
      // Release PRs are the only way into main: main only accepts PRs whose
      // head is develop. Feature work targets develop.
      when { expression { env.CHANGE_TARGET == 'main' } }
      steps {
        script {
          if (env.CHANGE_BRANCH != 'develop') {
            error("Pull requests into main must come from develop (this one comes from '${env.CHANGE_BRANCH}'). Target develop instead; releases are cut with a develop -> main PR.")
          }
        }
      }
    }

    stage('Docs checks') {
      // The Docker command builder (docs/index.html, published to the
      // gh-pages branch for GitHub Pages) must not drift from the runtime
      // contract, the wiki/ folder must render into a valid wiki page set,
      // and the Pages payload must assemble.
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/validate_command_builder.sh
bash scripts/ci/publish_wiki.sh --dry-run
bash scripts/ci/publish_pages.sh --dry-run
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

    stage('cutover-quick') {
      // Phase 3 cutover gate: canonical quick backend/frontend suite
      // (run_cutover_required_checks.sh -> run_v2_test_suite.sh), legacy-path
      // guard and the phase-1 parity baseline, with a JSON report. This is
      // the single place the unit/contract suite runs in the PR job, and it
      // runs before the docker smoke so test failures surface in ~2 min.
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
backend/venv/bin/python scripts/phase_gates/phase3_gate_runner.py --profile quick --json-output > phase3-gate-report-quick.json
'''
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase3-gate-report-quick.json, phase3-phase1-quick.json', allowEmptyArchive: true
        }
      }
    }

    stage('Required Cutover Checks') {
      // Four-flavor multi-arch matrix: dry-run build plan + manifest
      // verification per flavor (seconds). The engine sources each platform
      // resolves to are printed by build_multiarch_images.sh.
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper --result-file phase5-build-result-pr-scraper.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper.json --flavor scraper
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --result-file phase5-build-result-pr-scraper-acestream.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream.json --flavor scraper-acestream
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acexy --result-file phase5-build-result-pr-scraper-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acexy.json --flavor scraper-acexy
bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream-acexy --result-file phase5-build-result-pr-scraper-acestream-acexy.json
bash scripts/ci/verify_multiarch_manifest.sh --result-file phase5-build-result-pr-scraper-acestream-acexy.json --flavor scraper-acestream-acexy
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
# network (the docker-container driver's isolated network does not); the
# engine archives are vendored, so this is only load-bearing for pins that
# are not vendored yet.
export BUILDX_BUILDER=default
# Warm the build cache for the amd64 scraper-acestream image WITHOUT
# exporting it (cache-only output): the pytest below builds the same image
# through the same script and is the one that --load's it, so no extra
# multi-GB image is created. The self-hosted runner's build cache can rot
# ("failed to prepare extraction snapshot ... parent snapshot ... does not
# exist"); prune the corrupted cache and retry once before failing.
if ! bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --network host; then
  echo "Smoke image build failed; pruning builder cache and retrying once"
  docker builder prune -af || true
  bash scripts/ci/build_multiarch_images.sh --flavor scraper-acestream --platforms linux/amd64 --network host
fi
# The engine boots and answers on :6878, get_version matches the manifest,
# and the image's own healthcheck passes (amd64 here; arm64 when the host is arm64).
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
# The acexy flavor must ship the real upstream proxy, not the build fixture.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v
# ARM engine flavors: the Android engine payload + bionic runtime must install
# cleanly for both ARM platforms (QEMU build, no engine execution — the
# 32-bit bionic engine cannot run under qemu-user; arm64 runtime smoke runs on
# arm64 hosts via the same pytest).
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k "arm_oci_image_install_layout"
# The web player's static ffmpeg must build for every platform and run on it.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_ffmpeg_vendor.py backend/tests/docker/test_ffmpeg_build.py -v
'''
      }
      post {
        always {
          // The pytest runs remove their own images; trim dangling layers left
          // by the builds so the runner's small disk stays usable.
          sh '''#!/usr/bin/env bash
docker image prune -f >/dev/null 2>&1 || true
docker system df || true
'''
        }
      }
    }

    stage('Multi-Arch Quick Profile') {
      // Phase 5 gate (quick): publish-tag guard, the four-flavor dry-run
      // matrix + manifest checks and the arch smoke plan, with a JSON report.
      steps {
        sh '''#!/usr/bin/env bash
set -euo pipefail
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

    stage('Publish develop channel') {
      // Every validated build of develop's head publishes the floating
      // pre-release channel tags (pipepito/acestream-scraper:develop and
      // :develop-<flavor>) — never a version tag, never :latest. Runs for the
      // develop branch job and for a PR whose head is develop (the release PR),
      // since the branch job is suppressed while such a PR is open. PR builds
      // from any other branch never reach the credential.
      when {
        anyOf {
          branch 'develop'
          expression { env.CHANGE_BRANCH == 'develop' }
        }
      }
      steps {
        script {
          try {
            withCredentials([usernamePassword(credentialsId: 'dockerhub-publish', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
              sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/run_jenkins_release.sh --print-publish-plan --channel develop
bash scripts/ci/run_jenkins_release.sh --channel develop
'''
            }
          } catch (Exception e) {
            // Creating the credential is an operator step; a missing one must
            // not fail validation. Anything else (build/push failure) is real.
            def text = e.toString()
            if (text.contains('Could not find credentials') && text.contains('dockerhub-publish')) {
              unstable("develop channel not published: Jenkins credential 'dockerhub-publish' is missing")
            } else {
              throw e
            }
          }
        }
      }
      post {
        always {
          archiveArtifacts artifacts: 'phase5-build-result-channel-*.json', allowEmptyArchive: true
        }
      }
    }

    stage('Publish wiki') {
      // Every validated build of develop mirrors wiki/ to the GitHub wiki
      // repository (<repo>.wiki.git) with a plain git push from this runner —
      // no GitHub Actions involved. Gated like 'Publish develop channel':
      // the develop branch job, or a PR whose head is develop (the release
      // PR), since the branch job is suppressed while such a PR is open.
      when {
        anyOf {
          branch 'develop'
          expression { env.CHANGE_BRANCH == 'develop' }
        }
      }
      steps {
        script {
          try {
            withCredentials([usernamePassword(credentialsId: 'github-publish', usernameVariable: 'GITHUB_PUBLISH_USERNAME', passwordVariable: 'GITHUB_PUBLISH_TOKEN')]) {
              def wikiStatus = sh(returnStatus: true, script: '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/publish_wiki.sh
''')
              if (wikiStatus == 3) {
                // GitHub only creates <repo>.wiki.git once a page has been saved
                // in the web UI; that is a one-time operator step, not a build error.
                unstable("wiki not published: the GitHub wiki repository is not initialised yet (create any page in the Wiki tab once, then rebuild)")
              } else if (wikiStatus != 0) {
                error("publish_wiki.sh failed with exit status ${wikiStatus}")
              }
            }
          } catch (Exception e) {
            def text = e.toString()
            if (text.contains('Could not find credentials') && text.contains('github-publish')) {
              unstable("wiki not published: Jenkins credential 'github-publish' is missing")
            } else {
              throw e
            }
          }
        }
      }
    }

    stage('Publish docs site') {
      // Push the Docker command builder (docs/index.html + docs/builder/) to
      // the gh-pages branch; GitHub Pages serves that branch ("Deploy from a
      // branch": gh-pages, / root), so a validated develop build is the
      // deployment. Same gating and credential handling as 'Publish wiki'.
      when {
        anyOf {
          branch 'develop'
          expression { env.CHANGE_BRANCH == 'develop' }
        }
      }
      steps {
        script {
          try {
            withCredentials([usernamePassword(credentialsId: 'github-publish', usernameVariable: 'GITHUB_PUBLISH_USERNAME', passwordVariable: 'GITHUB_PUBLISH_TOKEN')]) {
              sh '''#!/usr/bin/env bash
set -euo pipefail
bash scripts/ci/publish_pages.sh
'''
            }
          } catch (Exception e) {
            def text = e.toString()
            if (text.contains('Could not find credentials') && text.contains('github-publish')) {
              unstable("docs site not published: Jenkins credential 'github-publish' is missing")
            } else {
              throw e
            }
          }
        }
      }
    }
  }
}
