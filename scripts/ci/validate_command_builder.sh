#!/usr/bin/env bash
# Validate the Docker command builder page (docs/index.html + docs/builder/).
#
# The page is served by GitHub Pages straight from the docs/ folder of main
# ("Deploy from a branch": main, /docs), so there is nothing to publish — this
# script only makes sure the page cannot drift from the runtime contract:
# flavors match the Dockerfile targets, the ports and env toggles it emits
# still exist in entrypoint.sh / Dockerfile / docker-compose.yml, and the
# script parses. Runs on every CI build (Jenkinsfile stage "Docs checks").
#
# Usage:
#   bash scripts/ci/validate_command_builder.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SITE_DIR="$ROOT/docs"

for arg in "$@"; do
  case "$arg" in
    -h|--help) sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

log() { printf '[command-builder] %s\n' "$*"; }
fail() { printf '[command-builder] ERROR: %s\n' "$*" >&2; exit 1; }

[[ -f "$SITE_DIR/index.html" ]] || fail "docs/index.html is missing"
[[ -f "$SITE_DIR/builder/app.js" ]] || fail "docs/builder/app.js is missing"
[[ -f "$SITE_DIR/builder/runtime-options.json" ]] || fail "docs/builder/runtime-options.json is missing"
[[ -f "$SITE_DIR/.nojekyll" ]] || fail "docs/.nojekyll is missing (GitHub Pages would run Jekyll over docs/)"

python3 - "$ROOT" <<'PY'
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
data = json.loads((root / "docs/builder/runtime-options.json").read_text(encoding="utf-8"))
dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
compose = (root / "docker-compose.yml").read_text(encoding="utf-8")
entrypoint = (root / "entrypoint.sh").read_text(encoding="utf-8")
errors = []

# Every flavor on the page must be a real Dockerfile target, and vice versa.
targets = set(re.findall(r"^FROM .+ AS (scraper[\w-]*)$", dockerfile, flags=re.M))
flavors = {f["id"] for f in data["flavors"]}
if flavors != targets:
    errors.append(f"flavors differ from Dockerfile targets: page={sorted(flavors)} Dockerfile={sorted(targets)}")

# The compose file must still name the image the page generates commands for.
if f"image: {data['image']}:latest" not in compose:
    errors.append(f"docker-compose.yml no longer uses {data['image']}:latest")

# The runtime toggles the page emits must still exist in the entrypoint.
for var in ("ENABLE_ACESTREAM_ENGINE", "ENABLE_ACEXY", "ENABLE_WARP", "ACEXY_HOST", "ACEXY_PORT", "ZERONET_URL", "FLASK_PORT"):
    if var not in entrypoint:
        errors.append(f"entrypoint.sh no longer references {var}")

# Ports the page publishes must match the container-side defaults.
ports = {p["id"]: p for p in data["ports"]}
if ports["web"]["container"] != int(re.search(r'FLASK_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("web port differs from FLASK_PORT default in entrypoint.sh")
if ports["engineApi"]["container"] != int(re.search(r'ACESTREAM_HTTP_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("engine API port differs from ACESTREAM_HTTP_PORT default in entrypoint.sh")
m = re.search(r'ACEXY_STATUS_PORT=(\d+)', dockerfile)
if m and ports["acexy"]["container"] != int(m.group(1)):
    errors.append("acexy port differs from ACEXY_STATUS_PORT in Dockerfile")

for f in data["flavors"]:
    for key in ("releaseTag", "developTag", "versionTagPattern"):
        if not f.get(key):
            errors.append(f"flavor {f['id']} is missing {key}")

if errors:
    print("[command-builder] docs/builder/runtime-options.json is out of sync:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
print(f"[command-builder] runtime-options.json ok: {len(flavors)} flavors, {len(data['ports'])} ports, {len(data['volumes'])} volumes")
PY

if command -v node >/dev/null 2>&1; then
  node --check "$SITE_DIR/builder/app.js"
  log "app.js syntax ok"
else
  log "node not available; skipped the app.js syntax check"
fi
log "command builder ok"
