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
  --acestream-manifest <p> acestream.json path (default: docker/manifests/acestream.json).
                           Drives platform derivation and the dry-run report only:
                           the image always installs from the manifest inside the
                           build context, so a different file is rejected for real
                           builds (edit the tracked manifest, or pass
                           --build-arg ACESTREAM_* overrides).
  --acexy-manifest <p>     acexy.json path (default: docker/manifests/acexy.json)
  --push                   Push image/manifest to registry (several platforms are
                           built one at a time, pushed by digest and assembled)
  --push-by-digest         Build ONE platform and push it by digest only (no tag);
                           needs --repo and a single --platforms value. Use with
                           --digest-file to collect <repo>@<digest> for a later
                           `docker buildx imagetools create` (platform-major publishes)
  --repo <name>            Repository for --push-by-digest (e.g. pipepito/acestream-scraper)
  --digest-file <path>     Write <repo>@<digest> here after --push-by-digest
  --prune-builder-after <cap>  After the build, prune the builder's BuildKit cache
                           down to <cap> (e.g. 2GB); keeps small-disk runners alive
  --load                   Load image into local docker daemon (single-platform only)
  --build-arg <k=v>        Build arg (repeatable)
  --builder <name>         Buildx builder name (default: $BUILDX_BUILDER if set,
                           otherwise the currently selected buildx builder)
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
ACEXY_MANIFEST="$ROOT_DIR/docker/manifests/acexy.json"
PUSH=0
PUSH_BY_DIGEST=0
REPO=""
DIGEST_FILE=""
PRUNE_AFTER=""
LOAD=0
DRY_RUN=0
# Respect buildx's own instance-selection env var; when neither it nor
# --builder is set, let buildx use the currently selected builder. Forcing
# "default" here would bypass the multi-platform-capable docker-container
# builder that docker/setup-buildx-action creates in GitHub Actions (the
# default docker-driver builder cannot build multi-platform matrices).
BUILDER="${BUILDX_BUILDER:-}"
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
    --acexy-manifest)
      ACEXY_MANIFEST="${2:-}"
      shift 2
      ;;
    --push)
      PUSH=1
      shift
      ;;
    --push-by-digest)
      PUSH_BY_DIGEST=1
      shift
      ;;
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --digest-file)
      DIGEST_FILE="${2:-}"
      shift 2
      ;;
    --prune-builder-after)
      PRUNE_AFTER="${2:-}"
      shift 2
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
if [[ "$PUSH_BY_DIGEST" -eq 1 ]]; then
  if [[ "$PUSH" -eq 1 || "$LOAD" -eq 1 ]]; then
    echo "--push-by-digest cannot be combined with --push or --load."
    exit 1
  fi
  if [[ -z "$REPO" ]]; then
    echo "--push-by-digest needs --repo <name>."
    exit 1
  fi
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

# AceStream-bearing flavors: the Dockerfile's acestream-installer stage resolves
# docker/manifests/acestream.json for each $TARGETPLATFORM on its own (vendored
# archive -> upstream URL -> mirrors), so no per-platform ACESTREAM_* build-args
# are injected here; a global value would apply the same engine to every
# platform of a multi-platform build. Explicit --build-arg ACESTREAM_* values
# still pass through as overrides. We do validate up front that every resolved
# platform has a manifest entry, and print what will be installed.
ACESTREAM_RESOLVER="$ROOT_DIR/docker/scripts/acestream_manifest.py"
ACESTREAM_BEARING_FLAVORS=("scraper-acestream" "scraper-acestream-acexy")
flavor_needs_acestream=0
for f in "${ACESTREAM_BEARING_FLAVORS[@]}"; do
    if [[ "$FLAVOR" == "$f" ]]; then
        flavor_needs_acestream=1
        break
    fi
done
if [[ "$flavor_needs_acestream" -eq 1 ]]; then
    if [[ ! -f "$ACESTREAM_RESOLVER" ]]; then
        echo "AceStream manifest resolver not found: $ACESTREAM_RESOLVER" >&2
        exit 1
    fi
    # The Dockerfile COPYs docker/manifests/acestream.json from the build
    # context, so a custom --acestream-manifest can only describe what a real
    # build would install if it IS that file. Refuse the mismatch instead of
    # printing an engine that will not be built.
    in_context_manifest="$CONTEXT/docker/manifests/acestream.json"
    if [[ "$DRY_RUN" -eq 0 ]] && ! cmp -s "$ACESTREAM_MANIFEST" "$in_context_manifest"; then
        printf 'ERROR: --acestream-manifest %s differs from the manifest the build installs from (%s).\n' \
            "$ACESTREAM_MANIFEST" "$in_context_manifest" >&2
        printf 'Edit the tracked manifest, or pass --build-arg ACESTREAM_* overrides for a single-platform experiment.\n' >&2
        exit 1
    fi
    IFS=',' read -r -a _ace_platforms <<< "$PLATFORMS"
    for _plat in "${_ace_platforms[@]}"; do
        if ! _resolved="$(python3 "$ACESTREAM_RESOLVER" "$ACESTREAM_MANIFEST" --platform "$_plat" --format json 2>&1)"; then
            printf 'ERROR: flavor %s cannot resolve an AceStream engine for %s\n%s\n' "$FLAVOR" "$_plat" "$_resolved" >&2
            exit 1
        fi
        printf 'AceStream engine for %s: %s\n' "$_plat" "$(printf '%s' "$_resolved" | python3 -c '
import json, sys
d = json.load(sys.stdin)
src = ("vendored " + d["ACESTREAM_VENDORED_FILE"]) if d.get("ACESTREAM_VENDORED_FILE") else d.get("ACESTREAM_DOWNLOAD_URL", "")
print("kind=%s version=%s support=%s source=%s" % (d["ACESTREAM_INSTALL_KIND"], d["ACESTREAM_ENGINE_VERSION"], d["ACESTREAM_PLATFORM_SUPPORT"], src))
')"
    done
fi

# Acexy-bearing flavors must compile the real proxy from the pinned upstream
# source in docker/manifests/acexy.json. Without ACEXY_REPO/ACEXY_REF the
# Dockerfile silently builds the test fixture (a stub that prints
# "fixture acexy" and exits), which is only ever wanted for contract tests
# that pass the args explicitly via --build-arg.
ACEXY_BEARING_FLAVORS=("scraper-acexy" "scraper-acestream-acexy")
for f in "${ACEXY_BEARING_FLAVORS[@]}"; do
    if [[ "$FLAVOR" == "$f" ]]; then
        if [[ ! -f "$ACEXY_MANIFEST" ]]; then
            echo "Acexy manifest not found: $ACEXY_MANIFEST" >&2
            exit 1
        fi
        if ! acexy_derived="$(python3 - "$ACEXY_MANIFEST" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
for key in ("repo", "ref"):
    if not m.get(key):
        raise SystemExit(f"acexy manifest missing required key: {key}")
print(f"ACEXY_REPO={m['repo']}")
print(f"ACEXY_REF={m['ref']}")
if m.get("expected_binary_name"):
    print(f"ACEXY_BINARY_NAME={m['expected_binary_name']}")
# Vendored archive (docker/vendor/acexy): the Dockerfile prefers it over the clone.
if m.get("vendored_file"):
    if not m.get("sha256"):
        raise SystemExit("acexy manifest names a vendored_file but no sha256")
    print(f"ACEXY_VENDORED_FILE={m['vendored_file']}")
    print(f"ACEXY_SHA256={m['sha256']}")
PY
)"; then
            printf 'ERROR: failed to derive acexy build args for flavor=%s\n%s\n' "$FLAVOR" "$acexy_derived" >&2
            exit 1
        fi
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
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
        done <<< "$acexy_derived"
        break
    fi
done

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

# Base command shared by every invocation below.
BASE_CMD=(docker buildx build)
if [[ -n "$BUILDER" ]]; then
  BASE_CMD+=(--builder "$BUILDER")
fi
BASE_CMD+=(--file "$DOCKERFILE" --target "$TARGET")
if [[ -n "$NETWORK" ]]; then
  BASE_CMD+=(--network "$NETWORK")
fi
if [[ "${#BUILD_ARGS[@]}" -gt 0 ]]; then
  BASE_CMD+=("${BUILD_ARGS[@]}")
fi

print_plan_header() {
  echo "Flavor: $FLAVOR"
  echo "Target: $TARGET"
  echo "Platforms: $PLATFORMS"
  echo "Tags: ${TAGS[*]}"
}

run_or_print() {
  # run_or_print <argv...>: eval the command, or print it in dry-run mode.
  local cmd_string
  cmd_string="$(printf '%q ' "$@")"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY RUN] ${cmd_string}"
  else
    eval "$cmd_string"
  fi
}

# build_platform_by_digest <repo> <platform> <meta_file>: build one platform and
# push it by digest (no tag). Needs a docker-container (or remote) builder.
build_platform_by_digest() {
  local repo="$1" platform="$2" meta_file="$3"
  echo "Building $platform (push by digest to $repo)"
  run_or_print "${BASE_CMD[@]}" --platform "$platform" \
    --output "type=image,name=$repo,push=true,push-by-digest=true,name-canonical=true" \
    --metadata-file "$meta_file" "$CONTEXT"
}

digest_from_meta() {
  python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["containerimage.digest"])' "$1"
}

prune_builder_after() {
  [[ -n "$PRUNE_AFTER" ]] || return 0
  local builder="${BUILDER:-default}"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[DRY RUN] docker buildx prune --builder $builder -f --max-used-space $PRUNE_AFTER"
    return 0
  fi
  docker buildx prune --builder "$builder" -f --max-used-space "$PRUNE_AFTER" >/dev/null 2>&1 \
    || docker buildx prune --builder "$builder" -f --keep-storage "$PRUNE_AFTER" >/dev/null 2>&1 \
    || true
  echo "Builder $builder cache after prune: $(docker buildx du --builder "$builder" 2>/dev/null | grep -E '^Total:' | tr -s '\t ' ' ' || echo unknown)"
}

if [[ "$PUSH_BY_DIGEST" -eq 1 ]]; then
  if [[ "$PLATFORMS" == *","* ]]; then
    echo "--push-by-digest builds exactly one platform; got: $PLATFORMS"
    exit 1
  fi
  META_DIR="$(mktemp -d)"
  trap 'rm -rf "$META_DIR"' EXIT
  [[ "$DRY_RUN" -eq 1 ]] && print_plan_header
  meta_file="$META_DIR/meta.json"
  build_platform_by_digest "$REPO" "$PLATFORMS" "$meta_file"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    ref="$REPO@<digest-of-$PLATFORMS>"
  else
    ref="$REPO@$(digest_from_meta "$meta_file")"
  fi
  echo "Pushed $PLATFORMS as $ref"
  if [[ -n "$DIGEST_FILE" ]]; then
    printf '%s\n' "$ref" > "$DIGEST_FILE"
  fi
  prune_builder_after
elif [[ "$PUSH" -eq 1 && "$PLATFORMS" == *","* ]]; then
  # Multi-platform PUSH: build one platform at a time and assemble the
  # manifest list afterwards. A single three-platform build runs two QEMU
  # emulations plus the native build concurrently inside BuildKit, which
  # starved the Jenkins runner (16 GB, mostly in use) until the agent's
  # durable-task wrapper stopped heartbeating (PR-162 #2). Sequential
  # per-platform builds cap the peak load; each pushes by digest (no
  # temporary tags) and `docker buildx imagetools create` merges the digests
  # into every requested tag — the documented distributed-build pattern.
  # Needs a docker-container (or remote) builder: the docker driver does not
  # implement push-by-digest (Jenkins uses acestream-builder).
  # Repository = the reference without its tag (the colon after the last
  # slash); registry host:port prefixes such as localhost:5055/name are kept.
  repo=""
  for tag in "${TAGS[@]}"; do
    tag_repo="$(python3 -c '
import sys
ref = sys.argv[1]
head, _, last = ref.rpartition("/")
if ":" in last:
    last = last.split(":", 1)[0]
print(head + "/" + last if head else last)
' "$tag")"
    if [[ -z "$repo" ]]; then
      repo="$tag_repo"
    elif [[ "$repo" != "$tag_repo" ]]; then
      echo "All --tag values must share one repository for a multi-platform push (got $repo and $tag_repo)." >&2
      exit 1
    fi
  done
  META_DIR="$(mktemp -d)"
  trap 'rm -rf "$META_DIR"' EXIT
  [[ "$DRY_RUN" -eq 1 ]] && print_plan_header
  IFS=',' read -r -a platform_list <<< "$PLATFORMS"
  digest_refs=()
  for platform in "${platform_list[@]}"; do
    meta_file="$META_DIR/$(printf '%s' "$platform" | tr '/' '-').json"
    build_platform_by_digest "$repo" "$platform" "$meta_file"
    if [[ "$DRY_RUN" -eq 1 ]]; then
      digest_refs+=("$repo@<digest-of-$platform>")
    else
      digest="$(digest_from_meta "$meta_file")"
      [[ -n "$digest" ]] || { echo "No containerimage.digest in $meta_file" >&2; exit 1; }
      digest_refs+=("$repo@$digest")
    fi
    prune_builder_after
  done
  imagetools_cmd=(docker buildx imagetools create)
  for tag in "${TAGS[@]}"; do
    imagetools_cmd+=(--tag "$tag")
  done
  imagetools_cmd+=("${digest_refs[@]}")
  echo "Assembling manifest list for ${TAGS[*]} from ${#digest_refs[@]} platform digests"
  run_or_print "${imagetools_cmd[@]}"
else
  BUILD_CMD=("${BASE_CMD[@]}" --platform "$PLATFORMS")
  for tag in "${TAGS[@]}"; do
    BUILD_CMD+=(--tag "$tag")
  done
  if [[ "$PUSH" -eq 1 ]]; then
    BUILD_CMD+=(--push)
  elif [[ "$LOAD" -eq 1 ]]; then
    BUILD_CMD+=(--load)
  else
    BUILD_CMD+=(--output type=cacheonly)
  fi
  BUILD_CMD+=("$CONTEXT")
  [[ "$DRY_RUN" -eq 1 ]] && print_plan_header
  run_or_print "${BUILD_CMD[@]}"
  prune_builder_after
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
