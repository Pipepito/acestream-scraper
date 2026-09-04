#!/usr/bin/env bash
# Build a one-use PR dependency runner from an explicitly selected Git ref.
# Jenkins extracts this script from the trusted validation ref before invoking
# it. The allowlisted context prevents unrelated PR files from reaching a
# network-enabled Docker build.
set -euo pipefail

SOURCE=""
REF=""
TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="${2:-}"; shift 2 ;;
    --ref) REF="${2:-}"; shift 2 ;;
    --tag) TAG="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: build_pr_runner.sh --source <repo> --ref <git-ref> --tag <image:tag>"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SOURCE" || -z "$REF" || -z "$TAG" ]]; then
  echo "--source, --ref, and --tag are required." >&2
  exit 2
fi

git -C "$SOURCE" cat-file -e "${REF}^{commit}"

CONTEXT=$(mktemp -d "${TMPDIR:-/tmp}/acestream-pr-runner.XXXXXX")
trap 'rm -rf "$CONTEXT"' EXIT

# These are the only inputs used by the network-enabled runner build and its
# host cleanup. For a fork, REF is the target branch, so neither operation can
# be changed by contributor-controlled requirements, scripts, npm hooks, or
# Docker instructions.
git -C "$SOURCE" archive "$REF" -- \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile \
  scripts/ci/cleanup_runner_docker.sh \
  | tar -x -C "$CONTEXT"

for required in \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile \
  scripts/ci/cleanup_runner_docker.sh; do
  if [[ ! -f "$CONTEXT/$required" || -L "$CONTEXT/$required" ]]; then
    echo "Trusted runner input is missing or not a regular file: $required" >&2
    exit 1
  fi
done

bash "$CONTEXT/scripts/ci/cleanup_runner_docker.sh" \
  --keep "$TAG" \
  --transient-age-hours 0 \
  --all-unused-images \
  --builder-keep 1GB \
  --min-free-gb 8

docker build \
  --file "$CONTEXT/docker/ci/pr-runner.Dockerfile" \
  --tag "$TAG" \
  "$CONTEXT"
