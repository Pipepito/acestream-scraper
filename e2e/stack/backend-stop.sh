#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"
if [ -f "$BACKEND_PID_FILE" ]; then
  pid=$(cat "$BACKEND_PID_FILE")
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do kill -0 "$pid" 2>/dev/null || break; sleep 0.5; done
    kill -9 "$pid" 2>/dev/null || true
    log "stopped backend pid $pid"
  fi
  rm -f "$BACKEND_PID_FILE"
fi
