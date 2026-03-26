#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=${LOG_DIR:-/app/logs}
mkdir -p "$LOG_DIR"
LOGROTATE_DIR=${LOGROTATE_DIR:-/tmp/acestream-scraper-logrotate}
mkdir -p "$LOGROTATE_DIR"
LOGROTATE_CONF="$LOGROTATE_DIR/acestream-services"

cat > "$LOGROTATE_CONF" <<EOF
$LOG_DIR/*.log {
    hourly
    rotate 7
    compress
    missingok
    notifempty
    create 0644 root root
}
EOF

normalize_bool() {
    case "${1:-false}" in
        1|true|TRUE|True|yes|YES|on|ON) printf 'true\n' ;;
        *) printf 'false\n' ;;
    esac
}

log() {
    printf '[entrypoint] %s\n' "$1"
}

fail() {
    printf '[entrypoint] %s\n' "$1" >&2
    exit 1
}

feature_enabled() {
    [ "$(normalize_bool "${1:-false}")" = "true" ]
}

image_has_feature() {
    [ "$(normalize_bool "${1:-false}")" = "true" ]
}

shutdown_children() {
    local pid
    for pid in "$@"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
    done
}

prune_finished_children() {
    local remaining_pids=()
    local remaining_labels=()
    local pid
    local label
    local status
    local index=0

    for pid in "${child_pids[@]:-}"; do
        label=${child_names[$index]:-Auxiliary service}
        [ -n "$pid" ] || continue
        if kill -0 "$pid" 2>/dev/null; then
            remaining_pids+=("$pid")
            remaining_labels+=("$label")
        else
            if wait "$pid" 2>/dev/null; then
                :
            else
                status=$?
                fail "$label startup command exited with status $status"
            fi
        fi
        index=$((index + 1))
    done

    child_pids=()
    child_names=()
    for pid in "${remaining_pids[@]:-}"; do
        child_pids+=("$pid")
    done
    for label in "${remaining_labels[@]:-}"; do
        child_names+=("$label")
    done
}

ENABLE_WARP=$(normalize_bool "${ENABLE_WARP:-false}")
ENABLE_ACESTREAM_ENGINE=$(normalize_bool "${ENABLE_ACESTREAM_ENGINE:-false}")
ENABLE_ACEXY=$(normalize_bool "${ENABLE_ACEXY:-false}")
IMAGE_HAS_ACESTREAM=$(normalize_bool "${IMAGE_HAS_ACESTREAM:-false}")
IMAGE_HAS_ACEXY=$(normalize_bool "${IMAGE_HAS_ACEXY:-false}")

export ENABLE_WARP ENABLE_ACESTREAM_ENGINE ENABLE_ACEXY IMAGE_HAS_ACESTREAM IMAGE_HAS_ACEXY
export FLASK_PORT="${FLASK_PORT:-8000}"
export ACESTREAM_HTTP_HOST="${ACESTREAM_HTTP_HOST:-localhost}"
export ACESTREAM_HTTP_PORT="${ACESTREAM_HTTP_PORT:-6878}"
export ZERONET_URL="${ZERONET_URL:-http://127.0.0.1:43110}"

if feature_enabled "$ENABLE_WARP"; then
    if ! bash "$(dirname "$0")/warp-setup.sh"; then
        fail "WARP setup failed"
    fi
else
    log "WARP disabled; skipping setup"
fi

if feature_enabled "$ENABLE_ACESTREAM_ENGINE" && ! image_has_feature "$IMAGE_HAS_ACESTREAM"; then
    fail "AceStream is enabled but not installed in this image flavor"
fi

if feature_enabled "$ENABLE_ACEXY" && ! image_has_feature "$IMAGE_HAS_ACEXY"; then
    fail "Acexy is enabled but not installed in this image flavor"
fi

if feature_enabled "$ENABLE_ACESTREAM_ENGINE"; then
    export ACEXY_HOST="${ACEXY_HOST:-$ACESTREAM_HTTP_HOST}"
    export ACEXY_PORT="${ACEXY_PORT:-$ACESTREAM_HTTP_PORT}"
else
    export ACEXY_HOST="${ACEXY_HOST:-localhost}"
    export ACEXY_PORT="${ACEXY_PORT:-6878}"
fi

if feature_enabled "$ENABLE_ACEXY" && ! feature_enabled "$ENABLE_ACESTREAM_ENGINE"; then
    case "$ACEXY_HOST:$ACEXY_PORT" in
        localhost:6878|127.0.0.1:6878)
            fail "Acexy cannot target localhost:6878 when in-container AceStream is disabled"
            ;;
    esac
fi

export ACE_ENGINE_URL="${ACE_ENGINE_URL:-http://$ACESTREAM_HTTP_HOST:$ACESTREAM_HTTP_PORT}"

log "ZeroNet compatibility mode enabled via ZERONET_URL=$ZERONET_URL"

child_pids=()
child_names=()

if feature_enabled "$ENABLE_ACESTREAM_ENGINE" && [ -n "${ACESTREAM_START_COMMAND:-}" ]; then
    bash -lc "$ACESTREAM_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("AceStream")
fi

if feature_enabled "$ENABLE_ACEXY" && [ -n "${ACEXY_START_COMMAND:-}" ]; then
    bash -lc "$ACEXY_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("Acexy")
fi

APP_COMMAND=("$@")
if [ "${#APP_COMMAND[@]}" -eq 0 ]; then
    APP_COMMAND=(uvicorn main:app --host 0.0.0.0 --port "$FLASK_PORT")
fi

wait_for_supervised_exit() {
    while :; do
        local pid
        prune_finished_children

        if ! kill -0 "$app_pid" 2>/dev/null; then
            wait "$app_pid" 2>/dev/null
            return $?
        fi

        sleep 1
    done
}

trap 'shutdown_children "${child_pids[@]:-}" "$app_pid"' INT TERM EXIT

"${APP_COMMAND[@]}" &
app_pid=$!

if wait_for_supervised_exit; then
    app_status=0
else
    app_status=$?
fi

shutdown_children "$app_pid" "${child_pids[@]:-}"

trap - INT TERM EXIT
exit "$app_status"
