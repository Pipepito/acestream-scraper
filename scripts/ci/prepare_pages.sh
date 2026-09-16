#!/usr/bin/env bash
# Prepare the tracked extraction helper for GitHub Pages (main /docs).
# Requires frontend dependencies installed. Never publishes or uses credentials.
# --check compares the existing fresh frontend build with the committed payload.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
case "${1:-}" in
  '')
    npm --prefix "$ROOT/frontend" run build:recipes
    ;;
  --check) ;;
  *) printf 'Usage: bash scripts/ci/prepare_pages.sh [--check]\n' >&2; exit 2 ;;
esac

SOURCE="$ROOT/frontend/dist-recipes"
TARGET="$ROOT/docs/recipes"
[[ -f "$SOURCE/index.html" ]] || {
  printf 'Build the helper first: npm --prefix frontend run build:recipes\n' >&2
  exit 1
}
if [[ "${1:-}" == '--check' ]]; then
  if ! diff -qr "$SOURCE" "$TARGET"; then
    printf 'Pages helper is stale. Run bash scripts/ci/prepare_pages.sh and commit docs/recipes/.\n' >&2
    exit 1
  fi
  printf 'Pages helper matches the frontend build.\n'
else
  # This directory contains only generated, tracked Pages assets.
  rm -rf "$TARGET"
  mkdir -p "$TARGET"
  cp -R "$SOURCE"/. "$TARGET"/
  printf 'Prepared docs/recipes/. Commit these assets with their source changes.\n'
fi
