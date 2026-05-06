#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Usage: build_multiarch_images.sh [options]

Build a flavor-aware image with Docker Buildx across a manifest-derived platform matrix.

Options:
  --flavor <name>          Flavor name used for platform derivation (default: scraper)
  --target <name>          Dockerfile target to build (default: flavor value)
  --platforms <list>       Comma-separated platform list; must be allowed for the flavor
  --tag <image:tag>        Image tag (repeatable; default: acestream-scraper:multiarch-local)
  --context <path>         Build context (default: .)
  --dockerfile <path>      Dockerfile path (default: Dockerfile)
  --platform-manifest <p>  platforms.json path (default: docker/manifests/platforms.json)
  --acestream-manifest <p> acestream.json path (default: docker/manifests/acestream.json)
  --push                   Push image/manifest to registry
  --load                   Load image into local docker daemon (single-platform only)
  --build-arg <k=v>        Build arg (repeatable)
  --builder <name>         Buildx builder name (default: default)
  --result-file <path>     Write JSON build result metadata to this file
  --network <mode>         BuildKit network mode for RUN steps (e.g. host)
  --dry-run                Print build command and metadata only
  --help                   Show this help

Examples:
  bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper
  bash scripts/ci/build_multiarch_images.sh --dry-run --flavor scraper-acestream --tag ghcr.io/acme/app:sha
EOF
}

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
FLAVOR_PLATFORM_HELPER="$ROOT_DIR/scripts/ci/flavor_platforms.py"

FLAVOR="scraper"
TARGET=""
PLATFORMS=""
CONTEXT="."
DOCKERFILE="Dockerfile"
PLATFORM_MANIFEST="$ROOT_DIR/docker/manifests/platforms.json"
ACESTREAM_MANIFEST="$ROOT_DIR/docker/manifests/acestream.json"
PUSH=0
LOAD=0
DRY_RUN=0
BUILDER="default"
NETWORK=""
RESULT_FILE=""
BUILD_ARGS=()
TAGS=("acestream-scraper:multiarch-local")
CUSTOM_TAGS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --flavor)
      FLAVOR="${2:-}"
      shift 2
      ;;
    --target)
      TARGET="${2:-}"
      shift 2
      ;;
    --platforms)
      PLATFORMS="${2:-}"
      shift 2
      ;;
    --tag)
      if [[ "$CUSTOM_TAGS" -eq 0 ]]; then
        TAGS=()
        CUSTOM_TAGS=1
      fi
      TAGS+=("${2:-}")
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
    --platform-manifest)
      PLATFORM_MANIFEST="${2:-}"
      shift 2
      ;;
    --acestream-manifest)
      ACESTREAM_MANIFEST="${2:-}"
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
    --network)
      NETWORK="${2:-}"
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

if [[ -z "$FLAVOR" ]]; then
  echo "Flavor cannot be empty."
  exit 1
fi

if [[ -z "$TARGET" ]]; then
  TARGET="$FLAVOR"
fi

if [[ ! -f "$PLATFORM_MANIFEST" ]]; then
  echo "Platforms manifest not found: $PLATFORM_MANIFEST"
  exit 1
fi

if [[ ! -f "$ACESTREAM_MANIFEST" ]]; then
  echo "AceStream manifest not found: $ACESTREAM_MANIFEST"
  exit 1
fi

if [[ ! -f "$FLAVOR_PLATFORM_HELPER" ]]; then
  echo "Flavor platform helper not found: $FLAVOR_PLATFORM_HELPER"
  exit 1
fi

resolved_platforms="$(python3 "$FLAVOR_PLATFORM_HELPER" "$PLATFORM_MANIFEST" "$ACESTREAM_MANIFEST" "$FLAVOR" "$PLATFORMS")"

if [[ -z "$resolved_platforms" ]]; then
  echo "Platforms cannot be empty."
  exit 1
fi

PLATFORMS="$resolved_platforms"

ACESTREAM_ARG_HELPER="$ROOT_DIR/scripts/ci/derive_acestream_build_args.py"
if [[ -f "$ACESTREAM_ARG_HELPER" ]]; then
    ACESTREAM_BEARING_FLAVORS=("scraper-acestream" "scraper-acestream-acexy")
    flavor_needs_acestream=0
    for f in "${ACESTREAM_BEARING_FLAVORS[@]}"; do
        if [[ "$FLAVOR" == "$f" ]]; then
            flavor_needs_acestream=1
            break
        fi
    done

    if ! derived="$(python3 "$ACESTREAM_ARG_HELPER" "$ACESTREAM_MANIFEST" "$FLAVOR" "${PLATFORMS%%,*}" 2>&1)"; then
        helper_rc=$?
        if [[ "$flavor_needs_acestream" -eq 1 ]]; then
            printf 'ERROR: failed to derive acestream build args for flavor=%s platform=%s\n%s\n' \
                "$FLAVOR" "${PLATFORMS%%,*}" "$derived" >&2
            exit "$helper_rc"
        else
            # Non-acestream flavor: helper crash is unexpected but not fatal.
            printf 'WARNING: derive helper exited %d for non-acestream flavor %s; continuing\n%s\n' \
                "$helper_rc" "$FLAVOR" "$derived" >&2
            derived=""
        fi
    fi
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        # Don't override args the caller already passed via --build-arg.
        key="${line%%=*}"
        already=0
        for existing in "${BUILD_ARGS[@]:-}"; do
            if [[ "$existing" == "$key="* ]]; then
                already=1
                break
            fi
        done
        if [[ "$already" -eq 0 ]]; then
            BUILD_ARGS+=("--build-arg" "$line")
        fi
    done <<< "$derived"
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
  --target "$TARGET"
)

for tag in "${TAGS[@]}"; do
  BUILD_CMD+=(--tag "$tag")
done

if [[ -n "$NETWORK" ]]; then
    BUILD_CMD+=(--network "$NETWORK")
fi

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
  echo "Flavor: $FLAVOR"
  echo "Target: $TARGET"
  echo "Platforms: $PLATFORMS"
  echo "Tags: ${TAGS[*]}"
  echo "[DRY RUN] ${build_cmd_string}"
else
  eval "$build_cmd_string"
fi

if [[ -n "$RESULT_FILE" ]]; then
  tags_json="$(python3 - "${TAGS[@]}" <<'PY'
import json
import sys

print(json.dumps(sys.argv[1:]))
PY
)"
  RESULT_TAGS_JSON="$tags_json" python3 - "$RESULT_FILE" "$FLAVOR" "$TARGET" "$PLATFORMS" "$PUSH" "$LOAD" "$DRY_RUN" <<'PY'
import json
import os
import sys
from datetime import datetime, timezone

result_file, flavor, target, platforms, push, load, dry_run = sys.argv[1:]
tags = json.loads(os.environ["RESULT_TAGS_JSON"])
payload = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "flavor": flavor,
    "target": target,
    "image": tags[0] if tags else "",
    "tags": tags,
    "target_tags": tags,
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
