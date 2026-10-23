#!/usr/bin/env bash
# Invoke only after owner approval and a fresh PR identity check, using the
# protected policy's copy. This job has no publication credentials.
set -euo pipefail
SOURCE="$(cd "${1:?source required}" && pwd)"
TRUSTED="$(cd "${2:?trusted helper directory required}" && pwd)"
cd "$SOURCE"
name="acestream-approved-pr-${BUILD_NUMBER:?Jenkins build number required}"
[[ "$BUILD_NUMBER" =~ ^[1-9][0-9]*$ ]]
test "$(git rev-parse HEAD)" = "$HEAD_SHA"
# Approved dependency/lifecycle inputs may execute while constructing the runner.
bash "$TRUSTED/build_pr_runner.sh" --source "$SOURCE" --ref "$HEAD_SHA" --image-file "$TRUSTED/runner-image"
runner=$(cat "$TRUSTED/runner-image")
cleanup() { docker rm --force "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
# Always run the full application gate against the approved dependency set.
# This also covers PRs whose dependency changes skipped the automatic suite.
docker run --rm --init --name "$name" \
  --network none --read-only --user "$(id -u):$(id -g)" \
  --cap-drop ALL --security-opt no-new-privileges \
  --pids-limit 1024 --memory 8g --memory-swap 8g --cpus 3 \
  --tmpfs /tmp:rw,nosuid,nodev,exec,size=1g \
  --tmpfs /workspace:rw,nosuid,nodev,exec,size=3g,mode=1777 \
  --env CI=true --env HOME=/tmp/ci-home --env PYTHONDONTWRITEBYTECODE=1 \
  --env GIT_CONFIG_COUNT=1 --env GIT_CONFIG_KEY_0=safe.directory \
  --env GIT_CONFIG_VALUE_0=/workspace --env "PR_VALIDATION_REF=$BASE_SHA" \
  --volume "$SOURCE:/source:ro" --workdir /workspace "$runner" \
  bash -c 'cp -R /source/. /workspace/ && git show "${PR_VALIDATION_REF}:scripts/ci/run_pr_validation.sh" > /tmp/trusted-validation.sh && cp /tmp/trusted-validation.sh scripts/ci/.trusted-validation.sh && bash scripts/ci/.trusted-validation.sh'
bash "$TRUSTED/bootstrap_jenkins_runner.sh"
PR_IMAGE_SOURCE_ROOT="$SOURCE" bash "$TRUSTED/validate_pr_images.sh" --name "$name"
