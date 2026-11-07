"""A channel's schedule page on Sincroguia, as an XMLTV guide.

Some channels are in no XMLTV guide at all. 7 TV La Rioja is one: none of
the fifteen merged guides carries it and its own website publishes no
schedule. Sincroguia does, as plain server-side HTML (no JavaScript, no
hidden API, no cookies), three days per page, with start AND end times,
synopsis and category. The source URL is the channel's page, e.g.
https://sincroguia-tv.expansion.com/programacion/la-7-rioja

Three traps:

1. Times are Spanish local time, and the offset is NOT fixed. The module
   this was ported from wrote a constant `+0200` (summer time), tested only
   with September dates; from the last Sunday of October the guide would
   have been one hour off until March. Times are converted with
   Europe/Madrid and written in UTC.
2. A schedule "day" does not start at midnight: 7 TV's runs 09:00 to 08:59
   the next day. When a start time goes BACKWARDS, midnight was crossed.
   An end time can cross it on its own too ("23:00 a 00:00h").
3. Day titles have no year. Choose the nearest year across December/January
   and reject dates more than 45 days away rather than silently moving stale data.

Aggregator pages carry `ld+json` blocks that look like the schedule and are
not: they are the big networks' highlights with the page's channel name on
top. Only the schedule HTML is read.
"""
# Adapted from scarcraft1's aporte/guias-html contribution to issue #233
# (commit 43bb3014d588e2373a6775fb4fe5ce6958fede4c).
import html
import re
from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from xml.sax.saxutils import escape, quoteattr
from zoneinfo import ZoneInfo

HOST = "sincroguia-tv.expansion.com"
ID_PREFIX = "sincroguia."
MADRID = ZoneInfo("Europe/Madrid")

MONTHS = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
          "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
          "diciembre": 12}

_DAY = re.compile(r'class="m-schedule-day__title"[^>]*>(.*?)</', re.S)
_DATE = re.compile(r"(\d{1,2})\s+de\s+([a-zá-ú]+)", re.I)
_PROGRAM = re.compile(
    r'<div class="m-program" id="event-\d+">(.*?)'
    r'(?=<div class="m-program" id="event-|<h2 class="m-schedule-day|\Z)', re.S)
_NAME = re.compile(r'class="m-program__name"[^>]*>(.*?)</h2>', re.S)
_TIMES = re.compile(r'class="m-program__info"[^>]*>\s*(\d{1,2}):(\d{2})\s*a\s*'
                    r'(\d{1,2}):(\d{2})\s*h?\s*</p>', re.S)
_SYNOPSIS = re.compile(r'class="m-program__short-description"[^>]*>(.*?)</p>', re.S)
_TITLE = re.compile(r'<h1 class="m-top__title"[^>]*>(.*?)</h1>', re.S)
_CANONICAL = re.compile(r'<link rel="canonical" href="([^"]+)"')
_TAGS = re.compile(r"<[^>]+>")


def is_sincroguia_url(url: str) -> bool:
    parsed = urlparse(url or "")
    return parsed.scheme in ("http", "https") and parsed.hostname == HOST and bool(re.fullmatch(r"/programacion/[a-z0-9-]+/?", parsed.path))


def _clean(text: str) -> str:
    return " ".join(html.unescape(_TAGS.sub(" ", text or "")).split())


def _day_date(title: str, today: date) -> Optional[date]:
    m = _DATE.search(title or "")
    month = MONTHS.get(m.group(2).lower()) if m else None
    if not month:
        return None
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, month, int(m.group(1))))
        except ValueError:
            pass
    if not candidates:
        return None
    result = min(candidates, key=lambda day: abs((day - today).days))
    return result if abs((result - today).days) <= 45 else None


def _utc(day: date, at: time) -> datetime:
    from app.schemas.events import event_time
    return event_time(datetime.combine(day, at), "Europe/Madrid")


def programmes(text: str, today: Optional[date] = None) -> List[Tuple[datetime, datetime, str, str]]:
    """[(start_utc, stop_utc, title, synopsis)] in page order."""
    today = today or datetime.now(MADRID).date()
    out = []
    parts = _DAY.split(text)
    # split() leaves [before, title1, body1, title2, body2, ...]
    for i in range(1, len(parts) - 1, 2):
        day = _day_date(_clean(parts[i]), today)
        if not day:
            raise ValueError("Invalid Sincroguía schedule date")
        previous = None
        for m in _PROGRAM.finditer(parts[i + 1]):
            block = m.group(1)
            t, n = _TIMES.search(block), _NAME.search(block)
            title = _clean(n.group(1)) if n else ""
            if not t or not title:
                raise ValueError("Incomplete Sincroguía programme")
            start = time(int(t.group(1)), int(t.group(2)))
            end = time(int(t.group(3)), int(t.group(4)))
            if previous is not None and start < previous:      # trap 2
                day += timedelta(days=1)
            previous = start
            stop_day = day + timedelta(days=1) if end <= start else day
            s = _SYNOPSIS.search(block)
            synopsis = _clean(s.group(1)) if s else ""
            out.append((_utc(day, start), _utc(stop_day, end), title,
                        "" if synopsis == title else synopsis))
    if len(re.findall(r'class="m-program"', text)) != len(out):
        raise ValueError("Incomplete Sincroguía programme")
    if not out or len(out) > 1500:
        raise ValueError("Sincroguía schedule is missing or exceeds its row limit")
    if any(out[i][1] > out[i + 1][0] for i in range(len(out) - 1)):
        raise ValueError("Sincroguía programmes overlap")
    return out


def channel_of(text: str, url: str = "") -> Tuple[str, str]:
    """(guide channel id, display name). The id comes from the URL slug, so
    it stays the same if the page renames the channel."""
    if not is_sincroguia_url(url):
        raise ValueError("Use a Sincroguía channel URL")
    path = urlparse(url).path.rstrip("/")
    slug = path.rsplit("/", 1)[-1] or "unknown"
    t = _TITLE.search(text)
    name = re.sub(r"^\s*Programación\s+", "", _clean(t.group(1))) if t else slug
    return ID_PREFIX + slug, name


def _xmltv_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S +0000")


def html_to_xmltv(content: bytes, url: str = "", today: Optional[date] = None) -> bytes:
    text = content.decode("utf-8", "replace")
    channel_id, name = channel_of(text, url)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<tv generator-info-name="acestream-scraper/sincroguia">',
             "  <channel id=%s><display-name>%s</display-name></channel>"
             % (quoteattr(channel_id), escape(name))]
    for start, stop, title, synopsis in programmes(text, today):
        lines.append("  <programme start=%s stop=%s channel=%s>"
                     % (quoteattr(_xmltv_time(start)), quoteattr(_xmltv_time(stop)),
                        quoteattr(channel_id)))
        lines.append('    <title lang="es">%s</title>' % escape(title))
        if synopsis:
            lines.append('    <desc lang="es">%s</desc>' % escape(synopsis))
        lines.append("  </programme>")
    lines.append("</tv>")
    return ("\n".join(lines) + "\n").encode("utf-8")
