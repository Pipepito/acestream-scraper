"""Atresmedia's live channels, from the public API its own website uses.

No public playlist carries Antena 3, laSexta, Neox, Nova, Mega or Atreseries.
The API needs no login. The live link embeds a signed token valid for eight
hours, so it is resolved when the channel is opened, never stored.
"""
from typing import Dict, List, Optional

from app.services.live_providers import base

SCHEME = 'atresplayer://'
HOSTS = ('atresplayer.com',)
GROUP = 'Generalistas'
API = 'https://api.atresplayer.com'
HEADERS = {
    'User-Agent': base.USER_AGENT,
    'Referer': 'https://www.atresplayer.com/',
    'Origin': 'https://www.atresplayer.com',
}
# Playback needs no header.
PLAY_HEADERS: Dict[str, str] = {}

# Title -> guide id. The API also lists the portal, Flooxer, ViX, Kidz and a
# podcast: not linear TV channels. The ids are dobleM's (guiaiptv.xml), which
# has all six a week ahead; TDTChannels' guide has none of them.
TV_CHANNELS = {
    'Antena 3': 'Antena 3 HD',
    'laSexta': 'La Sexta HD',
    'Neox': 'Neox',
    'Nova': 'Nova',
    'Mega': 'Mega',
    'Atreseries': 'Atreseries',
}


def channels() -> List[Dict[str, Optional[str]]]:
    data = base.http.get_json(f'{API}/client/v1/info/channels', HEADERS)
    return [{'ident': c['id'], 'name': c['title'], 'tvg_id': TV_CHANNELS[c['title']]}
            for c in data
            if c.get('title') in TV_CHANNELS and c.get('id')]


def resolve(ident: str) -> Optional[str]:
    """The first of `sourcesLive`: the API lists 'hlsts' before 'hlslegacy'."""
    data = base.http.get_json(f'{API}/player/v1/live/{ident}', HEADERS)
    for source in data.get('sourcesLive') or []:
        src = (source.get('src') or '').strip()
        if src:
            return src
    return None
