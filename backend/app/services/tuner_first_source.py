"""«Starts with»: the next opening of a TV channel from one device begins with
the source a person chose (acestream-tvbox #12, #20).

The Kodi skin asks for it with a short request and then opens the channel
through the PVR as always, so ↑ ↓ and the channel's info keep working.

- **Per device and channel.** The device is the client address the app sees
  (the route's peer, after the trusted forwarded headers). Clients that reach the app through the Docker
  gateway all show the gateway's address, so they share one choice.
- **Lasts CHOICE_SECONDS** from when it was made, and **only that opening.**
  Kodi opens a channel with a HEAD and two GETs, closing the first GET early
  (sometimes after the second has started): all of them must start with the
  chosen source. So the choice is not used up by a GET but by the end of the
  opening: when a GET that started with it ends -- played, closed or
  cancelled by Kodi -- GETs arriving within SAME_OPENING_SECONDS still start
  with it (Kodi's second GET), and once one of those ends too it is spent.
- **If the chosen source fails** the relay goes on in the automatic order
  and never comes back to it: its refreshed candidates leave it out, and the
  choice is spent at once, so the next GET does not start with it either.
  That does not depend on the relay's failure memory (FAILURE_COOLDOWN_SECONDS).
- **A source the relay saw fail a moment ago** (failed_recently) is not put
  first: the choice is ignored for that GET.

Process memory only; nothing is written to the DB.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from app.services.tuner_playback_service import STOP_LINGER_SECONDS, failed_recently

CHOICE_SECONDS = 30.0
# Kodi's second GET of the same opening comes within the engine's stop linger
# of the first one closing: the same window keeps the choice for it.
SAME_OPENING_SECONDS = STOP_LINGER_SECONDS


@dataclass
class _Choice:
    source_id: str
    chosen_at: float
    # When the first GET that started with it ended; None while none has.
    first_end_at: float | None = None
    spent: bool = False


_choices: dict[tuple[str, int], _Choice] = {}
_lock = threading.Lock()


def choose_first_source(device: str, tv_channel_id: int, source_id: str) -> None:
    """The next opening of this channel from this device starts with
    ``source_id`` (a relay source id: a content id or ``url:<sha1>``)."""
    with _lock:
        _choices[(device, tv_channel_id)] = _Choice(source_id, time.monotonic())


def clear_choice(device: str, tv_channel_id: int) -> None:
    """«Automatic»: the next opening from this device uses the normal order."""
    with _lock:
        _choices.pop((device, tv_channel_id), None)


class ChannelOpening:
    """One GET (or HEAD) of a channel, as far as the person's choice goes."""

    def __init__(self, choice: _Choice | None):
        self._choice = choice
        self.chosen: str | None = choice.source_id if choice is not None else None

    def order(self, candidates: list[str]) -> list[str]:
        """The candidates this GET starts with: the chosen source first."""
        if self.chosen is None:
            return candidates
        return [self.chosen] + [cid for cid in candidates if cid != self.chosen]

    def without_chosen(self, candidates: list[str]) -> list[str]:
        """Refreshed candidates: not back to the chosen source once it has
        played or failed -- each return is another cut."""
        return [cid for cid in candidates if cid != self.chosen]

    def source_failed(self, source_id: str) -> None:
        """The relay gave ``source_id`` up: if it is the chosen one, the
        choice is spent now."""
        if self.chosen is not None and source_id == self.chosen:
            with _lock:
                self._choice.spent = True

    def ended(self) -> None:
        """This GET is over, however it ended. The first end of the opening
        leaves SAME_OPENING_SECONDS for Kodi's second GET; a later one spends
        the choice."""
        if self._choice is None:
            return
        with _lock:
            if self._choice.first_end_at is None:
                self._choice.first_end_at = time.monotonic()
            else:
                self._choice.spent = True


def open_channel(device: str, tv_channel_id: int) -> ChannelOpening:
    """What the person chose for this GET of the channel, if anything still
    applies. Reading it uses nothing up: see :meth:`ChannelOpening.ended`."""
    with _lock:
        now = time.monotonic()
        for key in [k for k, c in _choices.items() if now - c.chosen_at >= CHOICE_SECONDS]:
            del _choices[key]
        choice = _choices.get((device, tv_channel_id))
        if choice is not None and (choice.spent or (
                choice.first_end_at is not None and now - choice.first_end_at >= SAME_OPENING_SECONDS)):
            del _choices[(device, tv_channel_id)]
            choice = None
    if choice is not None and failed_recently(choice.source_id):
        choice = None
    return ChannelOpening(choice)
