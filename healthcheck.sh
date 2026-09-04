#!/usr/bin/env bash
set -euo pipefail

normalize_bool() {
    case "${1:-false}" in
        1|true|TRUE|True|yes|YES|on|ON) printf 'true\n' ;;
        *) printf 'false\n' ;;
    esac
}

fail() {
    printf '%s\n' "$1" >&2
    exit 1
}

ENABLE_ACEXY=$(normalize_bool "${ENABLE_ACEXY:-false}")
ENABLE_ACESTREAM_ENGINE=$(normalize_bool "${ENABLE_ACESTREAM_ENGINE:-false}")
FLASK_PORT=${FLASK_PORT:-8000}
ACESTREAM_HTTP_HOST=${ACESTREAM_HTTP_HOST:-localhost}
ACESTREAM_HTTP_PORT=${ACESTREAM_HTTP_PORT:-6878}
ACEXY_HOST=${ACEXY_HOST:-localhost}
ACEXY_PORT=${ACEXY_PORT:-6878}
ACEXY_STATUS_PORT=${ACEXY_STATUS_PORT:-8080}
ACEXY_STATUS_HOST=localhost
# ACEXY_LISTEN_ADDR ([host]:port) is where Acexy really binds; an operator
# who moves it to another port changes only that, so it wins over the
# image-pinned ACEXY_STATUS_PORT. Wildcard hosts are probed on loopback.
if [ -n "${ACEXY_LISTEN_ADDR:-}" ]; then
    listen_port=${ACEXY_LISTEN_ADDR##*:}
    listen_host=${ACEXY_LISTEN_ADDR%:*}
    listen_host=${listen_host#[}
    listen_host=${listen_host%]}
    case "$listen_port" in
        ''|*[!0-9]*) ;;
        *) ACEXY_STATUS_PORT=$listen_port ;;
    esac
    case "$listen_host" in
        ''|0.0.0.0|::) ;;
        *) ACEXY_STATUS_HOST=$listen_host ;;
    esac
fi

response=$(curl -fsS "http://localhost:${FLASK_PORT}/api/v1/health") || fail "App healthcheck failed"
case "$response" in
    *'"status":"degraded"'*) fail "System health is degraded" ;;
esac

if [ "$ENABLE_ACEXY" = "true" ]; then
    if [ "$ENABLE_ACESTREAM_ENGINE" != "true" ]; then
        case "$ACEXY_HOST:$ACEXY_PORT" in
            localhost:6878|127.0.0.1:6878)
                fail "External AceStream target must not use localhost:6878 when in-container engine is disabled"
                ;;
        esac

        curl -fsS "http://${ACEXY_HOST}:${ACEXY_PORT}/webui/api/service?method=get_version" > /dev/null || fail "External AceStream engine not accessible"
    fi

    curl -fsS "http://${ACEXY_STATUS_HOST}:${ACEXY_STATUS_PORT}/ace/status" > /dev/null || fail "Acexy healthcheck failed"
elif [ "$ENABLE_ACESTREAM_ENGINE" = "true" ]; then
    # The engine root URL answers HTTP 500 ("couldn't find resource") on both
    # the native 3.2.x and the Android engine; get_version is the lightest
    # unauthenticated endpoint they all serve.
    curl -fsS "http://${ACESTREAM_HTTP_HOST}:${ACESTREAM_HTTP_PORT}/webui/api/service?method=get_version" > /dev/null || fail "In-container AceStream engine not accessible"
fi

printf 'All health checks passed\n'
