"""Drop MPEG-TS null packets (PID 0x1FFF) from an engine source.

An engine can keep a dead source "alive" with padding alone: on a small ARM
box a source that had no picture delivered 9.4 MB, every byte of it null
packets. The relay took that for media, so the first byte arrived at once,
the stall timer never ran and no other source was tried; the viewer waited
for nothing until Kodi gave up.

Null packets carry nothing a player needs (they only pad a constant bitrate),
so the relay leaves them out: a source that sends only padding looks silent
and fails its start or stall deadline like any other silent source.

Fail-open: when the chunks are not aligned 188-byte packets, the rest of the
source passes through unchanged, once logged.
"""
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)

PACKET = 188
SYNC = 0x47


def _split(buf: bytes) -> tuple[bytes, bytes, bool]:
    """(kept, remainder, aligned): ``kept`` is ``buf``'s whole packets without
    the null ones, ``remainder`` the incomplete packet at its end."""
    if buf[:1] != bytes([SYNC]):
        return buf, b"", False
    whole = len(buf) - len(buf) % PACKET
    count = whole // PACKET
    if count == 0:
        return b"", buf, True
    if buf[0:whole:PACKET] != bytes([SYNC]) * count:
        return buf, b"", False
    third = buf[2:whole:PACKET]
    if b"\xff" not in third:  # the common case: no candidate null at all
        return buf[:whole], buf[whole:], True
    second = buf[1:whole:PACKET]
    keep = [i for i in range(count) if not (third[i] == 0xFF and second[i] & 0x1F == 0x1F)]
    if len(keep) == count:
        return buf[:whole], buf[whole:], True
    return b"".join(buf[i * PACKET:(i + 1) * PACKET] for i in keep), buf[whole:], True


async def drop_null_packets(iterator: AsyncIterator[bytes], content_id: str = "") -> AsyncIterator[bytes]:
    """The chunks of ``iterator`` without null packets; a chunk left empty is not yielded."""
    rest = b""
    aligned = True
    try:
        async for chunk in iterator:
            if not aligned:
                yield chunk
                continue
            kept, rest, aligned = _split(rest + chunk)
            if not aligned:
                logger.info("TV relay source %s is not aligned MPEG-TS; null packets kept", content_id)
            if kept:
                yield kept
        if rest:
            yield rest
    finally:
        await iterator.aclose()
