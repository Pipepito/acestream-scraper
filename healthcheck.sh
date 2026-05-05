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

        curl -fsS "http://${ACEXY_HOST}:${ACEXY_PORT}" > /dev/null || fail "External AceStream engine not accessible"
    fi

    curl -fsS "http://localhost:${ACEXY_STATUS_PORT}/ace/status" > /dev/null || fail "Acexy healthcheck failed"
elif [ "$ENABLE_ACESTREAM_ENGINE" = "true" ]; then
    curl -fsS "http://${ACESTREAM_HTTP_HOST}:${ACESTREAM_HTTP_PORT}" > /dev/null || fail "In-container AceStream engine not accessible"
fi

printf 'All health checks passed\n'
