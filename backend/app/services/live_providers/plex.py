"""Plex's free live channels for Spain (268 on 2026-10-28).

Plex publishes no playlist. i.mjh.nz keeps its channel list, by region, as a
gzip JSON file whose `headers` carry the shared, non-personal X-Plex-Token
the channels play with. The usual link, `jmp2.uk/plex-<id>.m3u8`, only
redirects to `epg.provider.plex.tv/library/parts/<id>.m3u8?X-Plex-Token=...`
and answered 429 after about 35 requests, so the link is built here from
the list's token instead, with no request at all when the channel opens.

Measured from Spain: master and variants answer 200 to Kodi's User-Agent as
to a browser's; segments are plain `.ts` (no DRM, no beacons); the list's
X-Forwarded-For for Spain was not needed.
"""
import re
import threading
from typing import Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = 'plex://'
HOSTS = ('watch.plex.tv',)
GROUP = 'Plex'
LIST = 'https://i.mjh.nz/Plex/.channels.json.gz'
PART = 'https://epg.provider.plex.tv/library/parts/%s.m3u8'
REGION = 'es'
HEADERS = {'User-Agent': base.USER_AGENT}
PLAY_HEADERS: Dict[str, str] = {}
# The list is 570 KB: read again for its token at most this often.
TOKEN_SECONDS = 6 * 3600
_ID = re.compile(r'[0-9a-f]{24}-[0-9a-f]{24}')

_lock = threading.Lock()
_token: Optional[tuple] = None   # (value, read at)


def forget() -> None:
    global _token
    with _lock:
        _token = None


def _read_list() -> dict:
    global _token
    data = base.http.get_json(LIST, HEADERS)
    token = next((value for name, value in (data.get('headers') or {}).items()
                  if name.lower() == 'x-plex-token'), None)
    if token:
        with _lock:
            _token = (token, base.now())
    else:
        base.log.warning('plex: the channel list carries no token')
    return data


def token() -> Optional[str]:
    with _lock:
        if _token and base.now() - _token[1] < TOKEN_SECONDS:
            return _token[0]
    try:
        _read_list()
    except Exception:
        # i.mjh.nz down: an older token beats no channel.
        if not _token:
            raise
        base.log.warning('plex: could not read the list again; keeping the previous token')
    with _lock:
        return _token[0] if _token else None


def channels() -> List[Dict[str, Optional[str]]]:
    data = _read_list()
    return [{'ident': ident, 'name': channel['name'], 'logo': channel.get('logo')}
            for ident, channel in (data.get('channels') or {}).items()
            if _ID.fullmatch(ident) and channel.get('name')
            and REGION in (channel.get('regions') or [])]


def resolve(ident: str) -> Optional[str]:
    if not _ID.fullmatch(ident):
        return None
    value = token()
    if not value:
        return None
    return PART % ident + '?X-Plex-Token=' + quote(value, safe='')
