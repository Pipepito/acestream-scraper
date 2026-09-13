#!/usr/bin/env bash
# Execute the trusted runtime-contract validator against PR runtime scripts in
# real amd64, arm64, and arm/v7 userlands. Contributor files run in disposable,
# network-disabled containers and never receive the Docker socket or host env.
set -euo pipefail

SOURCE=""
VALIDATION_REF=""
NAME_PREFIX="acestream-pr-arch"
BASE_IMAGE="python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254"
PLATFORMS=("linux/amd64" "linux/arm64" "linux/arm/v7")

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="${2:-}"; shift 2 ;;
    --validation-ref) VALIDATION_REF="${2:-}"; shift 2 ;;
    --name-prefix) NAME_PREFIX="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: run_pr_arch_contracts.sh --source <repo> --validation-ref <git-ref> [--name-prefix <name>]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SOURCE" || -z "$VALIDATION_REF" ]]; then
  echo "--source and --validation-ref are required." >&2
  exit 2
fi
if ! git -C "$SOURCE" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Source is not a Git checkout: $SOURCE" >&2
  exit 1
fi

TRUSTED_DIR=$(mktemp -d "${TMPDIR:-/tmp}/acestream-pr-arch.XXXXXX")
TRUSTED_VALIDATOR="$TRUSTED_DIR/validate-runtime-contract.sh"
git -C "$SOURCE" show "${VALIDATION_REF}:scripts/ci/validate_runtime_contract.sh" > "$TRUSTED_VALIDATOR"
if [[ ! -s "$TRUSTED_VALIDATOR" ]]; then
  echo "Trusted runtime validator is empty." >&2
  exit 1
fi

host_uid=$(id -u)
host_gid=$(id -g)

cleanup() {
  local platform suffix
  for platform in "${PLATFORMS[@]}"; do
    suffix=${platform//\//-}
    docker rm --force "${NAME_PREFIX}-${suffix}" >/dev/null 2>&1 || true
  done
  rm -rf "$TRUSTED_DIR"
}
trap cleanup EXIT INT TERM

run_with_timeout() {
  "$@" &
  local command_pid=$!
  (
    sleep 300
    if kill -0 "$command_pid" >/dev/null 2>&1; then
      echo "Architecture contract exceeded 5 minutes; terminating it." >&2
      kill -TERM "$command_pid" >/dev/null 2>&1 || true
      sleep 10
      kill -KILL "$command_pid" >/dev/null 2>&1 || true
    fi
  ) &
  local watchdog_pid=$!

  local status=0
  wait "$command_pid" || status=$?
  kill "$watchdog_pid" >/dev/null 2>&1 || true
  wait "$watchdog_pid" >/dev/null 2>&1 || true
  return "$status"
}

for platform in "${PLATFORMS[@]}"; do
  suffix=${platform//\//-}
  container_name="${NAME_PREFIX}-${suffix}"
  echo "Running PR runtime contracts on ${platform}..."
  docker rm --force "$container_name" >/dev/null 2>&1 || true
  set +e
  run_with_timeout docker run --rm --init \
      --name "$container_name" \
      --platform "$platform" \
      --network none \
      --read-only \
      --user "$host_uid:$host_gid" \
      --cap-drop ALL \
      --security-opt no-new-privileges \
      --pids-limit 256 \
      --memory 512m \
      --memory-swap 512m \
      --cpus 1 \
      --tmpfs /tmp:rw,nosuid,nodev,exec,size=128m,mode=1777 \
      --env HOME=/tmp \
      --volume "$SOURCE:/source:ro" \
      --volume "$TRUSTED_VALIDATOR:/trusted/validate-runtime-contract.sh:ro" \
      --workdir /source \
      "$BASE_IMAGE" \
      bash -c 'set -euo pipefail; bash -n entrypoint.sh warp-setup.sh healthcheck.sh; RUNTIME_CONTRACT_ROOT=/source bash /trusted/validate-runtime-contract.sh'
  status=$?
  set -e
  docker rm --force "$container_name" >/dev/null 2>&1 || true
  if [[ "$status" -ne 0 ]]; then
    echo "Runtime contract matrix failed on ${platform} (exit ${status})." >&2
    exit "$status"
  fi
done

echo "Isolated amd64/arm64/armv7 runtime contract matrix passed."
