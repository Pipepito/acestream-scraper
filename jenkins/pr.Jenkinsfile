// Administrator-managed pipeline. Never load the PR copy.
// Render __PRIVILEGED_JOB__ with prepare_jenkins_collaboration.py.
pipeline {
  agent none
  environment {
    TRUSTED_POLICY_SHA = '__POLICY_SHA__'
  }

  options {
    skipDefaultCheckout(true)
    // Multiple revisions may wait for approval; Docker work is still FIFO.
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 7, unit: 'DAYS')
    timestamps()
  }

  stages {
    stage('Serialized Docker work') {
      // Stage options acquire the FIFO lock before allocating an executor.
      options {
        timeout(time: 4, unit: 'HOURS')
        lock(resource: 'acestream-scraper-nuc-docker', reason: 'Exclusive Docker and BuildKit access on dorat-nuc-ci')
      }
      agent { label 'dorat-nuc-ci' }
      stages {
        stage('Pull request validation') {
          when { changeRequest() }
          stages {
            stage('Checkout') {
              steps {
                checkout scm
                script {
                  currentBuild.displayName = "#${env.BUILD_NUMBER} ${env.BRANCH_NAME ?: 'pull-request'}"
                  env.PR_SANDBOX_NAME = "acestream-${env.JOB_BASE_NAME}-${env.BUILD_NUMBER}"
                    .replaceAll('[^A-Za-z0-9_.-]', '-')
                  if (!(env.CHANGE_ID ==~ /[1-9][0-9]*/) ||
                      !(env.CHANGE_TARGET in ['develop', 'main'])) {
                    error('Only numbered PRs targeting develop or main are accepted.')
                  }
                  if ('__PRIVILEGED_JOB__'.startsWith('__')) {
                    error('Install the administrator-managed PR pipeline before enabling builds.')
                  }
                  env.PR_NUMBER = env.CHANGE_ID
                  env.PR_TARGET = env.CHANGE_TARGET
                  env.PR_HEAD_SHA = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                  // Origin branches have exactly the same trust as forks.
                  sh 'git fetch --no-tags origin "+refs/heads/$PR_TARGET:refs/remotes/origin/$PR_TARGET" "+refs/pull/$PR_NUMBER/head:refs/remotes/origin/validated-pr"'
                  env.PR_VALIDATION_REF = sh(returnStdout: true,
                    script: 'git rev-parse "refs/remotes/origin/$PR_TARGET"').trim()
                  sh 'test "$PR_HEAD_SHA" = "$(git rev-parse refs/remotes/origin/validated-pr)"'
                }
              }
            }

            stage('Branch Policy') {
              when { expression { env.CHANGE_TARGET == 'main' } }
              steps {
                script {
                  if (env.CHANGE_BRANCH != 'develop' || env.CHANGE_FORK) {
                    error("Pull requests into main must come from develop (this one comes from '${env.CHANGE_BRANCH}'). Target develop instead; releases are cut with a develop -> main PR.")
                  }
                }
              }
            }

            stage('Select affected work') {
              steps {
                script {
                  // Always use the target's selector, even for origin PRs. A proposed
                  // skip-rule change cannot exempt itself from the application gate.
                  def selection = sh(returnStdout: true, script: '''#!/usr/bin/env bash
set -euo pipefail
selector="$WORKSPACE@tmp/classify-changes-${BUILD_NUMBER}.py"
if git show "${PR_VALIDATION_REF}:scripts/ci/classify_changes.py" > "$selector" 2>/dev/null; then
  python3 -I "$selector" --repo "$WORKSPACE" --base "$PR_VALIDATION_REF" --pull-request
else
  # First rollout: the target does not have a trusted selector yet.
  echo 'CI_APPLICATION=true'
fi
''').trim()
                  // env is a Pipeline object, not a Map: bracket assignment invokes
                  // an unapproved Groovy putAt. Use its sandbox-approved properties.
                  // Only an explicit false disables work; missing flags keep full scope.
                  def selected = selection.readLines()
                  env.CI_APPLICATION = selected.contains('CI_APPLICATION=false') ? 'false' : 'true'
                  env.CI_WIKI = selected.contains('CI_WIKI=false') ? 'false' : 'true'
                  env.CI_PAGES = selected.contains('CI_PAGES=false') ? 'false' : 'true'
                  env.CI_DOCKERHUB = selected.contains('CI_DOCKERHUB=false') ? 'false' : 'true'
                  env.CI_METADATA = selected.contains('CI_METADATA=false') ? 'false' : 'true'
                  echo selection
                  currentBuild.description = env.CI_APPLICATION == 'true' ? 'Full application validation' : 'Documentation/metadata checks; application unchanged'
                }
              }
            }

            stage('Repository metadata validation') {
              when { expression { env.CI_METADATA != 'false' } }
              steps {
                // All host-side policy comes from the pinned protected target.
                sh '''#!/usr/bin/env bash
set -euo pipefail
trusted_dir="$(mktemp -d "$WORKSPACE@tmp/metadata-checks.XXXXXX")"
trap 'rm -rf "$trusted_dir"' EXIT
metadata_ref="$PR_VALIDATION_REF"
# Older release targets can predate metadata validation. Only an explicitly
# administrator-pinned policy may supply the missing validator, never HEAD.
if ! git cat-file -e "$metadata_ref:scripts/ci/validate_repository_metadata.sh" 2>/dev/null; then
  [[ "$TRUSTED_POLICY_SHA" =~ ^[0-9a-f]{40}$ ]]
  git fetch --no-tags origin "$TRUSTED_POLICY_SHA"
  test "$(git rev-parse "${TRUSTED_POLICY_SHA}^{commit}")" = "$TRUSTED_POLICY_SHA"
  metadata_ref="$TRUSTED_POLICY_SHA"
fi
mkdir -p "$trusted_dir/metadata-tools"
git show "$metadata_ref:scripts/ci/validate_repository_metadata.sh" > "$trusted_dir/validate_repository_metadata.sh"
for file in package.json package-lock.json validate.cjs test.cjs assignment-workflow.json; do
  git show "$metadata_ref:scripts/ci/metadata-tools/$file" > "$trusted_dir/metadata-tools/$file"
done
bash "$trusted_dir/validate_repository_metadata.sh" "$WORKSPACE"
'''
              }
            }

            stage('Documentation-only validation') {
              when { expression { env.CI_APPLICATION == 'false' } }
              steps {
                // Only target-owned validators run on the host. Proposed Markdown,
                // JSON and JavaScript are read as data (node --check never executes it).
                sh '''#!/usr/bin/env bash
set -euo pipefail
trusted_dir="$(mktemp -d "$WORKSPACE@tmp/docs-checks.XXXXXX")"
trap 'rm -rf "$trusted_dir"' EXIT
for validator in validate_documentation.py validate_docker_docs_contract.py validate_command_builder.sh; do
  git show "${PR_VALIDATION_REF}:scripts/ci/$validator" > "$trusted_dir/$validator"
done
export DOCS_CHECK_ROOT="$WORKSPACE"
python3 -I "$trusted_dir/validate_documentation.py" --root "$WORKSPACE"
python3 -I "$trusted_dir/validate_docker_docs_contract.py"
bash "$trusted_dir/validate_command_builder.sh"
'''
              }
            }

            stage('Build isolated trusted runner') {
              when { expression { env.CI_APPLICATION != 'false' } }
              steps {
                script {
                  def runnerInputsChanged = sh(
                    returnStatus: true,
                    script: '''#!/usr/bin/env bash
git diff --no-ext-diff --no-textconv --quiet "$PR_VALIDATION_REF" HEAD -- \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile \
  docker/manifests/ffmpeg.json \
  docker/scripts/build-ffmpeg.sh \
  scripts/ci/build_pr_runner.sh \
  scripts/ci/cleanup_runner_docker.sh \
  scripts/ci/docker_lifecycle.py
'''
                  ) != 0

                  env.PR_DEPENDENCIES_CHANGED = runnerInputsChanged ? 'true' : 'false'
                  if (runnerInputsChanged) {
                    echo 'Dependency changes require owner-approved validation. Automatic checks will not install them with network access.'
                  }

                  // The trusted ref selects dependency inputs. Matching inputs share
                  // a verified cached image; every validation still gets a fresh container.
                  sh '''#!/usr/bin/env bash
set -euo pipefail
trusted_builder="$WORKSPACE@tmp/build-pr-runner-${BUILD_NUMBER}.sh"
git show "${PR_VALIDATION_REF}:scripts/ci/build_pr_runner.sh" > "$trusted_builder"
bash "$trusted_builder" \
  --source "$WORKSPACE" \
  --ref "$PR_VALIDATION_REF" \
  --image-file "$WORKSPACE@tmp/runner-image-${BUILD_NUMBER}"
'''
                  env.PR_RUNNER_IMAGE = readFile("${env.WORKSPACE}@tmp/runner-image-${env.BUILD_NUMBER}").trim()
                }
              }
            }

            stage('Credential-free PR validation') {
              when { expression { env.CI_APPLICATION != 'false' && env.PR_DEPENDENCIES_CHANGED != 'true' } }
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
              when { expression { env.CI_APPLICATION != 'false' } }
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
        }
        stage('Ordinary branch skipped') {
          when { not { changeRequest() } }
          steps {
            echo 'This job validates pull requests only. Branch publication belongs to the develop and release jobs.'
            script { currentBuild.description = 'Skipped: ordinary branch in PR-only job' }
          }
        }
      }

      post {
        always {
          sh '''#!/usr/bin/env bash
if [[ -n "${CHANGE_ID:-}" && "${CI_APPLICATION:-true}" != "false" ]]; then
docker rm --force "$PR_SANDBOX_NAME" >/dev/null 2>&1 || true
for platform in linux-amd64 linux-arm64 linux-arm-v7; do
  docker rm --force "${PR_SANDBOX_NAME}-${platform}" >/dev/null 2>&1 || true
done
fi
'''
          deleteDir()
        }
      }
    }
    stage('Owner-approved validation') {
      when { expression { env.CHANGE_ID && env.CI_APPLICATION != 'false' } }
      steps {
        // Wait outside the Docker lock. PR Validation stays pending until the
        // owner approves this exact revision and the privileged child succeeds.
        build job: '__PRIVILEGED_JOB__', wait: true, propagate: true, parameters: [
          string(name: 'PR_NUMBER', value: env.PR_NUMBER),
          string(name: 'HEAD_SHA', value: env.PR_HEAD_SHA),
          string(name: 'BASE_SHA', value: env.PR_VALIDATION_REF),
          string(name: 'TARGET_BRANCH', value: env.PR_TARGET)
        ]
      }
    }

  }
}
