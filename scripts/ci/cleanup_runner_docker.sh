#!/usr/bin/env bash
# Reclaim Docker disk space on the shared CI runner. The Jenkins pipelines
# serialize through one NUC/Docker lock before invoking this script.
#
# Removes, in order:
#   1. this repo's transient CI images older than --transient-age-hours
#      (acestream-scraper:smoke-*, acestream-scraper:release-smoke,
#       acestream-scraper-smoke:*, acestream-installer-test:*,
#       acestream-scraper-task3:*, acestream-scraper-pr-ci:pr-*) — leaked when
#      a test run crashes before
#      its finalizers or when a build tag was never cleaned up;
#   2. dangling layers and unused images older than --image-age-hours (or all
#      unused images with --all-unused-images);
#   3. every builder's BuildKit cache above --builder-keep (default 3GB).
#   4. optionally verifies that the workspace and Docker filesystems have at
#      least --min-free-gb available, failing early when cleanup was insufficient.
# --keep excludes tags from the explicit transient sweep. Images that must also
# survive --all-unused-images carry org.acestream-scraper.ci.keep=true.
#
# Usage: cleanup_runner_docker.sh [--keep <image:tag>]... [--transient-age-hours N]
#        [--image-age-hours N] [--all-unused-images] [--builder-keep SIZE]
#        [--min-free-gb N] [--dry-run]
set -euo pipefail

TRANSIENT_AGE_HOURS=3
IMAGE_AGE_HOURS=24
BUILDER_KEEP="3GB"
ALL_UNUSED_IMAGES=0
MIN_FREE_GB=0
DRY_RUN=0
KEEP=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP+=("${2:-}"); shift 2 ;;
    --transient-age-hours) TRANSIENT_AGE_HOURS="${2:-}"; shift 2 ;;
    --image-age-hours) IMAGE_AGE_HOURS="${2:-}"; shift 2 ;;
    --all-unused-images) ALL_UNUSED_IMAGES=1; shift ;;
    --builder-keep) BUILDER_KEEP="${2:-}"; shift 2 ;;
    --min-free-gb) MIN_FREE_GB="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if ! [[ "$MIN_FREE_GB" =~ ^[0-9]+$ ]]; then
  echo "--min-free-gb must be a non-negative integer" >&2
  exit 2
fi

run() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] %s\n' "$*"
  else
    "$@" || true
  fi
}

echo "Docker disk usage before cleanup:"
docker system df 2>/dev/null || true

# 1. Transient CI images older than the threshold (never the ones we keep).
KEEP_JSON="$(printf '%s\n' "${KEEP[@]+"${KEEP[@]}"}" | python3 -c 'import json,sys; print(json.dumps([l for l in sys.stdin.read().splitlines() if l]))')"
stale="$(docker images --format '{{.Repository}}:{{.Tag}}|{{.CreatedAt}}' 2>/dev/null \
  | KEEP_JSON="$KEEP_JSON" AGE_HOURS="$TRANSIENT_AGE_HOURS" python3 -c '
import json, os, re, sys
from datetime import datetime, timedelta, timezone
keep = set(json.loads(os.environ["KEEP_JSON"]))
age = timedelta(hours=float(os.environ["AGE_HOURS"]))
now = datetime.now(timezone.utc)
patterns = [
    r"^acestream-scraper:smoke-",
    r"^acestream-scraper:release-smoke$",
    r"^acestream-scraper-smoke:",
    r"^acestream-installer-test:",
    r"^acestream-scraper-task3:",
    r"^acestream-scraper-pr-ci:pr-",
]
for line in sys.stdin:
    line = line.strip()
    if "|" not in line:
        continue
    ref, created = line.split("|", 1)
    if ref in keep or not any(re.search(p, ref) for p in patterns):
        continue
    # docker prints e.g. "2026-08-28 07:01:12 +0000 UTC"
    m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([+-]\d{4})", created)
    if not m:
        continue
    ts = datetime.strptime(m.group(1) + m.group(2), "%Y-%m-%d %H:%M:%S%z")
    if now - ts >= age:
        print(ref)
')"
if [[ -n "$stale" ]]; then
  echo "Removing transient CI images older than ${TRANSIENT_AGE_HOURS}h:"
  printf '  %s\n' $stale
  # shellcheck disable=SC2086
  run docker image rm -f $stale
else
  echo "No transient CI images older than ${TRANSIENT_AGE_HOURS}h."
fi

# 2. Dangling layers + unused images older than the threshold.
run docker image prune -f
if [[ "$ALL_UNUSED_IMAGES" -eq 1 ]]; then
  run docker image prune -af \
    --filter "label!=org.acestream-scraper.ci.keep=true"
else
  run docker image prune -af \
    --filter "until=${IMAGE_AGE_HOURS}h" \
    --filter "label!=org.acestream-scraper.ci.keep=true"
fi

# 3. Bound the BuildKit cache of EVERY builder. The docker-container builder
#    (acestream-builder) keeps its cache in its own volume, invisible to
#    `docker system df`'s "Build Cache" line and untouched by a prune of the
#    default builder — that volume grew to 6 GB on a 32 GB disk (PR-162 #2/#3).
#    Newer buildx spells the cap --max-used-space; older --keep-storage.
prune_builder() {
  local builder="$1"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    printf '[dry-run] docker buildx prune --builder %s -f (keep %s)\n' "$builder" "$BUILDER_KEEP"
    return 0
  fi
  docker buildx prune --builder "$builder" -f --max-used-space "$BUILDER_KEEP" >/dev/null 2>&1 \
    || docker buildx prune --builder "$builder" -f --keep-storage "$BUILDER_KEEP" >/dev/null 2>&1 \
    || true
  printf 'builder %s cache: %s\n' "$builder" "$(docker buildx du --builder "$builder" 2>/dev/null | grep -E '^Total:' | tr -s '\t ' ' ' || echo unknown)"
}
builders="$(docker buildx ls 2>/dev/null | awk 'NR>1 && $1 !~ /^\\_/ && $1 != "" {sub(/\*$/, "", $1); print $1}' | sort -u)"
if [[ -z "$builders" ]]; then
  builders="default"
fi
for builder in $builders; do
  prune_builder "$builder"
done

echo "Docker disk usage after cleanup:"
docker system df 2>/dev/null || true
agent_path="${JENKINS_AGENT_DIR:-${WORKSPACE:-/}}"
df -h "$agent_path" 2>/dev/null || true

if [[ "$MIN_FREE_GB" -gt 0 && "$DRY_RUN" -eq 0 ]]; then
  check_paths=("$agent_path")
  docker_root="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || true)"
  if [[ -n "$docker_root" && "$docker_root" != "$agent_path" ]]; then
    check_paths+=("$docker_root")
  fi
  required_kb=$((MIN_FREE_GB * 1024 * 1024))
  for check_path in "${check_paths[@]}"; do
    available_kb="$(df -Pk "$check_path" 2>/dev/null | awk 'NR == 2 {print $4}')"
    if ! [[ "$available_kb" =~ ^[0-9]+$ ]]; then
      echo "Unable to verify free space for $check_path after cleanup." >&2
      exit 1
    fi
    if (( available_kb < required_kb )); then
      available_gb=$((available_kb / 1024 / 1024))
      echo "Cleanup left only ${available_gb}GB free on $check_path; ${MIN_FREE_GB}GB is required before building." >&2
      exit 1
    fi
  done
  echo "Free-space preflight passed (minimum ${MIN_FREE_GB}GB)."
fi
