# Shared paths/ports for the e2e stack scripts. Source, do not execute.
E2E_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_ROOT="$(cd "$E2E_DIR/.." && pwd)"
STACK_DIR="$E2E_DIR/.stack"
COMPOSE_FILE="$E2E_DIR/stack/docker-compose.e2e.yml"

export E2E_APP_PORT="${E2E_APP_PORT:-8000}"
export E2E_ENGINE_URL="${E2E_ENGINE_URL:-http://127.0.0.1:6878}"
export E2E_ACEXY_URL="${E2E_ACEXY_URL:-http://127.0.0.1:8081}"
export E2E_IPFS_GATEWAY="${E2E_IPFS_GATEWAY:-http://127.0.0.1:8080}"
export E2E_DOCKER_APP_URL="${E2E_DOCKER_APP_URL:-http://127.0.0.1:8001}"
# Opt-in WARP inside the engine container (needs the caps/device declared in the compose file).
export E2E_ENABLE_WARP="${E2E_ENABLE_WARP:-false}"

BACKEND_PID_FILE="$STACK_DIR/backend.pid"
BACKEND_LOG="$STACK_DIR/backend.log"

log() { printf '[e2e-stack] %s\n' "$*"; }

wait_for_http() {
  # wait_for_http <url> <timeout_seconds> [label]
  local url="$1" timeout="$2" label="${3:-$1}" start now
  start=$(date +%s)
  while :; do
    if curl -fsS -m 5 "$url" >/dev/null 2>&1; then
      log "$label is up"
      return 0
    fi
    now=$(date +%s)
    if [ $((now - start)) -ge "$timeout" ]; then
      log "timed out after ${timeout}s waiting for $label"
      return 1
    fi
    sleep 2
  done
}
