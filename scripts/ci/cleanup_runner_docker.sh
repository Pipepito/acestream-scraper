#!/usr/bin/env bash
# Shared CI retention policy. Caller must hold the Jenkins FIFO Docker lock.
# Never removes volumes, container-referenced images, explicit --keep images,
# or images outside this project's CI namespaces. --dry-run is read-only.
set -euo pipefail
exec python3 "$(dirname "$0")/docker_lifecycle.py" cleanup "$@"
