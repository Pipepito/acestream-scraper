#!/usr/bin/env bash
# Promote the floating :latest tag by RETAGGING the already-published,
# canary-validated version manifest — never by rebuilding. Rebuilding for the
# promotion run would push images that differ from the ones that were
# validated (builds are not bit-reproducible) and costs a full multi-platform
# build on the runner.
#
# Usage: promote_latest.sh --version <vX.Y.Z> [--repo pipepito/acestream-scraper]
#                          [--flavor scraper-acestream-acexy] [--dry-run]
#
# Steps: (1) the source manifest <repo>:<version> must exist in the registry
# (docker buildx imagetools inspect); (2) docker buildx imagetools create
# -t <repo>:latest <repo>:<version>; (3) verify_multiarch_manifest.sh checks
# :latest carries every platform the flavor requires.
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
REPO="pipepito/acestream-scraper"
VERSION=""
FLAVOR="scraper-acestream-acexy"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="${2:-}"; shift 2 ;;
    --repo) REPO="${2:-}"; shift 2 ;;
    --flavor) FLAVOR="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$VERSION" ]]; then
  echo "promote_latest: --version is required (e.g. $(tr -d '\n' < "$ROOT_DIR/version.txt" 2>/dev/null || echo vX.Y.Z))" >&2
  exit 1
fi

SOURCE="$REPO:$VERSION"
TARGET="$REPO:latest"

echo "promote_latest: $TARGET <- $SOURCE (retag of the canary-validated manifest; no rebuild)"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[dry-run] docker buildx imagetools inspect $SOURCE"
  echo "[dry-run] docker buildx imagetools create -t $TARGET $SOURCE"
  echo "[dry-run] bash scripts/ci/verify_multiarch_manifest.sh --image $TARGET --flavor $FLAVOR"
  exit 0
fi

if ! docker buildx imagetools inspect "$SOURCE" >/dev/null 2>&1; then
  echo "promote_latest: $SOURCE is not in the registry. Run the phase-1 publish (PUBLISH_LATEST=0) for this version first." >&2
  exit 1
fi

docker buildx imagetools create -t "$TARGET" "$SOURCE"
bash "$ROOT_DIR/scripts/ci/verify_multiarch_manifest.sh" --image "$TARGET" --flavor "$FLAVOR"
echo "promote_latest: $TARGET now points at $SOURCE"
