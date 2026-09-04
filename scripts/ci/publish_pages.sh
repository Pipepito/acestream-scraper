#!/usr/bin/env bash
# Publish the Docker command builder to GitHub Pages.
#
# The builder is a static page (docs/index.html + docs/builder/, no build
# step). This script assembles exactly that payload — index.html, builder/,
# .nojekyll — and pushes it to the gh-pages branch of the repository; GitHub
# Pages is configured once to serve gh-pages / root ("Deploy from a branch"),
# so a validated Jenkins build is the deployment and no GitHub Actions
# workflow is authored here. Only the site files are published: the rest of
# docs/ (operator guides and so on) stays out of the Pages payload.
#
# The gh-pages branch is created on the first publish; afterwards the script
# commits on top of it and pushes only when the content changed.
#
# Usage:
#   bash scripts/ci/publish_pages.sh [--dry-run]
#
# Exit codes: 0 published or nothing to do; 1 error.
#
# Environment:
#   GITHUB_PUBLISH_USERNAME / GITHUB_PUBLISH_TOKEN  (Jenkins 'github-publish')
#   PAGES_REMOTE_URL  override the push URL (default: derived from origin)
#   PAGES_BRANCH      target branch (default: gh-pages)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,23p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

log() { printf '[publish-pages] %s\n' "$*"; }
fail() { printf '[publish-pages] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -f "$ROOT/docs/index.html" ]] || fail "docs/index.html is missing"
[[ -d "$ROOT/docs/builder" ]] || fail "docs/builder/ is missing"
[[ -f "$ROOT/docs/builder/runtime-options.json" ]] || fail "docs/builder/runtime-options.json is missing"

origin_url="$(git -C "$ROOT" remote get-url origin)"
base_url="${origin_url%.git}"
case "$base_url" in
  git@github.com:*) base_url="https://github.com/${base_url#git@github.com:}" ;;
  ssh://git@github.com/*) base_url="https://github.com/${base_url#ssh://git@github.com/}" ;;
esac
remote_url="${PAGES_REMOTE_URL:-$base_url.git}"
branch="${PAGES_BRANCH:-gh-pages}"
source_sha="$(git -C "$ROOT" rev-parse --short HEAD)"
source_branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# --- Assemble the Pages payload (site files only, nothing else from docs/) ------
payload="$work/payload"
mkdir -p "$payload"
cp "$ROOT/docs/index.html" "$payload/index.html"
cp -R "$ROOT/docs/builder" "$payload/builder"
touch "$payload/.nojekyll"

log "target: $remote_url ($branch)"
log "source: $source_branch@$source_sha"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "dry-run: payload:"
  (cd "$payload" && find . -type f | sort | sed 's/^/  /')
  exit 0
fi

[[ -n "${GITHUB_PUBLISH_USERNAME:-}" && -n "${GITHUB_PUBLISH_TOKEN:-}" ]] \
  || fail "GITHUB_PUBLISH_USERNAME and GITHUB_PUBLISH_TOKEN are required to publish"

askpass="$work/askpass.sh"
cat > "$askpass" <<'ASK'
#!/usr/bin/env bash
case "$1" in
  Username*) printf '%s\n' "$GITHUB_PUBLISH_USERNAME" ;;
  Password*) printf '%s\n' "$GITHUB_PUBLISH_TOKEN" ;;
esac
ASK
chmod 700 "$askpass"
export GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0

# --- Clone gh-pages (or start it), replace its content, push if changed ---------
clone="$work/site"
if git clone -q --depth 1 --branch "$branch" "$remote_url" "$clone" 2>"$work/clone.err"; then
  find "$clone" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
else
  if ! grep -qiE "not found in upstream|could not find remote branch" "$work/clone.err"; then
    cat "$work/clone.err" >&2
    fail "could not clone $branch from $remote_url"
  fi
  log "$branch does not exist yet; creating it"
  git init -q "$clone"
  git -C "$clone" checkout -q --orphan "$branch"
  git -C "$clone" remote add origin "$remote_url"
fi

cp -R "$payload"/. "$clone"/

git -C "$clone" add -A
if git -C "$clone" diff --cached --quiet; then
  log "Pages site already up to date; nothing to push"
  exit 0
fi

git -C "$clone" -c user.name="acestream-scraper CI" -c user.email="ci@users.noreply.github.com" \
  commit -q -m "Publish command builder from $source_branch@$source_sha"
git -C "$clone" push -q origin "HEAD:refs/heads/$branch"
log "published $branch from $source_branch@$source_sha"
