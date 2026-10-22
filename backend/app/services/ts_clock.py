"""Log when a relayed MPEG-TS source jumps back (or far ahead) in time.

A viewer saw some sources "jump back" mid-match while the
relay served them without switching: nothing in any log showed it, because
nobody looked at the stream's own clock. This reads the PCR (the MPEG-TS
program clock) from a sample of each chunk and logs a line when it goes back
more than BACK_SECONDS, or ahead of the wall clock by more than AHEAD_SECONDS.
It only reads the bytes, never changes them.

Cost: at most SAMPLE_PACKETS packet headers per chunk, so a small fraction of
the stream on a 1080p source.
"""
import logging
import time
from typing import AsyncIterator, Optional

logger = logging.getLogger(__name__)

PACKET = 188
SYNC = 0x47
SAMPLE_PACKETS = 64
BACK_SECONDS = 1.0
AHEAD_SECONDS = 30.0
PCR_WRAP = (1 << 33) / 90000.0  # the 33-bit PCR base wraps every ~26.5 h
QUIET_SECONDS = 10.0             # at most one line per jump burst


def _sync_offset(chunk: bytes) -> Optional[int]:
    for offset in range(min(PACKET, len(chunk) - PACKET)):
        if chunk[offset] == SYNC and chunk[offset + PACKET] == SYNC:
            return offset
    return None


def _pcr(packet: bytes):
    """(pid, seconds) when this packet carries a PCR, else None."""
    if len(packet) < 11 or not packet[3] & 0x20 or packet[4] < 7 or not packet[5] & 0x10:
        return None
    pid = ((packet[1] & 0x1F) << 8) | packet[2]
    base = (packet[6] << 25) | (packet[7] << 17) | (packet[8] << 9) | (packet[9] << 1) | (packet[10] >> 7)
    return pid, base / 90000.0


class ClockWatch:
    """Follows one source's PCR and logs its jumps."""

    def __init__(self, content_id: str, clock=time.monotonic):
        self.content_id = content_id
        self._clock = clock
        self._pid = None
        self._last = None
        self._last_at = None
        self._quiet_until = 0.0
        self.back_jumps = 0
        self.worst_back = 0.0

    def feed(self, chunk: bytes) -> None:
        offset = _sync_offset(chunk)
        if offset is None:
            return
        end = min(len(chunk), offset + SAMPLE_PACKETS * PACKET)
        for start in range(offset, end - PACKET + 1, PACKET):
            packet = chunk[start:start + PACKET]
            if packet[0] != SYNC:
                return
            found = _pcr(packet)
            if found is None:
                continue
            pid, seconds = found
            if self._pid is None:
                self._pid = pid
            if pid == self._pid:
                self._observe(seconds)

    def _observe(self, seconds: float) -> None:
        now = self._clock()
        if self._last is not None:
            delta = seconds - self._last
            if delta < -PCR_WRAP / 2:
                delta += PCR_WRAP
            elapsed = now - self._last_at
            if delta < -BACK_SECONDS:
                self.back_jumps += 1
                self.worst_back = max(self.worst_back, -delta)
                self._report("TV relay source clock went back %.1f s content_id=%s", -delta)
            elif delta - elapsed > AHEAD_SECONDS:
                self._report("TV relay source clock jumped ahead %.1f s content_id=%s", delta - elapsed)
        self._last, self._last_at = seconds, now

    def _report(self, message: str, seconds: float) -> None:
        now = self._clock()
        if now >= self._quiet_until:
            logger.info(message, seconds, self.content_id)
            self._quiet_until = now + QUIET_SECONDS

    def summary(self) -> None:
        if self.back_jumps:
            logger.info("TV relay source clock summary content_id=%s back_jumps=%d worst_back=%.1f s",
                        self.content_id, self.back_jumps, self.worst_back)


async def watch_clock(iterator: AsyncIterator[bytes], content_id: str) -> AsyncIterator[bytes]:
    """Pass the chunks through unchanged, watching the source's clock."""
    watch = ClockWatch(content_id)
    try:
        async for chunk in iterator:
            try:
                watch.feed(chunk)
            except Exception:  # the watch must never break playback
                logger.debug("TV relay clock watch failed", exc_info=True)
            yield chunk
    finally:
        watch.summary()
        await iterator.aclose()
