"""À Punt (RTVV), the Valencian regional broadcaster, which streams through
Brightcove and no list carries.

Same mechanism as telemadrid: Brightcove's playback API serves the live
stream without registration, given the player's policy key, which lives in
the player's JavaScript and is read again once when the API refuses it.

À Punt publishes no stable `ref:` id, so the channel is addressed by the
numeric video id (`bcId`) its own live page embeds. The page is read again
when the stored id stops resolving, so a rotation heals itself.
"""
import re
from typing import Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = 'apunt://'
HOSTS = ('apuntmedia.es',)
GROUP = 'Valencia'
WEB = 'https://www.apuntmedia.es/'
ACCOUNT = '6057955885001'
PLAYER = 'wM4NX8x9T'
PLAYER_JS = f'https://players.brightcove.net/{ACCOUNT}/{PLAYER}_default/index.min.js'
PLAYER_JS_MAX_BYTES = 8 * 1024 * 1024
API = f'https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT}/videos/%s'
DIRECTE = WEB + 'directe/directe-tv_136_1392524.html'
HEADERS = {'User-Agent': base.USER_AGENT, 'Referer': WEB, 'Origin': WEB.rstrip('/')}
# Measured over 30 minutes: playback needs no header.
PLAY_HEADERS: Dict[str, str] = {}

# The live page's Brightcove video id -> (name, guide id).
CHANNELS = {
    '6137605659001': ('À Punt', 'APunt.TV'),
}

_POLICY = re.compile(r'policyKey\s*:\s*"([^"]+)"')
_BCID = re.compile(r'"bcId"\s*:\s*"?(\d+)')
_policy_key: Optional[str] = None


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


def _live_id() -> Optional[str]:
    """The current live video id from the channel's own live page."""
    try:
        match = _BCID.search(base.http.get_text(DIRECTE, HEADERS, max_bytes=2 * 1024 * 1024))
    except Exception:
        return None
    return match.group(1) if match else None


def resolve(ident: str, _retry: bool = False) -> Optional[str]:
    key = policy_key(refresh=_retry)
    if not key:
        return None
    try:
        data = base.http.get_json(API % quote(ident, safe=''),
                                  dict(HEADERS, Accept=f'application/json;pk={key}'))
    except Exception:
        # A rotated key or a rotated live id are the usual causes: retry once
        # with both read again.
        if _retry:
            raise
        current = list(CHANNELS)
        updated = _live_id()
        if updated and updated not in CHANNELS:
            current = [updated]
        return resolve(current[0], _retry=True) if current else None
    # A DVR live answers with duration 0, a recording with a positive one;
    # only the live may be served as the channel.
    if data.get('duration') not in (-1, 0, None):
        base.log.warning('apunt: %s is not live (duration=%s)', ident, data.get('duration'))
        return None
    for source in data.get('sources') or []:
        if source.get('type') == 'application/x-mpegURL' and source.get('src'):
            return source['src']
    return None
