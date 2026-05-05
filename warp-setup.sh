#!/usr/bin/env bash
set -euo pipefail

normalize_bool() {
    case "${1:-false}" in
        1|true|TRUE|True|yes|YES|on|ON) printf 'true\n' ;;
        *) printf 'false\n' ;;
    esac
}

wait_for_warp_ready() {
    local description=$1
    local attempts=${2:-30}
    local interval=${3:-1}
    local attempt=1

    while [ "$attempt" -le "$attempts" ]; do
        if warp-cli --accept-tos status >> "$WARP_LOG" 2>&1; then
            log "$description ready"
            return 0
        fi
        sleep "$interval"
        attempt=$((attempt + 1))
    done

    fail "$description did not become ready"
}

log() {
    printf '%s: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$WARP_LOG"
}

fail() {
    log "$1"
    printf 'WARP setup failed: %s\n' "$1" >&2
    exit 1
}

run_privileged() {
    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
    fi
}

ENABLE_WARP=$(normalize_bool "${ENABLE_WARP:-false}")
DEBUG_ENABLE_QLOG=$(normalize_bool "${DEBUG_ENABLE_QLOG:-false}")
WARP_ENABLE_NAT=$(normalize_bool "${WARP_ENABLE_NAT:-false}")
LOG_DIR=${LOG_DIR:-/app/logs}
mkdir -p "$LOG_DIR"
WARP_LOG="$LOG_DIR/warp.log"
: > "$WARP_LOG"

if [ "$ENABLE_WARP" != "true" ]; then
    log "WARP disabled; skipping setup"
    printf 'WARP is disabled, skipping initialization\n'
    exit 0
fi

IFS=' ' read -r -a required_commands <<< "${WARP_REQUIRED_COMMANDS:-warp-cli warp-svc dbus-daemon}"
for cmd in "${required_commands[@]}"; do
    [ -n "$cmd" ] || continue
    if ! command -v "$cmd" >/dev/null 2>&1; then
        fail "missing required command: $cmd"
    fi
done

log "Starting WARP setup"

if [ ! -e /dev/net/tun ]; then
    log "Creating TUN device"
    run_privileged mkdir -p /dev/net
    run_privileged mknod /dev/net/tun c 10 200
    run_privileged chmod 600 /dev/net/tun
fi

log "Starting DBus"
run_privileged mkdir -p /run/dbus
if [ -f /run/dbus/pid ]; then
    run_privileged rm -f /run/dbus/pid
fi
run_privileged dbus-daemon --config-file=/usr/share/dbus-1/system.conf --fork >> "$WARP_LOG" 2>&1

export WARP_FORCE_IPV4=true

log "Starting WARP service"
run_privileged warp-svc --accept-tos >> "$WARP_LOG" 2>&1 &
wait_for_warp_ready "WARP service" "${WARP_READY_ATTEMPTS:-30}" "${WARP_READY_INTERVAL:-1}"

if [ ! -f /var/lib/cloudflare-warp/reg.json ] && [ ! -f /var/lib/cloudflare-warp/mdm.xml ]; then
    log "Registering WARP client"
    warp-cli --accept-tos registration new >> "$WARP_LOG" 2>&1
    if [ -n "${WARP_LICENSE_KEY:-}" ]; then
        log "Registering WARP license"
        warp-cli --accept-tos registration license "$WARP_LICENSE_KEY" >> "$WARP_LOG" 2>&1
    fi
else
    log "WARP client already registered"
fi

if [ "$DEBUG_ENABLE_QLOG" = "true" ]; then
    warp-cli --accept-tos debug qlog enable >> "$WARP_LOG" 2>&1
else
    warp-cli --accept-tos debug qlog disable >> "$WARP_LOG" 2>&1
fi

if [ "$WARP_ENABLE_NAT" = "true" ]; then
    log "Configuring WARP NAT"
    warp-cli --accept-tos mode warp+doh >> "$WARP_LOG" 2>&1
    warp-cli --accept-tos connect >> "$WARP_LOG" 2>&1
    wait_for_warp_ready "WARP NAT connect" "${WARP_READY_ATTEMPTS:-30}" "${WARP_READY_INTERVAL:-1}"
    run_privileged nft add table ip nat >> "$WARP_LOG" 2>&1 || true
    run_privileged nft add chain ip nat WARP_NAT '{ type nat hook postrouting priority 100 ; }' >> "$WARP_LOG" 2>&1 || true
    run_privileged nft add rule ip nat WARP_NAT oifname CloudflareWARP masquerade >> "$WARP_LOG" 2>&1 || true
fi

log "Checking WARP status"
warp-cli --accept-tos status >> "$WARP_LOG" 2>&1
log "WARP initialization completed"
printf 'WARP initialization completed - logs available at %s\n' "$WARP_LOG"
