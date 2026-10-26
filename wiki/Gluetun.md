# Gluetun port forwarding

Set `ACESTREAM_GLUETUN_PORT_FILE` to a shared forwarded-port file to keep the
**bundled playback engine** on the VPN provider's assigned P2P port. This is
opt-in and works with both engine image flavours on amd64, arm64 and experimental
arm/v7. It needs no Gluetun API key or Docker socket.

Gluetun must support forwarding for your chosen provider, have forwarding enabled,
and share its network namespace with the scraper. Configure the provider using
[Gluetun's forwarding guide](https://github.com/qdm12/gluetun-wiki/blob/main/setup/advanced/vpn-port-forwarding.md).
A port number alone does not route traffic through a VPN or establish reachability.

## Compose setup

Adapt your existing Gluetun service; keep its provider settings, credentials,
capabilities, healthcheck and VPN device configuration. The relevant additions are:

```yaml
services:
  gluetun:
    # Keep your existing image and provider configuration.
    environment:
      VPN_PORT_FORWARDING: "on"
      VPN_PORT_FORWARDING_STATUS_FILE: /tmp/gluetun/forwarded_port
      FIREWALL_INPUT_PORTS: "8000,6878,8080"
    volumes:
      - gluetun-port:/tmp/gluetun
    ports:
      - "0.0.0.0:8000:8000" # Scraper UI; change FLASK_PORT if Gluetun control uses 8000
      - "0.0.0.0:6878:6878" # Engine API: trusted networks only
      - "0.0.0.0:8080:8080" # Acexy, when enabled

  acestream-scraper:
    image: pipepito/acestream-scraper:latest
    network_mode: "service:gluetun"
    depends_on:
      gluetun:
        condition: service_healthy
    environment:
      ACESTREAM_GLUETUN_PORT_FILE: /gluetun/forwarded_port
    volumes:
      - gluetun-port:/gluetun:ro
      # Keep your existing persistent configuration and engine-state mounts.

volumes:
  gluetun-port:
```

Gluetun's control server also commonly uses port 8000. If it is enabled there,
set the scraper's `FLASK_PORT=8002`, publish `0.0.0.0:8002:8002` on Gluetun instead and
allow 8002 in `FIREWALL_INPUT_PORTS`. Merge firewall/volume settings with your
existing ones. Publish only interfaces you need, bound to trusted host addresses.
Do not put `ports` on the scraper when it shares Gluetun's network namespace.
Do not publish the assigned P2P port through Docker: incoming VPN traffic arrives
inside the shared namespace. The assigned port must not belong to another app
sharing that namespace.

Mount the **directory**, not a single file: Gluetun may replace the file. The
scraper reads it read-only. Gluetun currently documents the status file but plans
to deprecate it in v4. A future deployment may instead write the single decimal
port to this same shared file from Gluetun's port-forwarding up/down hooks; clear
it on forwarding loss. This integration does not poll the control API.

## Runtime behavior

- Poll every five seconds. Accept a single decimal port in 1024–65535 after two
  consecutive observations. Reject known container-listener conflicts, port
  8622 reserved for the checker, multiple ports, symlinks and non-regular files.
- A changed accepted port terminates the old playback process group and restarts
  the engine with `--port`. **Active playback is interrupted** by port rotation.
  Engine HTTP/API URLs and Acexy upstream ports do not change.
- Missing, cleared, invalid or conflicting input leaves the last accepted port
  unchanged and logs a notice once per outage. Before the first accepted value,
  the engine’s configured P2P port (normally 8621) is used. This is not a VPN kill switch; Gluetun owns
  routing/firewall protection. After container restart, the file is read again.
- UI Stop stays stopped across file changes. Start/Restart uses the latest accepted
  port. Normal crash recovery remains persistent. Checker supervision, identity,
  state and port 8622 remain independent: one forwarded port cannot be assigned
  to both engines.
- Requires the packaged foreground playback command. Custom
  `ACESTREAM_START_COMMAND` overrides and external playback engines must manage
  their ports separately; combining a custom command with sync fails startup
  with an actionable message. Flavours without an enabled bundled engine reject
  the option. Leave WARP disabled when Gluetun owns VPN routing.

Check the `acestream` service log (or the diagnostics download) for accepted
port changes and unavailable/invalid input. Automated tests cover parsing and
supervisor transitions; actual provider reachability and ARMv7 hardware remain
operator validation, not implied by passing a local lifecycle test.
