#!/usr/bin/env bash
# Start engine + Acexy (one container) and a kubo IPFS gateway, then wait until
# every service answers. Idempotent: re-running just re-checks readiness.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/env.sh"

mkdir -p "$STACK_DIR/container-config"
image="${E2E_IMAGE:-acestream-scraper:e2e-arm64}"
if ! docker image inspect "$image" >/dev/null 2>&1; then
  log "image $image is missing; building scraper-acestream-acexy for ${E2E_PLATFORM:-linux/arm64}"
  (cd "$REPO_ROOT" && bash scripts/ci/build_multiarch_images.sh \
      --flavor scraper-acestream-acexy --platforms "${E2E_PLATFORM:-linux/arm64}" --load --tag "$image")
fi

docker compose -f "$COMPOSE_FILE" up -d

wait_for_http "$E2E_ENGINE_URL/webui/api/service?method=get_version" 240 "AceStream engine"
wait_for_http "$E2E_ACEXY_URL/ace/status" 120 "Acexy"
wait_for_http "$E2E_DOCKER_APP_URL/api/v1/health" 120 "containerised app"

# kubo: the gateway answers once the daemon is up; IPNS resolution warms on first use.
for _ in $(seq 1 30); do
  if docker exec acestream-e2e-ipfs ipfs id >/dev/null 2>&1; then log "kubo daemon is up"; break; fi
  sleep 2
done
if [ -n "${E2E_IPNS_WARMUP_URL:-}" ]; then
  log "warming IPNS resolution for $E2E_IPNS_WARMUP_URL"
  curl -sS -m 180 -o /dev/null -w 'IPNS warmup http=%{http_code} in %{time_total}s\n' "$E2E_IPNS_WARMUP_URL" || true
fi
log "stack ready: engine=$E2E_ENGINE_URL acexy=$E2E_ACEXY_URL ipfs=$E2E_IPFS_GATEWAY docker-app=$E2E_DOCKER_APP_URL"
