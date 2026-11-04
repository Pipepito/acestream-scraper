"""Bounded source selection with opt-in experimental transcoding recovery."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
import threading
import asyncio
import logging
import time
from typing import AsyncIterator, Awaitable, Callable, Collection

import anyio
import httpx

from app.services.engine_client import EngineClient, EngineRefusedError, EngineUnavailableError
from app.services.stream_relay import EngineStreamError, RelayInfo, RelayRegistry, relay_engine_stream, relay_registry
from app.services.tuner_remux import remux_source, compatible_audio_source
from app.services.tuner_http_source import relay_http_stream
from app.utils.stream_kind import stream_kind
from app.services.ts_clock import ClockWatch, watch_clock

STARTUP_BUDGET_SECONDS = 45.0
ATTEMPT_SECONDS = 15.0
# A healthy source can be silent for over 16 s: the engine hands over whole
# pieces (~1.5 MB), so a low-bitrate source arrives in bursts. Measured on a
# live engine: a source at 97 kB/s had 19 gaps of 12 s or more in 5 minutes,
# the longest 16.4 s, and a 15 s stall timeout cut it; a source at 458 kB/s
# was never silent for more than 4.6 s. 25 s is above the longest gap seen.
STALL_SECONDS = 25.0
HEALTHY_SECONDS = 30.0
# Kodi opens a channel with two GETs and closes the first one; the engine
# session outlives a closed client this long, so the second GET finds the
# source still running instead of starting it cold (measured: 1.8 s more on
# an amd64 bench, 3.2 s on an ARM box).
STOP_LINGER_SECONDS = 5.0
# An engine session that ends with no byte at all this soon is retried once
# before the source counts as failed. Seen with Kodi (intermittent): its
# second GET joined a source whose first reader had just left, the engine
# answered 200 and closed at once, and with a single source the channel
# failed. Only when no other candidate is left: otherwise the next source
# goes first.
EMPTY_START_RETRY_SECONDS = 3.0
# Sources tried only because the others ran out (a recent check marked them
# offline, or they were not reached) are most likely dead: a shorter wait each.
LAST_RESORT_SECONDS = 10.0
# And at most this many of them (Óscar, 02-11): on the box most channels have
# none or one left by then, but the football ones keep up to 38, which at
# 10 s each was minutes of waiting card.
LAST_RESORT_LIMIT = 3
logger = logging.getLogger(__name__)

# Short, bounded process-local memory prevents reconnects picking a known failure
# ahead of healthy alternatives. It does not overwrite verified DB probe results.
_failures: OrderedDict[str, float] = OrderedDict()
_failure_lock = threading.Lock()
FAILURE_COOLDOWN_SECONDS = 60.0
# Video that dies within its first minute is most likely an old broadcast the
# engine still holds pieces of: the source failed to start, and stays behind
# the others for longer.
EARLY_DEATH_SECONDS = 60.0
EARLY_DEATH_COOLDOWN_SECONDS = 1800.0


def record_source_failure(content_id: str, cooldown: float = FAILURE_COOLDOWN_SECONDS) -> None:
    with _failure_lock:
        # Stored as if it had failed later, so the usual cooldown lasts `cooldown`.
        _failures[content_id] = time.monotonic() + cooldown - FAILURE_COOLDOWN_SECONDS
        _failures.move_to_end(content_id)
        while len(_failures) > 4096:
            _failures.popitem(last=False)


def prefer_recovered_sources(content_ids: list[str]) -> list[str]:
    with _failure_lock:
        now = time.monotonic()
        for cid, failed_at in list(_failures.items()):
            if now - failed_at >= FAILURE_COOLDOWN_SECONDS:
                del _failures[cid]
        return sorted(content_ids, key=lambda cid: (cid in _failures, _failures.get(cid, 0)))


# How each attempt at a source ended, for per-source statistics. Outcomes:
# no_data (no byte in time), empty_session (the engine ended it at once),
# engine_refused, engine_unavailable, upstream_error, early_death (video, then
# dead within EARLY_DEATH_SECONDS), stall (silent for STALL_SECONDS after
# that), ended (the source ended after that), ok (it played until the
# viewer left) and handover (it played until a newer GET of the channel took
# over); `seconds` is how long it played.
_outcome_recorder: Callable[..., None] | None = None


def set_outcome_recorder(recorder: Callable[..., None] | None) -> None:
    global _outcome_recorder
    _outcome_recorder = recorder


def record_outcome(content_id: str, tv_channel_id: int | None, outcome: str, *, seconds: float,
                   peers: int | None = None, speed_down: int | None = None, attempt: object = None,
                   final: bool = True) -> None:
    """``attempt`` ties the checkpoints of one viewing (``final=False``) to its
    final outcome, so they rewrite one row instead of adding one each."""
    if _outcome_recorder is None:
        return
    extra = {} if attempt is None else {'attempt': attempt, 'final': final}
    try:
        _outcome_recorder(content_id, tv_channel_id, outcome, seconds=seconds, peers=peers, speed_down=speed_down,
                          **extra)
    except Exception:  # noqa: BLE001 - statistics must never break playback
        logger.exception('TV relay outcome recorder failed')


# A viewing is written while it plays, not only when it ends: a machine
# switched off right after Stop never wrote its viewing, however long it was. Once a source has played CHECKPOINT_SECONDS it is written as an
# ``ok`` of that length and rewritten every CHECKPOINT_SECONDS; its end rewrites
# the outcome. Shorter than that is Kodi's double GET, and nothing is written early.
CHECKPOINT_SECONDS = 30.0


class ViewingCheckpoint:
    """Writes one attempt's progress at most every CHECKPOINT_SECONDS."""

    def __init__(self, content_id: str, tv_channel_id: int | None):
        self.content_id = content_id
        self.tv_channel_id = tv_channel_id
        self.attempt = object()
        self.written_at = 0.0
        self.outcome: str | None = None

    def tick(self, played: float, outcome: str = 'ok') -> None:
        if played >= CHECKPOINT_SECONDS and played - self.written_at >= CHECKPOINT_SECONDS:
            self.written_at, self.outcome = played, outcome
            record_outcome(self.content_id, self.tv_channel_id, outcome, seconds=played,
                           attempt=self.attempt, final=False)

    def finish(self, outcome: str, played: float) -> None:
        record_outcome(self.content_id, self.tv_channel_id, outcome, seconds=played, attempt=self.attempt)


# Kodi opens a channel with two GETs and sends the second as soon as the first
# gets bytes. Each GET ran its own rotation from the first source, so a dead
# first source was tried again by the second GET once the first had found a
# working one. The GETs of one client and channel share an opening: a newer GET
# resumes where the older one is, and the older one starts no further source.
@dataclass
class ChannelOpening:
    current: str | None = None
    # When the source being tried runs out of time; None once it plays.
    current_deadline: float | None = None
    failed: list[str] = field(default_factory=list)
    # In the last resort: a newer GET goes straight into it.
    last_resort: bool = False
    superseded: bool = False
    done: bool = False
    ended_at: float | None = None


_openings: dict = {}
_openings_lock = threading.Lock()


def _with_clock(outcome: str, watch: ClockWatch) -> str:
    """A source that played but kept jumping back in time repeated what the
    viewer had already seen (the same corner kick over and over): that is recorded against it, not as a good viewing. A source that
    never played keeps its own outcome."""
    return 'jumpy' if watch.jumpy and outcome in ('ok', 'ended', 'stall') else outcome


def _record_ok(opening: ChannelOpening | None, content_id: str, tv_channel_id: int | None,
               seconds: float, outcome: str = 'ok', attempt: object = None) -> None:
    """A source that played until its GET ended. Kodi closes its first GET as
    soon as it gets bytes and its second takes the opening over: that is a
    hand-over, not a viewing, and counting it as one put an `ok` of 0 s next
    to every real one (the bench, 02-11). Whether a newer GET takes over is
    known STOP_LINGER_SECONDS later."""
    if opening is None:
        record_outcome(content_id, tv_channel_id, outcome, seconds=seconds, attempt=attempt)
        return

    def settle() -> None:
        final = 'handover' if opening.superseded else outcome
        record_outcome(content_id, tv_channel_id, final, seconds=seconds, attempt=attempt)
    try:
        asyncio.get_running_loop().call_later(STOP_LINGER_SECONDS, settle)
    except RuntimeError:
        settle()


def take_over_opening(key) -> tuple[ChannelOpening, ChannelOpening | None]:
    """A new opening for ``key`` (client and channel) and the one in progress,
    which gives way to it, or the one that ended less than
    STOP_LINGER_SECONDS ago: Kodi closes its first GET as soon as it gets
    bytes, and the second came 30 ms later on the bench (02-11) and found
    nothing to go on from."""
    with _openings_lock:
        previous = _openings.get(key)
        if previous is not None and previous.done and time.monotonic() - previous.ended_at >= STOP_LINGER_SECONDS:
            previous = None
        if previous is not None:
            previous.superseded = True
        opening = ChannelOpening()
        _openings[key] = opening
        return opening, previous


def end_opening(key, opening: ChannelOpening) -> None:
    """Kept for STOP_LINGER_SECONDS, for a GET that comes right after."""
    with _openings_lock:
        opening.done, opening.ended_at = True, time.monotonic()
        now = time.monotonic()
        for other in [k for k, o in _openings.items() if o.done and now - o.ended_at >= STOP_LINGER_SECONDS]:
            del _openings[other]


def resume_order(content_ids: list[str], previous: ChannelOpening) -> tuple[list[str], float | None, set[str]]:
    """Where a newer GET goes on from: the sources in the order it tries them,
    the deadline of the first one, and those it skips. First the source the
    older GET is on (with the time it has left, or none if it plays), then
    those it has not tried; the ones it saw fail are skipped."""
    current = previous.current
    deadline = previous.current_deadline
    failed = set(previous.failed)
    if current is not None and deadline is not None and deadline <= time.monotonic():
        failed.add(current)
    first = [current] if current is not None and current not in failed else []
    rest = [cid for cid in content_ids if cid not in failed and cid not in first]
    return first + rest, deadline if first else None, failed



async def relay_ranked_streams(
    engine: EngineClient | None, content_ids: list[str], client_label: str, claim: RelayInfo,
    *, client_factory: Callable[..., httpx.AsyncClient] | None = None,
    registry: RelayRegistry = relay_registry,
    candidate_provider: Callable[[], Awaitable[tuple[list[str], bool]]] | None = None,
    experimental_transcoding: bool = False,
    plex_compatible_audio: bool = False,
    on_source_failure: Callable[[str], Awaitable[None]] | None = None,
    attempt_seconds: float | None = None,
    startup_budget_seconds: float | None = None,
    switch_midstream: bool = False,
    opening: ChannelOpening | None = None,
    resume_deadline: float | None = None,
    skip: Collection[str] = (),
    last_resort_provider: Callable[[], Awaitable[list[str]]] | None = None,
    last_resort_now: bool = False,
    tv_channel_id: int | None = None,
) -> AsyncIterator[bytes]:
    """Retry startup failures; midstream transcoding recovery is explicit opt-in.

    One 45-second recovery window tries each candidate once. Only a source that
    delivers for 30 seconds resets the failure history, so flapping sources do
    not hold a slot forever. Cancellation never starts another source.

    With ``opening``, the relay notes the source it is on and those that fail,
    starts no further source once a newer GET of the channel takes the opening
    over, and ends one that plays. ``resume_deadline`` caps the first source's
    attempt (the time the older GET had left on it); ``skip`` are sources not
    to start. ``last_resort_provider`` gives every source of the channel,
    offline ones included: when the candidates run out, the ones not tried yet
    are tried within what is left of the budget, LAST_RESORT_SECONDS each.
    """
    # The tuner settings when the route passes them; the module defaults otherwise.
    attempt_seconds = ATTEMPT_SECONDS if attempt_seconds is None else attempt_seconds
    startup_budget_seconds = STARTUP_BUDGET_SECONDS if startup_budget_seconds is None else startup_budget_seconds
    started = time.monotonic()
    deadline = started + startup_budget_seconds
    attempted: set[str] = set(skip)
    retried_empty: set[str] = set()
    candidates = prefer_recovered_sources(content_ids)
    version = 0
    # The relay's own deadline (start or stall) of the read in progress.
    # When it fires, the engine reader is cancelled just like when the
    # client leaves; only this tells the two apart.
    timer: list = [None]

    def stop_linger() -> float:
        return 0 if timer[0] is not None and timer[0].cancel_called else STOP_LINGER_SECONDS

    last_resort: list[str] = []
    last_resort_taken = False

    async def take_last_resort() -> bool:
        nonlocal last_resort, last_resort_taken
        if last_resort_taken or last_resort_provider is None or (opening is not None and opening.superseded):
            return False
        last_resort_taken = True
        every = await last_resort_provider()
        last_resort = [cid for cid in dict.fromkeys(list(candidates) + every) if cid not in attempted]
        last_resort = last_resort[:LAST_RESORT_LIMIT]
        if last_resort:
            if opening is not None:
                opening.last_resort = True
            logger.info('TV relay last resort: trying %d sources not tried yet', len(last_resort))
        return bool(last_resort)
    try:
        if last_resort_now:
            # The older GET was already there: go on with it, not after a refresh.
            await take_last_resort()
        while True:
            while time.monotonic() < deadline:
                if opening is not None and opening.superseded:
                    # A newer GET of this channel goes on from here.
                    return
                candidates = prefer_recovered_sources(list(dict.fromkeys(list(candidates) + last_resort)))
                pending = [cid for cid in candidates if cid not in attempted]
                if not pending:
                    if candidate_provider is None:
                        break
                    with anyio.move_on_after(max(0, deadline - time.monotonic())) as scope:
                        candidates, refreshing = await candidate_provider()
                        candidates = prefer_recovered_sources(candidates)
                    if scope.cancel_called:
                        break
                    pending = [cid for cid in candidates if cid not in attempted]
                    if not pending:
                        if not refreshing:
                            break
                        await asyncio.sleep(min(.25, max(0, deadline - time.monotonic())))
                        continue
                content_id = pending[0]
                attempted.add(content_id)
                registry.select_stream(claim.id, content_id)
                logger.info('TV relay trying content_id=%s', content_id)
                wait = min(attempt_seconds, LAST_RESORT_SECONDS) if content_id in last_resort else attempt_seconds
                attempt_deadline = min(deadline, time.monotonic() + wait)
                if resume_deadline is not None:
                    attempt_deadline = min(attempt_deadline, resume_deadline)
                    resume_deadline = None
                if opening is not None:
                    opening.current, opening.current_deadline = content_id, attempt_deadline
                is_http = stream_kind(content_id) == 'http'

                async def source():
                    if is_http:
                        upstream = relay_http_stream(content_id, claim, startup_deadline=attempt_deadline,
                            plex_compatible_audio=plex_compatible_audio and not experimental_transcoding)
                    else:
                        if engine is None:
                            raise EngineUnavailableError('Acestream Engine URL is not configured')
                        upstream = relay_engine_stream(engine, content_id, client_label, registry=registry,
                            client_factory=client_factory, claim=claim, release_claim=False,
                            stop_linger=stop_linger, read_seconds=wait,
                            startup_deadline=attempt_deadline)
                    try:
                        async for chunk in upstream:
                            yield chunk
                    finally:
                        with anyio.CancelScope(shield=True):
                            await upstream.aclose()

                raw = source()
                # Log the source's own clock jumps (a viewer saw sources jump back
                # mid-match with no relay switch, and nothing showed it): read-only.
                clock_watch = ClockWatch(content_id)
                raw = watch_clock(raw, content_id, clock_watch)
                checkpoint = ViewingCheckpoint(content_id, tv_channel_id)
                if experimental_transcoding:
                    iterator = remux_source(raw, version=version, offset=time.monotonic() - started,
                        plex_compatible_audio=plex_compatible_audio)
                elif plex_compatible_audio and not is_http:
                    iterator = compatible_audio_source(raw)
                else:
                    iterator = raw
                version += 1
                first_at = last_at = None
                outcome = None
                healthy = False
                attempt_started = time.monotonic()
                try:
                    with anyio.fail_after(max(0, attempt_deadline - time.monotonic())) as timer[0]:
                        first = await anext(iterator)
                    first_at = last_at = time.monotonic()
                    # Bytes of the source itself: from here on the source plays.
                    registry.source_playing(claim.id)
                    if opening is not None:
                        opening.current_deadline = None
                    yield first
                    while True:
                        with anyio.fail_after(STALL_SECONDS) as timer[0]:
                            chunk = await anext(iterator)
                        last_at = time.monotonic()
                        yield chunk
                        checkpoint.tick(last_at - first_at, _with_clock('ok', clock_watch))
                        if opening is not None and opening.superseded:
                            # The newer GET plays this source too: Kodi left this one.
                            return
                except (EngineRefusedError, EngineUnavailableError, EngineStreamError, StopAsyncIteration, TimeoutError) as exc:
                    empty_start = (isinstance(exc, StopAsyncIteration) and first_at is None
                                   and content_id not in retried_empty
                                   and time.monotonic() - attempt_started < EMPTY_START_RETRY_SECONDS
                                   and not [cid for cid in candidates if cid not in attempted])
                    if empty_start:
                        # Empty at once and nothing else left to try: the same
                        # source again, not as a failure.
                        retried_empty.add(content_id)
                        attempted.discard(content_id)
                        logger.info('TV relay source %s ended empty at start; retrying it once', content_id)
                        continue
                    played = (last_at - first_at) if first_at is not None else 0.0
                    early_death = first_at is not None and played < EARLY_DEATH_SECONDS
                    record_source_failure(content_id, EARLY_DEATH_COOLDOWN_SECONDS if early_death else FAILURE_COOLDOWN_SECONDS)
                    outcome = (
                        'early_death' if early_death else
                        'stall' if first_at is not None and isinstance(exc, TimeoutError) else
                        'ended' if first_at is not None else
                        'no_data' if isinstance(exc, TimeoutError) else
                        'empty_session' if isinstance(exc, StopAsyncIteration) else
                        'engine_refused' if isinstance(exc, EngineRefusedError) else
                        'engine_unavailable' if isinstance(exc, EngineUnavailableError) else
                        'upstream_error'
                    )
                    checkpoint.finish(_with_clock(outcome, clock_watch), played)
                    if opening is not None:
                        opening.failed.append(content_id)
                    # Count delivery only through the last chunk, regardless of
                    # how the source ends. Silence before EOF/transport failure
                    # must not renew the budget any more than a stall wait does.
                    if first_at is not None:
                        healthy = last_at - first_at >= HEALTHY_SECONDS
                    # Do not include upstream exception text: it can contain URLs
                    # with credentials. Keep EOF distinct from our read deadline.
                    reason = (
                        'read_timeout' if isinstance(exc, TimeoutError) else
                        'upstream_eof' if isinstance(exc, StopAsyncIteration) else
                        'engine_refused' if isinstance(exc, EngineRefusedError) else
                        'engine_unavailable' if isinstance(exc, EngineUnavailableError) else
                        'upstream_error'
                    )
                    logger.info(
                        'TV relay source ended content_id=%s reason=%s phase=%s route=%s experimental_transcoding=%s',
                        content_id, reason, 'streaming' if first_at is not None else 'starting',
                        'http' if is_http else 'acexy' if engine is not None and engine.use_acexy else 'direct', experimental_transcoding,
                    )
                finally:
                    if outcome is None and first_at is not None:
                        # The viewer left, or a newer GET took over.
                        _record_ok(opening, content_id, tv_channel_id, last_at - first_at,
                                   outcome=_with_clock('ok', clock_watch),
                                   attempt=checkpoint.attempt)
                    with anyio.CancelScope(shield=True):
                        await iterator.aclose()
                if healthy:
                    attempted = {content_id}
                    deadline = time.monotonic() + startup_budget_seconds
                if on_source_failure is not None:
                    await on_source_failure(content_id)
                if first_at is not None and not experimental_transcoding and not switch_midstream:
                    # Headers and media have already been sent. End this response so
                    # the client reconnects to the same stable TV URL for a new source.
                    return
                if first_at is not None and switch_midstream:
                    # Carry on with the next source in the SAME response: Kodi does
                    # not reconnect, it goes back to its menu. Measured: Kodi
                    # follows a raw switch to another source (new PIDs, other
                    # resolution) as a stream change. It waits up to 60 s for data
                    # (curllowspeedtime), so a fresh startup budget fits.
                    deadline = time.monotonic() + startup_budget_seconds
                # Always use current eligibility after a failure, not the startup snapshot.
                if candidate_provider is not None:
                    with anyio.move_on_after(max(0, deadline - time.monotonic())) as scope:
                        candidates, _ = await candidate_provider()
                    if scope.cancel_called:
                        break
            # Out of candidates: the channel's sources not tried yet, offline
            # ones too, within what is left of the budget.
            if time.monotonic() >= deadline or not await take_last_resort():
                break
        raise EngineStreamError('No source could sustain TV channel playback within the recovery budget')
    finally:
        registry.close(claim.id)
        if engine is not None:
            engine.close()
