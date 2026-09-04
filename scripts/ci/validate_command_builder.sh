#!/usr/bin/env bash
# Validate the Docker command builder page (docs/index.html + docs/builder/).
#
# Validated develop builds publish the page to the gh-pages branch. This script
# makes sure the payload is complete and cannot drift from the runtime contract:
# flavors match the Dockerfile targets, the ports and environment settings it
# emits still exist in the image or backend runtime, and the
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
[[ -f "$SITE_DIR/builder/style.css" ]] || fail "docs/builder/style.css is missing"
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
builder = (root / "docs/builder/app.js").read_text(encoding="utf-8")
backend_runtime = "\n".join(
    path.read_text(encoding="utf-8")
    for path in (root / "backend/app").rglob("*.py")
)
runtime_sources = "\n".join(
    [
        entrypoint,
        dockerfile,
        backend_runtime,
        (root / "warp-setup.sh").read_text(encoding="utf-8"),
    ]
)
errors = []

# Every flavor on the page must be a real Dockerfile target, and vice versa.
targets = set(re.findall(r"^FROM .+ AS (scraper[\w-]*)$", dockerfile, flags=re.M))
flavors = {f["id"] for f in data["flavors"]}
if flavors != targets:
    errors.append(f"flavors differ from Dockerfile targets: page={sorted(flavors)} Dockerfile={sorted(targets)}")

# Platform feature switches must match what the image actually installs. This
# catches silent UI drift such as hiding WARP on arm64 after the Dockerfile grew
# arm64 package support.
warp_platforms = {p["id"] for p in data["platforms"] if p.get("warpAvailable")}
warp_install = re.search(r'case "\$TARGETARCH" in ([^)]+)\).*?cloudflare-warp', dockerfile, flags=re.S)
if not warp_install:
    errors.append("could not determine WARP platforms from Dockerfile")
else:
    docker_warp_platforms = set(warp_install.group(1).split("|"))
    if warp_platforms != docker_warp_platforms:
        errors.append(
            "WARP platforms differ from Dockerfile: "
            f"page={sorted(warp_platforms)} Dockerfile={sorted(docker_warp_platforms)}"
        )

# The compose file must still name the image the page generates commands for.
if f"image: {data['image']}:latest" not in compose:
    errors.append(f"docker-compose.yml no longer uses {data['image']}:latest")

# The runtime toggles the page emits must still exist in the entrypoint.
for var in ("ENABLE_ACESTREAM_ENGINE", "ENABLE_ACEXY", "ENABLE_WARP", "ACEXY_HOST", "ACEXY_PORT", "ZERONET_URL", "ENABLE_ZERONET", "ENABLE_IPFS", "IPFS_GATEWAY_URL", "FLASK_PORT", "PUBLIC_BASE_URL", "TUNER_ALLOWED_NETWORKS", "PLAYER_MAX_SESSIONS"):
    if var not in entrypoint:
        errors.append(f"entrypoint.sh no longer references {var}")

# Advanced environment settings are declarative so adding a runtime knob does
# not require another hard-coded HTML field. Their applicability is part of the
# safety contract: unsupported image/platform options must never be rendered or
# emitted for the current selection.
groups = {group["id"] for group in data.get("settingGroups", [])}
settings = data.get("runtimeSettings", [])
allowed_types = {"text", "password", "number", "boolean"}
allowed_conditions = {
    "always",
    "engineOn",
    "zeronetEmbeddedOn",
    "zeronetUiPublished",
    "ipfsEmbeddedOn",
    "warpOn",
}
expected_conditions = {
    "ACESTREAM_BIND_ALL": "engineOn",
    "ENABLE_TOR": "zeronetEmbeddedOn",
    "ZERONET_UI_HOST": "zeronetUiPublished",
    "IPFS_PROFILE": "ipfsEmbeddedOn",
    "WARP_LICENSE_KEY": "warpOn",
}
seen_ids = set()
seen_env = set()
inherited_runtime_env = {"TZ"}
for setting in settings:
    setting_id = setting.get("id")
    env_name = setting.get("env")
    if not setting_id or setting_id in seen_ids:
        errors.append(f"runtime setting id is missing or duplicated: {setting_id!r}")
    seen_ids.add(setting_id)
    if not env_name or env_name in seen_env:
        errors.append(f"runtime setting env is missing or duplicated: {env_name!r}")
    seen_env.add(env_name)
    if setting.get("group") not in groups:
        errors.append(f"runtime setting {setting_id} references unknown group {setting.get('group')!r}")
    if setting.get("type") not in allowed_types:
        errors.append(f"runtime setting {setting_id} has unknown type {setting.get('type')!r}")
    if "integer" in setting and (
        setting.get("type") != "number" or not isinstance(setting.get("integer"), bool)
    ):
        errors.append(f"runtime setting {setting_id} has invalid integer constraint")
    if setting.get("appliesWhen") not in allowed_conditions:
        errors.append(f"runtime setting {setting_id} has unknown appliesWhen {setting.get('appliesWhen')!r}")
    if env_name and env_name not in runtime_sources and env_name not in inherited_runtime_env:
        errors.append(f"runtime setting {env_name} is not referenced by the image or backend runtime")
for env_name, condition in expected_conditions.items():
    matches = [setting for setting in settings if setting.get("env") == env_name]
    if not matches or matches[0].get("appliesWhen") != condition:
        errors.append(f"runtime setting {env_name} must use appliesWhen={condition}")
if "engineOn && platform.id !== 'amd64'" not in builder:
    errors.append("engine state volume is not limited to ARM engine selections")

for required in ("WARP_ENABLE_NAT", "/dev/net/tun:/dev/net/tun", "--cap-add NET_ADMIN", "--cap-add SYS_ADMIN"):
    if required not in builder:
        errors.append(f"command builder no longer emits required WARP setting: {required}")

# Ports the page publishes must match the container-side defaults.
ports = {p["id"]: p for p in data["ports"]}
if ports["web"]["container"] != int(re.search(r'FLASK_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("web port differs from FLASK_PORT default in entrypoint.sh")
if ports["engineApi"]["container"] != int(re.search(r'ACESTREAM_HTTP_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("engine API port differs from ACESTREAM_HTTP_PORT default in entrypoint.sh")
m = re.search(r'ACEXY_STATUS_PORT=(\d+)', dockerfile)
if m and ports["acexy"]["container"] != int(m.group(1)):
    errors.append("acexy port differs from ACEXY_STATUS_PORT in Dockerfile")
if ports["ipfsGateway"]["container"] != int(re.search(r'IPFS_GATEWAY_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("IPFS gateway port differs from IPFS_GATEWAY_PORT default in entrypoint.sh")
if ports["ipfsSwarm"]["container"] != int(re.search(r'IPFS_SWARM_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("IPFS swarm port differs from IPFS_SWARM_PORT default in entrypoint.sh")
if ports["zeronetUi"]["container"] != int(re.search(r'ZERONET_UI_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("ZeroNet UI port differs from ZERONET_UI_PORT default in entrypoint.sh")
if ports["zeronetFileserver"]["container"] != int(re.search(r'ZERONET_FILESERVER_PORT:-(\d+)', entrypoint).group(1)):
    errors.append("ZeroNet fileserver port differs from ZERONET_FILESERVER_PORT default in entrypoint.sh")

if data["player"]["maxSessionsDefault"] != int(re.search(r'PLAYER_MAX_SESSIONS:-(\d+)', entrypoint).group(1)):
    errors.append("player.maxSessionsDefault differs from PLAYER_MAX_SESSIONS default in entrypoint.sh")
if data["player"]["tunerNetworksDefault"] != re.search(r'TUNER_ALLOWED_NETWORKS:-([^}]+)\}', entrypoint).group(1):
    errors.append("player.tunerNetworksDefault differs from TUNER_ALLOWED_NETWORKS default in entrypoint.sh")
if data["player"]["startTimeoutSecondsDefault"] != int(re.search(r'PLAYER_START_TIMEOUT_SECONDS:-(\d+)', entrypoint).group(1)):
    errors.append("player.startTimeoutSecondsDefault differs from PLAYER_START_TIMEOUT_SECONDS default in entrypoint.sh")
if data["player"]["mediaServerMinRefreshMinutesDefault"] != int(re.search(r'MEDIA_SERVER_MIN_REFRESH_MINUTES:-(\d+)', entrypoint).group(1)):
    errors.append("player.mediaServerMinRefreshMinutesDefault differs from MEDIA_SERVER_MIN_REFRESH_MINUTES default in entrypoint.sh")
if data["player"]["forwardedAllowIpsDefault"] != re.search(r'FORWARDED_ALLOW_IPS:-([^}]+)\}', entrypoint).group(1):
    errors.append("player.forwardedAllowIpsDefault differs from FORWARDED_ALLOW_IPS default in entrypoint.sh")
if data["player"]["hlsDirDefault"] != re.search(r'PLAYER_HLS_DIR:-([^}]+)\}', entrypoint).group(1):
    errors.append("player.hlsDirDefault differs from PLAYER_HLS_DIR default in entrypoint.sh")

for f in data["flavors"]:
    for key in ("releaseTag", "developTag", "versionTagPattern"):
        if not f.get(key):
            errors.append(f"flavor {f['id']} is missing {key}")

if errors:
    print("[command-builder] docs/builder/runtime-options.json is out of sync:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
print(f"[command-builder] runtime-options.json ok: {len(flavors)} flavors, {len(data['ports'])} ports, {len(data['volumes'])} volumes, {len(settings)} conditional settings")
PY

if command -v node >/dev/null 2>&1; then
  node --check "$SITE_DIR/builder/app.js"
  log "app.js syntax ok"
else
  log "node not available; skipped the app.js syntax check"
fi
log "command builder ok"
