#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: build_multiarch_images.sh [options]

Build the canonical image with Docker Buildx across a platform matrix.

Options:
  --platforms <list>       Comma-separated platform list (default: linux/amd64,linux/arm/v7,linux/arm64)
  --tag <image:tag>        Image tag (default: acestream-scraper:multiarch-local)
  --context <path>         Build context (default: .)
  --dockerfile <path>      Dockerfile path (default: Dockerfile)
  --push                   Push image/manifest to registry
  --load                   Load image into local docker daemon (single-platform only)
  --build-arg <k=v>        Build arg (repeatable)
  --builder <name>         Buildx builder name (default: default)
  --result-file <path>     Write JSON build result metadata to this file
  --dry-run                Print build command and metadata only
  --help                   Show this help

Examples:
  bash scripts/ci/build_multiarch_images.sh --dry-run --platforms linux/arm/v7,linux/arm64
  bash scripts/ci/build_multiarch_images.sh --tag ghcr.io/acme/app:sha --push
EOF
}

PLATFORMS="linux/amd64,linux/arm/v7,linux/arm64"
TAG="acestream-scraper:multiarch-local"
CONTEXT="."
DOCKERFILE="Dockerfile"
PUSH=0
LOAD=0
DRY_RUN=0
BUILDER="default"
RESULT_FILE=""
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms)
      PLATFORMS="${2:-}"
      shift 2
      ;;
    --tag)
      TAG="${2:-}"
      shift 2
      ;;
    --context)
      CONTEXT="${2:-}"
      shift 2
      ;;
    --dockerfile)
      DOCKERFILE="${2:-}"
      shift 2
      ;;
    --push)
      PUSH=1
      shift
      ;;
    --load)
      LOAD=1
      shift
      ;;
    --build-arg)
      BUILD_ARGS+=("--build-arg" "${2:-}")
      shift 2
      ;;
    --builder)
      BUILDER="${2:-}"
      shift 2
      ;;
    --result-file)
      RESULT_FILE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      show_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      show_help
      exit 1
      ;;
  esac
done

if [[ "$PUSH" -eq 1 && "$LOAD" -eq 1 ]]; then
  echo "Cannot use --push and --load together."
  exit 1
fi

if [[ -z "$PLATFORMS" ]]; then
  echo "Platforms cannot be empty."
  exit 1
fi

if [[ "$LOAD" -eq 1 && "$PLATFORMS" == *","* ]]; then
  echo "--load supports a single platform only. Use --push for multi-platform manifests."
  exit 1
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "docker is required."
    exit 1
  fi
fi

BUILD_CMD=(
  docker buildx build
  --builder "$BUILDER"
  --platform "$PLATFORMS"
  --file "$DOCKERFILE"
  --tag "$TAG"
)

if [[ "$PUSH" -eq 1 ]]; then
  BUILD_CMD+=(--push)
elif [[ "$LOAD" -eq 1 ]]; then
  BUILD_CMD+=(--load)
else
  BUILD_CMD+=(--output type=cacheonly)
fi

if [[ "${#BUILD_ARGS[@]}" -gt 0 ]]; then
  BUILD_CMD+=("${BUILD_ARGS[@]}")
fi

BUILD_CMD+=("$CONTEXT")

build_cmd_string="$(printf '%q ' "${BUILD_CMD[@]}")"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[DRY RUN] ${build_cmd_string}"
else
  eval "$build_cmd_string"
fi

if [[ -n "$RESULT_FILE" ]]; then
  python3 - "$RESULT_FILE" "$TAG" "$PLATFORMS" "$PUSH" "$LOAD" "$DRY_RUN" <<'PY'
import json
import sys
from datetime import datetime, timezone

result_file, tag, platforms, push, load, dry_run = sys.argv[1:]
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "image": tag,
    "platforms": [p.strip() for p in platforms.split(",") if p.strip()],
    "push": push == "1",
    "load": load == "1",
    "dry_run": dry_run == "1",
}
with open(result_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY
  echo "Wrote build result metadata: $RESULT_FILE"
fi

echo "Multi-arch build command completed."

