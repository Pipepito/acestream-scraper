"""Task notifications through one webhook (#41).

When `notification_webhook_url` is set, the end of a URL scrape and of a
channel status pass -- or their failure -- is POSTed there as JSON:

    {"event": "url_scraping.completed", "title": "...", "message": "...",
     "data": {...the task's result...}}

`title` and `message` are the fields Gotify reads from a JSON POST to
`/message?token=...`, so a Gotify URL works as it is; anything else that
accepts a JSON POST (Home Assistant, n8n, a small relay to Telegram) can use
`event` and `data`. A notification never fails the task that sends it: errors
are logged and dropped. Exception text is left out on purpose, as in the
relay: it can contain URLs with credentials.
"""
import logging
from typing import Optional

from app.config.database import SessionLocal
from app.repositories.settings_repository import SettingsRepository
from app.utils import outbound_http, url_guard

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10


def webhook_url() -> str:
    db = SessionLocal()
    try:
        return (SettingsRepository(db).get_setting(SettingsRepository.NOTIFICATION_WEBHOOK_URL) or "").strip()
    finally:
        db.close()


def notify(event: str, title: str, message: str, data: Optional[dict] = None) -> bool:
    """POST one notification. True if the webhook answered 2xx; never raises."""
    try:
        url = webhook_url()
        if not url:
            return False
        url_guard.validate_outbound_url(url)
        response = outbound_http.source_post_json(
            url, {"event": event, "title": title, "message": message, "data": data or {}},
            timeout=TIMEOUT_SECONDS)
        if not 200 <= response.status_code < 300:
            logger.warning("Notification %s: webhook answered HTTP %s", event, response.status_code)
            return False
        return True
    except Exception as exc:
        logger.warning("Notification %s not sent: %s", event, type(exc).__name__)
        return False


def scraping_completed(result: dict) -> bool:
    message = "%s URL(s) scraped, %s failed" % (result.get("processed", 0), result.get("failures", 0))
    title = 'URL scraping finished'
    if result.get('saved_search_id') is not None:
        title = 'Saved search finished'
        message = 'Saved search run finished'
    if result.get('catalogues'):
        message += "; %s W3U catalogue(s), %s partial" % (result['catalogues'], result.get('catalogue_partial', 0))


    events = result.get('events', {})
    if any(events.values()):
        message += "; events: %s updated, %s need review, %s source failures, %s sources deferred" % (
            events.get('updated', 0), events.get('pending', 0), events.get('failures', 0), events.get('deferred', 0))
    searches = result.get('saved_searches', {})
    if searches:
        message += "; saved searches: %s added, %s existing, %s excluded, %s unresolved, %s partial, %s failed, %s skipped, %s interrupted, %s candidates deferred, %s searches deferred" % (
            searches.get('added', 0), searches.get('existing', 0), searches.get('excluded_candidates', 0),
            searches.get('unresolved_candidates', 0), searches.get('partial', 0), searches.get('failed', 0),
            searches.get('skipped', 0), searches.get('interrupted', 0),
            searches.get('deferred_candidates', 0), searches.get('deferred_searches', 0))
    excluded = result.get('import_exclusions', {}).get('excluded_candidates', 0)
    if excluded:
        message += "; %s source candidates excluded" % excluded
    return notify("url_scraping.completed", title, message, result)


def channel_status_completed(result: dict) -> bool:
    if result.get("message"):
        return False          # nothing was checked (no engine configured)
    message = "%s checked: %s online, %s offline, %s failed" % (
        result.get("checked", 0), result.get("online", 0),
        result.get("offline", 0), result.get("failed", 0))
    title = "Channel check finished"
    if result.get("deferred", 0):
        reason = "playback active" if result.get("stop_reason") == "viewing" else "application stopping"
        title = "Channel check incomplete"
        message += "; %s deferred (%s)" % (result["deferred"], reason)
    return notify("channel_status.completed", title, message, result)


def task_failed(task: str, exc: BaseException) -> bool:
    return notify("%s.failed" % task, "Task failed: %s" % task, type(exc).__name__,
                  {"task": task, "error": type(exc).__name__})


def channel_check_completed(result: dict) -> bool:
    """Notify an explicit single-channel check, never a playback/background probe."""
    if result["status"] == "skipped":
        return False
    # Probe messages/errors may contain upstream details; publish only fixed
    # status fields, never source URLs, names, or the raw engine response.
    data = {
        "channel_id": result["channel_id"],
        "status": result["status"],
        "is_online": result["is_online"],
        "network_status": result.get("network_status", "unknown"),
    }
    return notify("channel_check.completed", "Channel check finished",
                  "Channel is %s" % result["status"], data)


def channel_check_failed(channel_id: str, exc: BaseException) -> bool:
    return notify("channel_check.failed", "Channel check failed", type(exc).__name__,
                  {"channel_id": channel_id, "error": type(exc).__name__})
