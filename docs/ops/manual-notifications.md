# Manual-action notifications

Settings → Automation → Notifications uses the same saved webhook for scheduled
jobs, run-now jobs, manual source scrapes and individual channel checks.
An empty webhook disables delivery. A Gotify `/message?token=…` URL accepts the
payload directly; other systems can consume the JSON through their own relay.

| Action | Event | Payload |
| --- | --- | --- |
| Scrape URL, saved source, or scrape all | `url_scraping.completed` | One summary: processed sources, failures, channel count |
| Scrape action raises an exception | `url_scraping.failed` | Task name and exception class |
| Individual channel check | `channel_check.completed` | Channel ID, online/offline status, verified-signal boolean and network status |
| Individual check raises an exception | `channel_check.failed` | Channel ID and exception class |
| Scheduled/run-now stream check | `channel_status.completed` / `channel_status.failed` | Existing task summary, without per-channel messages |

A completed scrape summary can contain failed sources; it is still one message
for the whole action. A skipped individual check (no engine, unavailable engine
or playback ownership) sends nothing and preserves its existing result.
Cancelled actions send no failure notification. Playback/background probes and
EPG refreshes do not generate these individual notifications.

Delivery runs off the event loop after the action; the existing bounded HTTP
timeout still applies. Delivery failure is logged without failing the action.
Payloads exclude source URLs, channel names, engine response text and exception
messages. Notifications report each explicit action, not online/offline
transitions. Native Telegram bot configuration and continuous offline monitoring
remain outside this implementation.

Coverage: `backend/tests/test_manual_notifications.py` and the built-app journey
`e2e/tests/16-manual-notifications.spec.ts`.
