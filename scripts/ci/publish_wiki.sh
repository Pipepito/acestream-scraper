#!/usr/bin/env bash
# Sync the repository's wiki/ folder to the GitHub wiki.
#
# The GitHub wiki is its own git repository (<repo>.wiki.git). This script
# clones it, replaces its pages with the contents of wiki/, rewrites the
# relative Markdown links so they resolve as wiki page names, and pushes a
# commit only when something changed. Files that exist in the wiki but not in
# wiki/ are removed, so the folder is the single source of truth.
#
# Link rewriting (repo files stay normal, previewable Markdown):
#   [FAQ](FAQ.md)                    -> [FAQ](FAQ)
#   [x](Docker.md#some-section)      -> [x](Docker#some-section)
#   [x](tasks/channel-management.md) -> [x](channel-management)   (wiki flattens folders)
# Absolute URLs, anchors-only links and non-.md targets are left alone.
#
# Usage:
#   bash scripts/ci/publish_wiki.sh [--dry-run]
#
# Exit codes: 0 published or nothing to do; 1 error; 3 wiki repository not
# initialised (GitHub only creates <repo>.wiki.git after the first page is
# created in the web UI — create any page once, then re-run).
#
# Environment:
#   GITHUB_PUBLISH_USERNAME / GITHUB_PUBLISH_TOKEN  (Jenkins 'github-publish')
#   WIKI_REMOTE_URL   override the wiki push URL (default: derived from origin)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WIKI_DIR="$ROOT/wiki"
DRY_RUN=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

log() { printf '[publish-wiki] %s\n' "$*"; }
fail() { printf '[publish-wiki] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -d "$WIKI_DIR" ]] || fail "wiki/ directory is missing"
[[ -f "$WIKI_DIR/Home.md" ]] || fail "wiki/Home.md is missing (the wiki needs a Home page)"

origin_url="$(git -C "$ROOT" remote get-url origin)"
base_url="${origin_url%.git}"
case "$base_url" in
  git@github.com:*) base_url="https://github.com/${base_url#git@github.com:}" ;;
  ssh://git@github.com/*) base_url="https://github.com/${base_url#ssh://git@github.com/}" ;;
esac
remote_url="${WIKI_REMOTE_URL:-$base_url.wiki.git}"
source_sha="$(git -C "$ROOT" rev-parse --short HEAD)"
source_branch="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo detached)"

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# --- Render wiki/ into the flattened, link-rewritten page set -------------------
rendered="$work/rendered"
mkdir -p "$rendered"
python3 - "$WIKI_DIR" "$rendered" <<'PY'
import re, shutil, sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
link_re = re.compile(r"(\]\()([^)\s]+?)\.md(#[^)\s]*)?(\))")

def rewrite(match):
    target = match.group(2)
    if re.match(r"^[a-z]+:", target):  # http:, https:, mailto: ...
        return match.group(0)
    page = target.rsplit("/", 1)[-1]  # the wiki has no folders
    return f"{match.group(1)}{page}{match.group(3) or ''}{match.group(4)}"

seen = {}
for path in sorted(src.rglob("*")):
    if path.is_dir() or path.name.startswith("."):
        continue
    rel = path.relative_to(src)
    out = dst / path.name  # flatten: GitHub wiki pages have no directory structure
    if path.name in seen:
        print(f"[publish-wiki] ERROR: duplicate page name {path.name}: {seen[path.name]} and {rel}", file=sys.stderr)
        sys.exit(1)
    seen[path.name] = rel
    if path.suffix.lower() == ".md":
        out.write_text(link_re.sub(rewrite, path.read_text(encoding="utf-8")), encoding="utf-8")
    else:
        shutil.copy2(path, out)
print(f"[publish-wiki] rendered {len(seen)} files")
PY

log "target: $remote_url"
log "source: $source_branch@$source_sha"

if [[ "$DRY_RUN" -eq 1 ]]; then
  log "dry-run: rendered pages:"
  (cd "$rendered" && ls -1 | sed 's/^/  /')
  log "dry-run: example rewritten links:"
  grep -rhoE '\]\([A-Za-z0-9_-]+(#[^)]*)?\)' "$rendered" | sort -u | head -8 | sed 's/^/  /'
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

# --- Clone the wiki, replace its content, push if changed -------------------------
clone="$work/wiki"
if ! git clone -q --depth 1 "$remote_url" "$clone" 2>"$work/clone.err"; then
  if grep -qiE 'not found|does not exist|access rights|repository .* not found' "$work/clone.err"; then
    printf '[publish-wiki] The wiki repository %s is not initialised (or the token cannot reach it).\n' "$remote_url" >&2
    printf '[publish-wiki] GitHub creates it after the first page is saved in the web UI: open the Wiki tab, create any page once, then re-run.\n' >&2
    exit 3
  fi
  cat "$work/clone.err" >&2
  fail "could not clone the wiki repository"
fi

find "$clone" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -R "$rendered"/. "$clone"/

git -C "$clone" add -A
if git -C "$clone" diff --cached --quiet; then
  log "wiki already up to date; nothing to push"
  exit 0
fi

git -C "$clone" -c user.name="acestream-scraper CI" -c user.email="ci@users.noreply.github.com" \
  commit -q -m "Sync wiki from $source_branch@$source_sha"
git -C "$clone" push -q origin HEAD
log "published $(git -C "$clone" diff --stat HEAD~1 | tail -1)"
