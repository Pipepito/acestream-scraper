#!/usr/bin/env bash
# Maintainer-owned PRs only: build each supported flavor/platform without
# publishing. Keep dependency runners/build cache, remove every PR image tag.
# Caller holds the full-run FIFO Docker lock and has installed binfmt handlers.
set -euo pipefail
cd "$(dirname "$0")/../.."
NAME=""
DRY_RUN=0
BUILDER="${JENKINS_BUILDER:-acestream-builder}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [[ ! "$NAME" =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]{0,80}$ ]]; then
  echo "--name must be a unique CI run identifier (up to 81 safe characters)." >&2
  exit 2
fi
NAME=$(printf '%s' "$NAME" | tr '[:upper:]' '[:lower:]')
active_tag=""
private_config=""
original_docker_config="${DOCKER_CONFIG:-$HOME/.docker}"
remove_image() {
  local ids
  ids=$(docker image ls --quiet --filter "reference=$1") || return $?
  if [[ -n "$ids" ]]; then
    docker image rm "$1"
  fi
}
cleanup() {
  local result=$?
  trap - EXIT
  if [[ -n "$active_tag" && "$DRY_RUN" -eq 0 ]]; then
    remove_image "$active_tag" || result=1
  fi
  if [[ -n "$private_config" ]]; then rm -rf "$private_config"; fi
  exit "$result"
}
trap cleanup EXIT
if [[ "$DRY_RUN" -eq 0 ]]; then
  # Keep the publication builder and its warm cache while isolating registry
  # authentication. Buildx stores instance metadata separately from auths.
  export BUILDX_CONFIG="${BUILDX_CONFIG:-$original_docker_config/buildx}"
  private_config=$(mktemp -d)
  export DOCKER_CONFIG="$private_config"
  printf '{"auths":{}}\n' > "$DOCKER_CONFIG/config.json"
fi
plan=$(python3 - <<'PY'
import json, subprocess
from pathlib import Path
matrix = json.loads(Path('docker/manifests/platforms.json').read_text())
for platform in matrix['baseline_platforms']:
    for flavor in matrix['flavors']:
        supported = subprocess.check_output(['python3', 'scripts/ci/flavor_platforms.py',
            'docker/manifests/platforms.json', 'docker/manifests/acestream.json', flavor], text=True).strip().split(',')
        if platform in supported:
            print(platform, flavor)
PY
)
while read -r platform flavor; do
  [[ -n "$platform" && -n "$flavor" ]] || continue
  tag="acestream-scraper-pr-build:${NAME}-${platform//\//-}-${flavor}"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    existing=$(docker image ls --quiet --filter "reference=$tag")
    if [[ -n "$existing" ]]; then
      echo "Refusing to overwrite pre-existing PR image: $tag" >&2
      exit 1
    fi
    DOCKER_CONFIG="$original_docker_config" bash scripts/ci/cleanup_runner_docker.sh --min-free-gb 8
  fi
  active_tag="$tag"
  args=(bash scripts/ci/build_multiarch_images.sh --flavor "$flavor" --platforms "$platform"
        --builder "$BUILDER" --network host --load --tag "$tag")
  if [[ "$DRY_RUN" -eq 1 ]]; then args+=(--dry-run); fi
  "${args[@]}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY RUN] docker image rm $tag"
  else
    docker image inspect "$tag" --format '{{.Id}} {{.Os}}/{{.Architecture}}'
    remove_image "$tag"
  fi
  active_tag=""
done <<< "$plan"
echo "PR image build matrix passed; no images published or PR image tags retained."
