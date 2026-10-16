#!/usr/bin/env bash
# Prepare a reusable dependency runner from an explicitly selected trusted ref.
# Fork jobs extract this script from their target before invoking it. Both the
# lifecycle policy and allowlisted Docker context come from that same ref.
set -euo pipefail
SOURCE=""
REF=""
IMAGE_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --source) SOURCE="${2:-}"; shift 2 ;;
    --ref) REF="${2:-}"; shift 2 ;;
    --image-file) IMAGE_FILE="${2:-}"; shift 2 ;;
    -h|--help)
      echo "Usage: build_pr_runner.sh --source <repo> --ref <git-ref> --image-file <output>"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [[ -z "$SOURCE" || -z "$REF" || -z "$IMAGE_FILE" ]]; then
  echo "--source, --ref, and --image-file are required." >&2
  exit 2
fi
# Resolve once so a moving branch cannot mix inputs from different commits.
REF="$(git -C "$SOURCE" rev-parse --verify "${REF}^{commit}")"
CONTEXT=$(mktemp -d "${TMPDIR:-/tmp}/acestream-pr-runner.XXXXXX")
trap 'rm -rf "$CONTEXT"' EXIT
git -C "$SOURCE" archive "$REF" -- \
  backend/requirements.txt \
  frontend/package.json \
  frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile \
  scripts/ci/docker_lifecycle.py \
  | tar -x -C "$CONTEXT"
for required in backend/requirements.txt frontend/package.json frontend/package-lock.json \
  docker/ci/pr-runner.Dockerfile scripts/ci/docker_lifecycle.py; do
  if [[ ! -f "$CONTEXT/$required" || -L "$CONTEXT/$required" ]]; then
    echo "Trusted runner input is missing or not a regular file: $required" >&2
    exit 1
  fi
done
python3 -I "$CONTEXT/scripts/ci/docker_lifecycle.py" runner \
  --context "$CONTEXT" --image-file "$IMAGE_FILE"
