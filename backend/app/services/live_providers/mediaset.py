"""Mediaset's live channels: anonymous login and Google DAI's unencrypted HLS.

Public lists mark Telecinco, Cuatro and the rest as needing external
authentication and publish no link. Their web player, however, logs in
anonymously and plays the HLS that Google DAI stitches -- unencrypted, since
server-side ad insertion needs the content in the clear. Three calls:

    POST idm/v3.0/anonymous/login          -> sid and beToken
    POST playback/v3.0/check               -> the channel's DAI assetKey
    POST ssai/event/<assetKey>/streams     -> the stitched m3u8

The master playlist answers 403 about ten minutes after it is issued, while
a variant fetched at once keeps playing for at least thirty: the token
expires for OPENING, not for watching. So it is resolved at open time, and a
reconnecting player resolves again. The manifest answers 403 without the
Referer; the User-Agent does not matter.
"""
from typing import Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = 'mediaset://'
HOSTS = ('mediasetinfinity.es', 'mitele.es')
GROUP = 'Generalistas'
API = 'https://services-ott-prod-fe.mediaset.net/esp'
DAI = 'https://pubads.g.doubleclick.net/ssai/event/%s/streams'
REFERER = 'https://www.mediasetinfinity.es/'
PLAY_HEADERS = {'Referer': REFERER}
# Taken from the real login request of their website; the app name carries
# their build version and may change with their deployments.
APP_NAME = 'web//mediasetplay-web/1.3.3-d4f6c8a'
CLIENT_ID = 'e76449e2-5e36-404f-af77-94828c61ee63'
HEADERS = {
    'User-Agent': base.USER_AGENT,
    'Referer': REFERER,
    'Origin': 'https://www.mediasetinfinity.es',
}

# Code -> (name, guide id). Left out: AC, FS and ML are paid ("doesn't have
# rights to"), and MT authorises but returns no DAI assetKey.
CHANNELS = {
    'T5': ('Telecinco', 'Telecinco.TV'),
    'CT': ('Cuatro', 'Cuatro.TV'),
    'FD': ('FDF', 'FDF.TV'),
    'DV': ('Divinity', 'Divinity.TV'),
    'EN': ('Energy', 'Energy.TV'),
    'BM': ('Be Mad', 'Bemad.TV'),
    'BO': ('Boing', 'Boing.TV'),
}


def channels() -> List[Dict[str, Optional[str]]]:
    return [{'ident': code, 'name': name, 'tvg_id': tvg_id}
            for code, (name, tvg_id) in CHANNELS.items()]


def resolve(ident: str) -> Optional[str]:
    login = base.http.post_json(f'{API}/idm/v3.0/anonymous/login',
                                {'appName': APP_NAME, 'client_id': CLIENT_ID}, HEADERS)
    session = login.get('response') or {}
    sid, token = session.get('sid'), session.get('beToken')
    if not sid:
        return None
    check = base.http.post_json(
        f'{API}/playback/v3.0/check?sid={quote(sid)}',
        {'channelCode': ident, 'streamType': 'LIVE', 'delivery': 'Streaming',
         'createDevice': True, 'overrideAppName': APP_NAME},
        dict(HEADERS, Authorization=f'Bearer {token}'))
    if not check.get('isOk'):
        base.log.warning('mediaset: %s refused: %s', ident, (check.get('error') or {}).get('message'))
        return None
    asset_key = ((check.get('response') or {}).get('dai') or {}).get('assetKey')
    if not asset_key:
        return None
    stream = base.http.post_json(DAI % quote(asset_key), {},
                                 {'User-Agent': base.USER_AGENT, 'Referer': REFERER})
    return (stream or {}).get('stream_manifest')
