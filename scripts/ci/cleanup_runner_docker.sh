#!/usr/bin/env bash
# Reclaim Docker disk space on a shared CI runner (dorat-nuc-ci has a small
# disk; two Jenkins jobs build the same commit concurrently).
#
# Removes, in order:
#   1. this repo's transient CI images older than --transient-age-hours
#      (acestream-scraper:smoke-*, acestream-scraper:release-smoke,
#       acestream-scraper-smoke:*, acestream-installer-test:*,
#       acestream-scraper-task3:*) — leaked when a test run crashes before
#      its finalizers or when a build tag was never cleaned up;
#   2. dangling layers and unused images older than --image-age-hours;
#   3. every builder's BuildKit cache above --builder-keep (default 3GB).
# Images named in --keep are never touched (the current build's own tags).
#
# Usage: cleanup_runner_docker.sh [--keep <image:tag>]... [--transient-age-hours N]
#        [--image-age-hours N] [--builder-keep SIZE] [--dry-run]
set -euo pipefail

TRANSIENT_AGE_HOURS=3
IMAGE_AGE_HOURS=24
BUILDER_KEEP="3GB"
DRY_RUN=0
KEEP=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --keep) KEEP+=("${2:-}"); shift 2 ;;
    --transient-age-hours) TRANSIENT_AGE_HOURS="${2:-}"; shift 2 ;;
    --image-age-hours) IMAGE_AGE_HOURS="${2:-}"; shift 2 ;;
    --builder-keep) BUILDER_KEEP="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

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
run docker image prune -af \
  --filter "until=${IMAGE_AGE_HOURS}h" \
  --filter "label!=org.acestream-scraper.ci.keep=true"

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
df -h "${JENKINS_AGENT_DIR:-${WORKSPACE:-/}}" 2>/dev/null || true
