#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: phase5_arch_smoke.sh [options]

Run architecture-focused runtime smoke checks by building and running the app image
for each target platform, then validating core endpoints.

Options:
  --platforms <list>       Comma-separated platforms (default: linux/arm/v7,linux/arm64)
  --base-tag <prefix>      Base image tag prefix (default: acestream-scraper-smoke)
  --context <path>         Build context (default: .)
  --dockerfile <path>      Dockerfile path (default: Dockerfile)
  --target <name>          Dockerfile target to build (default: scraper — the
                           baseline app-only flavor; the engine-bearing
                           flavors also build for ARM, but the Android engine
                           payload cannot execute under qemu-user, so their
                           runtime smoke runs on real ARM hosts instead)
  --timeout <sec>          Per-platform startup timeout (default: 60)
  --dry-run                Print planned actions only
  --help                   Show this help
EOF
}

PLATFORMS="linux/arm/v7,linux/arm64"
BASE_TAG="acestream-scraper-smoke"
CONTEXT="."
DOCKERFILE="Dockerfile"
TARGET="scraper"
TIMEOUT=60
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms)
      PLATFORMS="${2:-}"
      shift 2
      ;;
    --base-tag)
      BASE_TAG="${2:-}"
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
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --timeout)
      TIMEOUT="${2:-60}"
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

IFS=',' read -r -a PLATFORM_LIST <<< "$PLATFORMS"
if [[ "${#PLATFORM_LIST[@]}" -eq 0 ]]; then
  echo "No platforms configured."
  exit 1
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
  for platform in "${PLATFORM_LIST[@]}"; do
    platform="$(echo "$platform" | xargs)"
    [[ -z "$platform" ]] && continue
    tag_suffix="${platform//\//-}"
    image_tag="${BASE_TAG}:${tag_suffix}"
    echo "[DRY RUN] build: docker buildx build --platform ${platform} --target ${TARGET} --load -f ${DOCKERFILE} -t ${image_tag} ${CONTEXT}"
    echo "[DRY RUN] run: docker run --rm -d --name phase5-smoke-${tag_suffix} -p <ephemeral>:8000 ${image_tag}"
    echo "[DRY RUN] probe: GET /api/v1/health and GET /"
  done
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required."
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required."
  exit 1
fi

run_smoke_for_platform() {
  local platform="$1"
  local platform_trimmed
  platform_trimmed="$(echo "$platform" | xargs)"
  local tag_suffix="${platform_trimmed//\//-}"
  local image_tag="${BASE_TAG}:${tag_suffix}"
  local container_name="phase5-smoke-${tag_suffix}-$$"
  local host_port=$((18080 + RANDOM % 1000))

  echo "Building platform image: ${platform_trimmed}"
  docker buildx build \
    --platform "${platform_trimmed}" \
    --target "${TARGET}" \
    --file "${DOCKERFILE}" \
    --tag "${image_tag}" \
    --load \
    "${CONTEXT}"

  echo "Starting container: ${container_name} on port ${host_port}"
  docker run -d --rm \
    --name "${container_name}" \
    -p "${host_port}:8000" \
    "${image_tag}" >/dev/null

  cleanup_platform() {
    docker rm -f "${container_name}" >/dev/null 2>&1 || true
  }
  trap cleanup_platform RETURN

  local start_time
  start_time="$(date +%s)"
  local health_ok=0
  while [[ $(( $(date +%s) - start_time )) -lt "${TIMEOUT}" ]]; do
    if curl -fsS "http://127.0.0.1:${host_port}/api/v1/health" >/dev/null 2>&1; then
      health_ok=1
      break
    fi
    sleep 2
  done

  if [[ "$health_ok" -ne 1 ]]; then
    echo "Health endpoint failed for platform ${platform_trimmed}"
    docker logs "${container_name}" || true
    return 1
  fi

  curl -fsS "http://127.0.0.1:${host_port}/" >/dev/null
  echo "Smoke checks passed for ${platform_trimmed}"
}

for platform in "${PLATFORM_LIST[@]}"; do
  platform="$(echo "$platform" | xargs)"
  [[ -z "$platform" ]] && continue
  run_smoke_for_platform "$platform"
done

echo "All architecture smoke checks passed."

