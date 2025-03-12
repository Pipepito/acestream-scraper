#!/bin/bash
set -e

# Check Flask app
response=$(curl -s http://localhost:$FLASK_PORT/health)
if [ $? -ne 0 ]; then
    echo "Flask app healthcheck failed"
    exit 1
fi

# Check if response indicates degraded status
if echo "$response" | grep -q '"status":"degraded"'; then
    echo "System health is degraded"
    exit 1
fi

# Check Acexy (only if enabled)
if [ "$ENABLE_ACEXY" = "true" ]; then
    if [ "$ENABLE_ACESTREAM_ENGINE" = "false" ]; then
        # Check external Acestream Engine
        if ! curl -s -f "$ACEXY_HOST:$ACEXY_PORT" > /dev/null; then
            echo "External Acestream Engine not accessible"
            exit 1
        fi
    fi
    
    if ! curl -s -f http://localhost:8080/ace/status > /dev/null; then
        echo "Acexy healthcheck failed"
        exit 1
    fi
fi

# All checks passed
echo "All health checks passed"
exit 0