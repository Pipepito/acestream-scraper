# Reporting a bug

Check [Troubleshooting](Troubleshooting.md) and search [existing issues](https://github.com/Pipepito/acestream-scraper/issues) first. When testing a newer image, back up the config directory and retain the old tag/digest; see [safe upgrades](Installation.md#updating-to-a-newer-image).

## Download diagnostics

In **Overview → Services**, select **Download diagnostics**. The ZIP contains bounded recent scraper, entrypoint and per-service logs, plus file availability and runtime details. It includes the separate checker log when that engine is enabled. The download does not restart services or run channel checks.

During failed startup, use the startup screen's diagnostics and the runtime diagnostic endpoint `GET /api/v1/system/diagnostics`; both preserve normal optional API-token protection. Startup diagnostics describe milestones; runtime diagnostics include recent process output. Neither contains a database backup.

Common credentials and addresses are masked on export. **Review before attaching**: arbitrary source names and third-party output may still be private. Do not post database files, full environment dumps, unredacted Compose files, tokens, license keys, player passwords or QR codes containing authenticated URLs.

Capture starts with the container image providing the collector. Old output, host kernel logs and external-engine logs are not recoverable from this ZIP. See [diagnostic retention and limits](https://github.com/Pipepito/acestream-scraper/blob/develop/docs/ops/runtime-diagnostics.md).

## Record the deployment

Run these read-only commands, replacing the container name if needed:

```bash
docker inspect --format 'Image tag: {{.Config.Image}}; image ID: {{.Image}}' acestream-scraper
docker inspect --format '{{.State.Health.Status}}' acestream-scraper
docker version
docker compose version
docker logs --timestamps --tail 200 acestream-scraper
```

The first command reports the image actually used by this container. Moving tags such as `develop` and `latest` are not enough to identify a build; include the image ID/digest too. Inspect and redact raw Docker logs before sharing them.

Record CPU architecture, host OS, browser/version and enabled services. Say whether playback is direct or through Acexy, whether checks use a separate engine, and whether the player uses a stable TV relay or an individual stream URL. Include any reverse proxy or remote-player setup relevant to the failure, with private details removed.

## Useful checks

- **Overview:** service state, engine version, scheduled job launch/result and open-stream counts. Counts are not viewer totals and do not prove media delivery.
- **Health:** `curl -i http://localhost:8000/api/v1/health` (public). Startup failures return 503 while the recovery page remains available.
- **Playback:** note the player message, selected stream/audio track, approximate start/failure times and whether another source succeeds.
- **Scraping:** note source type and last result. Share a minimal public sample you are permitted to redistribute, not private source credentials.
- **EPG:** record station mapping, source refresh result, programme time and the viewing device timezone.

For startup failures, follow [recovery guidance](Troubleshooting.md#startup-or-upgrade-does-not-finish) before attempting a database reset. Do not delete migration markers or backups to silence an error.

## Issue template

Copy this into a [new GitHub issue](https://github.com/Pipepito/acestream-scraper/issues/new):

```text
Summary:
Image tag and image ID/digest:
Architecture / host OS:
Browser or media player:
Enabled services; playback and checker routing:

Steps to reproduce:
1.
2.
3.

Expected behavior:
Actual behavior and exact error:
When it happened (include timezone):
Always or intermittent:
What else I tried:

Attachments: reviewed diagnostics, redacted configuration, screenshots
```
