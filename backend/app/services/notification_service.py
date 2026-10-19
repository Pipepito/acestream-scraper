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
    return notify("url_scraping.completed", "URL scraping finished",
                  "%s URL(s) scraped, %s failed" % (result.get("processed", 0), result.get("failures", 0)),
                  result)


def channel_status_completed(result: dict) -> bool:
    if result.get("message"):
        return False          # nothing was checked (no engine configured)
    return notify("channel_status.completed", "Channel check finished",
                  "%s checked: %s online, %s offline, %s failed" % (
                      result.get("checked", 0), result.get("online", 0),
                      result.get("offline", 0), result.get("failed", 0)),
                  result)


def task_failed(task: str, exc: BaseException) -> bool:
    return notify("%s.failed" % task, "Task failed: %s" % task, type(exc).__name__,
                  {"task": task, "error": type(exc).__name__})
