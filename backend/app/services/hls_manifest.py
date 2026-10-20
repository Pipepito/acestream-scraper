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


def prune(text: str, origin: str, window: int = WINDOW) -> str:
    """The chunklist with its last `window` segments, absolute to the CDN.

    `#EXT-X-MEDIA-SEQUENCE` is recomputed: otherwise the player is told the
    first segment it gets is number 0 when it is 2,632, and at the next
    reload it believes the broadcast started over.

    `#EXT-X-KEY` and `#EXT-X-MAP` hold from where they appear until the next
    one, so they are re-emitted before the first kept segment. Cutting
    without that left the first segments of the window under a key that was
    no longer in the list: an encrypted channel played 2 of 4 times from
    the origin and 0 of 4 through us, with every tag present but in the
    wrong ORDER.
    """
    lines = text.splitlines()
    header, entries = [], []
    key = init_map = None
    loose = []          # #EXT-X-DISCONTINUITY belongs to ITS segment
    i, sequence = 0, 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('#EXT-X-MEDIA-SEQUENCE'):
            try:
                sequence = int(line.split(':', 1)[1])
            except (IndexError, ValueError):
                sequence = 0
        elif line.startswith('#EXTINF'):
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or lines[j].startswith('#')):
                j += 1
            if j < len(lines):
                entries.append({'inf': line, 'segment': lines[j], 'key': key,
                                'map': init_map, 'loose': loose})
                loose = []
                i = j + 1
                continue
        elif line.startswith('#EXT-X-KEY'):
            key = line
        elif line.startswith('#EXT-X-MAP'):
            init_map = line
        elif line.startswith('#EXT-X-ENDLIST'):
            pass
        elif line == '#EXT-X-DISCONTINUITY' or line.startswith('#EXT-X-DISCONTINUITY:'):
            loose.append(line)
        elif line.startswith('#EXTM3U') or line.startswith('#EXT-X-'):
            header.append(line)
        i += 1

    if not entries:
        return text if text.endswith('\n') else text + '\n'
    kept = entries[-window:] if window > 0 else entries
    out = ['#EXTM3U'] + [h for h in header if not h.startswith('#EXTM3U')]
    out.append('#EXT-X-MEDIA-SEQUENCE:%d' % (sequence + len(entries) - len(kept)))
    # Re-emitted only when they CHANGE: a key repeated on every segment is
    # legal but makes the player fetch it once per segment.
    key_out = map_out = None
    for entry in kept:
        if entry['map'] and entry['map'] != map_out:
            out.append(entry['map'])
            map_out = entry['map']
        if entry['key'] and entry['key'] != key_out:
            out.append(entry['key'])
            key_out = entry['key']
        out.extend(entry['loose'])
        out.append(entry['inf'])
        out.append(urljoin(origin, entry['segment'].strip()))
    return '\n'.join(out) + '\n'


def serve(text: str, origin: str, link, window: int = WINDOW) -> str:
    """What the player gets for this manifest."""
    if is_master(text):
        return rewrite_master(text, origin, link)
    return prune(text, origin, window)

