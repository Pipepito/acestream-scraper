#!/usr/bin/env bash
# Idempotent Cloudflare WARP setup for the Jenkins build VM.
#
# Some upstream domains (download.acestream.media in particular) are
# blocked at the homelab ISP. Routing the host's egress through WARP
# bypasses that block and gets inherited by Docker daemons running on
# the same host, so buildx RUN steps reach the upstream cleanly.
#
# Safe to call from every Jenkins build: first run installs + connects;
# subsequent runs short-circuit once `warp=on`. Requires passwordless sudo
# for the install/enable steps (sudo -n: never prompts). The caller
# (bootstrap_jenkins_runner.sh) treats a non-zero exit as a warning.
set -euo pipefail

log() { printf '[setup-jenkins-warp] %s\n' "$*"; }
warn() { printf '[setup-jenkins-warp] WARN: %s\n' "$*" >&2; }

if [[ "$(uname -s)" != "Linux" ]]; then
    log "non-Linux host; skipping"
    exit 0
fi

WARP_CLI=("warp-cli" "--accept-tos")

# 1. Install the package if missing.
if ! command -v warp-cli >/dev/null 2>&1; then
    log "installing cloudflare-warp"
    sudo -n install -m 0755 -d /usr/share/keyrings
    if [[ ! -s /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg ]]; then
        curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
            | sudo -n gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
    fi
    distro="$(. /etc/os-release && echo "${VERSION_CODENAME:-noble}")"
    if [[ ! -f /etc/apt/sources.list.d/cloudflare-client.list ]]; then
        printf 'deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ %s main\n' \
            "$distro" | sudo -n tee /etc/apt/sources.list.d/cloudflare-client.list >/dev/null
    fi
    sudo -n apt-get update
    sudo -n apt-get install -y --no-install-recommends cloudflare-warp
fi

# 2. Make sure warp-svc is running. Service name varies by package version.
ensure_service() {
    local svc
    for svc in warp-svc cloudflare-warp; do
        if systemctl list-unit-files --type=service 2>/dev/null | grep -q "^${svc}\\.service"; then
            sudo -n systemctl enable --now "$svc" >/dev/null 2>&1 || true
            return 0
        fi
    done
    warn "no warp-svc service unit found; relying on existing init"
}
ensure_service

# 3. Wait for warp-cli to reach a stable state. The daemon may briefly
# return "Status update: Unable / Reason: Daemon Startup" right after
# install/start; we want either Connected, Disconnected, or
# Registration Missing before we do anything.
status_text=""
for _ in $(seq 1 30); do
    status_text="$( "${WARP_CLI[@]}" status 2>&1 || true )"
    if grep -qiE 'connected|disconnected|registration missing|not registered' <<<"$status_text"; then
        break
    fi
    sleep 1
done

if ! grep -qiE 'connected|disconnected|registration missing|not registered' <<<"$status_text"; then
    warn "warp-cli daemon never reached a stable state"
    printf '%s\n' "$status_text" >&2
    exit 1
fi

# 4. Register if needed. The daemon reports "Registration Missing"
# (sometimes with "due to: Daemon Startup") when no registration exists.
if grep -qiE 'registration missing|not registered|register first' <<<"$status_text"; then
    log "registering WARP"
    "${WARP_CLI[@]}" registration new
    # After registration, give the daemon a moment to refresh state.
    for _ in $(seq 1 10); do
        status_text="$( "${WARP_CLI[@]}" status 2>&1 || true )"
        if ! grep -qiE 'registration missing|not registered' <<<"$status_text"; then
            break
        fi
        sleep 1
    done
fi

# 5. Set full-tunnel mode (idempotent: warp-cli noop if already that mode).
# Must run AFTER registration; it is rejected on an unregistered daemon.
# warp-cli >= 2023.x spells it `mode warp`; older releases `set-mode warp`.
if ! "${WARP_CLI[@]}" mode warp >/dev/null 2>&1; then
    "${WARP_CLI[@]}" set-mode warp >/dev/null 2>&1 || warn "could not set WARP mode (continuing)"
fi

# 6. Connect if not already connected. Match only the "Connected" steady
# state — "Status update: Unable" with reason "Connecting" must NOT count.
status_text="$( "${WARP_CLI[@]}" status 2>&1 || true )"
if ! grep -qiE 'status update: connected|^connected|status: connected' <<<"$status_text"; then
    log "connecting WARP"
    "${WARP_CLI[@]}" connect
fi

# 7. Verify warp=on through the public trace endpoint.
trace_url='https://www.cloudflare.com/cdn-cgi/trace'
for attempt in $(seq 1 15); do
    if curl -fsS --max-time 5 "$trace_url" 2>/dev/null | grep -qx 'warp=on'; then
        log "WARP active (warp=on)"
        "${WARP_CLI[@]}" status 2>&1 | head -3 || true
        exit 0
    fi
    sleep 2
done

warn "WARP did not report warp=on after 30s"
"${WARP_CLI[@]}" status 2>&1 | head -10 || true
exit 1
