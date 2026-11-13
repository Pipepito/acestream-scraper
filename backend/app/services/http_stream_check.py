"""Verify bounded HTTP media bytes; URL resolution and HTTP success are not signal."""
import asyncio
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

from app.services import hls_manifest, live_providers
from app.services.stream_bitrate_service import SAMPLE_BYTES, verify_media_sample
from app.utils.bounded_source import source_get

TIMEOUT = 10
MAX_REDIRECTS = 5
MAX_MANIFEST_BYTES = 4 * 1024 * 1024


async def _get(url, headers, *, max_bytes=MAX_MANIFEST_BYTES, sample=False, media_limit=None):
    deadline = asyncio.get_running_loop().time() + TIMEOUT
    for _ in range(MAX_REDIRECTS + 1):
        response = await source_get(url, timeout=deadline - asyncio.get_running_loop().time(),
                                    headers=headers, max_bytes=max_bytes, sample=sample, media_limit=media_limit)
        if response.status_code in (301, 302, 303, 307, 308) and response.headers.get('Location'):
            url = urljoin(url, response.headers['Location'])
            continue
        return url, response
    raise ValueError('Too many redirects')


def _first_uri(text):
    return next((line.strip() for line in text.splitlines() if line.strip() and not line.startswith('#')), None)


async def check(stream_url: str, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[bool], Optional[str]]:
    """True/False is observed signal; None preserves prior status on an inconclusive check."""
    headers = dict(headers or {})
    try:
        async with asyncio.timeout(TIMEOUT + 5):
            if live_providers.for_stream_url(stream_url) is not None:
                stream_url = await live_providers.resolve_async(stream_url, timeout=TIMEOUT, checking=True)
                if not stream_url:
                    return None, 'The broadcaster did not return a live link'
            url, response = await _get(stream_url, headers, sample=True, media_limit=SAMPLE_BYTES)
            if response.status_code >= 400:
                return False, f'HTTP {response.status_code} from the playlist'
            text = response.content.decode('utf-8', 'replace')
            if '#EXTM3U' not in text[:512]:
                sample = response.content[:SAMPLE_BYTES]
            else:
                if response.truncated:
                    return None, 'Manifest exceeds byte limit'
                # Bound nested masters as well as network redirects.
                for _ in range(4):
                    if not hls_manifest.is_master(text):
                        break
                    variant = _first_uri(text)
                    if not variant:
                        return False, 'Master playlist without variants'
                    url, response = await _get(urljoin(url, variant), headers)
                    if response.status_code >= 400:
                        return False, f'HTTP {response.status_code} from the variant'
                    text = response.content.decode('utf-8', 'replace')
                if hls_manifest.is_master(text):
                    return None, 'Too many nested manifests'
                _header, entries = hls_manifest.media_entries(text, url)
                if not entries:
                    return False, 'Playlist without segments'
                entry = entries[-1]
                if entry['key'] and 'METHOD=NONE' not in entry['key']:
                    return None, 'Encrypted media cannot be verified by the bounded sample probe'
                sample = b''
                if entry['map']:
                    match = re.search(r'URI="([^"]+)"', entry['map'])
                    if not match:
                        return None, 'Invalid media initialization map'
                    init_headers = dict(headers)
                    byterange = re.search(r'BYTERANGE="(\d+)(?:@(\d+))?"', entry['map'])
                    if byterange and byterange[2] is None:
                        return None, 'Initialization byte range needs an explicit offset for verification'
                    if byterange:
                        size, start = int(byterange[1]), int(byterange[2] or 0)
                        init_headers['Range'] = f'bytes={start}-{start + size - 1}'
                    _, initial = await _get(match[1], init_headers, max_bytes=SAMPLE_BYTES // 2)
                    if initial.status_code >= 400:
                        return False, f'HTTP {initial.status_code} from media initialization'
                    if byterange and initial.status_code != 206:
                        return None, 'Origin ignored the initialization byte range'
                    sample = initial.content
                remaining = SAMPLE_BYTES - len(sample)
                start, size = entry['range'] or (0, remaining)
                size = min(size, remaining)
                segment_headers = dict(headers, Range=f'bytes={start}-{start + size - 1}')
                _, segment = await _get(entry['segment'], segment_headers, max_bytes=size, sample=True)
                if segment.status_code >= 400:
                    return False, f'HTTP {segment.status_code} from a segment'
                if entry['range'] and segment.status_code != 206:
                    return None, 'Origin ignored the segment byte range'
                if not segment.content:
                    return False, 'Empty segment'
                sample += segment.content
            if not sample:
                return False, 'Empty response'
            verified = await verify_media_sample(sample)
            if verified is None:
                return None, 'Media verification unavailable or timed out'
            return verified, None if verified else 'No audio or video packets verified'
    except Exception as error:
        # Do not expose signed upstream URLs/tokens in the API or stored error.
        return None, f'HTTP media check could not complete ({type(error).__name__})'
