"""One priority-ordered engine probe across HTTP and scheduler event loops."""
import asyncio
from enum import IntEnum
from itertools import count
from threading import Lock
from time import monotonic


class ProbePriority(IntEnum):
    PLAYBACK = 0
    MANUAL = 1
    BACKGROUND = 2


class ProbeQueue:
    def __init__(self, cooldown: float = 2.0, outage_backoff: float = 10.0):
        self.cooldown = cooldown
        self.outage_backoff = outage_backoff
        self._lock = Lock()
        self._sequence = count()
        self._waiting: dict[int, ProbePriority] = {}
        self._active: int | None = None
        self._available_at = 0.0

    def enqueue(self, priority: ProbePriority) -> int:
        with self._lock:
            ticket = next(self._sequence)
            self._waiting[ticket] = priority
            return ticket

    async def acquire(self, ticket: int) -> None:
        # asyncio locks/futures cannot be shared between the scheduler thread
        # and HTTP loop. Hold this thread lock only for in-memory bookkeeping.
        try:
            while True:
                with self._lock:
                    first = min(self._waiting, key=lambda key: (self._waiting[key], key))
                    if self._active is None and first == ticket and monotonic() >= self._available_at:
                        self._waiting.pop(ticket)
                        self._active = ticket
                        return
                await asyncio.sleep(0.05)
        except BaseException:
            self.cancel(ticket)
            raise

    def cancel(self, ticket: int) -> None:
        with self._lock:
            self._waiting.pop(ticket, None)

    def release(self, ticket: int, *, probed: bool, engine_unavailable: bool = False) -> None:
        with self._lock:
            if self._active != ticket:
                return
            self._active = None
            if probed:
                delay = self.outage_backoff if engine_unavailable else self.cooldown
                self._available_at = monotonic() + delay


probe_queue = ProbeQueue()
