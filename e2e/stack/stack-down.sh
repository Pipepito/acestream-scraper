#!/usr/bin/env bash
# Stop the stack. Pass --volumes to also drop engine/IPFS state.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
bash "$E2E_DIR/stack/backend-stop.sh" || true
if [ "${1:-}" = "--volumes" ]; then
  docker compose -f "$COMPOSE_FILE" down --volumes
else
  docker compose -f "$COMPOSE_FILE" down
fi
