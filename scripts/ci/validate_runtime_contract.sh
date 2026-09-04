#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
ENTRYPOINT_SCRIPT="$REPO_ROOT/entrypoint.sh"
WARP_SETUP_SCRIPT="$REPO_ROOT/warp-setup.sh"
HEALTHCHECK_SCRIPT="$REPO_ROOT/healthcheck.sh"

TMP_DIR=$(mktemp -d)
FAKE_BIN="$TMP_DIR/bin"
mkdir -p "$FAKE_BIN"
trap 'rm -rf "$TMP_DIR"' EXIT

fail() {
    printf 'VALIDATION FAILED: %s\n' "$1" >&2
    exit 1
}

expect_failure_contains() {
    local description=$1
    local expected=$2
    shift 2

    local output
    local status
    set +e
    output=$("$@" 2>&1)
    status=$?
    set -e

    if [ "$status" -eq 0 ]; then
        fail "$description unexpectedly succeeded"
    fi

    case "$output" in
        *"$expected"*) ;;
        *) fail "$description did not include expected text: $expected" ;;
    esac
}

expect_success() {
    local description=$1
    shift

    local output
    local status
    set +e
    output=$("$@" 2>&1)
    status=$?
    set -e

    if [ "$status" -ne 0 ]; then
        printf '%s\n' "$output" >&2
        fail "$description failed"
    fi
}

assert_log_contains() {
    local log_file=$1
    local expected=$2
    grep -F -- "$expected" "$log_file" >/dev/null || fail "curl log missing expected URL: $expected"
}

assert_log_not_contains() {
    local log_file=$1
    local unexpected=$2
    if grep -F -- "$unexpected" "$log_file" >/dev/null; then
        fail "curl log unexpectedly contained URL fragment: $unexpected"
    fi
}

assert_file_contains() {
    local file_path=$1
    local expected=$2
    grep -F -- "$expected" "$file_path" >/dev/null || fail "file missing expected text: $expected"
}

assert_file_not_contains() {
    local file_path=$1
    local unexpected=$2
    if grep -F -- "$unexpected" "$file_path" >/dev/null; then
        fail "file unexpectedly contained text: $unexpected"
    fi
}

cat > "$FAKE_BIN/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

log_file=${CURL_LOG_FILE:?CURL_LOG_FILE is required}
url=""
for arg in "$@"; do
    case "$arg" in
        http://*|https://*) url=$arg ;;
    esac
done

if [ -z "$url" ]; then
    printf 'fake curl expected a URL argument\n' >&2
    exit 2
fi

printf '%s\n' "$url" >> "$log_file"

if [ -n "${CURL_FAIL_MATCH:-}" ]; then
    case "$url" in
        *"$CURL_FAIL_MATCH"*)
            printf 'simulated curl failure for %s\n' "$url" >&2
            exit 22
            ;;
    esac
fi

case "$url" in
    */api/v1/health|*/health)
        printf '{"status":"ok"}'
        ;;
    */ace/status)
        printf '{"status":"ok"}'
        ;;
    *)
        printf 'ok'
        ;;
esac
EOF
chmod +x "$FAKE_BIN/curl"

cat > "$FAKE_BIN/zeronet" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$@" > "${ZERONET_ARG_LOG:?ZERONET_ARG_LOG is required}"
EOF
chmod +x "$FAKE_BIN/zeronet"

cat > "$FAKE_BIN/sudo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exec "$@"
EOF
chmod +x "$FAKE_BIN/sudo"

cat > "$FAKE_BIN/mkdir" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
target=${!#}
case "$target" in
    /dev/net|/run/dbus)
        exit 0
        ;;
esac
exec /bin/mkdir "$@"
EOF
chmod +x "$FAKE_BIN/mkdir"

cat > "$FAKE_BIN/rm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
target=${!#}
case "$target" in
    /run/dbus/pid)
        exit 0
        ;;
esac
exec /bin/rm "$@"
EOF
chmod +x "$FAKE_BIN/rm"

cat > "$FAKE_BIN/mknod" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
exit 0
EOF
chmod +x "$FAKE_BIN/mknod"

cat > "$FAKE_BIN/chmod" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
target=${!#}
case "$target" in
    /dev/net/tun)
        exit 0
        ;;
esac
exec /bin/chmod "$@"
EOF
chmod +x "$FAKE_BIN/chmod"

cat > "$FAKE_BIN/dbus-daemon" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_DBUS_LOG:?FAKE_DBUS_LOG is required}"
case " $* " in
    *" --fork "*) exit 0 ;;
    *) printf 'dbus-daemon requires --fork\n' >&2; exit 64 ;;
esac
EOF
chmod +x "$FAKE_BIN/dbus-daemon"

cat > "$FAKE_BIN/warp-svc" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_WARP_SVC_LOG:?FAKE_WARP_SVC_LOG is required}"
sleep "${FAKE_WARP_READY_DELAY:-0.2}"
touch "${FAKE_WARP_READY_FILE:?FAKE_WARP_READY_FILE is required}"
EOF
chmod +x "$FAKE_BIN/warp-svc"

cat > "$FAKE_BIN/warp-cli" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

command_log=${FAKE_WARP_CLI_LOG:?FAKE_WARP_CLI_LOG is required}
ready_file=${FAKE_WARP_READY_FILE:?FAKE_WARP_READY_FILE is required}
printf '%s\n' "$*" >> "$command_log"

args=()
for arg in "$@"; do
    if [ "$arg" != "--accept-tos" ]; then
        args+=("$arg")
    fi
done

subcommand=${args[0]:-}
case "$subcommand" in
    registration)
        exit 0
        ;;
    debug)
        exit 0
        ;;
    mode)
        exit 0
        ;;
    connect)
        if [ "${FAKE_WARP_RESET_READY_ON_CONNECT:-false}" = "true" ]; then
            rm -f "$ready_file"
        fi
        (
            sleep "${FAKE_WARP_CONNECT_DELAY:-0.2}"
            touch "$ready_file"
        ) &
        exit 0
        ;;
    status)
        if [ -f "$ready_file" ]; then
            printf 'Connected\n'
            exit 0
        fi
        printf 'Not ready\n' >&2
        exit 1
        ;;
    *)
        exit 0
        ;;
esac
EOF
chmod +x "$FAKE_BIN/warp-cli"

cat > "$FAKE_BIN/nft" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "${FAKE_NFT_LOG:?FAKE_NFT_LOG is required}"
exit 0
EOF
chmod +x "$FAKE_BIN/nft"

for required_script in "$ENTRYPOINT_SCRIPT" "$WARP_SETUP_SCRIPT" "$HEALTHCHECK_SCRIPT"; do
    if [ ! -f "$required_script" ]; then
        fail "Missing runtime script: ${required_script#$REPO_ROOT/}"
    fi
done

BASE_PATH="$FAKE_BIN:/usr/bin:/bin:/usr/sbin:/sbin"
VALIDATION_LOG_DIR="$TMP_DIR/logs"
mkdir -p "$VALIDATION_LOG_DIR"

FAKE_DBUS_LOG="$TMP_DIR/dbus.log"
FAKE_WARP_SVC_LOG="$TMP_DIR/warp-svc.log"
FAKE_WARP_CLI_LOG="$TMP_DIR/warp-cli.log"
FAKE_NFT_LOG="$TMP_DIR/nft.log"
FAKE_WARP_READY_FILE="$TMP_DIR/warp-ready"

expect_failure_contains \
    "AceStream-missing flavor guard" \
    "AceStream is enabled but not installed in this image flavor" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=false IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=false ENABLE_ACESTREAM_ENGINE=true ENABLE_ACEXY=false bash "$ENTRYPOINT_SCRIPT" true

expect_failure_contains \
    "Acexy-missing flavor guard" \
    "Acexy is enabled but not installed in this image flavor" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=false IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=false ENABLE_ACESTREAM_ENGINE=false ENABLE_ACEXY=true bash "$ENTRYPOINT_SCRIPT" true

expect_failure_contains \
    "Acexy external-engine localhost default guard" \
    "Acexy cannot target localhost:6878 when in-container AceStream is disabled" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=false IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=true ENABLE_ACESTREAM_ENGINE=false ENABLE_ACEXY=true ACEXY_HOST=localhost ACEXY_PORT=6878 bash "$ENTRYPOINT_SCRIPT" true

expect_failure_contains \
    "WARP setup propagates startup failure" \
    "WARP setup failed" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=true WARP_REQUIRED_COMMANDS=definitely-missing IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=false ENABLE_ACESTREAM_ENGINE=false ENABLE_ACEXY=false bash "$ENTRYPOINT_SCRIPT" true

expect_success \
    "WARP disabled skip path" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=false bash "$WARP_SETUP_SCRIPT"

ZERONET_ARG_LOG="$TMP_DIR/zeronet-args.log"
expect_success \
    "ZeroNet tracker override does not consume the main action" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=false ENABLE_ZERONET=true IMAGE_HAS_ZERONET=true ZERONET_BINARY_PATH="$FAKE_BIN/zeronet" ZERONET_DATA_DIR="$TMP_DIR/zeronet-data" ZERONET_TRACKERS="udp://tracker-one.example:80/announce udp://tracker-two.example:80/announce" ZERONET_ARG_LOG="$ZERONET_ARG_LOG" bash "$ENTRYPOINT_SCRIPT" sleep 1
zeronet_args=$(tr '\n' ' ' < "$ZERONET_ARG_LOG")
case "$zeronet_args" in
    *"--trackers udp://tracker-one.example:80/announce udp://tracker-two.example:80/announce --ui_ip 0.0.0.0"*" main ") ;;
    *) fail "ZeroNet arguments did not terminate --trackers before the main action: $zeronet_args" ;;
esac

: > "$FAKE_DBUS_LOG"
: > "$FAKE_WARP_SVC_LOG"
: > "$FAKE_WARP_CLI_LOG"
: > "$FAKE_NFT_LOG"
rm -f "$FAKE_WARP_READY_FILE"
expect_success \
    "WARP enabled path waits for readiness and honors false booleans" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=true WARP_SLEEP=0 DEBUG_ENABLE_QLOG=false WARP_ENABLE_NAT=false FAKE_DBUS_LOG="$FAKE_DBUS_LOG" FAKE_WARP_SVC_LOG="$FAKE_WARP_SVC_LOG" FAKE_WARP_CLI_LOG="$FAKE_WARP_CLI_LOG" FAKE_NFT_LOG="$FAKE_NFT_LOG" FAKE_WARP_READY_FILE="$FAKE_WARP_READY_FILE" bash "$WARP_SETUP_SCRIPT"
assert_file_contains "$FAKE_DBUS_LOG" "--fork"
assert_file_contains "$FAKE_WARP_CLI_LOG" "debug qlog disable"
assert_file_not_contains "$FAKE_WARP_CLI_LOG" "debug qlog enable"
assert_file_not_contains "$FAKE_WARP_CLI_LOG" "mode warp+doh"
assert_file_not_contains "$FAKE_WARP_CLI_LOG" "connect"
assert_file_not_contains "$FAKE_NFT_LOG" "add table ip nat"

: > "$FAKE_DBUS_LOG"
: > "$FAKE_WARP_SVC_LOG"
: > "$FAKE_WARP_CLI_LOG"
: > "$FAKE_NFT_LOG"
rm -f "$FAKE_WARP_READY_FILE"
expect_success \
    "WARP NAT path waits for post-connect readiness" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" ENABLE_WARP=true WARP_SLEEP=0 DEBUG_ENABLE_QLOG=false WARP_ENABLE_NAT=true FAKE_WARP_RESET_READY_ON_CONNECT=true FAKE_WARP_CONNECT_DELAY=0.2 FAKE_DBUS_LOG="$FAKE_DBUS_LOG" FAKE_WARP_SVC_LOG="$FAKE_WARP_SVC_LOG" FAKE_WARP_CLI_LOG="$FAKE_WARP_CLI_LOG" FAKE_NFT_LOG="$FAKE_NFT_LOG" FAKE_WARP_READY_FILE="$FAKE_WARP_READY_FILE" bash "$WARP_SETUP_SCRIPT"
assert_file_contains "$FAKE_WARP_CLI_LOG" "mode warp+doh"
assert_file_contains "$FAKE_WARP_CLI_LOG" "connect"
assert_file_contains "$FAKE_NFT_LOG" "add table ip nat"

: > "$TMP_DIR/health-disabled.log"
expect_success \
    "Healthcheck ignores disabled optional services" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" CURL_LOG_FILE="$TMP_DIR/health-disabled.log" FLASK_PORT=8000 ENABLE_ACEXY=false ENABLE_ACESTREAM_ENGINE=false bash "$HEALTHCHECK_SCRIPT"
assert_log_contains "$TMP_DIR/health-disabled.log" "http://localhost:8000/api/v1/health"
assert_log_not_contains "$TMP_DIR/health-disabled.log" "/ace/status"

: > "$TMP_DIR/health-external.log"
expect_success \
    "Healthcheck uses explicit external engine host and port" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" CURL_LOG_FILE="$TMP_DIR/health-external.log" FLASK_PORT=8000 ENABLE_ACEXY=true ENABLE_ACESTREAM_ENGINE=false ACEXY_HOST=engine.example ACEXY_PORT=9999 bash "$HEALTHCHECK_SCRIPT"
assert_log_contains "$TMP_DIR/health-external.log" "http://engine.example:9999/webui/api/service?method=get_version"
assert_log_contains "$TMP_DIR/health-external.log" "http://localhost:8080/ace/status"

: > "$TMP_DIR/health-listen-addr.log"
expect_success \
    "Healthcheck follows ACEXY_LISTEN_ADDR instead of the pinned status port" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" CURL_LOG_FILE="$TMP_DIR/health-listen-addr.log" FLASK_PORT=8000 ENABLE_ACEXY=true ENABLE_ACESTREAM_ENGINE=true ACEXY_LISTEN_ADDR=:8084 ACEXY_STATUS_PORT=8080 bash "$HEALTHCHECK_SCRIPT"
assert_log_contains "$TMP_DIR/health-listen-addr.log" "http://localhost:8084/ace/status"
assert_log_not_contains "$TMP_DIR/health-listen-addr.log" "localhost:8080/ace/status"

: > "$TMP_DIR/health-engine-only.log"
expect_success \
    "Healthcheck probes in-container AceStream engine when enabled without Acexy" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" CURL_LOG_FILE="$TMP_DIR/health-engine-only.log" FLASK_PORT=8000 ENABLE_ACEXY=false ENABLE_ACESTREAM_ENGINE=true ACESTREAM_HTTP_HOST=engine.local ACESTREAM_HTTP_PORT=7000 bash "$HEALTHCHECK_SCRIPT"
assert_log_contains "$TMP_DIR/health-engine-only.log" "http://engine.local:7000/webui/api/service?method=get_version"

expect_failure_contains \
    "Healthcheck fails when in-container AceStream engine is down" \
    "In-container AceStream engine not accessible" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" CURL_LOG_FILE="$TMP_DIR/health-engine-only.log" CURL_FAIL_MATCH="engine.local:7000" FLASK_PORT=8000 ENABLE_ACEXY=false ENABLE_ACESTREAM_ENGINE=true ACESTREAM_HTTP_HOST=engine.local ACESTREAM_HTTP_PORT=7000 bash "$HEALTHCHECK_SCRIPT"

expect_failure_contains \
    "Entrypoint surfaces failed auxiliary launcher" \
    "Acexy startup command exited with status 7" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" LOGROTATE_DIR="$TMP_DIR/logrotate-fail" ENABLE_WARP=false IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=true ENABLE_ACESTREAM_ENGINE=false ENABLE_ACEXY=true ACEXY_HOST=engine.example ACEXY_PORT=9999 ACEXY_START_COMMAND='exit 7' bash "$ENTRYPOINT_SCRIPT" bash -lc 'sleep 2'

APP_DONE_FILE="$TMP_DIR/app-done"
rm -f "$APP_DONE_FILE"
expect_success \
    "Entrypoint tolerates successful daemonizing launcher" \
    env PATH="$BASE_PATH" LOG_DIR="$VALIDATION_LOG_DIR" LOGROTATE_DIR="$TMP_DIR/logrotate" ENABLE_WARP=false IMAGE_HAS_ACESTREAM=false IMAGE_HAS_ACEXY=true ENABLE_ACESTREAM_ENGINE=false ENABLE_ACEXY=true ACEXY_HOST=engine.example ACEXY_PORT=9999 ACEXY_START_COMMAND='sleep 1 &' APP_DONE_FILE="$APP_DONE_FILE" bash "$ENTRYPOINT_SCRIPT" bash -lc 'sleep 0.3; printf done > "$APP_DONE_FILE"'
[ -f "$APP_DONE_FILE" ] || fail "Entrypoint returned before the main app command completed"

printf 'Runtime contract validation passed.\n'
