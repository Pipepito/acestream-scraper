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


# All the HLS entries carry the same ladder from 360p to 1080p in AVC, save
# the one the API types 'hls+4K': that ladder is HEVC and adds 1440p and
# 2160p on top of the same steps, so a player following it reaches 4K when it
# can decode it and the step below when it cannot. The rest are fallbacks.
# The first entry, 'hlsts', is the same 1080p ladder and answers 492 -- a
# status code of its own, not in any RFC -- often enough that resolving to it
# alone leaves the channel dead until the player retries.
PREFERENCE = ('application/hls+4K', 'application/hls+legacy', 'application/hls+legacyv3',
              'application/vnd.apple.mpegurl', 'application/hls+ssai',
              'application/dash+xml', 'application/dash+ssai')
# Ladders probed before giving up. Each probe is one request; the first one
# that answers is what this returns.
ATTEMPTS = 3
# A master playlist is about a kilobyte; the cap only has to be generous
# enough that a longer one is not mistaken for a refusal.
PROBE_BYTES = 64 * 1024


def channels() -> List[Dict[str, Optional[str]]]:
    data = base.http.get_json(f'{API}/client/v1/info/channels', HEADERS)
    return [{'ident': c['id'], 'name': c['title'], 'tvg_id': TV_CHANNELS[c['title']]}
            for c in data
            if c.get('title') in TV_CHANNELS and c.get('id')]


def _ladders(data: Dict) -> List[Dict]:
    """`sourcesLive` in preference order; an unknown type goes last."""
    sources = [source for source in data.get('sourcesLive') or []
               if isinstance(source, dict) and (source.get('src') or '').strip()]
    return sorted(sources, key=lambda source: PREFERENCE.index(source.get('type'))
                  if source.get('type') in PREFERENCE else len(PREFERENCE))


def resolve(ident: str) -> Optional[str]:
    """The best ladder the CDN serves, not merely the first one it lists."""
    data = base.http.get_json(f'{API}/player/v1/live/{ident}', HEADERS)
    for source in _ladders(data)[:ATTEMPTS]:
        src = source['src'].strip()
        try:
            base.http.get_text(src, {'User-Agent': HEADERS['User-Agent']}, max_bytes=PROBE_BYTES)
        except Exception as error:
            base.log.warning('atresplayer: %s refused its %s ladder (%s)',
                             ident, source.get('type'), type(error).__name__)
            continue
        return src
    return None
