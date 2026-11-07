"""Select one HLS video rendition, retaining only its associated media groups."""
from __future__ import annotations

import re

_ATTRIBUTE = re.compile(r'(?:^|,)([A-Z0-9-]+)=("[^"\r\n]*"|[^,\r\n]*)')


def attributes(line: str) -> dict[str, str]:
    return {match[1]: match[2].strip('"') for match in _ATTRIBUTE.finditer(line.partition(':')[2])}


def best_variant(text: str) -> str:
    """Rank by resolution then bandwidth; preserve ties in publisher order.

    All returned references still pass through PlayerHTTPSource's guarded URL
    rewriter. Keeping a master (rather than following only its video URI) retains
    alternate languages, subtitles, session keys and in-band audio metadata.
    """
    lines = [line.strip() for line in text.splitlines()]
    variants = []
    pending = None
    for index, line in enumerate(lines):
        if line.startswith('#EXT-X-STREAM-INF:'):
            pending = index
        elif line and not line.startswith('#') and pending is not None:
            attrs = attributes(lines[pending])
            resolution = re.fullmatch(r'(\d{1,6})x(\d{1,6})', attrs.get('RESOLUTION', ''))
            pixels = int(resolution[1]) * int(resolution[2]) if resolution else 0
            bandwidth = attrs.get('AVERAGE-BANDWIDTH', attrs.get('BANDWIDTH', '0'))
            rate = int(bandwidth) if re.fullmatch(r'\d{1,12}', bandwidth) else 0
            variants.append(((pixels, rate), pending, index, attrs))
            pending = None
    if not variants:
        return text
    _, selected_tag, selected_uri, selected = max(variants, key=lambda item: item[0])
    variant_lines = {index for _, tag, uri, _ in variants for index in (tag, uri)}
    out = []
    for index, line in enumerate(lines):
        if index in variant_lines and index not in (selected_tag, selected_uri):
            continue
        if line.startswith('#EXT-X-I-FRAME-STREAM-INF:'):
            continue
        if line.startswith('#EXT-X-MEDIA:'):
            attrs = attributes(line)
            if attrs.get('GROUP-ID') != selected.get(attrs.get('TYPE', '')):
                continue
        out.append(line)
    return '\n'.join(out) + '\n'
