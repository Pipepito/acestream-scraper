// Administrator-managed inline Pipeline, never Pipeline-from-PR-SCM.
// The preparer pins one Jenkins approver and one reviewed policy commit.
pipeline {
  agent none
  environment {
    TRUSTED_POLICY_SHA = '__POLICY_SHA__'
  }
  options {
    skipDefaultCheckout(true)
    buildDiscarder(logRotator(numToKeepStr: '20'))
    timeout(time: 7, unit: 'DAYS')
    timestamps()
  }
  parameters {
    string(name: 'PR_NUMBER', defaultValue: '', description: 'Pull request number')
    string(name: 'HEAD_SHA', defaultValue: '', description: 'Exact reviewed PR head (40 hex characters)')
    string(name: 'BASE_SHA', defaultValue: '', description: 'Exact protected target commit')
    choice(name: 'TARGET_BRANCH', choices: ['develop', 'main'], description: 'Protected target')
  }
  stages {
    stage('Owner approval') {
      steps {
        script {
          if (!(params.PR_NUMBER ==~ /[1-9][0-9]*/) ||
              !(params.HEAD_SHA ==~ /[0-9a-f]{40}/) ||
              !(params.BASE_SHA ==~ /[0-9a-f]{40}/) ||
              !(params.TARGET_BRANCH in ['develop', 'main']) ||
              '__PR_APPROVER__'.startsWith('__') ||
              !(env.TRUSTED_POLICY_SHA ==~ /[0-9a-f]{40}/)) {
            error('Invalid revision or missing administrator-configured approver.')
          }
          // No executor or Docker lock is held while waiting. Approval is for
          // these immutable parameters, never a moving branch or a PR label.
          input message: "Allow host builds for https://github.com/Pipepito/acestream-scraper/pull/${params.PR_NUMBER}? Review head ${params.HEAD_SHA} against ${params.TARGET_BRANCH} at ${params.BASE_SHA}. This permits proposed build/dependency code to run on the build host.",
            ok: 'Approve this revision', submitter: '__PR_APPROVER__'
        }
      }
    }
    stage('Serialized Docker work') {
      // Stage options acquire the FIFO lock before allocating an executor.
      options {
        timeout(time: 4, unit: 'HOURS')
        lock(resource: 'acestream-scraper-nuc-docker', reason: 'Owner-approved PR image validation')
      }
      agent { label 'dorat-nuc-ci' }
      stages {
        stage('Revalidate approved revision') {
          steps {
            deleteDir()
            sh '''#!/usr/bin/env bash
set -euo pipefail
mkdir source
git -C source init -q
git -C source remote add origin https://github.com/Pipepito/acestream-scraper.git
git -C source fetch --no-tags origin "+refs/heads/$TARGET_BRANCH:refs/remotes/origin/approved-target" "+refs/pull/$PR_NUMBER/head:refs/remotes/origin/approved-head"
test "$(git -C source rev-parse refs/remotes/origin/approved-target)" = "$BASE_SHA"
test "$(git -C source rev-parse refs/remotes/origin/approved-head)" = "$HEAD_SHA"
# The administrator pins reviewed host policy in the managed definition.
# No PR author, branch, label or build parameter may choose this revision.
git -C source fetch --no-tags origin "$TRUSTED_POLICY_SHA"
policy_ref=$(git -C source rev-parse "${TRUSTED_POLICY_SHA}^{commit}")
test "$policy_ref" = "$TRUSTED_POLICY_SHA"
mkdir trusted
for name in verify_pr_revision.py run_approved_pr_validation.sh build_pr_runner.sh bootstrap_jenkins_runner.sh validate_pr_images.sh; do
  mode=$(git -C source ls-tree "$policy_ref" -- "scripts/ci/$name" | cut -d ' ' -f 1)
  [[ "$mode" = 100644 || "$mode" = 100755 ]]
  git -C source show "$policy_ref:scripts/ci/$name" > "trusted/$name"
done
python3 -I trusted/verify_pr_revision.py --pr "$PR_NUMBER" --head "$HEAD_SHA" --base "$BASE_SHA" --target "$TARGET_BRANCH"
git -C source checkout --detach "$HEAD_SHA"
'''
          }
        }
        stage('Validate approved application and images') {
          steps {
            sh '''#!/usr/bin/env bash
set -euo pipefail
# Recheck after approval and lock waiting, immediately before proposed code.
python3 -I trusted/verify_pr_revision.py --pr "$PR_NUMBER" --head "$HEAD_SHA" --base "$BASE_SHA" --target "$TARGET_BRANCH"
bash trusted/run_approved_pr_validation.sh "$WORKSPACE/source" "$WORKSPACE/trusted"
python3 -I trusted/verify_pr_revision.py --pr "$PR_NUMBER" --head "$HEAD_SHA" --base "$BASE_SHA" --target "$TARGET_BRANCH"
'''
          }
        }
      }
      post {
        always {
          sh '''#!/usr/bin/env bash
if [[ -n "${BUILD_NUMBER:-}" ]]; then
  docker rm --force "acestream-approved-pr-${BUILD_NUMBER}" >/dev/null 2>&1 || true
fi
'''
          deleteDir()
        }
      }
    }
  }
}
