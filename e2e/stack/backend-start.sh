#!/usr/bin/env bash
# Run the scraper backend from source against the containerised engine, with an
# isolated SQLite database under e2e/.stack/config and a fresh SPA build.
#   E2E_SKIP_FRONTEND_BUILD=1  reuse backend/frontend_build as-is
#   E2E_RESET_DB=1             delete the e2e database before starting
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

bash "$E2E_DIR/stack/backend-stop.sh" >/dev/null 2>&1 || true
mkdir -p "$STACK_DIR/config"
if [ "${E2E_RESET_DB:-0}" = "1" ]; then
  rm -f "$STACK_DIR/config/scraper.db" "$STACK_DIR/config/scraper.db-journal"
  log "reset e2e database"
fi

if [ "${E2E_SKIP_FRONTEND_BUILD:-0}" != "1" ]; then
  log "building the SPA into backend/frontend_build"
  (cd "$REPO_ROOT/frontend" && npm run build:backend >"$STACK_DIR/frontend-build.log" 2>&1) || {
    log "frontend build failed; see $STACK_DIR/frontend-build.log"; exit 1; }
fi

export DATABASE_URL="sqlite:///$STACK_DIR/config/scraper.db"
export LEGACY_DATABASE_URL="sqlite:///$STACK_DIR/config/acestream.db"
export ACE_ENGINE_URL="$E2E_ENGINE_URL"
export ALLOW_PRIVATE_SCRAPE_TARGETS="true"
# Native ipfs:// and ipns:// sources are fetched through this gateway (the kubo sidecar).
export IPFS_GATEWAY_URL="$E2E_IPFS_GATEWAY"
export EPG_PROGRAM_RETENTION_HOURS="${EPG_PROGRAM_RETENTION_HOURS:-24}"

cd "$REPO_ROOT/backend"
: >"$BACKEND_LOG"
nohup "$REPO_ROOT/backend/venv/bin/uvicorn" main:app --host 127.0.0.1 --port "$E2E_APP_PORT" \
  >>"$BACKEND_LOG" 2>&1 &
echo $! >"$BACKEND_PID_FILE"
log "backend pid $(cat "$BACKEND_PID_FILE"), log $BACKEND_LOG"
wait_for_http "http://127.0.0.1:$E2E_APP_PORT/api/v1/health" 90 "local backend"
