#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

DRY_RUN=0
PRINT_PLAN=0
CHANNEL=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --print-publish-plan)
      PRINT_PLAN=1
      shift
      ;;
    --channel)
      # Pre-release channel publish (the `develop` branch): push floating
      # channel tags only — never a version tag, never :latest. Validation
      # already ran in the branch's PR pipeline before this is invoked.
      CHANNEL="${2:-}"
      shift 2
      ;;
    *)
      echo "Usage: bash scripts/ci/run_jenkins_release.sh [--dry-run | --print-publish-plan] [--channel <name>]"
      exit 1
      ;;
  esac
done

BUILDER="${JENKINS_BUILDER:-acestream-builder}"
VERSION=$(tr -d '\n' < version.txt)
# Image repository and registry login target. Overridable only for local
# end-to-end tests against a throwaway registry; production is Docker Hub.
IMAGE_REPO="${RELEASE_IMAGE_REPO:-pipepito/acestream-scraper}"
REGISTRY_LOGIN_SERVER="${RELEASE_LOGIN_SERVER:-}"
# BuildKit cache cap applied between platforms of a publish (the runner has
# a 32 GB disk shared with other jobs).
PUBLISH_CACHE_CAP="${PUBLISH_CACHE_CAP:-2GB}"
PLATFORM_MANIFEST="docker/manifests/platforms.json"
ACESTREAM_MANIFEST="docker/manifests/acestream.json"

if [[ -n "$CHANNEL" ]] && ! [[ "$CHANNEL" =~ ^[a-z][a-z0-9-]{0,30}$ ]]; then
  echo "Invalid channel name: $CHANNEL (lowercase letters, digits and dashes)" >&2
  exit 1
fi
if [[ -z "$CHANNEL" && "$VERSION" == *-dev* ]]; then
  # develop carries the next version as vX.Y.Z-dev; the bump to vX.Y.Z lands
  # on develop (via PR) right before the develop -> main release PR, so a
  # release run must never see a -dev version.
  echo "Refusing to release a development version (version.txt = $VERSION). Land the version bump on develop (via PR) before the develop -> main release PR." >&2
  exit 1
fi

# Floating pre-release tags for a channel: <channel> is the full payload
# (mirrors what :latest means for releases) plus <channel>-<flavor> for every
# flavor. Immutable per-commit tags are deliberately not pushed.
channel_tags_for_flavor() {
  case "$1" in
    scraper-acestream-acexy)
      printf '%s\n' "${IMAGE_REPO}:${CHANNEL} ${IMAGE_REPO}:${CHANNEL}-scraper-acestream-acexy"
      ;;
    scraper|scraper-acestream|scraper-acexy)
      printf '%s\n' "${IMAGE_REPO}:${CHANNEL}-$1"
      ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

FLAVORS=(
  "scraper"
  "scraper-acestream"
  "scraper-acexy"
  "scraper-acestream-acexy"
)

PUBLISH_FLAVORS=(
  "scraper-acestream-acexy"
  "scraper"
  "scraper-acestream"
  "scraper-acexy"
)

preflight_result_file_for_flavor() {
  case "$1" in
    scraper) printf '%s\n' "phase5-build-result-release-scraper.json" ;;
    scraper-acestream) printf '%s\n' "phase5-build-result-release-scraper-acestream.json" ;;
    scraper-acexy) printf '%s\n' "phase5-build-result-release-scraper-acexy.json" ;;
    scraper-acestream-acexy) printf '%s\n' "phase5-build-result-release-scraper-acestream-acexy.json" ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

publish_result_file_for_flavor() {
  case "$1" in
    scraper-acestream-acexy) printf '%s\n' "phase5-build-result-release-full-publish.json" ;;
    scraper) printf '%s\n' "phase5-build-result-release-scraper-publish.json" ;;
    scraper-acestream) printf '%s\n' "phase5-build-result-release-scraper-acestream-publish.json" ;;
    scraper-acexy) printf '%s\n' "phase5-build-result-release-scraper-acexy-publish.json" ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

# The floating :latest tag is never pushed by a build. Phase 1
# (PUBLISH_LATEST=0, the default) pushes versioned + flavor-channel tags only,
# so users on :latest are untouched during the canary window. Phase 2
# (PUBLISH_LATEST=1) RETAGS the canary-validated
# ${IMAGE_REPO}:${VERSION} manifest to ${IMAGE_REPO}:latest
# via scripts/ci/promote_latest.sh — no rebuild, so :latest is byte-identical
# to what was validated. Only the full payload flavor
# (scraper-acestream-acexy, whose manifest the version tag points at) can
# ever become :latest.
LATEST_SOURCE_FLAVOR="scraper-acestream-acexy"

publish_tags_for_flavor() {
  case "$1" in
    scraper-acestream-acexy)
      printf '%s\n' "${IMAGE_REPO}:${VERSION} ${IMAGE_REPO}:scraper-acestream-acexy ${IMAGE_REPO}:${VERSION}-scraper-acestream-acexy"
      ;;
    scraper)
      printf '%s\n' "${IMAGE_REPO}:scraper ${IMAGE_REPO}:${VERSION}-scraper"
      ;;
    scraper-acestream)
      printf '%s\n' "${IMAGE_REPO}:scraper-acestream ${IMAGE_REPO}:${VERSION}-scraper-acestream"
      ;;
    scraper-acexy)
      printf '%s\n' "${IMAGE_REPO}:scraper-acexy ${IMAGE_REPO}:${VERSION}-scraper-acexy"
      ;;
    *)
      echo "Unsupported flavor: $1"
      exit 1
      ;;
  esac
}

PROMOTE_LATEST="${PUBLISH_LATEST:-0}"

registry_login() {
  : "${DOCKERHUB_USERNAME:?DOCKERHUB_USERNAME is required}"
  : "${DOCKERHUB_TOKEN:?DOCKERHUB_TOKEN is required}"
  if [[ -n "$REGISTRY_LOGIN_SERVER" ]]; then
    printf '%s' "$DOCKERHUB_TOKEN" | docker login "$REGISTRY_LOGIN_SERVER" --username "$DOCKERHUB_USERNAME" --password-stdin
  else
    printf '%s' "$DOCKERHUB_TOKEN" | docker login --username "$DOCKERHUB_USERNAME" --password-stdin
  fi
}

flavor_platforms_csv() {
  python3 scripts/ci/flavor_platforms.py "$PLATFORM_MANIFEST" "$ACESTREAM_MANIFEST" "$1"
}

# publish_platform_major <tags_fn> <result_prefix> <dry_run>
#
# Builds every flavor for one platform before moving to the next platform
# (platform-major), pushing each image by digest, and prunes the builder's
# BuildKit cache between platforms; then assembles every flavor's tags with
# `docker buildx imagetools create` from its per-platform digests and verifies
# the remote manifests. Platform-major order keeps the peak cache to one
# platform's worth of layers (flavors share their base stages), which is what
# lets a four-flavor, three-platform publish fit the runner's 32 GB disk.
publish_platform_major() {
  local tags_fn="$1" result_prefix="$2" dry="$3"
  local digest_dir platform flavor key platforms_csv union flavor_csv tags tag refs
  digest_dir="$(mktemp -d)"
  union="$(python3 - "$PLATFORM_MANIFEST" <<'PY2'
import json, sys
print(",".join(json.load(open(sys.argv[1]))["baseline_platforms"]))
PY2
)"
  PUBLISHED_TAGS=()
  IFS=',' read -r -a platform_list <<< "$union"
  for platform in "${platform_list[@]}"; do
    for flavor in "${PUBLISH_FLAVORS[@]}"; do
      flavor_csv="$(flavor_platforms_csv "$flavor")"
      case ",$flavor_csv," in
        *",$platform,"*) ;;
        *) continue ;;
      esac
      key="$flavor.$(printf '%s' "$platform" | tr '/' '-')"
      build_args=(
        bash scripts/ci/build_multiarch_images.sh
        --flavor "$flavor"
        --platforms "$platform"
        --push-by-digest
        --repo "$IMAGE_REPO"
        --builder "$BUILDER"
        --digest-file "$digest_dir/$key"
        --result-file "${result_prefix}-${flavor}-$(printf '%s' "$platform" | tr '/' '-').json"
      )
      if [[ "$dry" -eq 1 ]]; then
        build_args+=(--dry-run)
      fi
      "${build_args[@]}"
    done
    if [[ "$dry" -eq 1 ]]; then
      echo "[DRY RUN] docker buildx prune --builder $BUILDER -f --max-used-space $PUBLISH_CACHE_CAP"
    else
      docker buildx prune --builder "$BUILDER" -f --max-used-space "$PUBLISH_CACHE_CAP" >/dev/null 2>&1 \
        || docker buildx prune --builder "$BUILDER" -f --keep-storage "$PUBLISH_CACHE_CAP" >/dev/null 2>&1 \
        || true
      echo "Builder $BUILDER cache after $platform: $(docker buildx du --builder "$BUILDER" 2>/dev/null | grep -E '^Total:' | tr -s '\t ' ' ' || echo unknown)"
    fi
  done
  for flavor in "${PUBLISH_FLAVORS[@]}"; do
    IFS=' ' read -r -a tags <<< "$("$tags_fn" "$flavor")"
    if [[ "$dry" -eq 1 ]]; then
      echo "[DRY RUN] docker buildx imagetools create $(printf -- '--tag %s ' "${tags[@]}")<digests of $flavor>"
    else
      refs="$(cat "$digest_dir/$flavor".* 2>/dev/null | tr '\n' ' ')"
      [[ -n "$refs" ]] || { echo "No digests collected for flavor $flavor" >&2; exit 1; }
      imagetools_cmd=(docker buildx imagetools create)
      for tag in "${tags[@]}"; do
        imagetools_cmd+=(--tag "$tag")
      done
      # shellcheck disable=SC2086
      "${imagetools_cmd[@]}" $refs
      for tag in "${tags[@]}"; do
        bash scripts/ci/verify_multiarch_manifest.sh --image "$tag" --flavor "$flavor"
      done
    fi
    PUBLISHED_TAGS+=("${tags[@]}")
  done
  rm -rf "$digest_dir"
}

if [[ "$PRINT_PLAN" -eq 1 && -n "$CHANNEL" ]]; then
  echo "Channel publish plan (channel=${CHANNEL}, VERSION=${VERSION}; no version tag, no :latest):"
  for flavor in "${PUBLISH_FLAVORS[@]}"; do
    printf '  %s: %s\n' "$flavor" "$(channel_tags_for_flavor "$flavor")"
  done
  exit 0
fi

if [[ "$PRINT_PLAN" -eq 1 ]]; then
  echo "Release publish plan (PUBLISH_LATEST=${PROMOTE_LATEST}, VERSION=${VERSION}):"
  if [[ "$PROMOTE_LATEST" == "1" ]]; then
    echo "  promote: ${IMAGE_REPO}:latest <- ${IMAGE_REPO}:${VERSION} (retag of the canary-validated ${LATEST_SOURCE_FLAVOR} manifest; no flavor rebuild)"
  else
    for flavor in "${PUBLISH_FLAVORS[@]}"; do
      printf '  %s: %s\n' "$flavor" "$(publish_tags_for_flavor "$flavor")"
    done
  fi
  exit 0
fi

GIT_SHA=$(git rev-parse HEAD)

if ! docker buildx inspect "$BUILDER" >/dev/null 2>&1; then
  echo "Required buildx builder not found: $BUILDER"
  exit 1
fi

# Pre-release channel publish (develop). The PR pipeline already ran every
# validation and smoke stage on this exact revision; this stage only builds
# the multi-platform flavors and pushes the floating channel tags.
if [[ -n "$CHANNEL" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    publish_platform_major channel_tags_for_flavor "phase5-build-result-channel-${CHANNEL}" 1
    echo "Dry-run channel publish plan completed."
    exit 0
  fi
  registry_login
  publish_platform_major channel_tags_for_flavor "phase5-build-result-channel-${CHANNEL}" 0
  CHANNEL_TAGS_JSON="$(python3 - "${PUBLISHED_TAGS[@]}" <<'PY2'
import json, sys
print(json.dumps(sys.argv[1:]))
PY2
)"
  RELEASE_CHANNEL="$CHANNEL" RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_BUILDER="$BUILDER" RELEASE_TAGS_JSON="$CHANNEL_TAGS_JSON" python3 - "phase5-build-result-channel-${CHANNEL}-metadata.json" <<'PY2'
import json, os, sys
from datetime import datetime, timezone
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "mode": "channel",
    "channel": os.environ["RELEASE_CHANNEL"],
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "tags": json.loads(os.environ["RELEASE_TAGS_JSON"]),
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY2
  echo "Channel publish completed: ${CHANNEL}"
  exit 0
fi

# Phase 2: promotion run. Nothing is rebuilt or re-tested — the images were
# built, smoke-tested and canaried in phase 1; this only moves :latest.
if [[ "$PROMOTE_LATEST" == "1" ]]; then
  if [[ "$DRY_RUN" -eq 1 ]]; then
    bash scripts/ci/promote_latest.sh --version "$VERSION" --flavor "$LATEST_SOURCE_FLAVOR" --repo "$IMAGE_REPO" --dry-run
    echo "Dry-run promotion plan completed."
    exit 0
  fi
  registry_login
  bash scripts/ci/promote_latest.sh --version "$VERSION" --flavor "$LATEST_SOURCE_FLAVOR" --repo "$IMAGE_REPO"
  RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_BUILDER="$BUILDER" python3 - "phase5-build-result-release-metadata.json" <<'PY2'
import json, os, sys
from datetime import datetime, timezone
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "mode": "promote-latest",
    "tags": ["${IMAGE_REPO}:latest"],
    "source": "${IMAGE_REPO}:" + os.environ["RELEASE_VERSION"],
}
with open(sys.argv[1], "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY2
  echo "Release promotion completed."
  exit 0
fi

bash scripts/ci/run_cutover_required_checks.sh --profile full

for flavor in "${FLAVORS[@]}"; do
  result_file="$(preflight_result_file_for_flavor "$flavor")"

  bash scripts/ci/build_multiarch_images.sh \
    --dry-run \
    --builder "$BUILDER" \
    --flavor "$flavor" \
    --result-file "$result_file"

  bash scripts/ci/verify_multiarch_manifest.sh \
    --result-file "$result_file" \
    --flavor "$flavor"
done

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "Dry-run preflight completed."
  exit 0
fi

# Real AceStream engine runtime smoke. Mirrors Jenkinsfile's
# 'Acestream Engine Runtime Smoke' stage so the release path validates that
# the published image will actually start the engine before any tags reach
# Docker Hub. BUILDX_BUILDER=default forces the docker driver because the
# docker-container driver's isolated network breaks curl to
# download.acestream.media on WARP-routed builders.
# scraper-acestream resolves to amd64 + arm64 + arm/v7; --load needs a single
# platform, so pin the runner's native one. The ARM engine layouts are
# verified by the installer-stage tests (QEMU build, no execution).
(
  export BUILDX_BUILDER=default
  bash scripts/ci/build_multiarch_images.sh \
    --flavor scraper-acestream \
    --platforms linux/amd64 \
    --load \
    --network host \
    --tag acestream-scraper:release-smoke
)
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acestream_runtime_smoke.py -v
# The acexy flavors must ship the real upstream proxy, not the build fixture.
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_acexy_runtime_smoke.py -v
PYTHONPATH=backend backend/venv/bin/pytest -q backend/tests/docker/test_install_acestream.py -v -k "arm_oci_image_install_layout"
# The ~2 GB smoke image is not needed for the publish step; reclaim the
# runner's disk before the multi-platform builds (see cleanup_runner_docker.sh).
docker image rm -f acestream-scraper:release-smoke >/dev/null 2>&1 || true
bash scripts/ci/cleanup_runner_docker.sh || true

registry_login

publish_platform_major publish_tags_for_flavor "phase5-build-result-release" 0
all_tags=("${PUBLISHED_TAGS[@]}")

ALL_TAGS_JSON="$(python3 - "${all_tags[@]}" <<'PY'
import json
import sys

print(json.dumps(sys.argv[1:]))
PY
)"

RELEASE_METADATA_FILE="phase5-build-result-release-metadata.json"
RELEASE_BUILDER="$BUILDER" RELEASE_VERSION="$VERSION" RELEASE_GIT_SHA="$GIT_SHA" RELEASE_TAGS_JSON="$ALL_TAGS_JSON" python3 - "$RELEASE_METADATA_FILE" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

metadata_file = sys.argv[1]
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "version": os.environ["RELEASE_VERSION"],
    "git_sha": os.environ["RELEASE_GIT_SHA"],
    "builder": os.environ["RELEASE_BUILDER"],
    "tags": json.loads(os.environ["RELEASE_TAGS_JSON"]),
}
with open(metadata_file, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, indent=2)
PY

echo "Release publish completed."
