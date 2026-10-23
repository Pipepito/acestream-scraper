// Administrator-managed inline Pipeline, never Pipeline-from-PR-SCM.
// The preparer pins the approver, policy commit and discovery App credential.
def validateApprovedMetadata(data) {
  if (!(data instanceof Map) || data.number?.toString() != params.PR_NUMBER ||
      data.state != 'open' || data.merged != false ||
      data.base?.repo?.full_name != 'Pipepito/acestream-scraper' ||
      data.base?.ref != params.TARGET_BRANCH || data.base?.sha != params.BASE_SHA ||
      data.head?.sha != params.HEAD_SHA ||
      (params.TARGET_BRANCH == 'main' &&
       (data.head?.ref != 'develop' || data.head?.repo?.full_name != 'Pipepito/acestream-scraper'))) {
    error('PR is closed or its approved identity changed. Request fresh validation and approval.')
  }
}

def verifyApprovedRevision() {
  // Called only in agent-none stages. HTTP Request uses the controller when no
  // Launcher is in scope; putting this inside node would send auth to the agent.
  def response = httpRequest(
    url: "https://api.github.com/repos/Pipepito/acestream-scraper/pulls/${params.PR_NUMBER}",
    httpMode: 'GET', authentication: '__PR_METADATA_CREDENTIAL__',
    acceptType: 'APPLICATION_JSON', validResponseCodes: '200', timeout: 20,
    quiet: true, consoleLogResponseBody: false, responseHandle: 'STRING')
  if (response.content.length() > 1048576) {
    error('PR metadata exceeds the response limit.')
  }
  validateApprovedMetadata(readJSON(text: response.content, returnPojo: true))
}

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
              '__PR_METADATA_CREDENTIAL__'.startsWith('__') ||
              !(env.TRUSTED_POLICY_SHA ==~ /[0-9a-f]{40}/)) {
            error('Invalid revision or missing administrator configuration.')
          }
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
      agent none
      stages {
        stage('Revalidate approved revision') {
          steps { script { verifyApprovedRevision() } }
        }
        stage('Approved host validation') {
          agent { label 'dorat-nuc-ci' }
          stages {
            stage('Checkout approved revision') {
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
git -C source fetch --no-tags origin "$TRUSTED_POLICY_SHA"
policy_ref=$(git -C source rev-parse "${TRUSTED_POLICY_SHA}^{commit}")
test "$policy_ref" = "$TRUSTED_POLICY_SHA"
mkdir trusted
for name in run_approved_pr_validation.sh build_pr_runner.sh bootstrap_jenkins_runner.sh validate_pr_images.sh; do
  mode=$(git -C source ls-tree "$policy_ref" -- "scripts/ci/$name" | cut -d ' ' -f 1)
  [[ "$mode" = 100644 || "$mode" = 100755 ]]
  git -C source show "$policy_ref:scripts/ci/$name" > "trusted/$name"
done
git -C source checkout --detach "$HEAD_SHA"
'''
              }
            }
            stage('Validate approved application and images') {
              steps {
                sh '''#!/usr/bin/env bash
set -euo pipefail
bash trusted/run_approved_pr_validation.sh "$WORKSPACE/source" "$WORKSPACE/trusted"
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
        stage('Recheck PR after validation') {
          // No agent/Launcher context: the App token stays on the controller.
          steps { script { verifyApprovedRevision() } }
        }
      }
    }
  }
}
