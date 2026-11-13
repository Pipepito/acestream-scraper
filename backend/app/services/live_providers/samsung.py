"""Samsung TV Plus's channels for Spain (189 on 2026-10-28, 176 without DRM).

Samsung publishes no playlist. i.mjh.nz keeps its channel list, by region,
as a gzip JSON file without stream links; the link comes from its author's
redirector, `jmp2.uk/stvp-<id>`, which answers 302 to the channel's own
host (Amagi, MediaTailor, Wurl, Samsung's `sis-global`...). That redirector
answered 429 after about 35 requests in 25 minutes, so its answers are kept
and its use is capped: never more than REDIRECTS_PER_HOUR, a pause after a
refusal, and none at all for status checks, which would spend the quota
sweeping the catalogue: a check only gets a link already kept from the last
LINK_SECONDS, and reports "not checked" otherwise. The links seen carry no
token.

13 channels carry a Widevine licence in the list (public and regional
broadcasters among them): CENC that Kodi cannot play here, left out.
Amagi channels use extension-less beacon segments; the tuner relay already
turns them into links of its own.
"""
import re
import threading
from collections import deque
from typing import Dict, List, Optional

from app.services.live_providers import base

SCHEME = 'samsung://'
HOSTS = ('samsungtvplus.com',)
GROUP = 'Samsung TV Plus'
LIST = 'https://i.mjh.nz/SamsungTVPlus/.channels.json.gz'
REDIRECTOR = 'https://jmp2.uk/stvp-%s'
REGION = 'es'
# The User-Agent the list itself names for its links.
HEADERS = {'User-Agent': 'okhttp/4.12.0'}
# Measured: no host answered 403 to Kodi's User-Agent.
PLAY_HEADERS: Dict[str, str] = {}
LINK_SECONDS = 12 * 3600
REDIRECTS_PER_HOUR = 15
PAUSE_AFTER_REFUSAL = 30 * 60
_ID = re.compile(r'[A-Z0-9]{8,20}')

_lock = threading.Lock()
_links: Dict[str, tuple] = {}   # id -> (link, resolved at)
_asked: deque = deque()          # when the redirector was asked, last hour
_paused_until = 0.0


def forget() -> None:
    global _paused_until
    with _lock:
        _links.clear()
        _asked.clear()
        _paused_until = 0.0


def channels() -> List[Dict[str, Optional[str]]]:
    data = base.http.get_json(LIST, HEADERS)
    region = ((data.get('regions') or {}).get(REGION) or {}).get('channels') or {}
    return [{'ident': ident, 'name': channel['name'], 'logo': channel.get('logo')}
            for ident, channel in region.items()
            if _ID.fullmatch(ident) and channel.get('name') and not channel.get('license_url')]


def _may_ask(now: float) -> bool:
    while _asked and now - _asked[0] >= 3600:
        _asked.popleft()
    return now >= _paused_until and len(_asked) < REDIRECTS_PER_HOUR


def resolve(ident: str) -> Optional[str]:
    global _paused_until
    if not _ID.fullmatch(ident):
        return None
    now = base.now()
    with _lock:
        known = _links.get(ident)
        if known and now - known[1] < LINK_SECONDS:
            return known[0]
        if base.checking.get():
            return None
        if not _may_ask(now):
            base.log.warning('samsung: redirector quota spent or paused; %s %s', ident,
                             'keeps its previous link' if known else 'has no link')
            return known[0] if known else None
        _asked.append(now)
    try:
        link = base.http.get_location(REDIRECTOR % ident, HEADERS)
    except ValueError as error:
        if '429' in str(error):
            with _lock:
                _paused_until = base.now() + PAUSE_AFTER_REFUSAL
            base.log.warning('samsung: the redirector refused (429); resting %d min',
                             PAUSE_AFTER_REFUSAL // 60)
            return known[0] if known else None
        raise
    if not link:
        return known[0] if known else None
    with _lock:
        _links[ident] = (link, base.now())
    return link
