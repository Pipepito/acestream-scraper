#!/usr/bin/env bash
set -euo pipefail

LOG_DIR=${LOG_DIR:-/app/logs}
mkdir -p "$LOG_DIR"
# Supervisor state the app reads to report/restart sidecar services:
#   <run dir>/<service>.pid      pid of the current launch (session leader)
#   <run dir>/<service>.started  epoch of the current launch
#   <run dir>/<service>.restart  marker: the next exit is an operator restart
SUPERVISOR_RUN_DIR=${SUPERVISOR_RUN_DIR:-/run/acestream-scraper}
if ! mkdir -p "$SUPERVISOR_RUN_DIR" 2>/dev/null; then
    # Not root (e.g. the runtime-contract validator on a dev host): keep the
    # bookkeeping in a temp dir instead of aborting startup.
    SUPERVISOR_RUN_DIR="${TMPDIR:-/tmp}/acestream-scraper-run"
    mkdir -p "$SUPERVISOR_RUN_DIR"
fi
export SUPERVISOR_RUN_DIR
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

# Supervise an auxiliary service: restart it when it dies (#119 — Acexy can
# wedge or crash under fast stream switching), but fail the container on a
# crash loop (SUPERVISED_FAST_EXIT_LIMIT consecutive exits within
# SUPERVISED_FAST_EXIT_WINDOW seconds) so a genuine misconfiguration still
# surfaces instead of restarting forever. Exit 0 stops supervision (a
# daemonizing launcher or intentional stop must not be respawned), and a
# first launch that fails fast propagates its real status immediately — the
# runtime contract expects "<label> startup command exited with status N".
supervise_service() {
    local label="$1"
    local command="$2"
    local relaunch_command="${3:-}"
    local restart_delay="${SUPERVISED_RESTART_DELAY_SECONDS:-5}"
    local fast_exit_limit="${SUPERVISED_FAST_EXIT_LIMIT:-3}"
    local fast_exit_window="${SUPERVISED_FAST_EXIT_WINDOW:-10}"
    local fast_exits=0
    local launches=0
    local inner_pid=""
    local sleeper_pid=""
    local slug
    slug=$(printf '%s' "$label" | tr '[:upper:]' '[:lower:]')

    trap '
        for p in ${inner_pid:-$(jobs -p)}; do
            kill -TERM -- "-$p" 2>/dev/null || kill -TERM "$p" 2>/dev/null || true
        done
        if [ -n "$sleeper_pid" ]; then kill "$sleeper_pid" 2>/dev/null || true; fi
        if [ -n "$inner_pid" ]; then
            # Give the service its TERM grace period before the entrypoint
            # (PID 1) exits and the runtime SIGKILLs the namespace.
            wait "$inner_pid" 2>/dev/null || true
        fi
        exit 0
    ' INT TERM

    while :; do
        local started_at ended_at status
        started_at=$(date +%s)
        # setsid puts the service in its own process group so shutdown can
        # kill the whole tree, not just the bash wrapper. It is absent on
        # macOS (developer runs of the runtime contract); fall back to a
        # plain background job there — the trap already handles both.
        if command -v setsid >/dev/null 2>&1; then
            setsid bash -lc "$command" &
        else
            bash -lc "$command" &
        fi
        inner_pid=$!
        launches=$((launches + 1))
        printf '%s\n' "$inner_pid" > "$SUPERVISOR_RUN_DIR/$slug.pid"
        printf '%s\n' "$started_at" > "$SUPERVISOR_RUN_DIR/$slug.started"
        # Some daemons need their runtime state restored after the process is
        # relaunched. WARP, for example, starts disconnected even when the
        # container was configured to auto-connect. The initial launch is
        # configured synchronously by the entrypoint; this hook handles every
        # later operator/crash relaunch.
        if [ "$launches" -gt 1 ] && [ -n "$relaunch_command" ]; then
            if ! bash -lc "$relaunch_command"; then
                log "$label relaunch configuration failed"
                kill -TERM -- "-$inner_pid" 2>/dev/null || kill -TERM "$inner_pid" 2>/dev/null || true
                wait "$inner_pid" 2>/dev/null || true
                return 1
            fi
        fi
        if wait "$inner_pid"; then
            status=0
        else
            status=$?
        fi
        inner_pid=""
        ended_at=$(date +%s)
        rm -f "$SUPERVISOR_RUN_DIR/$slug.pid"
        if [ -f "$SUPERVISOR_RUN_DIR/$slug.restart" ]; then
            # An operator asked for this restart (via the app): relaunch right
            # away and do not count it against the fast-exit budget.
            rm -f "$SUPERVISOR_RUN_DIR/$slug.restart"
            fast_exits=0
            log "$label restart requested; relaunching"
            continue
        fi

        if [ "$status" -eq 0 ]; then
            # Clean exit: the launcher daemonized (its children keep running
            # in the setsid group) or the service stopped on purpose.
            # Restarting would spawn duplicates.
            log "$label exited cleanly; not restarting"
            exit 0
        fi

        if [ $((ended_at - started_at)) -lt "$fast_exit_window" ]; then
            fast_exits=$((fast_exits + 1))
        else
            fast_exits=0
        fi

        if [ "$launches" -eq 1 ] && [ "$fast_exits" -gt 0 ]; then
            log "$label startup command exited with status $status"
            exit "$status"
        fi

        if [ "$fast_exits" -ge "$fast_exit_limit" ]; then
            log "$label exited with status $status $fast_exits times within ${fast_exit_window}s of starting; giving up"
            exit "$status"
        fi

        log "$label exited with status $status; restarting in ${restart_delay}s"
        sleep "$restart_delay" &
        sleeper_pid=$!
        wait "$sleeper_pid" 2>/dev/null || exit 0
        sleeper_pid=""
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
ENABLE_IPFS=$(normalize_bool "${ENABLE_IPFS:-false}")
ENABLE_ZERONET=$(normalize_bool "${ENABLE_ZERONET:-false}")
ENABLE_TOR=$(normalize_bool "${ENABLE_TOR:-false}")
IMAGE_HAS_ACESTREAM=$(normalize_bool "${IMAGE_HAS_ACESTREAM:-false}")
IMAGE_HAS_ACEXY=$(normalize_bool "${IMAGE_HAS_ACEXY:-false}")
# The bundled ZeroNet node ships on amd64 images only: detect the installed
# launcher instead of hard-coding an ENV per platform.
ZERONET_BINARY_PATH="${ZERONET_BINARY_PATH:-/opt/zeronet/bin/zeronet}"
if [ -z "${IMAGE_HAS_ZERONET:-}" ]; then
    if [ -x "$ZERONET_BINARY_PATH" ]; then IMAGE_HAS_ZERONET=true; else IMAGE_HAS_ZERONET=false; fi
fi
IMAGE_HAS_ZERONET=$(normalize_bool "$IMAGE_HAS_ZERONET")
# Kubo ships no 32-bit ARM build, so IPFS availability is per-platform: detect
# the installed binary instead of hard-coding an ENV per flavor.
IPFS_BINARY_PATH="${IPFS_BINARY_PATH:-/opt/ipfs/bin/ipfs}"
if [ -z "${IMAGE_HAS_IPFS:-}" ]; then
    if [ -x "$IPFS_BINARY_PATH" ]; then IMAGE_HAS_IPFS=true; else IMAGE_HAS_IPFS=false; fi
fi
IMAGE_HAS_IPFS=$(normalize_bool "$IMAGE_HAS_IPFS")

export ENABLE_WARP ENABLE_ACESTREAM_ENGINE ENABLE_ACEXY ENABLE_IPFS ENABLE_ZERONET ENABLE_TOR IMAGE_HAS_ACESTREAM IMAGE_HAS_ACEXY IMAGE_HAS_IPFS IMAGE_HAS_ZERONET IPFS_BINARY_PATH ZERONET_BINARY_PATH
export FLASK_PORT="${FLASK_PORT:-8000}"
export ACESTREAM_HTTP_HOST="${ACESTREAM_HTTP_HOST:-localhost}"
export ACESTREAM_HTTP_PORT="${ACESTREAM_HTTP_PORT:-6878}"
export ZERONET_DATA_DIR="${ZERONET_DATA_DIR:-/data/zeronet}"
export ZERONET_UI_PORT="${ZERONET_UI_PORT:-43110}"
export ZERONET_FILESERVER_PORT="${ZERONET_FILESERVER_PORT:-26552}"
# ZeroNet ships --trackers empty and pulls its tracker list from
# --trackers_file, which defaults to a path INSIDE the Syncronite zite.
# Downloading that zite needs trackers, so a fresh data dir can never
# bootstrap: it announces to 0 trackers, finds 0 peers and downloads
# nothing, not even ZeroHello. Seed a few public BitTorrent trackers so
# the node can reach Syncronite and take over the list from there.
export ZERONET_TRACKERS="${ZERONET_TRACKERS:-udp://tracker.opentrackr.org:1337/announce udp://open.stealth.si:80/announce udp://tracker.torrent.eu.org:451/announce}"
if feature_enabled "$ENABLE_ZERONET"; then
    # Keep the scraper pointed at the embedded node when the operator hasn't
    # chosen an explicit external endpoint (the image bakes the 43110
    # default, so also rewrite that when the UI port moved).
    case "${ZERONET_URL:-}" in
        ""|http://127.0.0.1:43110)
            ZERONET_URL="http://127.0.0.1:$ZERONET_UI_PORT"
            ;;
    esac
fi
export ZERONET_URL="${ZERONET_URL:-http://127.0.0.1:43110}"
export IPFS_SWARM_PORT="${IPFS_SWARM_PORT:-4001}"
export IPFS_API_PORT="${IPFS_API_PORT:-5001}"
# 8080 belongs to Acexy in-container, so the embedded gateway defaults to 8081.
export IPFS_GATEWAY_PORT="${IPFS_GATEWAY_PORT:-8081}"
export IPFS_GATEWAY_URL="${IPFS_GATEWAY_URL:-http://127.0.0.1:$IPFS_GATEWAY_PORT}"

if ! feature_enabled "$ENABLE_WARP"; then
    log "WARP disabled; skipping setup"
fi

if feature_enabled "$ENABLE_ACESTREAM_ENGINE" && ! image_has_feature "$IMAGE_HAS_ACESTREAM"; then
    fail "AceStream is enabled but not installed in this image flavor"
fi

if feature_enabled "$ENABLE_ACEXY" && ! image_has_feature "$IMAGE_HAS_ACEXY"; then
    fail "Acexy is enabled but not installed in this image flavor"
fi

if feature_enabled "$ENABLE_IPFS" && ! image_has_feature "$IMAGE_HAS_IPFS"; then
    fail "IPFS is enabled but Kubo is not installed in this image (upstream ships no 32-bit ARM build)"
fi

if feature_enabled "$ENABLE_ZERONET" && ! image_has_feature "$IMAGE_HAS_ZERONET"; then
    fail "ZeroNet is enabled but not installed in this image (bundled on linux/amd64 only; point ZERONET_URL at an external node instead)"
fi

if feature_enabled "$ENABLE_TOR" && ! feature_enabled "$ENABLE_ZERONET"; then
    log "ENABLE_TOR=true has no effect without ENABLE_ZERONET=true; skipping TOR"
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

log "ZeroNet endpoint for zero:// sources: $ZERONET_URL (embedded node: $ENABLE_ZERONET)"
log "IPFS gateway for ipfs:// sources: $IPFS_GATEWAY_URL (embedded daemon: $ENABLE_IPFS)"
if feature_enabled "$ENABLE_ZERONET"; then
    case "$ZERONET_URL" in
        http://127.0.0.1:*|http://localhost:*) ;;
        *) log "WARNING: ENABLE_ZERONET=true but ZERONET_URL points at $ZERONET_URL — the scraper will not use the embedded node" ;;
    esac
fi

start_tor() {
    if ! command -v tor >/dev/null 2>&1; then
        fail "ENABLE_TOR=true but the tor binary is not installed in this image (amd64 images only)"
    fi
    local torrc="${TORRC_PATH:-/tmp/acestream-scraper-torrc}"
    local tor_data="${TOR_DATA_DIR:-/var/lib/tor-zeronet}"
    mkdir -p "$tor_data"
    # ControlPort + cookie auth is what ZeroNet's tor auto-detection expects
    # (same contract as the v1 image).
    cat > "$torrc" <<EOF
SocksPort 9050
ControlPort 9051
CookieAuthentication 1
DataDirectory $tor_data
EOF
    supervise_service "Tor" "tor -f $torrc" &
    child_pids+=("$!")
    child_names+=("Tor")
}

configure_ipfs_repo() {
    export IPFS_PATH="${IPFS_PATH:-/data/ipfs}"
    mkdir -p "$IPFS_PATH"
    if [ ! -f "$IPFS_PATH/config" ]; then
        log "Initializing IPFS repository at $IPFS_PATH"
        # shellcheck disable=SC2086 — IPFS_PROFILE is intentionally optional
        "$IPFS_BINARY_PATH" init ${IPFS_PROFILE:+--profile "$IPFS_PROFILE"}
    fi
    # Re-applied every boot so IPFS_*_PORT env changes take effect. The RPC
    # API binds to loopback by default: it has no authentication and full
    # control of the node (set IPFS_API_HOST=0.0.0.0 only on trusted networks,
    # e.g. to reach the WebUI).
    "$IPFS_BINARY_PATH" config Addresses.API "/ip4/${IPFS_API_HOST:-127.0.0.1}/tcp/$IPFS_API_PORT"
    "$IPFS_BINARY_PATH" config Addresses.Gateway "/ip4/0.0.0.0/tcp/$IPFS_GATEWAY_PORT"
    "$IPFS_BINARY_PATH" config --json Addresses.Swarm "[\"/ip4/0.0.0.0/tcp/$IPFS_SWARM_PORT\", \"/ip6/::/tcp/$IPFS_SWARM_PORT\", \"/ip4/0.0.0.0/udp/$IPFS_SWARM_PORT/quic-v1\", \"/ip6/::/udp/$IPFS_SWARM_PORT/quic-v1\"]"
}

child_pids=()
child_names=()

if feature_enabled "$ENABLE_WARP"; then
    # warp-svc runs under the supervisor (restartable from the app, relaunched
    # on crash); warp-setup.sh prepares the host (TUN, DBus) before it starts
    # and registers/connects once it answers.
    if ! bash "$(dirname "$0")/warp-setup.sh" prepare; then
        fail "WARP setup failed"
    fi
    # warp-svc inherits this from its supervisor (warp-setup.sh only exports it for its own run).
    export WARP_FORCE_IPV4="${WARP_FORCE_IPV4:-true}"
    WARP_SETUP_SCRIPT="$(dirname "$0")/warp-setup.sh"
    supervise_service "WARP" "${WARP_START_COMMAND:-warp-svc --accept-tos >> \"$LOG_DIR/warp-svc.log\" 2>&1}" "bash \"$WARP_SETUP_SCRIPT\" configure" &
    child_pids+=("$!")
    child_names+=("WARP")
    if ! bash "$WARP_SETUP_SCRIPT" configure; then
        fail "WARP setup failed"
    fi
fi

if feature_enabled "$ENABLE_ZERONET"; then
    mkdir -p "$ZERONET_DATA_DIR"
    if feature_enabled "$ENABLE_TOR"; then
        start_tor
        zeronet_tor_mode="enable"
    else
        zeronet_tor_mode="disable"
    fi
    if [ -z "${ZERONET_START_COMMAND:-}" ]; then
        # --ui_ip 0.0.0.0 so publishing 43110 works; ZeroNet still only
        # accepts requests whose Host header it knows, so set
        # ZERONET_UI_HOST (space-separated hostnames) to reach the UI from
        # another machine. ZERONET_EXTRA_ARGS passes anything else through.
        ZERONET_START_COMMAND="$ZERONET_BINARY_PATH${ZERONET_TRACKERS:+ --trackers $ZERONET_TRACKERS} --ui_ip 0.0.0.0 --ui_port $ZERONET_UI_PORT --fileserver_port $ZERONET_FILESERVER_PORT --data_dir $ZERONET_DATA_DIR --log_dir $LOG_DIR --tor $zeronet_tor_mode${ZERONET_UI_HOST:+ --ui_host $ZERONET_UI_HOST}${ZERONET_EXTRA_ARGS:+ $ZERONET_EXTRA_ARGS} main"
    fi
    supervise_service "ZeroNet" "$ZERONET_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("ZeroNet")
fi

if feature_enabled "$ENABLE_IPFS" && [ -n "${IPFS_START_COMMAND:-}" ]; then
    if ! configure_ipfs_repo; then
        fail "IPFS repository initialization failed"
    fi
    supervise_service "IPFS" "$IPFS_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("IPFS")
fi

if feature_enabled "$ENABLE_ACESTREAM_ENGINE" && [ -n "${ACESTREAM_START_COMMAND:-}" ]; then
    supervise_service "AceStream" "$ACESTREAM_START_COMMAND" &
    child_pids+=("$!")
    child_names+=("AceStream")
fi

if feature_enabled "$ENABLE_ACEXY" && [ -n "${ACEXY_START_COMMAND:-}" ]; then
    supervise_service "Acexy" "$ACEXY_START_COMMAND" &
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
