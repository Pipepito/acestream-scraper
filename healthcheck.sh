#!/bin/bash
set -e

# Check Flask app
if ! curl -s -f http://localhost:8000/health > /dev/null; then
  echo "Flask app healthcheck failed"
  exit 1
fi

# Check Acexy (only if enabled)
if [ "$ENABLE_ACEXY" = "true" ]; then
  if ! curl -s -f http://localhost:8080/ace/status > /dev/null; then
    echo "Acexy healthcheck failed"
    exit 1
  fi
fi

# All checks passed
exit 0