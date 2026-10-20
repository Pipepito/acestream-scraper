"""Serve an HLS stream's manifests ourselves; the video never passes through.

Some IPTV streams that need headers (101TV, PTV, TeleBilbao, ETB Deportes,
the cdnmedia locals) did not play in Kodi even with the right headers. The
cause, found with `ffprobe -loglevel verbose`, is that ffmpeg reads their
chunklist CUT SHORT -- 8,635 of 108,546 bytes -- so the last entry loses its
`.ts`, ffmpeg's `extension_picky` rejects it, and the WHOLE list is dropped:

    [hls] URL .../media-uk3p1ea13_DVR_3080 is not in allowed_segment_extensions
    [hls] parse_playlist error Invalid data found

The cut falls somewhere different each time, so the channel seemed
intermittent: when it lands on a line break, it opens. Served by us, with a
Content-Length, ffmpeg reads it whole (288,954 of 288,954 bytes) and plays:
6 of 6 openings against 0 of 3 straight from the CDN, on an amd64 machine
and on an ARM TV box. Proven: serving it ourselves fixes it. NOT isolated: whether the
origin's chunked transfer is the cause.

Only the manifests are served. Segments stay absolute to the CDN: ffmpeg
sends the playlist's `|Referer=...` headers with every child request, so a
few KB per reload pass through the server, not the video.

Not an open proxy: a nested manifest is fetched only if its URL carries a
signature made here, with a secret that changes on every start.
"""
import hashlib
import hmac
import os
import re
from urllib.parse import urljoin

_SECRET = os.urandom(32)

# Segments served per chunklist reload. cdnmedia's carries 2,642 -- three
# hours of DVR -- and Kodi reloads it every few seconds: 10 takes each reload
# from ~290 KB to ~1 KB while leaving the player some margin ahead.
WINDOW = 10

# `URI="..."` appears in encryption keys, alternative audio and init maps;
# left alone, those requests would bypass us.
_URI = re.compile(r'(URI=")([^"]+)(")')


def needs_manifest(stream_url, stream_headers) -> bool:
    """An HTTP stream whose playlist publishes headers: the streams this was
    measured on (101TV, PTV, TeleBilbao...) are exactly those."""
    return bool(stream_headers) and str(stream_url or '').lower().startswith(('http://', 'https://'))


def sign(url: str) -> str:
    return hmac.new(_SECRET, url.encode('utf-8'), hashlib.sha256).hexdigest()[:32]


def is_signed(url: str, signature: str) -> bool:
    # compare_digest, not ==: comparing signatures with == can be timed.
    return bool(signature) and hmac.compare_digest(sign(url), signature)


def is_master(text: str) -> bool:
    """A master lists variants; a chunklist lists segments. They are treated
    the opposite way: variants come back through us, segments do not."""
    return '#EXT-X-STREAM-INF' in text or '#EXT-X-I-FRAME-STREAM-INF' in text


def rewrite_master(text: str, origin: str, link) -> str:
    """The master with EVERY variant pointing back at us.

    Pointing at a single variant takes the quality choice away from Kodi:
    it played 720p instead of 1080p for exactly that reason.
    `link(url)` returns our URL for an absolute origin URL.
    """
    def ours(uri):
        return link(urljoin(origin, uri.strip()))

    out = []
    for line in text.splitlines():
        if not line.strip():
            out.append(line)
        elif line.startswith('#'):
            out.append(_URI.sub(lambda m: m.group(1) + ours(m.group(2)) + m.group(3), line))
        else:
            out.append(ours(line))
    return '\n'.join(out) + '\n'


def absolute_attributes(line: str, origin: str) -> str:
    return _URI.sub(lambda match: match.group(1) + urljoin(origin, match.group(2)) + match.group(3), line)


def media_entries(text: str, origin: str):
    """Retain each segment's tags and make implicit byte offsets explicit.

    This is also the sampling inventory. Never hand an upstream playlist to
    ffprobe: URLs, keys and init data are fetched only through the guarded client.
    """
    header, entries, pending = [], [], []
    key = init_map = None
    sequence = discontinuities = 0
    previous_url, previous_end = None, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#EXT-X-MEDIA-SEQUENCE:'):
            sequence = int(line.split(':', 1)[1])
        elif line.startswith('#EXT-X-DISCONTINUITY-SEQUENCE:'):
            discontinuities = int(line.split(':', 1)[1])
        elif line.startswith('#EXT-X-KEY:'):
            key = absolute_attributes(line, origin)
        elif line.startswith('#EXT-X-MAP:'):
            init_map = absolute_attributes(line, origin)
        elif line.startswith(('#EXTINF:', '#EXT-X-BYTERANGE:', '#EXT-X-PROGRAM-DATE-TIME:', '#EXT-X-GAP')) or line == '#EXT-X-DISCONTINUITY':
            pending.append(line)
        elif line.startswith('#'):
            header.append(absolute_attributes(line, origin))
        else:
            url = urljoin(origin, line)
            byte_range = None
            tags = []
            for tag in pending:
                if tag.startswith('#EXT-X-BYTERANGE:'):
                    value = tag.split(':', 1)[1].split('@')
                    size = int(value[0])
                    offset = int(value[1]) if len(value) == 2 else previous_end if url == previous_url else None
                    if size <= 0 or offset is None or offset < 0:
                        raise ValueError('Invalid implicit HLS byte range')
                    byte_range = (offset, size)
                    tag = f'#EXT-X-BYTERANGE:{size}@{offset}'
                tags.append(tag)
            if not any(tag.startswith('#EXTINF:') for tag in tags):
                raise ValueError('Missing HLS segment duration')
            entries.append({'segment': url, 'tags': tags, 'key': key, 'map': init_map,
                            'range': byte_range, 'sequence': sequence + len(entries),
                            'discontinuities': discontinuities})
            discontinuities += tags.count('#EXT-X-DISCONTINUITY')
            previous_url = url
            previous_end = byte_range[0] + byte_range[1] if byte_range else None
            pending = []
    return header, entries


def prune(text: str, origin: str, window: int = WINDOW) -> str:
    """Keep a live window without changing segment/key/map/range semantics."""
    # Low-latency/delta playlists need their complete tag relationships. Keep
    # them and completed playlists intact, resolving all references to the CDN.
    if (any(tag in text for tag in ('#EXT-X-PART:', '#EXT-X-SKIP:', '#EXT-X-ENDLIST', 'KEYFORMAT='))
            or ('#EXT-X-MAP:' in text and '#EXT-X-KEY:' in text)
            or re.search(r'#EXT-X-MAP:[^\n]*BYTERANGE=', text)):
        return '\n'.join(absolute_attributes(line, origin) if line.startswith('#') or not line.strip()
                         else urljoin(origin, line.strip()) for line in text.splitlines()) + '\n'
    header, entries = media_entries(text, origin)
    if not entries:
        return '\n'.join(absolute_attributes(line, origin) for line in text.splitlines()) + '\n'
    kept = entries[-window:] if window > 0 else entries
    out = ['#EXTM3U'] + [line for line in header if not line.startswith('#EXTM3U')]
    out.append(f"#EXT-X-MEDIA-SEQUENCE:{kept[0]['sequence']}")
    if kept[0]['discontinuities'] or '#EXT-X-DISCONTINUITY-SEQUENCE:' in text:
        out.append(f"#EXT-X-DISCONTINUITY-SEQUENCE:{kept[0]['discontinuities']}")
    key_out = map_out = None
    for entry in kept:
        if entry['key'] and entry['key'] != key_out:
            out.append(entry['key'])
            key_out = entry['key']
        if entry['map'] and entry['map'] != map_out:
            out.append(entry['map'])
            map_out = entry['map']
        out.extend(entry['tags'])
        out.append(entry['segment'])
    return '\n'.join(out) + '\n'


def serve(text: str, origin: str, link, window: int = WINDOW) -> str:
    """What the player gets for this manifest."""
    if is_master(text):
        return rewrite_master(text, origin, link)
    return prune(text, origin, window)

