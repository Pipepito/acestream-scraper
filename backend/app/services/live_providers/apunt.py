"""À Punt, the Valencian public broadcaster, which streams through Brightcove
and no list carries.

Brightcove's playback API returns the live stream without registration, given
the player's policy key, exactly as for Telemadrid: the key lives in the
player's JavaScript, is kept in memory, and is read again once when the API
refuses it.

À Punt publishes no stable `ref:` reference, so the channel is stored under
the numeric video id (`bcId`) its live page embeds. When that id stops
answering with the live stream -- an error, a recording, or no HLS source --
the live page is asked once for the id it embeds now. Reading the key again
never waits for the website: a rejected key is recovered from the player
script first, and the page lookup has a short deadline of its own so it
cannot use up the time the last request needs.
"""
import html
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = 'apunt://'
HOSTS = ('apuntmedia.es',)
GROUP = 'Valencia'
WEB = 'https://www.apuntmedia.es/'
ACCOUNT = '6057955885001'
PLAYER = 'wM4NX8x9T'
PLAYER_JS = f'https://players.brightcove.net/{ACCOUNT}/{PLAYER}_default/index.min.js'
# Brightcove player scripts exceed the 2 MiB provider response bound (see
# telemadrid): without room for it no key, and no channel.
PLAYER_JS_MAX_BYTES = 8 * 1024 * 1024
API = f'https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT}/videos/%s'
LIVE_PAGE = WEB + 'directe/directe-tv_136_1392524.html'
LIVE_PAGE_MAX_BYTES = 2 * 1024 * 1024
# The page lookup is optional recovery: it never gets the whole resolution
# budget (15 s when a player opens the channel), so one request still fits.
LIVE_PAGE_SECONDS = 5.0
HEADERS = {'User-Agent': base.USER_AGENT, 'Referer': WEB, 'Origin': WEB.rstrip('/')}
# No playback header is known to be needed: the master playlist answered
# without Referer or Origin on 2026-11-10.
PLAY_HEADERS: Dict[str, str] = {}

# The live page's Brightcove video id -> (name, guide id).
CHANNELS = {
    '6137605659001': ('À Punt', 'APunt.TV'),
}

# Brightcove has answered with either HLS type (2026-11-10: the Apple one).
HLS_TYPES = ('application/x-mpegurl', 'application/vnd.apple.mpegurl')

_POLICY = re.compile(r'policyKey\s*:\s*"([^"]+)"')
# A Brightcove video id is a run of digits; anything else is not taken. The
# page carries it twice (2026-11-10): as `bcId` in the player's settings,
# which sit HTML-escaped in an attribute, and in the player link of its
# structured data, with JSON-escaped slashes.
_BCID = re.compile(r'"bcId"\s*:\s*"?(\d{6,20})(?!\d)')
_PLAYER_LINK = re.compile(re.escape(PLAYER) + r'_default\\?/index\.html\?videoId=(\d{6,20})(?!\d)')
_policy_key: Optional[str] = None
# Stored id -> the id that last served the live stream in its place. Kept in
# memory only: the stored id stays what the playlist and the database know.
_live_ids: Dict[str, str] = {}


def channels() -> List[Dict[str, Optional[str]]]:
    return [{'ident': ident, 'name': name, 'tvg_id': tvg_id}
            for ident, (name, tvg_id) in CHANNELS.items()]


def policy_key(refresh: bool = False) -> Optional[str]:
    global _policy_key
    if _policy_key and not refresh:
        return _policy_key
    match = _POLICY.search(base.http.get_text(PLAYER_JS, HEADERS, max_bytes=PLAYER_JS_MAX_BYTES))
    if not match:
        base.log.warning('apunt: the player no longer publishes policyKey where expected')
        return None
    _policy_key = match.group(1)
    return _policy_key


def _live_link(ident: str, key: str) -> Optional[str]:
    """The HLS link of this video if it is the live stream, or None.

    Raises what the API request raises: the caller decides what a refusal means.
    """
    data: Any = base.http.get_json(API % quote(ident, safe=''),
                                   dict(HEADERS, Accept=f'application/json;pk={key}'))
    if not isinstance(data, dict):
        return None
    # -1 marks a live stream and 0 a live stream with a rewind window; a
    # positive number is a recording, which must not be served as the channel.
    if data.get('duration') not in (-1, 0, None):
        base.log.warning('apunt: %s is not live (duration=%s)', ident, data.get('duration'))
        return None
    for source in data.get('sources') or []:
        if (isinstance(source, dict) and str(source.get('type') or '').lower() in HLS_TYPES
                and source.get('src')):
            return source['src']
    return None


def _page_live_id() -> Optional[str]:
    """The video id the live page embeds now, within its own short deadline."""
    limits = base.resolution_limits.get()
    deadline, cancelled = limits if limits else (time.monotonic() + base.TIMEOUT, None)
    token = base.resolution_limits.set((min(deadline, time.monotonic() + LIVE_PAGE_SECONDS), cancelled))
    try:
        page = base.http.get_text(LIVE_PAGE, HEADERS, max_bytes=LIVE_PAGE_MAX_BYTES)
    except Exception as error:
        base.log.warning('apunt: the live page could not be read (%s)', type(error).__name__)
        return None
    finally:
        base.resolution_limits.reset(token)
    page = html.unescape(page)
    match = _BCID.search(page) or _PLAYER_LINK.search(page)
    return match.group(1) if match else None


def resolve(ident: str) -> Optional[str]:
    """At most six requests: key, video, key again, video, live page, video."""
    key = policy_key()
    if not key:
        return None
    known = _live_ids.get(ident, ident)
    try:
        link = _live_link(known, key)
    except Exception:
        # A rotated key is the usual cause, and recovering from it needs only
        # the player script: read it again, once, before asking the website.
        key = policy_key(refresh=True)
        if not key:
            return None
        try:
            link = _live_link(known, key)
        except Exception:
            link = None
    if link:
        return link
    # The id answers with an error, a recording or no HLS source: the live
    # stream has moved. Ask the live page which id it embeds now, once.
    _live_ids.pop(ident, None)
    current = _page_live_id()
    if not current or current == known:
        return None
    link = _live_link(current, key)
    if link:
        _live_ids[ident] = current
    return link
