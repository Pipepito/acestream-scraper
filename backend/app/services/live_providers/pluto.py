"""Pluto TV's channels for Spain, through the path its own website plays.

Measured on 2026-10-28 from a Spanish home line. The path public lists carry,
`stitcher.pluto.tv/stitch/hls/channel/<id>/master.m3u8`, answers 200 with
segments of a takedown slate for every channel and every parameter set: it
no longer serves the channels. They play from `/v2/stitch/...` with a JWT
from `boot.pluto.tv/v4/start` and `masterJWTPassthrough=true` (without it
the variants answer 401). One JWT, valid 24 h, served four different
channels, so a single session is kept and shared. The boot also fixes the
region by the asking address; its token lists Spain's channels (146), and
only those exist: half of the Spanish entries in public catalogues answer
404 `Unknown Sequence`.

Pluto's CloudFront answers 403 to a User-Agent starting with `Kodi/`, on
the boot and on the stitcher alike; any browser's is accepted.
"""
import re
import threading
import uuid
from typing import Dict, List, Optional
from urllib.parse import quote, urlencode

from app.services.live_providers import base

SCHEME = 'pluto://'
HOSTS = ('pluto.tv',)
GROUP = 'Pluto TV'
BOOT = 'https://boot.pluto.tv/v4/start'
STITCHER = 'https://stitcher.pluto.tv/v2/stitch/hls/channel/%s/master.m3u8'
CHANNEL_LIST = '/v2/guide/channels?limit=1000&offset=0&sort=number%3Aasc'
COUNTRY = 'ES'
HEADERS = {'User-Agent': base.USER_AGENT}
PLAY_HEADERS = {'User-Agent': base.USER_AGENT}
# Well inside the JWT's 24 h, so a channel opened late in the session does
# not get a token about to expire; renewing costs one request.
SESSION_SECONDS = 2 * 3600
# What the boot validates (without clientModelNumber or appVersion: 400);
# the values themselves are not checked.
BOOT_QUERY = {'appName': 'web', 'appVersion': '9.0.0', 'deviceVersion': '130.0.0',
              'deviceModel': 'web', 'deviceMake': 'firefox', 'deviceType': 'web',
              'clientModelNumber': '1.0.0', 'serverSideAds': 'false'}
_ID = re.compile(r'[0-9a-f]{24}')

_lock = threading.Lock()
_session: Optional[dict] = None


def forget() -> None:
    global _session
    with _lock:
        _session = None


def session() -> Optional[dict]:
    """{'token', 'channels', 'country'} of a shared boot, renewed every two hours."""
    global _session
    with _lock:
        if _session and base.now() - _session['at'] < SESSION_SECONDS:
            return _session
    data = base.http.get_json(f'{BOOT}?' + urlencode(dict(BOOT_QUERY, clientID=str(uuid.uuid4()))),
                              HEADERS)
    token = data.get('sessionToken')
    if not token:
        base.log.warning('pluto: the boot returned no session token')
        return None
    fresh = {'token': token, 'at': base.now(),
             'channels': (data.get('servers') or {}).get('channels'),
             'country': (data.get('session') or {}).get('countryCode')}
    with _lock:
        _session = fresh
    return fresh


def _logo(channel: dict) -> Optional[str]:
    images = {image.get('type'): image.get('url') for image in channel.get('images') or []}
    return images.get('colorLogoPNG') or images.get('logo')


def channels() -> List[Dict[str, Optional[str]]]:
    current = session()
    if not current or not current.get('channels'):
        return []
    if current.get('country') != COUNTRY:
        # The list is the asking address's region: another country's list
        # would fill the grid with channels that do not play here.
        base.log.warning('pluto: the boot placed this address in %s, not %s; nothing imported',
                         current.get('country'), COUNTRY)
        return []
    data = base.http.get_json(current['channels'] + CHANNEL_LIST,
                              dict(HEADERS, Authorization=f'Bearer {current["token"]}'))
    return [{'ident': c['id'], 'name': c['name'], 'logo': _logo(c)}
            for c in data.get('data') or []
            if _ID.fullmatch(c.get('id') or '') and c.get('name')
            and c.get('isStitched') and not c.get('plutoOfficeOnly')]


def resolve(ident: str) -> Optional[str]:
    if not _ID.fullmatch(ident):
        return None
    current = session()
    if not current:
        return None
    return (STITCHER % ident + '?jwt=' + quote(current['token'], safe='')
            + '&masterJWTPassthrough=true')
