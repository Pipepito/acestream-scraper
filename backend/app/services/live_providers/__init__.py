"""Live channels that no playlist carries, read from each broadcaster's API.

Adding a broadcaster's website as a scraper source (https://www.atresplayer.com,
https://www.mediasetinfinity.es, https://www.7riojaplay.tv,
https://www.telemadrid.es) imports its channels like any M3U list: the
source is recognised by its host and its channels are written out as M3U,
each stream stored as `<scheme>://<id>` with the headers playback needs.

Their links carry signed tokens that expire -- Mediaset's master playlist
after about ten minutes, Atresmedia's after eight hours -- so they are never
stored. The playlist points each one at the `/live/{stream id}` route, which
resolves it when the player opens the channel and answers with a redirect.
"""
from typing import Optional
from types import ModuleType
from urllib.parse import urlparse

from app.services.live_providers import atresplayer, base, mediaset, sietetv, telemadrid

PROVIDERS = (atresplayer, mediaset, sietetv, telemadrid)
LIVE_PATH = '/live/'


def for_source_url(url: str) -> Optional[ModuleType]:
    """The provider whose website this source URL is, if any."""
    host = (urlparse(url or '').hostname or '').lower()
    for provider in PROVIDERS:
        if any(host == h or host.endswith('.' + h) for h in provider.HOSTS):
            return provider
    return None


def for_stream_url(stream_url: str) -> Optional[ModuleType]:
    """The provider that resolves this stored stream, if any."""
    for provider in PROVIDERS:
        if (stream_url or '').startswith(provider.SCHEME):
            return provider
    return None


def playlist(provider: ModuleType) -> str:
    """The provider's channels as an M3U list the normal import reads."""
    lines = ['#EXTM3U']
    for channel in provider.channels():
        tvg = f' tvg-id="{channel["tvg_id"]}"' if channel.get('tvg_id') else ''
        lines.append(f'#EXTINF:-1{tvg} group-title="{provider.GROUP}",{channel["name"]}')
        for name, value in provider.PLAY_HEADERS.items():
            lines.append(f'#EXTVLCOPT:http-{"referrer" if name == "Referer" else name.lower()}={value}')
        lines.append(f'{provider.SCHEME}{channel["ident"]}')
    return '\n'.join(lines) + '\n'


def resolve(stream_url: str) -> Optional[str]:
    """A freshly signed link for a stored `<scheme>://<id>`, or None.

    Never raises: a broadcaster that is down must give the player a clean
    failure, not a server error.
    """
    provider = for_stream_url(stream_url)
    if provider is None:
        return None
    try:
        return provider.resolve(stream_url[len(provider.SCHEME):]) or None
    except Exception as error:
        base.log.warning('%s: could not resolve %s (%s)', provider.__name__.rsplit('.', 1)[-1], stream_url, error)
        return None
