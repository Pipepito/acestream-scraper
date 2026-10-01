#!/usr/bin/env bash
# Use the same pinned, preinstalled application gate as trusted develop.
# No registry credentials or Docker socket enter the validation container.
set -euo pipefail
cd "$(dirname "$0")/../.."
artifact_dir="$PWD/.ci-release-artifacts"
rm -rf "$artifact_dir"
mkdir -p "$artifact_dir"
rm -f phase3-gate-report-full.json phase3-phase1-full.json
# Resolve this release's manifests; reuse only an exact dependency/platform match.
runner_file=$(mktemp)
trap 'rm -f "$runner_file"' EXIT
bash scripts/ci/build_pr_runner.sh --source "$PWD" --ref HEAD --image-file "$runner_file"
validation_image=$(cat "$runner_file")
host_uid="$(id -u)"
host_gid="$(id -g)"
set +e
docker run --rm \
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
  --env GIT_CONFIG_COUNT=1 \
  --env GIT_CONFIG_KEY_0=safe.directory \
  --env GIT_CONFIG_VALUE_0=/workspace \
  --volume "$PWD:/source:ro" \
  --volume "$artifact_dir:/artifacts:rw" \
  --workdir /workspace \
  "$validation_image" \
  bash -c 'cp -R /source/. /workspace/ && CI_OUTPUT_DIR=/artifacts bash scripts/ci/run_develop_validation.sh'
validation_status=$?
set -e
if [[ "$validation_status" -ne 0 ]]; then
  echo "Application validation failed (exit $validation_status); see the gate output and archived .ci-release-artifacts reports."
  exit "$validation_status"
fi
docker compose config -q
