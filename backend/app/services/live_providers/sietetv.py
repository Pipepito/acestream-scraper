"""7 TV La Rioja, a local channel received over the air in Logroño, which
streams through Dailymotion and is in no public list.

The video is tied to the broadcaster's domain ("ha limitado su acceso a
Dailymotion"). Measured with a real browser on 2026-10-15, when the old
metadata link started answering 403: the broadcaster's page embeds
Dailymotion's player (`geo.dailymotion.com`, player x11h8c), which asks
`geo.dailymotion.com/videos/<id>` with `x-dm-geo-*` headers naming the
embedder, player and publisher (without them: 404 DM016 embed_rules); the
manifest it returns then needs a browser User-Agent and `Sec-Fetch-Mode:
cors`, nothing more (cookies and Referer are not checked). Variants and
segments need nothing. Its `sec=` token expires within minutes, so it is
resolved at open time.
"""
from typing import Dict, List, Optional
from urllib.parse import quote

from app.services.live_providers import base

SCHEME = '7riojaplay://'
HOSTS = ('7riojaplay.tv',)
GROUP = 'La Rioja'
WEB = 'https://www.7riojaplay.tv/'
GEO = 'https://geo.dailymotion.com'
PLAYER_ID = 'x11h8c'
PUBLISHER_ID = 'x2mgfup'
VIDEO = GEO + '/videos/%s'
# Applied when the stream is opened (live.py), whatever the import stored.
PLAY_HEADERS = {'User-Agent': base.USER_AGENT, 'Referer': GEO + '/', 'Origin': GEO,
                'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Site': 'same-site', 'Sec-Fetch-Dest': 'empty'}

# Dailymotion id -> (name, guide id). dobleM's id: a week ahead, where
# TDTChannels' 7Rioja.TV has the same programmes but only today.
CHANNELS = {
    'x8dhao1': ('7 TV La Rioja', 'La 7 Rioja'),
}


def channels() -> List[Dict[str, Optional[str]]]:
    return [{'ident': ident, 'name': name, 'tvg_id': tvg_id}
            for ident, (name, tvg_id) in CHANNELS.items()]


def resolve(ident: str) -> Optional[str]:
    """The master manifest, as Dailymotion's embedded player gets it."""
    headers = {'User-Agent': base.USER_AGENT, 'Accept': 'application/json',
               'Referer': f'{GEO}/player/{PLAYER_ID}.html?video={quote(ident)}',
               'x-dm-geo-embedder': WEB, 'x-dm-geo-player-id': PLAYER_ID,
               'x-dm-geo-publisher-id': PUBLISHER_ID}
    data = base.http.get_json(VIDEO % quote(ident), headers)
    link = (data.get('stream') or {}).get('url')
    if not link:
        base.log.warning('7riojaplay: %s has no link (%s)', ident,
                         (data.get('error') or {}).get('reason') or 'no stream')
        return None
    return link
