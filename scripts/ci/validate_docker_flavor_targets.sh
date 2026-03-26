#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BUILD_PROGRESS=${BUILD_PROGRESS:-auto}

if ! command -v docker >/dev/null 2>&1; then
    printf 'docker is required for Docker flavor validation\n' >&2
    exit 1
fi

targets=(
    scraper:false:false
    scraper-acestream:true:false
    scraper-acexy:false:true
    scraper-acestream-acexy:true:true
)

ACESTREAM_DOWNLOAD_URL=${ACESTREAM_DOWNLOAD_URL:-}
ACESTREAM_DOWNLOAD_SHA256=${ACESTREAM_DOWNLOAD_SHA256:-}
ACESTREAM_ARCHIVE_TYPE=${ACESTREAM_ARCHIVE_TYPE:-tar.gz}
ACESTREAM_STRIP_COMPONENTS=${ACESTREAM_STRIP_COMPONENTS:-1}
ACESTREAM_BINARY_PATH=${ACESTREAM_BINARY_PATH:-start-engine}
ACEXY_REPO=${ACEXY_REPO:-fixture}
ACEXY_REF=${ACEXY_REF:-fixture}
ACEXY_BINARY_NAME=${ACEXY_BINARY_NAME:-acexy}

for target_spec in "${targets[@]}"; do
    IFS=':' read -r target expected_acestream expected_acexy <<< "$target_spec"
    image_tag="acestream-scraper-task3:${target}"

    printf 'Validating target %s\n' "$target"

    docker buildx build \
        --platform linux/amd64 \
        --load \
        --progress "$BUILD_PROGRESS" \
        --target "$target" \
        --tag "$image_tag" \
        --build-arg "ACESTREAM_DOWNLOAD_URL=$ACESTREAM_DOWNLOAD_URL" \
        --build-arg "ACESTREAM_DOWNLOAD_SHA256=$ACESTREAM_DOWNLOAD_SHA256" \
        --build-arg "ACESTREAM_ARCHIVE_TYPE=$ACESTREAM_ARCHIVE_TYPE" \
        --build-arg "ACESTREAM_STRIP_COMPONENTS=$ACESTREAM_STRIP_COMPONENTS" \
        --build-arg "ACESTREAM_BINARY_PATH=$ACESTREAM_BINARY_PATH" \
        --build-arg "ACEXY_REPO=$ACEXY_REPO" \
        --build-arg "ACEXY_REF=$ACEXY_REF" \
        --build-arg "ACEXY_BINARY_NAME=$ACEXY_BINARY_NAME" \
        "$ROOT_DIR"

    python3 - "$image_tag" "$expected_acestream" "$expected_acexy" <<'PY'
import json
import subprocess
import sys

image_tag, expected_acestream, expected_acexy = sys.argv[1:4]
result = subprocess.run(
    ["docker", "image", "inspect", image_tag],
    check=True,
    capture_output=True,
    text=True,
)
payload = json.loads(result.stdout)[0]
env_entries = payload.get("Config", {}).get("Env", [])
env_map = {}
for entry in env_entries:
    if "=" not in entry:
        continue
    key, value = entry.split("=", 1)
    env_map[key] = value

checks = {
    "IMAGE_HAS_ACESTREAM": expected_acestream,
    "IMAGE_HAS_ACEXY": expected_acexy,
    "ENABLE_WARP": "false",
    "ENABLE_ACESTREAM_ENGINE": "false",
    "ENABLE_ACEXY": "false",
}

for key, expected in checks.items():
    actual = env_map.get(key)
    if actual != expected:
        raise SystemExit(f"{image_tag}: expected {key}={expected}, got {actual!r}")

entrypoint = payload.get("Config", {}).get("Entrypoint") or []
if not any("entrypoint.sh" in part for part in entrypoint):
    raise SystemExit(f"{image_tag}: entrypoint.sh not configured in image entrypoint {entrypoint!r}")

healthcheck = payload.get("Config", {}).get("Healthcheck") or {}
test = healthcheck.get("Test") or []
if not any("healthcheck.sh" in part for part in test):
    raise SystemExit(f"{image_tag}: healthcheck.sh not configured in image healthcheck {test!r}")

print(f"validated {image_tag}")
PY
done

printf 'All Docker flavor targets validated successfully\n'
