"""Whether an IPTV stream addressed by URL is alive, without an engine.

The status check used to skip every stream with a stream_url, so half the
catalogue stayed unknown forever. An HLS stream is alive when its master
answers, a variant lists segments, and a segment starts arriving -- the
same three steps a player takes, measured by hand on the four broadcasters
in about half a second per stream. Only the first KB of the segment is
asked for: the video is not downloaded.

A broadcaster's channel (`mediaset://T5`) is only resolved: a signed link
is what fails when they change their API, and fetching the stream on top
would add a login and an ad-stitching request per check.

Every request goes through the guarded client with the stream's own
headers: these URLs come from third-party playlists.
"""
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

from app.services import hls_manifest, live_providers
from app.utils.outbound_http import source_get

TIMEOUT = 10
MAX_REDIRECTS = 5
MAX_MANIFEST_BYTES = 4 * 1024 * 1024


def _get(url: str, headers: Dict[str, str]):
    """(final URL, response), following redirects one guarded hop at a time."""
    for _ in range(MAX_REDIRECTS + 1):
        response = source_get(url, timeout=TIMEOUT, headers=headers)
        if response.status_code in (301, 302, 303, 307, 308) and response.headers.get('Location'):
            url = urljoin(url, response.headers['Location'])
            continue
        return url, response
    raise ValueError('too many redirects')


def _first_uri(text: str) -> Optional[str]:
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith('#'):
            return line
    return None


def _last_uri(text: str) -> Optional[str]:
    uris = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith('#')]
    return uris[-1] if uris else None


def check(stream_url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[bool, Optional[str]]:
    """(alive, why not). Never raises."""
    headers = dict(headers or {})
    try:
        if live_providers.for_stream_url(stream_url) is not None:
            if live_providers.resolve(stream_url):
                return True, None
            return False, 'The broadcaster did not return a live link'

        url, response = _get(stream_url, headers)
        if response.status_code >= 400:
            return False, f'HTTP {response.status_code} from the playlist'
        text = response.content[:MAX_MANIFEST_BYTES].decode('utf-8', 'replace')
        if '#EXTM3U' not in text[:512]:
            # Not a manifest: an origin that answers with the media itself.
            return (True, None) if response.content else (False, 'Empty response')

        if hls_manifest.is_master(text):
            variant = _first_uri(text)
            if not variant:
                return False, 'Master playlist without variants'
            url, response = _get(urljoin(url, variant), headers)
            if response.status_code >= 400:
                return False, f'HTTP {response.status_code} from the variant'
            text = response.content[:MAX_MANIFEST_BYTES].decode('utf-8', 'replace')

        # The newest segment: on a live list the oldest may already be gone.
        segment = _last_uri(text)
        if not segment:
            return False, 'Playlist without segments'
        _url, response = _get(urljoin(url, segment), dict(headers, Range='bytes=0-1023'))
        if response.status_code >= 400:
            return False, f'HTTP {response.status_code} from a segment'
        if not response.content:
            return False, 'Empty segment'
        return True, None
    except Exception as error:
        return False, f'{type(error).__name__}: {error}'
