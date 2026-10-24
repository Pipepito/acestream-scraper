"""Telemadrid and La Otra, which stream through Brightcove and no list carries.

Brightcove's playback API returns them without registration, given the
player's policy key. The key lives in the player's JavaScript (1.7 MB) and
Brightcove rotates it when it likes, so it is read from there, kept in
memory, and read again once when the API refuses it.
"""
import re
from typing import Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = 'telemadrid://'
HOSTS = ('telemadrid.es',)
GROUP = 'Madrid'
WEB = 'https://www.telemadrid.es/'
ACCOUNT = '6416060453001'
PLAYER = '2rfYSrHC79'
PLAYER_JS = f'https://players.brightcove.net/{ACCOUNT}/{PLAYER}_default/index.min.js'
API = f'https://edge.api.brightcove.com/playback/v1/accounts/{ACCOUNT}/videos/%s'
HEADERS = {'User-Agent': base.USER_AGENT, 'Referer': WEB, 'Origin': WEB.rstrip('/')}
# Measured over 30 minutes: playback needs no header.
PLAY_HEADERS: Dict[str, str] = {}

# Brightcove reference -> (name, guide id).
CHANNELS = {
    'ref:Live_Telemadrid': ('Telemadrid', 'Telemadrid.TV'),
    'ref:Live_LaOtra': ('La Otra', 'LaOtra.TV'),
}

_POLICY = re.compile(r'policyKey\s*:\s*"([^"]+)"')
_policy_key: Optional[str] = None


def channels() -> List[Dict[str, Optional[str]]]:
    return [{'ident': ident, 'name': name, 'tvg_id': tvg_id}
            for ident, (name, tvg_id) in CHANNELS.items()]


def policy_key(refresh: bool = False) -> Optional[str]:
    global _policy_key
    if _policy_key and not refresh:
        return _policy_key
    match = _POLICY.search(base.http.get_text(PLAYER_JS, HEADERS))
    if not match:
        base.log.warning('telemadrid: the player no longer publishes policyKey where expected')
        return None
    _policy_key = match.group(1)
    return _policy_key


def resolve(ident: str, _retry: bool = False) -> Optional[str]:
    key = policy_key(refresh=_retry)
    if not key:
        return None
    try:
        data = base.http.get_json(API % quote(ident, safe=''),
                                  dict(HEADERS, Accept=f'application/json;pk={key}'))
    except Exception:
        # A rotated key is the usual cause: fetch it again, once.
        if _retry:
            raise
        return resolve(ident, _retry=True)
    # duration -1 marks a live stream; a number means a recording was put
    # where the live one should be, and it must not be served as the channel.
    if data.get('duration') not in (-1, None):
        base.log.warning('telemadrid: %s is not live (duration=%s)', ident, data.get('duration'))
        return None
    for source in data.get('sources') or []:
        if source.get('type') == 'application/x-mpegURL' and source.get('src'):
            return source['src']
    return None
